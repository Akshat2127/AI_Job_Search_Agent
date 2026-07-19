import { type FormEvent, useEffect, useState } from 'react'
import { browserLogin, browserLogout, getCurrentUser, registerAccount, type CurrentUser } from './api'

export default function AuthControls({ onSessionChange }: { onSessionChange: (user: CurrentUser | null) => void }) {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getCurrentUser(controller.signal)
      .then((current) => { setUser(current); onSessionChange(current) })
      .catch(() => { setUser(null); onSessionChange(null) })
      .finally(() => setLoading(false))
    return () => controller.abort()
  }, [onSessionChange])

  async function authenticate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const email = String(data.get('email') || '')
    const password = String(data.get('password') || '')
    try {
      if (mode === 'register') await registerAccount(email, password)
      const result = await browserLogin(email, password)
      setUser(result.user); onSessionChange(result.user); setError(null)
    } catch (reason) { setError(reason instanceof Error ? reason.message : mode === 'register' ? 'Account creation failed' : 'Sign in failed') }
  }

  async function logout() {
    try { await browserLogout(); setUser(null); onSessionChange(null); setError(null) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign out failed') }
  }

  if (loading) return <span className="auth-status">Checking session…</span>
  if (user) return <div className="auth-status"><span>{user.email}</span><button type="button" onClick={logout}>Sign out</button></div>
  return <div className="auth-entry">
    <form className="auth-form" onSubmit={authenticate}>
      <label>Email<input name="email" type="email" required /></label>
      <label>Password<input name="password" type="password" required minLength={12} /></label>
      <button type="submit">{mode === 'register' ? 'Create account' : 'Sign in'}</button>
    </form>
    <button className="auth-switch" type="button" onClick={() => { setMode((value) => value === 'login' ? 'register' : 'login'); setError(null) }}>
      {mode === 'login' ? 'Create account' : 'Use existing account'}
    </button>
    {error && <span role="alert">{error}</span>}
  </div>
}
