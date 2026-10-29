"""Server-enforced access control. Cookies in production; compatible bearer in development.

Audit and session state persist in the application SQLite DB (multi-process safe).
A branch-limited identity is denied from all non-scope-aware business endpoints.
"""
import base64
import hashlib
import hmac
import json
import os
import re
import secrets
import time
from fastapi import APIRouter, HTTPException, Request, Response, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from .core import db, now

router = APIRouter()
_EPHEMERAL = secrets.token_hex(32)
OPEN = ('/api/health', '/api/auth/status', '/api/auth/login')
ADMIN_ONLY = ('/api/cv/', '/api/ai/status', '/api/product/readiness', '/api/readiness', '/api/auth/audit')
READ_ONLY_POST = frozenset(('/api/copilot/chat', '/api/copilot/query', '/api/analyst/ask', '/api/analyst/llm'))
SCOPED_SAFE = frozenset(('/api/branches', '/api/sales/intelligence', '/api/sales/filters', '/api/copilot/chat', '/api/copilot/agents', '/api/copilot/status', '/api/auth/me', '/api/auth/logout'))
_COOKIE = 'nexus_session'

def enabled(): return os.getenv('NEXUS_AUTH_ENABLED','').lower() in ('1','true','yes')
def production_mode(): return os.getenv('NEXUS_ENV','development').strip().lower() == 'production'
def _secret(): return (os.getenv('NEXUS_AUTH_SECRET') or _EPHEMERAL).encode()
def _users():
    out = {}
    for item in filter(None, (os.getenv('NEXUS_USERS') or '').split(';')):
        parts = item.split(':',2)
        if len(parts) == 3 and parts[0]:
            out[parts[0]] = (parts[1],parts[2] if parts[2] in ('viewer','admin') else 'viewer')
    return out

def branch_scope(username):
    """None means organization-wide; an explicit empty assignment denies all branches."""
    for item in filter(None, os.getenv('NEXUS_BRANCH_SCOPES','').split(';')):
        user,sep,branches = item.partition(':')
        if sep and user == username:
            return tuple(sorted({s.strip() for s in branches.split(',') if s.strip()}))
    return None

def _valid_password_hash(value):
    try:
        method,iterations,salt,digest = value.split('$')
        return method == 'pbkdf2' and int(iterations)>=200000 and len(bytes.fromhex(salt))>=16 and len(bytes.fromhex(digest))==32
    except (ValueError,TypeError):return False

def validate_production_config():
    if not production_mode():return
    problems=[]
    if not enabled(): problems.append('NEXUS_AUTH_ENABLED must be 1')
    secret=os.getenv('NEXUS_AUTH_SECRET','')
    if len(secret)<48 or secret.lower().startswith(('replace','change','test')):problems.append('NEXUS_AUTH_SECRET must be unique and >=48 characters')
    users=_users()
    if not users or not any(role=='admin' for _,role in users.values()):problems.append('NEXUS_USERS must include an admin')
    if any(not _valid_password_hash(stored) for stored,_ in users.values()):problems.append('NEXUS_USERS must contain PBKDF2 hashes >=200000 iterations')
    origins=[v.strip() for v in os.getenv('NEXUS_CORS','').split(',') if v.strip()]
    if not origins or any(not re.fullmatch(r'https://[A-Za-z0-9.-]+(?::\d+)?',o) for o in origins):problems.append('NEXUS_CORS must list explicit HTTPS origins')
    try:
        if not 1<=int(os.getenv('NEXUS_AUTH_TTL_MIN','480'))<=120:problems.append('NEXUS_AUTH_TTL_MIN must be 1..120')
    except ValueError:problems.append('NEXUS_AUTH_TTL_MIN must be integer')
    if problems:raise RuntimeError('Unsafe production configuration: '+'; '.join(problems))

def hash_secret(password,iterations=200_000):
    salt=secrets.token_bytes(16)
    return f'pbkdf2${iterations}${salt.hex()}${hashlib.pbkdf2_hmac("sha256",password.encode(),salt,iterations).hex()}'
def _verify(password,stored):
    if stored.startswith('pbkdf2$'):
        try:
            _,it,salt,h=stored.split('$')
            return hmac.compare_digest(hashlib.pbkdf2_hmac('sha256',password.encode(),bytes.fromhex(salt),int(it)).hex(),h)
        except Exception:return False
    return not production_mode() and hmac.compare_digest(password.encode(),stored.encode())
def _b64(blob):return base64.urlsafe_b64encode(blob).decode().rstrip('=')
def _hash(value):return hashlib.sha256(value.encode()).hexdigest()
def _ttl():return int(os.getenv('NEXUS_AUTH_TTL_MIN','480'))*60

def issue(user,role):
    sid=secrets.token_urlsafe(32)
    csrf=secrets.token_urlsafe(32)
    exp=int(time.time())+_ttl()
    body=_b64(json.dumps({'u':user,'r':role,'exp':exp,'sid':sid}).encode())
    token=body+'.'+_b64(hmac.new(_secret(),body.encode(),hashlib.sha256).digest())
    c=db()
    try:
        c.execute('INSERT INTO auth_sessions VALUES (?,?,?,?,?,?,?)',(_hash(sid),user,role,exp,None,_hash(csrf),now()))
        c.commit()
    finally:c.close()
    return token,csrf

def parse(token):
    try:
        body,sig=token.split('.')
        if not hmac.compare_digest(sig,_b64(hmac.new(_secret(),body.encode(),hashlib.sha256).digest())):return None
        data=json.loads(base64.urlsafe_b64decode(body+'='*(-len(body)%4)))
        if data.get('exp',0)<=time.time() or not isinstance(data.get('sid'),str):return None
        c=db()
        try:record=c.execute('SELECT username,role,expires_at,revoked_at,csrf_hash FROM auth_sessions WHERE sid_hash=?',(_hash(data['sid']),)).fetchone()
        finally:c.close()
        if not record or record['revoked_at'] or record['expires_at']<=time.time():return None
        if record['username']!=data.get('u') or record['role']!=data.get('r'):return None
        if _users().get(data['u'],(None,None))[1]!=data['r']:return None
        return {**data,'csrf_hash':record['csrf_hash']}
    except Exception:return None

def audit(actor,action,method,path,status,scope=None,details=None):
    """Never log secrets, passwords, token values or unbounded user content."""
    c=db()
    try:
        c.execute('INSERT INTO audit_log(occurred_at,actor,action,method,path,status,branch_scope,details) VALUES (?,?,?,?,?,?,?,?)',
            (now(),str(actor)[:100],str(action)[:80],str(method)[:12],str(path)[:250],int(status),json.dumps(scope) if scope is not None else None,json.dumps(details or {})))
        c.commit()
    finally:c.close()

class Login(BaseModel):
    username:str
    password:str

@router.get('/api/auth/status')
def status():return {'required':enabled()}

@router.post('/api/auth/login')
def login(body:Login,request:Request,response:Response):
    if production_mode():validate_production_config()
    if not enabled():return {'token':'','role':'admin','auth_required':False}
    username=body.username[:100]
    # Persist failed attempts across workers, bound to a hashed remote address.
    source=_hash((request.client.host if request.client else 'unknown') + os.getenv('NEXUS_AUTH_SECRET',_EPHEMERAL))
    c=db()
    try:
        cutoff=int(time.time())-900
        failures=c.execute('SELECT COUNT(*) FROM auth_attempts WHERE username=? AND source_hash=? AND attempted_at>? AND successful=0',(username,source,cutoff)).fetchone()[0]
        c.execute('DELETE FROM auth_attempts WHERE attempted_at<?',(int(time.time())-86400,));c.commit()
    finally:c.close()
    if failures>=6:
        audit(username,'auth_blocked','POST','/api/auth/login',429)
        raise HTTPException(429,'Too many attempts; try again later')
    user=_users().get(username)
    valid=_verify(body.password,user[0] if user else hash_secret('dummy-password'))
    if not user or not valid:
        c=db()
        try:c.execute('INSERT INTO auth_attempts VALUES (?,?,?,0)',(username,source,int(time.time())));c.commit()
        finally:c.close()
        audit(username,'login_failed','POST','/api/auth/login',401)
        raise HTTPException(401,'invalid credentials')
    c=db()
    try:c.execute('DELETE FROM auth_attempts WHERE username=? AND source_hash=?',(username,source));c.commit()
    finally:c.close()
    token,csrf=issue(username,user[1])
    response.set_cookie(_COOKIE,token,httponly=True,secure=production_mode(),samesite='strict',path='/api',max_age=_ttl())
    audit(username,'login_success','POST','/api/auth/login',200,branch_scope(username))
    # No bearer token in production response or browser storage.
    return {'token':'' if production_mode() else token,'role':user[1],'csrf':csrf,'auth_required':True}

@router.get('/api/auth/me')
def me(request:Request):
    claims=getattr(request.state,'claims',None)
    csrf=secrets.token_urlsafe(32)
    c=db()
    try:c.execute('UPDATE auth_sessions SET csrf_hash=? WHERE sid_hash=?',(_hash(csrf),_hash(claims['sid'])));c.commit()
    finally:c.close()
    return {'username':claims['u'],'role':claims['r'],'branch_scope':branch_scope(claims['u']),'csrf':csrf}

@router.post('/api/auth/logout')
def logout(request:Request,response:Response):
    claims=getattr(request.state,'claims',None)
    c=db()
    try:c.execute('UPDATE auth_sessions SET revoked_at=? WHERE sid_hash=?',(now(),_hash(claims['sid'])));c.commit()
    finally:c.close()
    response.delete_cookie(_COOKIE,path='/api',samesite='strict',secure=production_mode(),httponly=True)
    return {'logged_out':True}

@router.get('/api/auth/audit')
def audit_view(limit:int=100):
    if not 1<=limit<=500:raise HTTPException(422,'limit must be 1..500')
    c=db()
    try:return [dict(r) for r in c.execute('SELECT * FROM audit_log ORDER BY id DESC LIMIT ?',(limit,))]
    finally:c.close()

def require_write(request:Request,x_nexus_token:str|None=Header(default=None)):
    if enabled():
        claims=getattr(request.state,'claims',None)
        if not claims or claims['r']!='admin' or branch_scope(claims['u']) is not None:raise HTTPException(403,'Administrative write access required')
        return
    if production_mode():raise HTTPException(503,'Authentication is required in production')
    expected=os.getenv('NEXUS_WRITE_TOKEN')
    if not expected or not x_nexus_token or not hmac.compare_digest(expected,x_nexus_token):raise HTTPException(403,'Write access not configured')

async def middleware(request,call_next):
    path=request.url.path
    if production_mode():validate_production_config()
    if production_mode() and path in ('/docs','/redoc','/openapi.json'):
        return _secure(JSONResponse({'detail':'Not found'},status_code=404),path)
    claims=None;cookie_auth=False;scope=None
    if enabled() and path.startswith('/api/') and path not in OPEN and request.method!='OPTIONS':
        header=request.headers.get('authorization','')
        bearer=header[7:] if header.lower().startswith('bearer ') else ''
        cookie=request.cookies.get(_COOKIE,'')
        cookie_auth=not bool(bearer) and bool(cookie)
        token=bearer or cookie
        claims=parse(token) if token else None
        if not claims:
            audit('anonymous','access_denied',request.method,path,401)
            return _secure(JSONResponse({'detail':'authentication required'},status_code=401),path)
        request.state.claims=claims
        scope=branch_scope(claims['u'])
        if (path.startswith(ADMIN_ONLY) and claims['r']!='admin') or (request.method in ('POST','PATCH','PUT','DELETE') and path not in READ_ONLY_POST and path!='/api/auth/logout' and claims['r']!='admin'):
            audit(claims['u'],'access_denied',request.method,path,403,scope)
            return _secure(JSONResponse({'detail':'role does not allow this operation'},status_code=403),path)
        if scope is not None and path not in SCOPED_SAFE:
            audit(claims['u'],'scope_denied',request.method,path,403,scope)
            return _secure(JSONResponse({'detail':'endpoint does not support branch-scoped access'},status_code=403),path)
        if cookie_auth and request.method in ('POST','PUT','PATCH','DELETE') and path not in READ_ONLY_POST:
            csrf=request.headers.get('x-nexus-csrf','')
            if not csrf or not hmac.compare_digest(claims['csrf_hash'],_hash(csrf)):
                audit(claims['u'],'csrf_denied',request.method,path,403,scope)
                return _secure(JSONResponse({'detail':'CSRF token required'},status_code=403),path)
        if production_mode() and cookie_auth:
            allowed={x.strip() for x in os.getenv('NEXUS_CORS','').split(',')}
            origin=request.headers.get('origin')
            if origin and origin not in allowed:
                audit(claims['u'],'origin_denied',request.method,path,403,scope)
                return _secure(JSONResponse({'detail':'origin not allowed'},status_code=403),path)
    response=await call_next(request)
    if claims and (path.startswith('/api/reports/') or request.method in ('PATCH','PUT','DELETE') or (request.method=='POST' and path not in READ_ONLY_POST)):
        action='export' if path.startswith('/api/reports/') else 'sensitive_action'
        audit(claims['u'],action,request.method,path,response.status_code,scope)
    return _secure(response,path)

def _secure(response,path):
    response.headers['X-Content-Type-Options']='nosniff'
    response.headers['Referrer-Policy']='no-referrer'
    response.headers['X-Frame-Options']='DENY'
    response.headers['Cache-Control']='no-store' if path.startswith('/api/') else 'no-cache'
    response.headers['Permissions-Policy']='camera=(), microphone=(), geolocation=()'
    response.headers['Content-Security-Policy']=("default-src 'self'; base-uri 'self'; object-src 'none'; frame-ancestors 'none'; "
        "form-action 'self'; img-src 'self' data: blob:; font-src 'self' data:; "
        "style-src 'self' 'unsafe-inline'; script-src 'self'; connect-src 'self'")
    if production_mode():response.headers['Strict-Transport-Security']='max-age=31536000; includeSubDomains'
    return response
