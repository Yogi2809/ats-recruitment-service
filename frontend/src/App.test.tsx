import { afterEach, beforeEach, expect, test, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'

const sampleWorkspace = {
  jds: [{ id: 'data-engineer', title: 'Senior Data Engineer', required: ['Python'], preferred: [], evidence: [] }],
  candidates: [{ id: 'maya', name: 'Maya Shah', evidence: [] }],
  selected_jd_id: 'data-engineer',
  recruitment: [],
  drafts: [],
}

beforeEach(() => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'demo@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    return Response.json({ ok: true })
  }))
})

afterEach(() => { cleanup(); vi.unstubAllGlobals() })

test('login is minimal and create-account navigation works', async () => {
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  expect(screen.getByLabelText('Email')).toBeTruthy()
  expect(screen.getByLabelText('Password')).toBeTruthy()
  expect(screen.getByRole('button', { name: 'Log in' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  expect(await screen.findByRole('heading', { name: 'Create account' })).toBeTruthy()
})

test('new account sees empty onboarding instead of sample candidates', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'fresh@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json({ jds: [], candidates: [], selected_jd_id: '', recruitment: [], drafts: [] })
    if (url.endsWith('/api/compare')) return Response.json({ jd: null, results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'fresh@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  await screen.findByText('Add a job description and a CV to see matches.')
  expect(screen.queryByText('Maya Shah')).toBeNull()
  expect(screen.queryByText('SYNTHETIC DATA')).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Documents' }))
  expect(screen.getByText('No job descriptions yet')).toBeTruthy()
  expect(screen.getByText('No candidate CVs yet')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Compare candidates' }))
  expect(screen.getByText('Add a job description and a CV to compare candidates.')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Email drafts' }))
  expect(screen.getByText('Add a job description and a CV before creating a draft.')).toBeTruthy()
  expect(screen.getByRole('button', { name: /Create draft/ })).toHaveProperty('disabled', true)
  fireEvent.click(screen.getByRole('button', { name: 'Open recruiter assistant' }))
  expect(screen.getByText('Add a job description and a CV, then ask me about their match.')).toBeTruthy()
})

test('legacy account can remove bundled examples while keeping its own documents', async () => {
  const ownJD = { id: 'own-jd', title: 'My Role', required: ['Python'], preferred: [], evidence: [] }
  const ownCandidate = { id: 'own-cv', name: 'My Candidate', evidence: [] }
  let current = { ...sampleWorkspace, jds: [...sampleWorkspace.jds, ownJD], candidates: [...sampleWorkspace.candidates, ownCandidate] }
  vi.stubGlobal('confirm', vi.fn(() => true))
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'legacy@example.test' })
    if (url.endsWith('/api/workspace/sample-data') && options?.method === 'DELETE') {
      current = { ...current, jds: [ownJD], candidates: [ownCandidate], selected_jd_id: 'own-jd' }
      return Response.json({ ok: true })
    }
    if (url.endsWith('/api/workspace')) return Response.json(current)
    if (url.endsWith('/api/compare')) return Response.json({ jd: current.jds[0] || null, results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'legacy@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  expect(screen.getByText('Maya Shah')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Remove bundled samples' }))
  await waitFor(() => expect(screen.queryByText('Maya Shah')).toBeNull())
  expect(screen.getByText('My Role')).toBeTruthy()
  expect(screen.getByText('My Candidate')).toBeTruthy()
})

test('registered user can open and close floating chat', async () => {
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'demo@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  await waitFor(() => expect(screen.getByRole('button', { name: 'Open recruiter assistant' })).toBeTruthy())
  fireEvent.click(screen.getByRole('button', { name: 'Open recruiter assistant' }))
  expect(screen.getByRole('dialog', { name: 'Recruiter assistant' })).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Close chat' }))
  expect(screen.queryByRole('dialog', { name: 'Recruiter assistant' })).toBeNull()
})

test('asking from a candidate review selects that candidate in chat', async () => {
  const match = {
    candidate_id: 'maya', candidate_name: 'Maya Shah', score: 90,
    required_percent: 100, preferred_percent: 0, similarity_percent: 0,
    matched_required: ['Python'], missing_required: [],
    matched_preferred: [], missing_preferred: [], evidence: {},
  }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'demo@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [match] })
    if (url.endsWith('/api/candidates/maya/analysis')) return Response.json({ candidate: sampleWorkspace.candidates[0], jd: sampleWorkspace.jds[0], match, summary: '', questions: [] })
    return Response.json({ ok: true })
  }))

  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'demo@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: /01 MS Maya Shah/ }))
  fireEvent.click(await screen.findByRole('button', { name: /Ask about candidate/ }))
  expect((screen.getByRole('combobox', { name: 'Discussing' }) as HTMLSelectElement).value).toBe('maya')
})
