import { cleanup, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import App from './App'

const fetchMock = vi.fn<typeof fetch>()
const currentUser = { id: 'user-1', email: 'user@example.com' }

beforeEach(() => vi.stubGlobal('fetch', fetchMock))
afterEach(() => { cleanup(); vi.unstubAllGlobals(); vi.clearAllMocks() })

describe('App', () => {
  it('opens the authenticated candidate workspace by default', async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input)
      if (url === '/api/v1/auth/me') return Response.json(currentUser)
      if (url === '/api/v1/candidates') return Response.json([])
      throw new Error(`Unexpected request: ${url}`)
    })

    render(<App />)

    expect(await screen.findByRole('heading', { name: 'Profiles' })).toBeInTheDocument()
    expect(screen.getByText('Create the first candidate profile.')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Workspace' })).toHaveClass('active')
  })

  it('keeps the old sample dashboard explicitly separated', async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input)
      if (url === '/api/v1/auth/me') return Response.json(currentUser)
      if (url === '/api/v1/candidates') return Response.json([])
      if (url === '/jobs') return Response.json([{ id: 1, company: 'Acme', title: 'Business Analyst', location: 'Remote', remote_type: 'Remote', url: 'https://example.com/job', fit_score: 88, score_reason: 'role fit', decision: 'new', status: 'discovered' }])
      if (url === '/analytics/summary') return Response.json({ total_jobs: 1, excellent_matches: 1, approved: 0, average_score: 88 })
      throw new Error(`Unexpected request: ${url}`)
    })

    render(<App />)
    await screen.findByRole('heading', { name: 'Profiles' })
    await userEvent.click(screen.getByRole('button', { name: 'Legacy sample' }))

    expect(await screen.findByRole('link', { name: 'Business Analyst' })).toBeInTheDocument()
    expect(screen.getByText('Acme')).toBeInTheDocument()
  })

  it('creates an account, signs in, and enters the workspace without terminal setup', async () => {
    fetchMock.mockImplementation(async (input) => {
      const url = String(input)
      if (url === '/api/v1/auth/me') return new Response(null, { status: 401 })
      if (url === '/api/v1/auth/register') return Response.json(currentUser, { status: 201 })
      if (url === '/api/v1/auth/browser-login') return Response.json({ user: currentUser, expires_in: 43200 })
      if (url === '/api/v1/candidates') return Response.json([])
      throw new Error(`Unexpected request: ${url}`)
    })

    render(<App />)
    expect(await screen.findByRole('heading', { name: 'Sign in or create an account to begin' })).toBeInTheDocument()
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))
    await userEvent.type(screen.getByLabelText('Email'), 'user@example.com')
    await userEvent.type(screen.getByLabelText('Password'), 'correct horse battery staple')
    await userEvent.click(screen.getByRole('button', { name: 'Create account' }))

    expect(await screen.findByRole('heading', { name: 'Profiles' })).toBeInTheDocument()
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/register', expect.objectContaining({ method: 'POST' }))
    expect(fetchMock).toHaveBeenCalledWith('/api/v1/auth/browser-login', expect.objectContaining({ method: 'POST' }))
  })
})
