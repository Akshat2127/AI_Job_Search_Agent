import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import CandidateProfiles from './CandidateProfiles'

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => vi.stubGlobal('fetch', fetchMock))
afterEach(() => { vi.unstubAllGlobals(); vi.clearAllMocks() })

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
      .mockResolvedValueOnce(Response.json({
        id: 'run-1', provider: 'lever', source_key: 'example', status: 'completed',
        discovered_count: 3, created_count: 2, duplicate_count: 1, error_code: null,
        error_message: null, started_at: '2026-07-14T00:00:00Z',
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
    await userEvent.click(screen.getByRole('button', { name: 'Fetch jobs' }))
    expect(await screen.findByText('3 discovered · 2 created · 1 duplicates')).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith(
      '/api/v1/candidates/candidate-1/connector-runs',
      expect.objectContaining({ method: 'POST' }),
    )
  })
})
