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

test('job and candidate searches are independent', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.change(screen.getByLabelText('Search job descriptions'), { target: { value: 'missing role' } })
  expect(screen.getByText('No job descriptions match your search.')).toBeTruthy()
  expect(screen.getByText('Maya Shah')).toBeTruthy()
  fireEvent.change(screen.getByLabelText('Search job descriptions'), { target: { value: '' } })
  fireEvent.change(screen.getByLabelText('Search candidates'), { target: { value: 'missing candidate' } })
  expect(screen.getByText('No candidates match these filters.')).toBeTruthy()
  expect(screen.getByText('Senior Data Engineer')).toBeTruthy()
})

test('document view errors are visible without opening skill review', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/jds/data-engineer')) return Response.json({ detail: 'Job not found.' }, { status: 404 })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getAllByRole('button', { name: 'View' })[0])
  expect((await screen.findByRole('alert')).textContent).toContain('Job not found.')
})

test('compare page filters results using candidate checkboxes', async () => {
  const candidates = [sampleWorkspace.candidates[0], { id: 'other', name: 'Other Candidate', evidence: [] }]
  const match = (id: string, name: string) => ({ candidate_id: id, candidate_name: name, score: 80, required_percent: 100, preferred_percent: 0, similarity_percent: 0, matched_required: ['Python'], missing_required: [], matched_preferred: [], missing_preferred: [], evidence: {} })
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json({ ...sampleWorkspace, candidates })
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [match('maya', 'Maya Shah'), match('other', 'Other Candidate')] })
    if (url.endsWith('/api/candidates/maya/analysis')) return Response.json({ candidate: candidates[0], jd: sampleWorkspace.jds[0], match: match('maya', 'Maya Shah'), summary: '', questions: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Compare candidates' }))
  expect(screen.getByRole('heading', { name: '2 candidates' })).toBeTruthy()
  fireEvent.click(screen.getByRole('checkbox', { name: 'Other Candidate' }))
  expect(screen.getByRole('heading', { name: '1 candidate' })).toBeTruthy()
  expect(screen.queryByRole('heading', { name: 'Other Candidate' })).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: /View evidence and prepare/ }))
  await screen.findByRole('heading', { name: 'Maya Shah' })
  fireEvent.click(screen.getByRole('button', { name: 'Back to comparison' }))
  expect(screen.getByRole('heading', { name: '1 candidate' })).toBeTruthy()
  expect(screen.getByRole('checkbox', { name: 'Other Candidate' })).toHaveProperty('checked', false)
})

test('shared library supports viewing and importing an explicitly shared document', async () => {
  const item = { id: 'shared-one', kind: 'jd', title: 'Shared QA Role', department: 'Tech', tags: [], owned: false, download_available: true }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/library')) return Response.json({ items: [item] })
    if (url.endsWith('/api/library/shared-one')) return Response.json({ kind: 'jd', document: { title: 'Shared QA Role', evidence: [{ id: 'e', source: 'JD', location: 'line 1', text: 'Python required' }] } })
    if (url.endsWith('/api/library/shared-one/copy') && options?.method === 'POST') return Response.json({ id: 'copy' })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Shared library' }))
  await screen.findByText('Shared QA Role')
  fireEvent.click(screen.getByRole('button', { name: 'View' }))
  expect(await screen.findByText('Python required')).toBeTruthy()
  expect(screen.getByRole('link', { name: 'Download' }).getAttribute('href')).toBe('/api/library/shared-one/download')
  fireEvent.click(screen.getByRole('button', { name: 'Use a copy' }))
  expect(await screen.findByRole('heading', { name: 'Documents' })).toBeTruthy()
})

test('tags can be saved and used to filter candidates', async () => {
  let current = { ...sampleWorkspace, candidates: [{ ...sampleWorkspace.candidates[0], tags: [] as string[] }, { id: 'other', name: 'Other Candidate', evidence: [], tags: [] as string[] }] }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(current)
    if (url.endsWith('/api/compare')) return Response.json({ jd: current.jds[0], results: [] })
    if (url.endsWith('/api/candidates/maya/metadata') && options?.method === 'PATCH') {
      const body = JSON.parse(String(options.body))
      current = { ...current, candidates: current.candidates.map(item => item.id === 'maya' ? { ...item, tags: body.tags } : item) }
      return Response.json({ ok: true })
    }
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.change(screen.getByLabelText('Tags for Maya Shah'), { target: { value: 'QA, Automation' } })
  fireEvent.click(screen.getAllByRole('button', { name: 'Save tags' })[0])
  await screen.findByText('Tags updated.')
  fireEvent.change(screen.getByLabelText('Filter by tag'), { target: { value: 'QA' } })
  expect(screen.getByText('Maya Shah')).toBeTruthy()
  expect(screen.queryByText('Other Candidate')).toBeNull()
})

test('tag text remains visible when save succeeds but refresh fails', async () => {
  let reads = 0
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) { reads++; return reads === 1 ? Response.json(sampleWorkspace) : Response.json({ detail: 'Offline' }, { status: 503 }) }
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/candidates/maya/metadata')) return Response.json({ ok: true })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.change(screen.getByLabelText('Tags for Maya Shah'), { target: { value: 'QA' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save tags' }))
  await screen.findByText(/Saved, but the workspace could not refresh/)
  expect(screen.getByLabelText('Tags for Maya Shah')).toHaveProperty('value', 'QA')
})

test('multiple JD uploads keep completed files out of a retry', async () => {
  const uploads: string[] = []
  let failSecond = true
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/jds/upload')) {
      const name = ((options?.body as FormData).get('file') as File).name
      uploads.push(name)
      if (name === 'second.txt' && failSecond) { failSecond = false; return Response.json({ detail: 'Temporary failure' }, { status: 422 }) }
      return Response.json({ id: name })
    }
    if (url.includes('/skills/preview')) return Response.json({ roles: [], selected_role: null, suggestions: [], warnings: [], current_required: [], current_preferred: [], needs_review: true })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Upload file' }))
  const input = document.querySelector('.document-card input[type="file"]') as HTMLInputElement
  fireEvent.change(input, { target: { files: [new File(['a'], 'first.txt'), new File(['b'], 'second.txt')] } })
  fireEvent.click(await screen.findByRole('button', { name: 'Retry remaining JDs (1)' }))
  await waitFor(() => expect(uploads).toEqual(['first.txt', 'second.txt', 'second.txt']))
})

test('a conflicting save keeps pasted text and asks the recruiter to reload', async () => {
  let workspaceReads = 0
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) { workspaceReads++; return Response.json(sampleWorkspace) }
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/jds/paste')) return Response.json({ detail: 'Your workspace changed in another session. Refresh and try this action again.' }, { status: 409 })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.change(screen.getByRole('textbox', { name: 'Role title' }), { target: { value: 'New Role' } })
  fireEvent.change(screen.getByRole('textbox', { name: 'Job description' }), { target: { value: 'Required: SQL' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add job description' }))
  expect(await screen.findByText(/Copy unsaved edits, reload the page/)).toBeTruthy()
  expect(workspaceReads).toBe(1)
  expect(screen.getByRole('textbox', { name: 'Job description' })).toHaveProperty('value', 'Required: SQL')
})

test('retrying a partial CV upload does not upload completed files twice', async () => {
  const uploads: string[] = []
  let failSecond = true
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(sampleWorkspace)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/candidates/upload')) {
      const name = ((options?.body as FormData).get('file') as File).name
      uploads.push(name)
      if (name === 'second.txt' && failSecond) { failSecond = false; return Response.json({ detail: 'Your workspace changed in another session. Refresh and try this action again.' }, { status: 409 }) }
      return Response.json({ id: name })
    }
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Upload files' }))
  const input = document.querySelector('.document-card input[multiple]') as HTMLInputElement
  fireEvent.change(input, { target: { files: [new File(['a'], 'first.txt'), new File(['b'], 'second.txt')] } })
  fireEvent.click(await screen.findByRole('button', { name: 'Retry remaining files (1)' }))
  await waitFor(() => expect(uploads).toEqual(['first.txt', 'second.txt', 'second.txt']))
})

test('a JD editor retains its starting version after another workspace refresh', async () => {
  let revision = 3
  let submittedVersion: string | null = null
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json({ ...sampleWorkspace, revision })
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [] })
    if (url.endsWith('/api/candidates/paste')) { revision = 4; return Response.json({ id: 'new' }) }
    if (url.endsWith('/api/jds/data-engineer') && options?.method === 'PATCH') {
      submittedVersion = new Headers(options.headers).get('X-Workspace-Revision')
      return Response.json({ detail: 'Your workspace changed in another session. Refresh and try this action again.' }, { status: 409 })
    }
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Edit skills' }))
  fireEvent.change(screen.getByLabelText('Required skills, comma separated'), { target: { value: 'Python, SQL' } })
  fireEvent.change(screen.getByLabelText('Candidate name'), { target: { value: 'Example' } })
  fireEvent.change(screen.getByLabelText('CV text'), { target: { value: 'Python' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add candidate' }))
  await screen.findByText('Candidate CV added.')
  fireEvent.click(screen.getByRole('button', { name: 'Save skills' }))
  await screen.findByText(/Copy unsaved edits/)
  expect(submittedVersion).toBe('3')
  expect(screen.getByLabelText('Required skills, comma separated')).toHaveProperty('value', 'Python, SQL')
})

test('a recruiter can confirm deletion of their active JD', async () => {
  let current = { ...sampleWorkspace }
  vi.stubGlobal('confirm', vi.fn(() => true))
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return Response.json({ email: 'owner@example.test' })
    if (url.endsWith('/api/jds/data-engineer') && options?.method === 'DELETE') {
      current = { ...current, jds: [], selected_jd_id: '' }
      return Response.json({ ok: true })
    }
    if (url.endsWith('/api/workspace')) return Response.json(current)
    if (url.endsWith('/api/compare')) return Response.json({ jd: current.jds[0] || null, results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Delete Senior Data Engineer' }))
  expect(await screen.findByText('No job descriptions yet')).toBeTruthy()
})

test('choosing a JD file saves it before comparison', async () => {
  let current = { jds: [] as typeof sampleWorkspace.jds, candidates: sampleWorkspace.candidates, selected_jd_id: '', recruitment: [], drafts: [] }
  const upload = vi.fn()
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'upload@example.test' })
    if (url.endsWith('/api/jds/upload')) { upload(); current = { ...current, jds: sampleWorkspace.jds, selected_jd_id: 'data-engineer' }; return Response.json(sampleWorkspace.jds[0]) }
    if (url.endsWith('/api/jds/data-engineer/skills/preview')) return Response.json({ roles: ['Senior Data Engineer'], selected_role: 'Senior Data Engineer', suggestions: [], warnings: [], current_required: [], current_preferred: [], needs_review: true })
    if (url.endsWith('/api/workspace')) return Response.json(current)
    if (url.endsWith('/api/compare')) return Response.json({ jd: current.jds[0] || null, results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'upload@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Compare candidates' }))
  expect(screen.getByText('Add a job description to compare your saved CVs.')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Manage documents' }))
  fireEvent.click(screen.getByRole('button', { name: /^Upload file$/ }))
  fireEvent.change(document.querySelector('input[type="file"]')!, { target: { files: [new File(['Required: Python'], 'role.pdf', { type: 'application/pdf' })] } })
  await waitFor(() => expect(upload).toHaveBeenCalledTimes(1))
  await screen.findByRole('heading', { name: 'Job descriptions 1' })
})

test('unreviewed JD offers skill review before showing a comparison', async () => {
  let pending = { ...sampleWorkspace, jds: [{ ...sampleWorkspace.jds[0], needs_review: true }] }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'review@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(pending)
    if (url.endsWith('/api/compare')) return Response.json({ jd: pending.jds[0], results: [] })
    if (url.endsWith('/api/jds/data-engineer/skills/preview')) return Response.json({
      roles: ['Senior Data Engineer'], selected_role: 'Senior Data Engineer', warnings: [],
      current_required: ['Python'], current_preferred: [], needs_review: true,
      suggestions: [{ id: 'one', label: 'Python', kind: 'skill', category: 'required', options: ['Python'], source_id: 'source', source_location: 'line 1', source_quote: 'Required: Python', source_section: 'required', origin: 'suggested' }],
    })
    if (url.endsWith('/api/jds/data-engineer/skills') && options?.method === 'PUT') {
      pending = { ...pending, jds: [{ ...pending.jds[0], needs_review: false }] }
      return Response.json(pending.jds[0])
    }
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'review@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  expect(await screen.findByText('Review JD skills')).toBeTruthy()
  fireEvent.click(await screen.findByRole('button', { name: 'Compare candidates' }))
  expect(screen.getByText(/Review this job description's skills before comparing candidates/)).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Manage documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Review skills' }))
  expect(await screen.findByRole('heading', { name: 'Review detected skills' })).toBeTruthy()
  expect(await screen.findByText('line 1: Required: Python')).toBeTruthy()
  fireEvent.click(screen.getByRole('button', { name: 'Save reviewed skills' }))
  expect(await screen.findByRole('button', { name: 'Reanalyse skills' })).toBeTruthy()
})

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

test('failed document submission keeps pasted text for correction', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'retry@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json({ jds: [], candidates: [], selected_jd_id: '', recruitment: [], drafts: [] })
    if (url.endsWith('/api/compare')) return Response.json({ jd: null, results: [] })
    if (url.endsWith('/api/jds/paste')) return Response.json({ detail: 'No readable text found.' }, { status: 422 })
    if (url.endsWith('/api/candidates/paste')) return Response.json({ detail: 'Candidate text rejected.' }, { status: 422 })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'retry@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.change(screen.getByRole('textbox', { name: 'Role title' }), { target: { value: 'My Role' } })
  fireEvent.change(screen.getByRole('textbox', { name: 'Job description' }), { target: { value: 'Text to correct' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add job description' }))
  await screen.findByText('No readable text found.')
  expect(screen.getByRole('textbox', { name: 'Role title' })).toHaveProperty('value', 'My Role')
  expect(screen.getByRole('textbox', { name: 'Job description' })).toHaveProperty('value', 'Text to correct')
  fireEvent.change(screen.getByRole('textbox', { name: 'Candidate name' }), { target: { value: 'Test Person' } })
  fireEvent.change(screen.getByRole('textbox', { name: 'CV text' }), { target: { value: 'CV text to correct' } })
  fireEvent.click(screen.getByRole('button', { name: 'Add candidate' }))
  await screen.findByText('Candidate text rejected.')
  expect(screen.getByRole('textbox', { name: 'Candidate name' })).toHaveProperty('value', 'Test Person')
  expect(screen.getByRole('textbox', { name: 'CV text' })).toHaveProperty('value', 'CV text to correct')
})

test('oversized upload is stopped before leaving the browser', async () => {
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'size@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json({ jds: [], candidates: [], selected_jd_id: '', recruitment: [], drafts: [] })
    if (url.endsWith('/api/compare')) return Response.json({ jd: null, results: [] })
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'size@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: 'Documents' }))
  fireEvent.click(screen.getByRole('button', { name: 'Upload file' }))
  const file = new File([new Uint8Array(4 * 1024 * 1024 + 1)], 'large.txt', { type: 'text/plain' })
  const input = document.querySelector('.document-card input[type="file"]') as HTMLInputElement
  fireEvent.change(input, { target: { files: [file] } })
  expect(await screen.findByText('File exceeds the 4 MB limit.')).toBeTruthy()
  expect(screen.getByRole('heading', { name: 'Job descriptions 0' })).toBeTruthy()
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
  await screen.findByRole('heading', { name: 'Maya Shah' })
  expect(screen.queryByRole('button', { name: /Ask about candidate/ })).toBeNull()
  fireEvent.click(screen.getByRole('button', { name: 'Open recruiter assistant' }))
  expect((screen.getByRole('combobox', { name: 'Discussing' }) as HTMLSelectElement).value).toBe('maya')
})

test('recruiter can save a candidate stage from the review screen', async () => {
  const match = {
    candidate_id: 'maya', candidate_name: 'Maya Shah', score: 90,
    required_percent: 100, preferred_percent: 0, similarity_percent: 0,
    matched_required: ['Python'], missing_required: [],
    matched_preferred: [], missing_preferred: [], evidence: {},
  }
  let current = { ...sampleWorkspace, recruitment: [] as { candidate_id: string; stage: string; assessment: string }[] }
  vi.stubGlobal('fetch', vi.fn(async (input: RequestInfo | URL, options?: RequestInit) => {
    const url = String(input)
    if (url.endsWith('/api/auth/me')) return new Response('{}', { status: 401 })
    if (url.endsWith('/api/auth/register')) return Response.json({ id: 1, email: 'status@example.test' })
    if (url.endsWith('/api/workspace')) return Response.json(current)
    if (url.endsWith('/api/compare')) return Response.json({ jd: sampleWorkspace.jds[0], results: [match] })
    if (url.endsWith('/api/candidates/maya/analysis')) return Response.json({ candidate: sampleWorkspace.candidates[0], jd: sampleWorkspace.jds[0], match, summary: 'CV summary', questions: ['Ask about Python'] })
    if (url.endsWith('/api/candidates/maya/recruitment') && options?.method === 'PATCH') {
      const record = { candidate_id: 'maya', ...JSON.parse(String(options.body)) }
      current = { ...current, recruitment: [record] }
      return Response.json(record)
    }
    return Response.json({ ok: true })
  }))
  const { default: App } = await import('./App')
  render(<App />)
  await screen.findByRole('heading', { name: 'Log in' })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.change(screen.getByLabelText('Email'), { target: { value: 'status@example.test' } })
  fireEvent.change(screen.getByLabelText('Password'), { target: { value: 'long-demo-password' } })
  fireEvent.change(screen.getByLabelText('Confirm password'), { target: { value: 'long-demo-password' } })
  fireEvent.click(screen.getByRole('button', { name: 'Create account' }))
  fireEvent.click(await screen.findByRole('button', { name: /01 MS Maya Shah/ }))
  expect(await screen.findByText('No status recorded')).toBeTruthy()
  fireEvent.change(screen.getByRole('combobox', { name: 'Stage' }), { target: { value: 'Recruiter screen' } })
  fireEvent.change(screen.getByRole('textbox', { name: 'Assessment note' }), { target: { value: 'Data exercise pending' } })
  fireEvent.click(screen.getByRole('button', { name: 'Save status' }))
  expect(await screen.findByText('Current stage: Recruiter screen')).toBeTruthy()
  expect(screen.getByText('Data exercise pending')).toBeTruthy()
})
