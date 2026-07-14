import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const fetchMock = vi.fn<typeof fetch>()

beforeEach(() => {
  vi.stubGlobal('fetch', fetchMock)
})

afterEach(() => {
  vi.unstubAllGlobals()
  vi.clearAllMocks()
})

describe('App', () => {
  it('renders jobs and summary returned by the API', async () => {
    fetchMock
      .mockResolvedValueOnce(Response.json([{ id: 1, company: 'Acme', title: 'Business Analyst', location: 'Remote', remote_type: 'Remote', url: 'https://example.com/job', fit_score: 88, score_reason: 'role fit', decision: 'new', status: 'discovered' }]))
      .mockResolvedValueOnce(Response.json({ total_jobs: 1, excellent_matches: 1, approved: 0, average_score: 88 }))

    render(<App />)

    expect(await screen.findByRole('link', { name: 'Business Analyst' })).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
    expect(screen.getAllByText('88')).toHaveLength(2)
  })

  it('shows a useful empty state', async () => {
    fetchMock
      .mockResolvedValueOnce(Response.json([]))
      .mockResolvedValueOnce(Response.json({ total_jobs: 0, excellent_matches: 0, approved: 0, average_score: 0 }))

    render(<App />)
    expect(await screen.findByText(/No jobs have been discovered yet/i)).toBeInTheDocument()
  })

  it('shows an error and retries', async () => {
    fetchMock.mockRejectedValueOnce(new Error('offline')).mockRejectedValueOnce(new Error('offline'))
    render(<App />)

    expect(await screen.findByRole('alert')).toHaveTextContent('offline')
    await userEvent.click(screen.getByRole('button', { name: 'Try again' }))
    expect(fetchMock).toHaveBeenCalledTimes(4)
  })
})
