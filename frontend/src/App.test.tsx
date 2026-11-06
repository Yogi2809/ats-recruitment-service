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

afterEach(() => cleanup())

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
