import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CandidateProfiles from './CandidateProfiles'

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => vi.stubGlobal('fetch', fetchMock))
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.clearAllMocks() })

describe('CandidateProfiles', () => {
  it('shows the empty state and creates a candidate', async () => {
    fetchMock
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json({
        id: 'candidate-1', owner_id: 'user-1', display_name: 'Gurbani Sharma',
        headline: 'Senior Business Systems Analyst', summary: null, years_experience: 12, is_archived: false,
      }, { status: 201 }))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json({ items: [], total: 0, limit: 25, offset: 0 }))
      .mockResolvedValueOnce(Response.json({
        id: 'source-1', provider: 'lever', source_key: 'example', label: 'Example board',
        is_enabled: true, last_run_at: null,
      }, { status: 201 }))

    render(<CandidateProfiles />)
    expect(await screen.findByText('Create the first candidate profile.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Name'), 'Gurbani Sharma')
    await userEvent.type(screen.getByLabelText('Headline'), 'Senior Business Systems Analyst')
    await userEvent.click(screen.getByRole('button', { name: 'Create profile' }))

    expect(await screen.findByRole('heading', { name: 'Gurbani Sharma' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/candidates', expect.objectContaining({ method: 'POST' }))
    await userEvent.selectOptions(screen.getByLabelText('Provider'), 'lever')
    await userEvent.type(screen.getByLabelText('Board or site key'), 'example')
    await userEvent.type(screen.getByLabelText('Label'), 'Example board')
    await userEvent.click(screen.getByRole('button', { name: 'Save source' }))
    expect(await screen.findByText('Example board')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/candidates/candidate-1/sources',
      expect.objectContaining({ method: 'POST' }),
    )
  })

  it('adds a user-confirmed LinkedIn job to the candidate workspace', async () => {
    const candidate = {
      id: 'candidate-1', owner_id: 'user-1', display_name: 'Test Candidate',
      headline: null, summary: null, years_experience: null, is_archived: false,
    }
    const job = {
      id: 42, company: 'Example Company', title: 'Product Analyst', location: 'Remote',
      url: 'https://www.linkedin.com/jobs/view/12345', source: 'linkedin',
      description: 'User-confirmed description', decision: 'new', status: 'discovered',
    }
    let jobsLoaded = 0
    fetchMock.mockImplementation(async (input, init) => {
      const url = String(input)
      if (url === '/api/v1/candidates' && init?.method !== 'POST') return Response.json([candidate])
      if (url === '/api/v1/candidates/candidate-1/jobs/manual') {
        return Response.json({ job, created: true }, { status: 201 })
      }
      if (url.startsWith('/api/v1/candidates/candidate-1/jobs?')) {
        jobsLoaded += 1
        return Response.json({ items: jobsLoaded > 1 ? [job] : [], total: jobsLoaded > 1 ? 1 : 0, limit: 25, offset: 0 })
      }
      if (url.startsWith('/api/v1/audit') || url.endsWith('/skills') || url.endsWith('/resumes') ||
          url.endsWith('/experiences') || url.endsWith('/projects') || url.endsWith('/education') ||
          url.endsWith('/certifications') || url.endsWith('/answers') || url.endsWith('/ingestion-runs') ||
          url.endsWith('/sources')) return Response.json([])
      throw new Error(`Unexpected request: ${url}`)
    })

    render(<CandidateProfiles />)
    await screen.findByRole('heading', { name: 'Test Candidate' })
    await userEvent.type(screen.getByLabelText('LinkedIn or Indeed job URL'), 'https://www.linkedin.com/jobs/view/12345?trackingId=test')
    await userEvent.type(screen.getByLabelText('Company'), 'Example Company')
    await userEvent.type(screen.getByLabelText('Job title'), 'Product Analyst')
    await userEvent.type(screen.getByLabelText('Location'), 'Remote')
    await userEvent.type(screen.getByLabelText('Job description'), 'User-confirmed description')
    await userEvent.click(screen.getByRole('button', { name: 'Add job' }))

    expect(await screen.findByText('Job added to this candidate.')).toBeInTheDocument()
    expect(await screen.findByText('Product Analyst')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/candidates/candidate-1/jobs/manual',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
