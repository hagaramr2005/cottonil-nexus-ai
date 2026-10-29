"""Print a salted PBKDF2 secret for NEXUS_USERS.  Usage: python scripts/make_user_hash.py"""
import getpass, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
from app.auth import hash_secret
print(hash_secret(getpass.getpass('Password: ')))
