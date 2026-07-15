import { type FormEvent, useEffect, useState } from 'react'
import {
  createCandidate,
  createCertification,
  createEducation,
  createExperience,
  createProject,
  createSkill,
  createSource,
  getAnswers,
  getAudit,
  getCandidates,
  getCertifications,
  getEducation,
  getExperiences,
  getCandidateJobs,
  getIngestionRuns,
  getJobProvenance,
  getProjects,
  getResumes,
  getSkills,
  getSources,
  savePreferences,
  reviewResume,
  reviewCandidateJob,
  runSource,
  saveAnswer,
  uploadResume,
  updateSource,
  type Candidate,
  type CandidateJob,
  type CandidateJobPage,
  type CandidateSource,
  type ApplicationAnswer,
  type AuditEvent,
  type Certification,
  type Education,
  type Experience,
  type IngestionRun,
  type JobProvenance,
  type Project,
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
  const [experiences, setExperiences] = useState<Experience[]>([])
  const [projects, setProjects] = useState<Project[]>([])
  const [education, setEducation] = useState<Education[]>([])
  const [certifications, setCertifications] = useState<Certification[]>([])
  const [answers, setAnswers] = useState<ApplicationAnswer[]>([])
  const [activity, setActivity] = useState<AuditEvent[]>([])
  const [ingestionRuns, setIngestionRuns] = useState<IngestionRun[]>([])
  const [sources, setSources] = useState<CandidateSource[]>([])
  const [jobPage, setJobPage] = useState<CandidateJobPage>({ items: [], total: 0, limit: 25, offset: 0 })
  const [jobQuery, setJobQuery] = useState('')
  const [provenance, setProvenance] = useState<Record<number, JobProvenance[]>>({})
  const [connectorRunning, setConnectorRunning] = useState(false)

  useEffect(() => {
    Promise.all([getSkills(candidate.id), getResumes(candidate.id), getExperiences(candidate.id), getProjects(candidate.id), getEducation(candidate.id), getCertifications(candidate.id), getAnswers(candidate.id), getAudit(candidate.id), getIngestionRuns(candidate.id), getSources(candidate.id), getCandidateJobs(candidate.id)])
      .then(([skillItems, resumeItems, experienceItems, projectItems, educationItems, certificationItems, answerItems, auditItems, runItems, sourceItems, jobs]) => {
        setSkills(skillItems); setResumes(resumeItems); setExperiences(experienceItems); setProjects(projectItems)
        setEducation(educationItems); setCertifications(certificationItems); setAnswers(answerItems); setActivity(auditItems); setIngestionRuns(runItems); setSources(sourceItems); setJobPage(jobs)
      })
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
    const labelInput = document.getElementById(`resume-label-${item.id}`) as HTMLInputElement | null
    try {
      const updated = await reviewResume(candidate.id, item.id, {
        review_status: reviewStatus,
        extracted_text: textArea?.value,
        label: labelInput?.value || undefined,
        is_master: makeMaster,
      })
      setResumes((items) => items.map((resume) => resume.id === updated.id ? updated : { ...resume, is_master: makeMaster ? false : resume.is_master }))
      onError(null)
    } catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not review resume') }
  }

  async function addKnowledge(event: FormEvent<HTMLFormElement>, kind: string) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const primary = String(data.get('primary') || '')
    const secondary = String(data.get('secondary') || '')
    try {
      if (kind === 'experience') { const item = await createExperience(candidate.id, { employer: primary, title: secondary }); setExperiences((items) => [...items, item]) }
      if (kind === 'project') { const item = await createProject(candidate.id, { name: primary, role: secondary || undefined }); setProjects((items) => [...items, item]) }
      if (kind === 'education') { const item = await createEducation(candidate.id, { institution: primary, degree: secondary || undefined }); setEducation((items) => [...items, item]) }
      if (kind === 'certification') { const item = await createCertification(candidate.id, { name: primary, issuer: secondary || undefined }); setCertifications((items) => [...items, item]) }
      form.reset(); onError(null)
    } catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not save profile item') }
  }

  async function addAnswer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    try {
      const answer = await saveAnswer(candidate.id, {
        question_key: String(data.get('question_key') || ''), answer: String(data.get('answer') || ''), sensitive: data.get('sensitive') === 'on',
      })
      setAnswers((items) => [...items.filter((item) => item.question_key !== answer.question_key), answer])
      form.reset(); onError(null)
    } catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not save answer') }
  }

  async function addSource(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const form = event.currentTarget
    const data = new FormData(form)
    const provider = String(data.get('provider')) as 'greenhouse' | 'lever'
    const sourceKey = String(data.get('source_key') || '')
    try {
      const source = await createSource(candidate.id, { provider, source_key: sourceKey, label: String(data.get('label') || '') || undefined })
      setSources((items) => [...items, source]); form.reset()
      onError(null)
    } catch (reason) {
      onError(reason instanceof Error ? reason.message : 'Could not save source')
    }
  }

  async function executeSavedSource(source: CandidateSource) {
    setConnectorRunning(true)
    try {
      const run = await runSource(candidate.id, source.id)
      setIngestionRuns((items) => [run, ...items])
      setSources((items) => items.map((item) => item.id === source.id ? { ...item, last_run_at: run.started_at } : item))
      setJobPage(await getCandidateJobs(candidate.id, { q: jobQuery }))
      onError(null)
    } catch (reason) {
      getIngestionRuns(candidate.id).then(setIngestionRuns).catch(() => undefined)
      onError(reason instanceof Error ? reason.message : 'Connector execution failed')
    } finally { setConnectorRunning(false) }
  }

  async function toggleSource(source: CandidateSource) {
    try { const updated = await updateSource(candidate.id, source.id, { is_enabled: !source.is_enabled }); setSources((items) => items.map((item) => item.id === updated.id ? updated : item)); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not update source') }
  }

  async function searchJobs(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    try { setJobPage(await getCandidateJobs(candidate.id, { q: jobQuery })); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not load jobs') }
  }

  async function reviewJob(job: CandidateJob, decision: CandidateJob['decision']) {
    try { const updated = await reviewCandidateJob(candidate.id, job.id, decision); setJobPage((page) => ({ ...page, items: page.items.map((item) => item.id === updated.id ? updated : item) })); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not review job') }
  }

  async function showProvenance(jobId: number) {
    try { const items = await getJobProvenance(candidate.id, jobId); setProvenance((current) => ({ ...current, [jobId]: items })); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not load provenance') }
  }

  async function changeJobPage(offset: number) {
    try { setJobPage(await getCandidateJobs(candidate.id, { q: jobQuery, offset })); onError(null) }
    catch (reason) { onError(reason instanceof Error ? reason.message : 'Could not load jobs') }
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
    <KnowledgeEditor title="Employment" items={experiences.map((item) => `${item.title} — ${item.employer}`)} primary="Employer" secondary="Title" onSubmit={(event) => addKnowledge(event, 'experience')} />
    <KnowledgeEditor title="Projects" items={projects.map((item) => `${item.name}${item.role ? ` — ${item.role}` : ''}`)} primary="Project name" secondary="Role" onSubmit={(event) => addKnowledge(event, 'project')} />
    <KnowledgeEditor title="Education" items={education.map((item) => `${item.institution}${item.degree ? ` — ${item.degree}` : ''}`)} primary="Institution" secondary="Degree" onSubmit={(event) => addKnowledge(event, 'education')} />
    <KnowledgeEditor title="Certifications" items={certifications.map((item) => `${item.name}${item.issuer ? ` — ${item.issuer}` : ''}`)} primary="Certification" secondary="Issuer" onSubmit={(event) => addKnowledge(event, 'certification')} />
    <section className="panel"><h3>Application answers</h3>{answers.map((item) => <article className="knowledge-row" key={item.id}><strong>{item.question_key}</strong><span>{item.answer}</span>{item.require_confirmation_each_time && <em>Confirm every use</em>}</article>)}
      <form className="stacked-form" onSubmit={addAnswer}><label>Question key<input name="question_key" required pattern="[a-z0-9_]+" placeholder="work_authorization" /></label><label>Approved answer<textarea name="answer" required /></label><label className="checkbox"><input name="sensitive" type="checkbox" /> Sensitive—confirm every use</label><button type="submit">Save answer</button></form></section>
    <section className="panel"><h3>Resume library</h3><p className="muted">Extracted text is unconfirmed until reviewed.</p>
      {resumes.length === 0 ? <p>No resumes uploaded.</p> : resumes.map((resume) => <article className="resume-card" key={resume.id}>
        <div className="resume-row"><strong>{resume.label || resume.original_filename} · v{resume.version_number}</strong><span className="decision">{resume.is_master ? 'approved master' : resume.review_status}</span></div>
        <label>Variant name<input id={`resume-label-${resume.id}`} defaultValue={resume.label || ''} disabled={resume.is_master} placeholder="Healthcare BSA" /></label>
        <label>Extracted text<textarea id={`resume-text-${resume.id}`} defaultValue={resume.extracted_text} disabled={resume.is_master} /></label>
        {!resume.is_master && <div className="inline-form"><button type="button" onClick={() => review(resume, 'approved')}>Approve text</button><button type="button" onClick={() => review(resume, 'approved', true)}>Approve as master</button><button type="button" className="secondary" onClick={() => review(resume, 'rejected')}>Reject</button></div>}
      </article>)}
      <form className="inline-form" onSubmit={addResume}><label>PDF or DOCX<input name="resume" type="file" accept=".pdf,.docx" required /></label><button type="submit">Upload</button></form></section>
    <section className="panel"><h3>ATS sources</h3><p className="muted">Save public Greenhouse or Lever boards, then run enabled sources. This never submits an application.</p>
      <form className="inline-form" onSubmit={addSource}>
        <label>Provider<select name="provider"><option value="greenhouse">Greenhouse</option><option value="lever">Lever</option></select></label>
        <label>Board or site key<input name="source_key" required pattern="[A-Za-z0-9][A-Za-z0-9_-]*" maxLength={100} placeholder="company-slug" /></label>
        <label>Label<input name="label" maxLength={255} placeholder="Primary boards" /></label>
        <button type="submit">Save source</button>
      </form>
      {sources.length === 0 ? <p className="muted">No saved sources.</p> : sources.map((source) => <article className="source-row" key={source.id}>
        <span><strong>{source.label || source.source_key}</strong><small>{source.provider} · {source.source_key}</small></span>
        <button type="button" className="secondary" onClick={() => toggleSource(source)}>{source.is_enabled ? 'Disable' : 'Enable'}</button>
        <button type="button" disabled={!source.is_enabled || connectorRunning} onClick={() => executeSavedSource(source)}>{connectorRunning ? 'Fetching…' : 'Run now'}</button>
      </article>)}
      {ingestionRuns.length === 0 ? <p className="muted">No ingestion runs yet.</p> : ingestionRuns.map((run) => <article className="knowledge-row" key={run.id}>
        <strong>{run.provider} · {run.source_key} <span className="decision">{run.status}</span></strong>
        <span>{run.discovered_count} discovered · {run.created_count} created · {run.duplicate_count} duplicates</span>
        {run.error_message && <em>{run.error_message}</em>}
      </article>)}
    </section>
    <section className="panel"><h3>Candidate jobs</h3><form className="inline-form" onSubmit={searchJobs}><label>Search jobs<input value={jobQuery} onChange={(event) => setJobQuery(event.target.value)} placeholder="title, company, keywords" /></label><button type="submit">Search</button></form>
      <p className="muted">{jobPage.total} candidate-owned jobs</p>
      {jobPage.items.length === 0 ? <p>No jobs found.</p> : jobPage.items.map((job) => <article className="job-review" key={job.id}>
        <div><strong>{job.title}</strong><span>{job.company} · {job.location || 'Location not listed'}</span></div><span className="decision">{job.decision}</span>
        <a href={job.url} target="_blank" rel="noreferrer">Official posting</a>
        <div className="job-actions"><button type="button" onClick={() => reviewJob(job, 'approve')}>Approve</button><button type="button" className="secondary" onClick={() => reviewJob(job, 'maybe')}>Maybe</button><button type="button" className="secondary" onClick={() => reviewJob(job, 'skip')}>Skip</button><button type="button" className="secondary" onClick={() => showProvenance(job.id)}>Provenance</button></div>
        {provenance[job.id]?.map((item) => <small key={item.id}>{item.provider} · {item.source_key} · {item.external_id}</small>)}
      </article>)}
      <div className="pagination"><button type="button" className="secondary" disabled={jobPage.offset === 0} onClick={() => changeJobPage(Math.max(0, jobPage.offset - jobPage.limit))}>Previous</button><span>{jobPage.total === 0 ? 0 : jobPage.offset + 1}–{Math.min(jobPage.offset + jobPage.items.length, jobPage.total)} of {jobPage.total}</span><button type="button" className="secondary" disabled={jobPage.offset + jobPage.limit >= jobPage.total} onClick={() => changeJobPage(jobPage.offset + jobPage.limit)}>Next</button></div>
    </section>
    <section className="panel"><h3>Activity</h3>{activity.length === 0 ? <p className="muted">No activity recorded yet.</p> : activity.map((event) => <p className="knowledge-row" key={event.id}><strong>{event.action}</strong><span>{new Date(event.created_at).toLocaleString()}</span></p>)}</section>
  </div>
}

function KnowledgeEditor({ title, items, primary, secondary, onSubmit }: { title: string; items: string[]; primary: string; secondary: string; onSubmit: (event: FormEvent<HTMLFormElement>) => void }) {
  return <section className="panel"><h3>{title}</h3>{items.length === 0 ? <p className="muted">No confirmed entries.</p> : items.map((item) => <p className="knowledge-row" key={item}>{item}</p>)}
    <form className="inline-form" onSubmit={onSubmit}><label>{primary}<input name="primary" required /></label><label>{secondary}<input name="secondary" required={title === 'Employment'} /></label><button type="submit">Add</button></form></section>
}
