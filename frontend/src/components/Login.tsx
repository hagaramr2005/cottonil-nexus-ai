import React, { useState } from 'react'
import { Eye, EyeOff } from 'lucide-react'
import { Lang, t, LOGO_SRC } from '../i18n'
import { LangSwitch } from './ui'
import { setCsrf } from '../authSession'

export function Login({ lang, setLang, onSignedIn }: { lang: Lang; setLang: (l: Lang) => void; onSignedIn: (role: string) => void }) {
  const [u, setU] = useState(''), [p, setP] = useState(''), [show, setShow] = useState(false)
  const [errs, setErrs] = useState<{ u?: string; p?: string; form?: string }>({}), [busy, setBusy] = useState(false)
  const submit = async (e: React.FormEvent) => {
    e.preventDefault()
    const next: typeof errs = {}
    if (!u.trim()) next.u = t(lang, 'lg_req_user')
    if (!p) next.p = t(lang, 'lg_req_pass')
    setErrs(next)
    if (next.u || next.p) return
    setBusy(true)
    try {
      const r = await fetch('/api/auth/login', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username: u.trim(), password: p }) })
      if (r.status === 401) setErrs({ form: t(lang, 'lg_bad') })
      else if (!r.ok) setErrs({ form: t(lang, 'lg_down') })
      else { const data = await r.json(); setCsrf(data.csrf || ''); onSignedIn('session:' + data.role) }
    } catch { setErrs({ form: t(lang, 'lg_down') }) } finally { setBusy(false) }
  }
  return (
    <div className="login">
      <section className="loginBrand" aria-hidden={false}>
        {/* logo is navy on transparent: shown on a white plate, never recolored */}
        <div className="logoplate"><img src={LOGO_SRC} alt="Cottonil" width={345} height={50} /></div>
        <div><h1>{t(lang, 'lg_welcome')}</h1><p>{t(lang, 'lg_desc')}</p></div>
        <small style={{ opacity: .7 }}>{t(lang, 'app_tag')}</small>
      </section>
      <section className="loginPane">
        <div className="loginCard">
          <div className="sectionhead"><span className="mobilelogo"><img src={LOGO_SRC} alt="Cottonil" width={345} height={50} /></span><LangSwitch lang={lang} setLang={setLang} /></div>
          <h2>{t(lang, 'lg_signin')}</h2>
          <form onSubmit={submit} noValidate>
            {errs.form && <div role="alert" className="error">{errs.form}</div>}
            <label>{t(lang, 'lg_user')}
              <input value={u} onChange={(e) => setU(e.target.value)} autoComplete="username" aria-invalid={!!errs.u} aria-describedby={errs.u ? 'e-u' : undefined} dir="ltr" style={{ textAlign: 'start' }} />
              {errs.u && <span id="e-u" className="fielderr">{errs.u}</span>}
            </label>
            <label>{t(lang, 'lg_pass')}
              <span className="pwwrap">
                <input type={show ? 'text' : 'password'} value={p} onChange={(e) => setP(e.target.value)} autoComplete="current-password" aria-invalid={!!errs.p} aria-describedby={errs.p ? 'e-p' : undefined} dir="ltr" style={{ textAlign: 'start' }} />
                <button type="button" onClick={() => setShow(!show)} aria-label={t(lang, show ? 'lg_hide' : 'lg_show')}>{show ? <EyeOff size={18} /> : <Eye size={18} />}</button>
              </span>
              {errs.p && <span id="e-p" className="fielderr">{errs.p}</span>}
            </label>
            <button className="primary" type="submit" disabled={busy} style={{ justifyContent: 'center' }}>{busy ? t(lang, 'lg_busy') : t(lang, 'lg_submit')}</button>
          </form>
        </div>
      </section>
    </div>
  )
}
