import { type FormEvent, useEffect, useState } from 'react'
import { browserLogin, browserLogout, getCurrentUser, type CurrentUser } from './api'

export default function AuthControls() {
  const [user, setUser] = useState<CurrentUser | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getCurrentUser(controller.signal).then(setUser).catch(() => setUser(null)).finally(() => setLoading(false))
    return () => controller.abort()
  }, [])

  async function login(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    try {
      const result = await browserLogin(String(data.get('email') || ''), String(data.get('password') || ''))
      setUser(result.user); setError(null)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign in failed') }
  }

  async function logout() {
    try { await browserLogout(); setUser(null); setError(null) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Sign out failed') }
  }

  if (loading) return <span className="auth-status">Checking session…</span>
  if (user) return <div className="auth-status"><span>{user.email}</span><button type="button" onClick={logout}>Sign out</button></div>
  return <form className="auth-form" onSubmit={login}>
    <label>Email<input name="email" type="email" required /></label>
    <label>Password<input name="password" type="password" required minLength={12} /></label>
    <button type="submit">Sign in</button>{error && <span role="alert">{error}</span>}
  </form>
}
