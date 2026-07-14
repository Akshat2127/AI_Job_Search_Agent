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

async function getJson<T>(path: string, signal?: AbortSignal): Promise<T> {
  const response = await fetch(path, { headers: { Accept: 'application/json' }, signal })
  if (!response.ok) {
    throw new Error(`Request failed (${response.status})`)
  }
  return (await response.json()) as T
}

export function getJobs(signal?: AbortSignal): Promise<Job[]> {
  return getJson<Job[]>('/jobs', signal)
}

export function getSummary(signal?: AbortSignal): Promise<AnalyticsSummary> {
  return getJson<AnalyticsSummary>('/analytics/summary', signal)
}
