export interface Job {
  id: number
  company: string
  title: string
  location: string | null
  remote_type: string | null
  url: string
  fit_score: number
  score_reason: string | null
  decision: string
  status: string
}

export interface AnalyticsSummary {
  total_jobs: number
  excellent_matches: number
  approved: number
  average_score: number
}

export interface Candidate {
  id: string
  owner_id: string
  display_name: string
  headline: string | null
  summary: string | null
  years_experience: number | null
  is_archived: boolean
}

export interface Skill {
  id: string
  name: string
  years_experience: number | null
  confirmed: boolean
  source: string
}

export interface Resume {
  id: string
  original_filename: string
  media_type: string
  byte_size: number
  extracted_text: string
  review_status: string
  version_number: number
  is_master: boolean
  is_archived: boolean
}

export interface CurrentUser { id: string; email: string }

function csrfToken(): string | null {
  const prefix = 'jobagent_csrf='
  const cookie = document.cookie.split('; ').find((item) => item.startsWith(prefix))
  return cookie ? decodeURIComponent(cookie.slice(prefix.length)) : null
}

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { headers: { Accept: 'application/json' }, signal, credentials: 'include' })
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

async function sendJson<T>(path: string, method: string, body: unknown): Promise<T> {
  const csrf = csrfToken()
  const response = await fetch(path, {
    method,
    headers: { Accept: 'application/json', 'Content-Type': 'application/json', ...(csrf ? { 'X-CSRF-Token': csrf } : {}) },
    body: JSON.stringify(body),
    credentials: 'include',
  })
  if (!response.ok) throw new Error(`Request failed (${response.status})`)
  return (await response.json()) as T
}

export function getCurrentUser(signal?: AbortSignal): Promise<CurrentUser> {
  return getJson<CurrentUser>('/api/v1/auth/me', signal)
}

export function browserLogin(email: string, password: string): Promise<{ user: CurrentUser }> {
  return sendJson('/api/v1/auth/browser-login', 'POST', { email, password })
}

export async function browserLogout(): Promise<void> {
  const csrf = csrfToken()
  const response = await fetch('/api/v1/auth/logout', {
    method: 'POST', credentials: 'include', headers: csrf ? { 'X-CSRF-Token': csrf } : {},
  })
  if (!response.ok) throw new Error(`Logout failed (${response.status})`)
}

export function getJobs(signal?: AbortSignal): Promise<Job[]> {
  return getJson<Job[]>('/jobs', signal)
}

export function getSummary(signal?: AbortSignal): Promise<AnalyticsSummary> {
  return getJson<AnalyticsSummary>('/analytics/summary', signal)
}

export function getCandidates(signal?: AbortSignal): Promise<Candidate[]> {
  return getJson<Candidate[]>('/api/v1/candidates', signal)
}

export function createCandidate(body: { display_name: string; headline?: string }): Promise<Candidate> {
  return sendJson<Candidate>('/api/v1/candidates', 'POST', body)
}

export function getSkills(candidateId: string): Promise<Skill[]> {
  return getJson<Skill[]>(`/api/v1/candidates/${candidateId}/skills`)
}

export function createSkill(candidateId: string, name: string): Promise<Skill> {
  return sendJson<Skill>(`/api/v1/candidates/${candidateId}/skills`, 'POST', { name })
}

export function savePreferences(candidateId: string, body: unknown): Promise<unknown> {
  return sendJson(`/api/v1/candidates/${candidateId}/preferences`, 'PUT', body)
}

export function getResumes(candidateId: string): Promise<Resume[]> {
  return getJson<Resume[]>(`/api/v1/candidates/${candidateId}/resumes`)
}

export async function uploadResume(candidateId: string, file: File): Promise<Resume> {
  const body = new FormData()
  body.append('file', file)
  const csrf = csrfToken()
  const response = await fetch(`/api/v1/candidates/${candidateId}/resumes`, {
    method: 'POST', body, credentials: 'include', headers: csrf ? { 'X-CSRF-Token': csrf } : {},
  })
  if (!response.ok) {
    const payload = (await response.json().catch(() => null)) as { error?: { message?: string } } | null
    throw new Error(payload?.error?.message || `Upload failed (${response.status})`)
  }
  return (await response.json()) as Resume
}
