import { type FormEvent, useEffect, useState } from 'react'
import {
  createCandidate,
  createSkill,
  getCandidates,
  getResumes,
  getSkills,
  savePreferences,
  reviewResume,
  uploadResume,
  type Candidate,
  type Resume,
  type Skill,
} from './api'

export default function CandidateProfiles() {
  const [candidates, setCandidates] = useState<Candidate[] | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    getCandidates(controller.signal)
      .then((items) => {
        setCandidates(items)
        setSelectedId((current) => current || items[0]?.id || null)
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Could not load candidates'))
    return () => controller.abort()
  }, [])

  async function addCandidate(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    try {
      const candidate = await createCandidate({
        display_name: String(data.get('display_name') || ''),
        headline: String(data.get('headline') || '') || undefined,
      })
      setCandidates((items) => [...(items || []), candidate])
      setSelectedId(candidate.id)
      event.currentTarget.reset()
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Could not create candidate')
    }
  }

  if (candidates === null) return <p className="panel" role="status">Loading candidate profiles…</p>

  const selected = candidates.find((candidate) => candidate.id === selectedId) || null
  return (
    <div className="profile-layout">
      <aside className="panel profile-list">
        <p className="eyebrow">Candidate knowledge base</p>
        <h2>Profiles</h2>
        {candidates.length === 0 && <p className="muted">Create the first candidate profile.</p>}
        {candidates.map((candidate) => (
          <button
            className={candidate.id === selectedId ? 'profile-choice selected' : 'profile-choice'}
            key={candidate.id}
            type="button"
            onClick={() => setSelectedId(candidate.id)}
          >
            <strong>{candidate.display_name}</strong><span>{candidate.headline || 'No headline yet'}</span>
          </button>
        ))}
        <form className="stacked-form" onSubmit={addCandidate}>
          <h3>Add candidate</h3>
          <label>Name<input name="display_name" required maxLength={255} /></label>
          <label>Headline<input name="headline" maxLength={255} /></label>
          <button type="submit">Create profile</button>
        </form>
      </aside>
      <section>
        {error && <p className="panel error-panel" role="alert">{error}</p>}
        {selected ? <CandidateWorkspace candidate={selected} onError={setError} /> : <div className="panel empty-state">Select or create a candidate.</div>}
      </section>
    </div>
  )
}

function CandidateWorkspace({ candidate, onError }: { candidate: Candidate; onError: (message: string | null) => void }) {
  const [skills, setSkills] = useState<Skill[]>([])
  const [resumes, setResumes] = useState<Resume[]>([])

  useEffect(() => {
    Promise.all([getSkills(candidate.id), getResumes(candidate.id)])
      .then(([skillItems, resumeItems]) => { setSkills(skillItems); setResumes(resumeItems) })
      .catch((reason: unknown) => onError(reason instanceof Error ? reason.message : 'Could not load profile details'))
  }, [candidate.id, onError])

  async function addSkill(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const name = String(new FormData(form).get('skill') || '')
    try { const skill = await createSkill(candidate.id, name); setSkills((items) => [...items, skill]); form.reset(); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not add skill') }
  }

  async function updatePreferences(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const data = new FormData(event.currentTarget)
    const list = (name: string) => String(data.get(name) || '').split(',').map((item) => item.trim()).filter(Boolean)
    try {
      await savePreferences(candidate.id, {
        target_roles: list('target_roles'), preferred_locations: list('locations'), remote_preferences: list('remote'),
        excluded_employers: [], excluded_titles: [], keyword_preferences: [], salary_floor: null,
        work_authorization: null, sponsorship_required: null,
      })
      onError(null)
    } catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not save preferences') }
  }

  async function addResume(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const file = (new FormData(form).get('resume') as File | null)
    if (!file || file.size === 0) return
    try { const resume = await uploadResume(candidate.id, file); setResumes((items) => [resume, ...items]); form.reset(); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not upload resume') }
  }

  async function review(item: Resume, reviewStatus: 'approved' | 'rejected', makeMaster = false) {
    const textArea = document.getElementById(`resume-text-${item.id}`) as HTMLTextAreaElement | null
    try {
      const updated = await reviewResume(candidate.id, item.id, {
        review_status: reviewStatus,
        extracted_text: textArea?.value,
        is_master: makeMaster,
      })
      setResumes((items) => items.map((resume) => resume.id === updated.id ? updated : { ...resume, is_master: makeMaster ? false : resume.is_master }))
      onError(null)
    } catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not review resume') }
  }

  return <div className="profile-sections">
    <section className="panel"><p className="eyebrow">Selected candidate</p><h2>{candidate.display_name}</h2><p>{candidate.headline}</p></section>
    <section className="panel"><h3>Search preferences</h3><form className="stacked-form" onSubmit={updatePreferences}>
      <label>Target roles, comma separated<input name="target_roles" /></label>
      <label>Preferred locations<input name="locations" /></label>
      <label>Work modes<input name="remote" placeholder="remote, hybrid" /></label>
      <p className="muted">Work authorization and sponsorship remain unset until explicitly provided.</p><button type="submit">Save preferences</button>
    </form></section>
    <section className="panel"><h3>Confirmed skills</h3><div className="tag-list">{skills.map((skill) => <span className="decision" key={skill.id}>{skill.name}</span>)}</div>
      <form className="inline-form" onSubmit={addSkill}><label>Skill<input name="skill" required /></label><button type="submit">Add</button></form></section>
    <section className="panel"><h3>Resume library</h3><p className="muted">Extracted text is unconfirmed until reviewed.</p>
      {resumes.length === 0 ? <p>No resumes uploaded.</p> : resumes.map((resume) => <article className="resume-card" key={resume.id}>
        <div className="resume-row"><strong>{resume.original_filename}</strong><span className="decision">{resume.is_master ? 'approved master' : resume.review_status}</span></div>
        <label>Extracted text<textarea id={`resume-text-${resume.id}`} defaultValue={resume.extracted_text} disabled={resume.is_master} /></label>
        {!resume.is_master && <div className="inline-form"><button type="button" onClick={() => review(resume, 'approved')}>Approve text</button><button type="button" onClick={() => review(resume, 'approved', true)}>Approve as master</button><button type="button" className="secondary" onClick={() => review(resume, 'rejected')}>Reject</button></div>}
      </article>)}
      <form className="inline-form" onSubmit={addResume}><label>PDF or DOCX<input name="resume" type="file" accept=".pdf,.docx" required /></label><button type="submit">Upload</button></form></section>
  </div>
}
