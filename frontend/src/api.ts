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
  label: string | null
  version_number: number
  is_master: boolean
  is_archived: boolean
}

export interface CurrentUser { id: string; email: string }
export interface Experience { id: string; employer: string; title: string; start_date: string | null; end_date: string | null; confirmed: boolean }
export interface Project { id: string; name: string; role: string | null; confirmed: boolean }
export interface Education { id: string; institution: string; degree: string | null; confirmed: boolean }
export interface Certification { id: string; name: string; issuer: string | null; confirmed: boolean }
export interface ApplicationAnswer { id: string; question_key: string; answer: string; sensitive: boolean; require_confirmation_each_time: boolean }
export interface AuditEvent { id: string; action: string; entity_type: string; entity_id: string | null; created_at: string }
export interface IngestionRun {
  id: string
  provider: 'fixture' | 'greenhouse' | 'lever'
  source_key: string
  status: 'running' | 'completed' | 'failed'
  discovered_count: number
  created_count: number
  duplicate_count: number
  error_code: string | null
  error_message: string | null
  started_at: string
}
export interface CandidateSource {
  id: string
  provider: 'greenhouse' | 'lever'
  source_key: string
  label: string | null
  is_enabled: boolean
  last_run_at: string | null
}
export interface CandidateJob {
  id: number
  company: string
  title: string
  location: string | null
  url: string
  source: string | null
  description: string | null
  decision: 'new' | 'approve' | 'maybe' | 'skip'
  status: string
}
export interface CandidateJobPage { items: CandidateJob[]; total: number; limit: number; offset: number }
export interface JobProvenance { id: string; provider: string; source_key: string; external_id: string; source_url: string; first_seen_at: string; last_seen_at: string }

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

export function registerAccount(email: string, password: string): Promise<CurrentUser> {
  return sendJson('/api/v1/auth/register', 'POST', { email, password })
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

export function getExperiences(candidateId: string): Promise<Experience[]> { return getJson(`/api/v1/candidates/${candidateId}/experiences`) }
export function createExperience(candidateId: string, body: { employer: string; title: string }): Promise<Experience> { return sendJson(`/api/v1/candidates/${candidateId}/experiences`, 'POST', body) }
export function getProjects(candidateId: string): Promise<Project[]> { return getJson(`/api/v1/candidates/${candidateId}/projects`) }
export function createProject(candidateId: string, body: { name: string; role?: string }): Promise<Project> { return sendJson(`/api/v1/candidates/${candidateId}/projects`, 'POST', body) }
export function getEducation(candidateId: string): Promise<Education[]> { return getJson(`/api/v1/candidates/${candidateId}/education`) }
export function createEducation(candidateId: string, body: { institution: string; degree?: string }): Promise<Education> { return sendJson(`/api/v1/candidates/${candidateId}/education`, 'POST', body) }
export function getCertifications(candidateId: string): Promise<Certification[]> { return getJson(`/api/v1/candidates/${candidateId}/certifications`) }
export function createCertification(candidateId: string, body: { name: string; issuer?: string }): Promise<Certification> { return sendJson(`/api/v1/candidates/${candidateId}/certifications`, 'POST', body) }
export function getAnswers(candidateId: string): Promise<ApplicationAnswer[]> { return getJson(`/api/v1/candidates/${candidateId}/answers`) }
export function saveAnswer(candidateId: string, body: { question_key: string; answer: string; sensitive: boolean }): Promise<ApplicationAnswer> { return sendJson(`/api/v1/candidates/${candidateId}/answers`, 'PUT', body) }
export function getAudit(candidateId: string): Promise<AuditEvent[]> { return getJson(`/api/v1/audit?candidate_id=${encodeURIComponent(candidateId)}`) }
export function getIngestionRuns(candidateId: string): Promise<IngestionRun[]> { return getJson(`/api/v1/candidates/${candidateId}/ingestion-runs`) }
export function executeConnector(candidateId: string, provider: 'greenhouse' | 'lever', sourceKey: string): Promise<IngestionRun> {
  return sendJson(`/api/v1/candidates/${candidateId}/connector-runs`, 'POST', { provider, source_key: sourceKey })
}
export function getSources(candidateId: string): Promise<CandidateSource[]> { return getJson(`/api/v1/candidates/${candidateId}/sources`) }
export function createSource(candidateId: string, body: { provider: 'greenhouse' | 'lever'; source_key: string; label?: string }): Promise<CandidateSource> { return sendJson(`/api/v1/candidates/${candidateId}/sources`, 'POST', body) }
export function updateSource(candidateId: string, sourceId: string, body: { is_enabled?: boolean; label?: string }): Promise<CandidateSource> { return sendJson(`/api/v1/candidates/${candidateId}/sources/${sourceId}`, 'PATCH', body) }
export function runSource(candidateId: string, sourceId: string): Promise<IngestionRun> { return sendJson(`/api/v1/candidates/${candidateId}/sources/${sourceId}/run`, 'POST', {}) }
export function getCandidateJobs(candidateId: string, options: { q?: string; decision?: string; limit?: number; offset?: number } = {}): Promise<CandidateJobPage> {
  const query = new URLSearchParams()
  if (options.q) query.set('q', options.q)
  if (options.decision) query.set('decision', options.decision)
  query.set('limit', String(options.limit || 25)); query.set('offset', String(options.offset || 0))
  return getJson(`/api/v1/candidates/${candidateId}/jobs?${query}`)
}
export function reviewCandidateJob(candidateId: string, jobId: number, decision: CandidateJob['decision']): Promise<CandidateJob> { return sendJson(`/api/v1/candidates/${candidateId}/jobs/${jobId}/decision`, 'PATCH', { decision }) }
export function getJobProvenance(candidateId: string, jobId: number): Promise<JobProvenance[]> { return getJson(`/api/v1/candidates/${candidateId}/jobs/${jobId}/provenance`) }

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

export function reviewResume(
  candidateId: string,
  resumeId: string,
  body: { review_status: string; extracted_text?: string; is_master?: boolean; is_archived?: boolean; label?: string },
): Promise<Resume> {
  return sendJson<Resume>(`/api/v1/candidates/${candidateId}/resumes/${resumeId}`, 'PATCH', body)
}
