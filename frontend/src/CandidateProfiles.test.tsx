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

    render(<CandidateProfiles />)
    expect(await screen.findByText('Create the first candidate profile.')).toBeInTheDocument()
    await userEvent.type(screen.getByLabelText('Name'), 'Gurbani Sharma')
    await userEvent.type(screen.getByLabelText('Headline'), 'Senior Business Systems Analyst')
    await userEvent.click(screen.getByRole('button', { name: 'Create profile' }))

    expect(await screen.findByRole('heading', { name: 'Gurbani Sharma' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/candidates', expect.objectContaining({ method: 'POST' }))
  })
})
