import { useEffect, useState } from 'react'
import { getJobs, getSummary, type AnalyticsSummary, type Job } from './api'
import CandidateProfiles from './CandidateProfiles'
import AuthControls from './AuthControls'
import './styles.css'

type LoadState =
  | { status: 'loading' }
  | { status: 'error'; message: string }
  | { status: 'ready'; jobs: Job[]; summary: AnalyticsSummary }

const initialState: LoadState = { status: 'loading' }

export default function App() {
  const [state, setState] = useState<LoadState>(initialState)
  const [reloadKey, setReloadKey] = useState(0)
  const [view, setView] = useState<'jobs' | 'profiles'>('jobs')

  useEffect(() => {
    const controller = new AbortController()

    Promise.all([getJobs(controller.signal), getSummary(controller.signal)])
      .then(([jobs, summary]) => setState({ status: 'ready', jobs, summary }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          setState({
            status: 'error',
            message: error instanceof Error ? error.message : 'An unexpected error occurred',
          })
        }
      })

    return () => controller.abort()
  }, [reloadKey])

  function reload() {
    setState({ status: 'loading' })
    setReloadKey((value) => value + 1)
  }

  return (
    <div className="app-shell">
      <header className="topbar">
        <div>
          <p className="eyebrow">Human-controlled job search</p>
          <h1>JobAgent AI</h1>
        </div>
        <nav className="main-nav" aria-label="Primary navigation">
          <button type="button" className={view === 'jobs' ? 'active' : ''} onClick={() => setView('jobs')}>Jobs</button>
          <button type="button" className={view === 'profiles' ? 'active' : ''} onClick={() => setView('profiles')}>Candidates</button>
          <a href="http://localhost:8000/docs">API documentation</a>
          <AuthControls />
        </nav>
      </header>

      <main>
        {view === 'profiles' ? <CandidateProfiles /> : <>
        {state.status === 'loading' && <p role="status" className="panel">Loading job workspace…</p>}

        {state.status === 'error' && (
          <section role="alert" className="panel error-panel">
            <h2>Could not load the workspace</h2>
            <p>{state.message}</p>
            <button type="button" onClick={reload}>
              Try again
            </button>
          </section>
        )}

        {state.status === 'ready' && (
          <>
            <section className="metrics" aria-label="Job summary">
              <Metric label="Discovered jobs" value={state.summary.total_jobs} />
              <Metric label="Excellent matches" value={state.summary.excellent_matches} />
              <Metric label="Approved" value={state.summary.approved} />
              <Metric label="Average score" value={state.summary.average_score} />
            </section>

            <section className="panel">
              <div className="section-heading">
                <div>
                  <p className="eyebrow">Review queue</p>
                  <h2>Current jobs</h2>
                </div>
                <button type="button" onClick={reload}>
                  Refresh
                </button>
              </div>

              {state.jobs.length === 0 ? (
                <p className="empty-state">No jobs have been discovered yet. Import the sample CSV or configure a source.</p>
              ) : (
                <div className="table-scroll">
                  <table>
                    <thead>
                      <tr><th>Score</th><th>Role</th><th>Company</th><th>Location</th><th>Decision</th></tr>
                    </thead>
                    <tbody>
                      {state.jobs.map((job) => (
                        <tr key={job.id}>
                          <td><span className="score">{job.fit_score}</span></td>
                          <td><a href={job.url} target="_blank" rel="noreferrer">{job.title}</a></td>
                          <td>{job.company}</td>
                          <td>{job.location || job.remote_type || 'Not provided'}</td>
                          <td><span className="decision">{job.decision}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </section>
          </>
        )}
        </>}
      </main>
    </div>
  )
}

function Metric({ label, value }: { label: string; value: number }) {
  return <article className="metric"><span>{label}</span><strong>{value}</strong></article>
}
