import { useEffect, useMemo, useState, type CSSProperties, type FormEvent } from 'react'
import { ArrowLeft, ArrowRight, Check, ChevronDown, FileText, LayoutDashboard, LogOut, Menu, MessageCircle, Moon, Plus, Send, Sun, Trash2, Upload, Users, X } from 'lucide-react'

type Evidence = { id: string; source: string; location: string; text: string }
type JD = { id: string; title: string; required: string[]; preferred: string[]; evidence: Evidence[] }
type Candidate = { id: string; name: string; evidence: Evidence[] }
type Match = { candidate_id: string; candidate_name: string; score: number; required_percent: number; preferred_percent: number; similarity_percent: number; matched_required: string[]; missing_required: string[]; matched_preferred: string[]; missing_preferred: string[]; evidence: Record<string, Evidence> }
type Draft = { id: string; candidate_id: string; candidate_name: string; job_title: string; kind: string; text: string }
type Workspace = { jds: JD[]; candidates: Candidate[]; selected_jd_id: string; recruitment: { candidate_id: string; stage: string; assessment: string }[]; drafts: Draft[] }
type Analysis = { candidate: Candidate; jd: JD; match: Match; summary: string; questions: string[] }
type ChatMessage = { role: 'user' | 'assistant'; text: string; citations?: Evidence[] }
type Page = 'overview' | 'documents' | 'compare' | 'candidate' | 'drafts'

async function api<T>(path: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(path, { credentials: 'include', ...options, headers: options.body instanceof FormData ? options.headers : { 'Content-Type': 'application/json', ...options.headers } })
  if (!response.ok) {
    const error = await response.json().catch(() => ({}))
    throw new Error(error.detail || `Request failed (${response.status})`)
  }
  return response.json() as Promise<T>
}

const json = (body: object) => JSON.stringify(body)
const scoreLabel = (score: number) => score >= 80 ? 'Strong evidence match' : score >= 55 ? 'Partial evidence match' : 'Needs review'
const initials = (name: string) => name.split(' ').map(part => part[0]).slice(0, 2).join('').toUpperCase()

function AuthView({ onAuthenticated }: { onAuthenticated: (email: string) => void }) {
  const [mode, setMode] = useState<'login' | 'register'>('login')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [remember, setRemember] = useState(true)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (mode === 'register' && password !== confirm) { setError('Passwords do not match.'); return }
    setBusy(true); setError('')
    try {
      const user = await api<{ email: string }>(`/api/auth/${mode === 'login' ? 'login' : 'register'}`, { method: 'POST', body: json({ email, password, keep_signed_in: remember }) })
      onAuthenticated(user.email)
    } catch (err) { setError((err as Error).message) }
    finally { setBusy(false) }
  }
  return <div className="auth-page">
    <div className="auth-mark"><span className="brand-symbol">R<span>·</span></span><span>RoleTrace</span></div>
    <main className="auth-card">
      <div className="auth-card-top"><span className="eyebrow">RECRUITMENT WORKSPACE</span><div className="auth-decoration" /></div>
      <h1>{mode === 'login' ? 'Log in' : 'Create account'}</h1>
      <p className="muted auth-subtitle">{mode === 'login' ? 'Welcome back.' : 'A quieter way to review candidates.'}</p>
      <form onSubmit={submit}>
        <label>Email<input type="email" autoComplete="email" value={email} onChange={e => setEmail(e.target.value)} required /></label>
        <label>Password<input type="password" autoComplete={mode === 'login' ? 'current-password' : 'new-password'} value={password} onChange={e => setPassword(e.target.value)} minLength={mode === 'login' ? 1 : 12} required /></label>
        {mode === 'register' && <label>Confirm password<input type="password" autoComplete="new-password" value={confirm} onChange={e => setConfirm(e.target.value)} required /></label>}
        <label className="checkline"><input type="checkbox" checked={remember} onChange={e => setRemember(e.target.checked)} /> Keep me signed in</label>
        {error && <p role="alert" className="form-error">{error}</p>}
        <button className="button primary full" disabled={busy}>{busy ? 'Please wait…' : mode === 'login' ? 'Log in' : 'Create account'} <ArrowRight size={17} /></button>
      </form>
      <div className="auth-switch">{mode === 'login' ? 'New to RoleTrace?' : 'Already have an account?'} <button className="text-button" onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError('') }}>{mode === 'login' ? 'Create account' : 'Log in'}</button></div>
    </main>
    <span className="auth-foot">Made for thoughtful hiring.</span>
  </div>
}

function ScoreDonut({ score, size = 'large' }: { score: number; size?: 'large' | 'small' }) {
  return <div className={`donut ${size}`} style={{ '--score': `${score}%` } as CSSProperties} role="img" aria-label={`${score}% ATS-style JD alignment`}><div className="donut-inner"><strong>{score}%</strong><span>alignment</span></div></div>
}

function ScoreBar({ label, value, description }: { label: string; value: number; description?: string }) {
  return <div className="score-bar"><div className="score-bar-header"><span>{label}</span><strong>{value}%</strong></div><div className="bar-track"><span style={{ width: `${value}%` }} /></div>{description && <small>{description}</small>}</div>
}

export default function App() {
  const [email, setEmail] = useState<string | null>(null)
  const [checking, setChecking] = useState(true)
  const [workspace, setWorkspace] = useState<Workspace | null>(null)
  const [results, setResults] = useState<Match[]>([])
  const [page, setPage] = useState<Page>('overview')
  const [analysis, setAnalysis] = useState<Analysis | null>(null)
  const [chatOpen, setChatOpen] = useState(false)
  const [mobileNav, setMobileNav] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>(() => (window.localStorage?.getItem('roletrace-theme') as 'light' | 'dark') || (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'))
  const [notice, setNotice] = useState('')
  const activeJD = workspace?.jds.find(jd => jd.id === workspace.selected_jd_id)
  const top = results[0]

  useEffect(() => { document.documentElement.dataset.theme = theme; window.localStorage?.setItem('roletrace-theme', theme) }, [theme])
  useEffect(() => { api<{ email: string }>('/api/auth/me').then(user => setEmail(user.email)).catch(() => setEmail(null)).finally(() => setChecking(false)) }, [])
  useEffect(() => { if (email) refresh().catch(err => setNotice(err.message)) }, [email])

  async function refresh() {
    const [w, comparison] = await Promise.all([api<Workspace>('/api/workspace'), api<{ results: Match[] }>('/api/compare')])
    setWorkspace(w); setResults(comparison.results)
  }
  async function run(action: () => Promise<unknown>, success?: string) {
    setNotice('')
    try { await action(); await refresh(); if (success) setNotice(success) }
    catch (err) { setNotice((err as Error).message) }
  }
  async function openCandidate(id: string) {
    setNotice('')
    try { setAnalysis(await api<Analysis>(`/api/candidates/${id}/analysis`)); setPage('candidate') }
    catch (err) { setNotice((err as Error).message) }
  }
  async function logout() { await api('/api/auth/logout', { method: 'POST' }); setEmail(null); setWorkspace(null); setResults([]); setPage('overview'); setChatOpen(false) }
  const nav = (target: Page) => { setPage(target); setMobileNav(false); setNotice('') }

  if (checking) return <div className="loading-page"><span className="brand-symbol">R<span>·</span></span><p>Opening RoleTrace…</p></div>
  if (!email) return <AuthView onAuthenticated={setEmail} />
  return <div className="app-shell">
    <aside className={`sidebar ${mobileNav ? 'open' : ''}`}>
      <div className="sidebar-head"><button className="brand-button" onClick={() => nav('overview')}><span className="brand-symbol">R<span>·</span></span><span>RoleTrace</span></button><button className="icon-button mobile-only" aria-label="Close menu" onClick={() => setMobileNav(false)}><X size={20} /></button></div>
      <div className="sidebar-section-label">WORKSPACE</div>
      <nav aria-label="Main navigation">
        <button className={page === 'overview' ? 'active' : ''} onClick={() => nav('overview')}><LayoutDashboard size={19} /> Overview</button>
        <button className={page === 'documents' ? 'active' : ''} onClick={() => nav('documents')}><FileText size={19} /> Documents</button>
        <button className={page === 'compare' || page === 'candidate' ? 'active' : ''} onClick={() => nav('compare')}><Users size={19} /> Compare candidates</button>
        <button className={page === 'drafts' ? 'active' : ''} onClick={() => nav('drafts')}><Send size={18} /> Email drafts</button>
      </nav>
      <div className="sidebar-bottom"><div className="account-chip"><div className="avatar">{initials(email.split('@')[0])}</div><span title={email}>{email}</span></div><button className="sidebar-logout" onClick={logout}><LogOut size={18} /> Log out</button></div>
    </aside>
    {mobileNav && <button className="nav-scrim" aria-label="Close menu" onClick={() => setMobileNav(false)} />}
    <div className="main-column">
      <header className="topbar"><button className="icon-button mobile-only" aria-label="Open menu" onClick={() => setMobileNav(true)}><Menu size={22} /></button><span className="topbar-context">Recruitment workspace <span className="topbar-separator">/</span> <strong>{page === 'candidate' ? 'Candidate view' : page === 'compare' ? 'Comparison' : page === 'documents' ? 'Documents' : page === 'drafts' ? 'Email drafts' : 'Overview'}</strong></span><div className="topbar-right"><span className="sample-badge">SYNTHETIC DATA</span><button className="icon-button theme-button" aria-label={theme === 'light' ? 'Switch to dark mode' : 'Switch to light mode'} onClick={() => setTheme(theme === 'light' ? 'dark' : 'light')}>{theme === 'light' ? <Moon size={19} /> : <Sun size={19} />}</button></div></header>
      <main className="page-content">
        {notice && <div className="notice" role="status">{notice}<button aria-label="Dismiss message" onClick={() => setNotice('')}><X size={16} /></button></div>}
        {!workspace ? <div className="loading-content">Loading your workspace…</div> : <>
          {page === 'overview' && <Overview workspace={workspace} results={results} activeJD={activeJD} onDocuments={() => nav('documents')} onCompare={() => nav('compare')} onCandidate={openCandidate} />}
          {page === 'documents' && <Documents workspace={workspace} activeJD={activeJD} run={run} onCompare={() => nav('compare')} />}
          {page === 'compare' && <Compare activeJD={activeJD} results={results} onCandidate={openCandidate} onDocuments={() => nav('documents')} />}
          {page === 'candidate' && analysis && <CandidateView analysis={analysis} stage={workspace.recruitment.find(r => r.candidate_id === analysis.candidate.id)} onBack={() => nav('compare')} onDrafts={() => nav('drafts')} onAsk={() => setChatOpen(true)} />}
          {page === 'drafts' && <Drafts workspace={workspace} run={run} />}
        </>}
      </main>
    </div>
    {!chatOpen && <button className="chat-launcher" aria-label="Open recruiter assistant" title="Open recruiter assistant" onClick={() => setChatOpen(true)}><MessageCircle size={25} /></button>}
    {chatOpen && <ChatDrawer workspace={workspace} initialCandidateId={page === 'candidate' ? analysis?.candidate.id : undefined} onClose={() => setChatOpen(false)} />}
  </div>
}

function Overview({ workspace, results, activeJD, onDocuments, onCompare, onCandidate }: { workspace: Workspace; results: Match[]; activeJD?: JD; onDocuments: () => void; onCompare: () => void; onCandidate: (id: string) => void }) {
  const top = results[0]
  return <><div className="page-heading"><div><span className="eyebrow">YOUR HIRING DESK</span><h1>Good to see you.</h1><p>Review the evidence behind every match.</p></div><button className="button primary" onClick={onDocuments}><Plus size={18} /> Add documents</button></div>
    <div className="overview-stats"><div className="stat-card"><span>Active role</span><strong>{activeJD?.title || 'No role selected'}</strong><button className="inline-link" onClick={onDocuments}>Manage job descriptions <ArrowRight size={15} /></button></div><div className="stat-card"><span>Candidates</span><strong className="stat-number">{workspace.candidates.length}</strong><span className="muted">In this workspace</span></div><div className="stat-card"><span>Top alignment</span><strong className="stat-number">{top ? `${top.score}%` : '—'}</strong><span className="muted">{top?.candidate_name || 'Add a candidate'}</span></div></div>
    <div className="section-heading"><div><span className="eyebrow">AT A GLANCE</span><h2>Candidate overview</h2></div><button className="inline-link" onClick={onCompare}>View comparison <ArrowRight size={16} /></button></div>
    <div className="panel candidate-list">{results.length ? results.slice(0, 4).map((result, index) => <button className="candidate-row" key={result.candidate_id} onClick={() => onCandidate(result.candidate_id)}><span className="rank-index">{String(index + 1).padStart(2, '0')}</span><span className="candidate-name"><span className="small-avatar">{initials(result.candidate_name)}</span><span><strong>{result.candidate_name}</strong><small>{scoreLabel(result.score)}</small></span></span><span className="row-skills">{result.matched_required.slice(0, 3).map(skill => <span className="skill-pill found" key={skill}>{skill}</span>)}</span><strong className="row-score">{result.score}%</strong><ArrowRight size={18} className="row-arrow" /></button>) : <div className="empty-state">Add a CV to compare candidates.</div>}</div>
    <div className="overview-bottom"><div className="panel insight-panel"><span className="eyebrow">HOW IT WORKS</span><h3>From documents to decisions</h3><p>RoleTrace compares the skills named in a job description with evidence in each CV. Open any candidate to inspect the exact lines behind the result.</p><button className="inline-link" onClick={onCompare}>Explore the comparison <ArrowRight size={16} /></button></div><div className="panel quiet-panel"><span className="eyebrow">A USEFUL REMINDER</span><h3>Evidence, not a verdict.</h3><p>A missing CV mention is a question to ask, not a final judgment about a person.</p></div></div>
  </>
}

function Documents({ workspace, activeJD, run, onCompare }: { workspace: Workspace; activeJD?: JD; run: (action: () => Promise<unknown>, success?: string) => Promise<void>; onCompare: () => void }) {
  const [jdMethod, setJdMethod] = useState<'paste' | 'upload'>('paste')
  const [cvMethod, setCvMethod] = useState<'paste' | 'upload'>('paste')
  const [jdTitle, setJdTitle] = useState('')
  const [jdText, setJdText] = useState('')
  const [cvName, setCvName] = useState('')
  const [cvText, setCvText] = useState('')
  const [jdFile, setJdFile] = useState<File | null>(null)
  const [cvFiles, setCvFiles] = useState<File[]>([])
  const [editing, setEditing] = useState(false)
  const [title, setTitle] = useState(activeJD?.title || '')
  const [required, setRequired] = useState(activeJD?.required.join(', ') || '')
  const [preferred, setPreferred] = useState(activeJD?.preferred.join(', ') || '')
  useEffect(() => { setTitle(activeJD?.title || ''); setRequired(activeJD?.required.join(', ') || ''); setPreferred(activeJD?.preferred.join(', ') || ''); setEditing(false) }, [activeJD?.id])
  async function submitJD(event: FormEvent) { event.preventDefault(); await run(async () => { if (jdMethod === 'paste') await api('/api/jds/paste', { method: 'POST', body: json({ title: jdTitle, text: jdText }) }); else { if (!jdFile) throw new Error('Choose a job description file.'); const form = new FormData(); form.append('file', jdFile); await api('/api/jds/upload', { method: 'POST', body: form }) } }, 'Job description added. Review its extracted skills below.'); setJdTitle(''); setJdText(''); setJdFile(null) }
  async function submitCV(event: FormEvent) { event.preventDefault(); await run(async () => { if (cvMethod === 'paste') await api('/api/candidates/paste', { method: 'POST', body: json({ name: cvName, text: cvText }) }); else { if (!cvFiles.length) throw new Error('Choose at least one CV file.'); for (const file of cvFiles) { const form = new FormData(); form.append('file', file); await api('/api/candidates/upload', { method: 'POST', body: form }) } } }, 'Candidate CV added.'); setCvName(''); setCvText(''); setCvFiles([]) }
  const parse = (value: string) => value.split(',').map(item => item.trim()).filter(Boolean)
  return <><div className="page-heading"><div><span className="eyebrow">SOURCE MATERIAL</span><h1>Documents</h1><p>Bring in a role and the CVs you want to review.</p></div><button className="button secondary" onClick={onCompare}>View comparison <ArrowRight size={17} /></button></div>
    <div className="document-grid"><section className="panel document-card"><div className="card-heading"><span className="card-icon"><FileText size={21} /></span><div><h2>Job description</h2><p>Upload a file or paste the text.</p></div></div><div className="segmented"><button className={jdMethod === 'paste' ? 'selected' : ''} onClick={() => setJdMethod('paste')}>Paste text</button><button className={jdMethod === 'upload' ? 'selected' : ''} onClick={() => setJdMethod('upload')}>Upload file</button></div><form onSubmit={submitJD}>{jdMethod === 'paste' ? <><label>Role title<input value={jdTitle} onChange={e => setJdTitle(e.target.value)} placeholder="e.g. Senior Data Engineer" required /></label><label>Job description<textarea value={jdText} onChange={e => setJdText(e.target.value)} placeholder="Paste the full job description here…" rows={8} required /></label></> : <label className="file-drop"><Upload size={22} /><strong>{jdFile?.name || 'Choose JD file'}</strong><span>PDF, DOCX or TXT · up to 5 MB</span><input type="file" accept=".pdf,.docx,.txt" onChange={e => setJdFile(e.target.files?.[0] || null)} /></label>}<button className="button primary" type="submit">Add job description <Plus size={17} /></button></form></section>
      <section className="panel document-card"><div className="card-heading"><span className="card-icon sage"><Users size={21} /></span><div><h2>Candidate CV</h2><p>Add one or several candidates.</p></div></div><div className="segmented"><button className={cvMethod === 'paste' ? 'selected' : ''} onClick={() => setCvMethod('paste')}>Paste text</button><button className={cvMethod === 'upload' ? 'selected' : ''} onClick={() => setCvMethod('upload')}>Upload files</button></div><form onSubmit={submitCV}>{cvMethod === 'paste' ? <><label>Candidate name<input value={cvName} onChange={e => setCvName(e.target.value)} placeholder="e.g. Maya Shah" required /></label><label>CV text<textarea value={cvText} onChange={e => setCvText(e.target.value)} placeholder="Paste the CV text here…" rows={8} required /></label></> : <label className="file-drop"><Upload size={22} /><strong>{cvFiles.length ? `${cvFiles.length} file${cvFiles.length > 1 ? 's' : ''} selected` : 'Choose CV files'}</strong><span>PDF, DOCX or TXT · up to 5 MB each</span><input type="file" multiple accept=".pdf,.docx,.txt" onChange={e => setCvFiles(Array.from(e.target.files || []))} /></label>}<button className="button primary" type="submit">Add candidate <Plus size={17} /></button></form></section></div>
    <div className="section-heading"><div><span className="eyebrow">IN THIS WORKSPACE</span><h2>Current material</h2></div></div><div className="material-grid"><section className="panel material-panel"><h3>Job descriptions <span>{workspace.jds.length}</span></h3><div className="select-list">{workspace.jds.map(jd => <button key={jd.id} className={`select-row ${jd.id === workspace.selected_jd_id ? 'selected' : ''}`} onClick={() => run(() => api(`/api/jds/${jd.id}/select`, { method: 'POST' }))}><FileText size={17} /><span>{jd.title}</span>{jd.id === workspace.selected_jd_id && <span className="active-tag">Active</span>}</button>)}</div>{activeJD && <div className="skill-editor"><div className="skill-editor-head"><strong>Skills used for matching</strong><button className="text-button" onClick={() => setEditing(!editing)}>{editing ? 'Cancel' : 'Edit skills'}</button></div>{editing ? <div className="skill-edit-form"><label>Role title<input value={title} onChange={e => setTitle(e.target.value)} /></label><label>Required skills, comma separated<input value={required} onChange={e => setRequired(e.target.value)} /></label><label>Preferred skills, comma separated<input value={preferred} onChange={e => setPreferred(e.target.value)} /></label><button className="button primary" onClick={() => { run(() => api(`/api/jds/${activeJD.id}`, { method: 'PATCH', body: json({ title, required: parse(required), preferred: parse(preferred) }) }), 'Matching skills updated.'); setEditing(false) }}>Save skills</button></div> : <><p><b>Required</b> {activeJD.required.join(' · ') || 'None identified'}</p><p><b>Preferred</b> {activeJD.preferred.join(' · ') || 'None identified'}</p></>}</div>}</section><section className="panel material-panel"><h3>Candidate CVs <span>{workspace.candidates.length}</span></h3><div className="select-list">{workspace.candidates.map(candidate => <div className="select-row" key={candidate.id}><span className="small-avatar">{initials(candidate.name)}</span><span>{candidate.name}</span><button className="icon-button delete-button" aria-label={`Remove ${candidate.name}`} title={`Remove ${candidate.name}`} onClick={() => run(() => api(`/api/candidates/${candidate.id}`, { method: 'DELETE' }), `${candidate.name} removed.`)}><Trash2 size={16} /></button></div>)}</div></section></div>
  </>
}

function Compare({ activeJD, results, onCandidate, onDocuments }: { activeJD?: JD; results: Match[]; onCandidate: (id: string) => void; onDocuments: () => void }) {
  const [sort, setSort] = useState<'score' | 'name'>('score')
  const sorted = useMemo(() => [...results].sort((a, b) => sort === 'score' ? b.score - a.score : a.candidate_name.localeCompare(b.candidate_name)), [results, sort])
  return <><div className="page-heading"><div><span className="eyebrow">MATCH & RANK</span><h1>Compare candidates</h1><p>Evidence against <strong>{activeJD?.title || 'the active role'}</strong></p></div><button className="button secondary" onClick={onDocuments}>Manage documents</button></div><div className="method-note"><span className="method-mark">i</span><span><strong>ATS-style JD alignment</strong> is this app’s comparison: 70% required skills, 20% preferred skills, 10% wording similarity. It is not a hiring decision or an external ATS result.</span></div>
    <div className="section-heading"><div><span className="eyebrow">RANKED REVIEW</span><h2>{results.length} candidate{results.length === 1 ? '' : 's'}</h2></div><label className="sort-control">Sort by <select value={sort} onChange={e => setSort(e.target.value as 'score' | 'name')}><option value="score">Highest alignment</option><option value="name">Name</option></select><ChevronDown size={15} /></label></div>
    {sorted.length ? <div className="compare-grid">{sorted.map((result, index) => <article className="panel compare-card" key={result.candidate_id}><div className="compare-card-top"><span className="rank-label">#{index + 1} IN THIS VIEW</span><span className={`match-label ${result.score >= 80 ? 'strong' : result.score >= 55 ? 'partial' : 'review'}`}>{scoreLabel(result.score)}</span></div><div className="compare-card-main"><ScoreDonut score={result.score} size="small" /><div><div className="small-avatar large-avatar">{initials(result.candidate_name)}</div><h3>{result.candidate_name}</h3><p>{result.matched_required.length} of {result.matched_required.length + result.missing_required.length} required skills mentioned</p></div></div><div className="compare-bars"><ScoreBar label="Required skills" value={result.required_percent} /><ScoreBar label="Preferred skills" value={result.preferred_percent} /></div><div className="mini-skills"><span>Evidence in CV</span><div>{result.matched_required.length ? result.matched_required.map(skill => <span className="skill-pill found" key={skill}>{skill}</span>) : <small>No required skills found</small>}</div></div><div className="mini-skills missing"><span>No evidence found</span><div>{result.missing_required.length ? result.missing_required.map(skill => <span className="skill-pill gap" key={skill}>{skill}</span>) : <small>None for required skills</small>}</div></div><button className="button secondary full" onClick={() => onCandidate(result.candidate_id)}>View evidence and prepare <ArrowRight size={17} /></button></article>)}</div> : <div className="panel empty-state">No candidates yet. <button className="inline-link" onClick={onDocuments}>Add a CV <ArrowRight size={15} /></button></div>}
  </>
}

function CandidateView({ analysis, stage, onBack, onDrafts, onAsk }: { analysis: Analysis; stage?: { stage: string; assessment: string }; onBack: () => void; onDrafts: () => void; onAsk: () => void }) {
  const { candidate, jd, match, summary, questions } = analysis
  const skills = [...jd.required.map(skill => ({ skill, category: 'Required', found: match.matched_required.includes(skill) })), ...jd.preferred.map(skill => ({ skill, category: 'Preferred', found: match.matched_preferred.includes(skill) }))]
  return <><button className="back-link" onClick={onBack}><ArrowLeft size={17} /> Back to comparison</button><div className="page-heading candidate-heading"><div><span className="eyebrow">CANDIDATE REVIEW</span><h1>{candidate.name}</h1><p>{jd.title} · {scoreLabel(match.score)}</p></div><div className="heading-actions"><button className="button secondary" onClick={onDrafts}>Draft email</button><button className="button primary" onClick={onAsk}>Ask about candidate <MessageCircle size={17} /></button></div></div>
    <div className="analysis-top"><section className="panel score-panel"><div><span className="eyebrow">ATS-STYLE JD ALIGNMENT</span><h2>{match.score}% alignment</h2><p>Based on skills and wording in the supplied documents.</p></div><ScoreDonut score={match.score} /></section><section className="panel breakdown-panel"><span className="eyebrow">SCORE BREAKDOWN</span><ScoreBar label="Required skills · 70% weight" value={match.required_percent} /><ScoreBar label="Preferred skills · 20% weight" value={match.preferred_percent} /><ScoreBar label="Wording similarity · 10% weight" value={match.similarity_percent} /></section></div>
    <div className="analysis-grid"><section className="panel evidence-panel"><div className="section-heading compact"><div><span className="eyebrow">DOCUMENT EVIDENCE</span><h2>Skills against the role</h2></div></div><div className="table-wrap"><table><thead><tr><th>Skill</th><th>Type</th><th>CV evidence</th></tr></thead><tbody>{skills.map(item => <tr key={item.skill}><td><strong>{item.skill}</strong></td><td>{item.category}</td><td>{item.found ? <><span className="evidence-status found"><Check size={14} /> Found</span><p className="evidence-quote">“{match.evidence[item.skill]?.text}” <small>{match.evidence[item.skill]?.location}</small></p></> : <span className="evidence-status gap">No evidence found</span>}</td></tr>)}</tbody></table></div></section><aside className="analysis-side"><section className="panel summary-panel"><span className="eyebrow">CANDIDATE SUMMARY</span><h3>At a glance</h3><p>{summary}</p>{stage && <div className="stage-note"><b>Sample recruitment stage</b><span>{stage.stage}</span><small>{stage.assessment}</small></div>}</section><section className="panel questions-panel"><span className="eyebrow">INTERVIEW PREPARATION</span><h3>Questions to ask</h3><ol>{questions.map(question => <li key={question}>{question}</li>)}</ol></section></aside></div>
  </>
}

function Drafts({ workspace, run }: { workspace: Workspace; run: (action: () => Promise<unknown>, success?: string) => Promise<void> }) {
  const [candidateId, setCandidateId] = useState(workspace.candidates[0]?.id || '')
  const [kind, setKind] = useState('invitation')
  const [date, setDate] = useState('')
  const [time, setTime] = useState('')
  const [link, setLink] = useState('')
  const [editing, setEditing] = useState<Record<string, string>>({})
  const [copied, setCopied] = useState<string | null>(null)
  async function generate(event: FormEvent) { event.preventDefault(); await run(() => api('/api/drafts/generate', { method: 'POST', body: json({ candidate_id: candidateId, kind, date, time, link }) }), 'Draft created. Review it before sending.') }
  async function copy(id: string, value: string) { await navigator.clipboard.writeText(value); setCopied(id); setTimeout(() => setCopied(null), 2200) }
  return <><div className="page-heading"><div><span className="eyebrow">COMMUNICATION</span><h1>Email drafts</h1><p>Create a starting point, then make it yours.</p></div></div><div className="draft-layout"><section className="panel draft-form-panel"><span className="eyebrow">NEW DRAFT</span><h2>What would you like to write?</h2><form onSubmit={generate}><label>Candidate<select value={candidateId} onChange={e => setCandidateId(e.target.value)} required>{workspace.candidates.map(candidate => <option value={candidate.id} key={candidate.id}>{candidate.name}</option>)}</select></label><label>Message type<select value={kind} onChange={e => setKind(e.target.value)}><option value="invitation">Interview invitation</option><option value="assessment">Assessment instructions</option></select></label><div className="form-pair"><label>{kind === 'assessment' ? 'Deadline' : 'Interview date'}<input type="date" value={date} onChange={e => setDate(e.target.value)} /></label><label>Time<input type="time" value={time} onChange={e => setTime(e.target.value)} /></label></div><label>{kind === 'assessment' ? 'Assessment link' : 'Meeting link or location'}<input value={link} onChange={e => setLink(e.target.value)} placeholder={kind === 'assessment' ? 'https://…' : 'Video link or address'} /></label><button className="button primary full" disabled={!candidateId}>Create draft <ArrowRight size={17} /></button></form><small className="draft-hint">Drafts are prepared here only. Copy and send them from your own email.</small></section><section className="draft-output"><div className="section-heading compact"><div><span className="eyebrow">YOUR DRAFTS</span><h2>{workspace.drafts.length ? `${workspace.drafts.length} saved draft${workspace.drafts.length === 1 ? '' : 's'}` : 'No drafts yet'}</h2></div></div>{workspace.drafts.length ? [...workspace.drafts].reverse().map(draft => <article className="panel draft-card" key={draft.id}><div className="draft-card-head"><div><span className="eyebrow">{draft.kind === 'invitation' ? 'INTERVIEW INVITATION' : 'ASSESSMENT INSTRUCTIONS'}</span><h3>{draft.candidate_name}</h3><p>{draft.job_title}</p></div><button className="icon-button delete-button" aria-label={`Delete draft for ${draft.candidate_name}`} onClick={() => run(() => api(`/api/drafts/${draft.id}`, { method: 'DELETE' }), 'Draft deleted.')}><Trash2 size={17} /></button></div><textarea aria-label={`Email draft for ${draft.candidate_name}`} value={editing[draft.id] ?? draft.text} onChange={e => setEditing({ ...editing, [draft.id]: e.target.value })} rows={11} /><div className="draft-actions"><button className="button secondary" onClick={() => run(() => api(`/api/drafts/${draft.id}`, { method: 'PATCH', body: json({ text: editing[draft.id] ?? draft.text }) }), 'Draft saved.')}>Save edits</button><button className="button primary" onClick={() => copy(draft.id, editing[draft.id] ?? draft.text)}>{copied === draft.id ? 'Copied' : 'Copy text'}</button></div></article>) : <div className="panel empty-state">Select a candidate and create a draft to get started.</div>}</section></div></>
}

function ChatDrawer({ workspace, initialCandidateId, onClose }: { workspace: Workspace | null; initialCandidateId?: string; onClose: () => void }) {
  const [question, setQuestion] = useState('')
  const [candidateId, setCandidateId] = useState(initialCandidateId || '')
  const [messages, setMessages] = useState<ChatMessage[]>([{ role: 'assistant', text: 'Hi. Ask me about a candidate, a role, or interview preparation. I’ll use the documents in this workspace.' }])
  const [busy, setBusy] = useState(false)
  async function send(value = question) {
    if (!value.trim() || busy) return
    setMessages(prev => [...prev, { role: 'user', text: value }]); setQuestion(''); setBusy(true)
    try { const reply = await api<{ text: string; citations: Evidence[] }>('/api/chat', { method: 'POST', body: json({ question: value, candidate_id: candidateId || null }) }); setMessages(prev => [...prev, { role: 'assistant', ...reply }]) }
    catch (err) { setMessages(prev => [...prev, { role: 'assistant', text: (err as Error).message }]) }
    finally { setBusy(false) }
  }
  return <div className="chat-drawer" role="dialog" aria-label="Recruiter assistant"><div className="chat-header"><span className="chat-header-icon"><MessageCircle size={20} /></span><div><strong>Recruiter assistant</strong><small>Grounded in this workspace</small></div><button className="icon-button" aria-label="Close chat" onClick={onClose}><X size={20} /></button></div><div className="chat-context"><label>Discussing <select value={candidateId} onChange={e => setCandidateId(e.target.value)}><option value="">All candidates</option>{workspace?.candidates.map(candidate => <option key={candidate.id} value={candidate.id}>{candidate.name}</option>)}</select></label></div><div className="chat-messages" aria-live="polite">{messages.map((message, index) => <div className={`chat-message ${message.role}`} key={index}><div>{message.text}</div>{message.citations?.length ? <details><summary>{message.citations.length} source{message.citations.length === 1 ? '' : 's'}</summary>{message.citations.map(citation => <p key={citation.id}><b>{citation.source} · {citation.location}</b><br />{citation.text}</p>)}</details> : null}</div>)}{busy && <div className="chat-message assistant">Looking through the documents…</div>}</div><div className="chat-suggestions">{['Who is the top match?', 'What should I ask the top match?'].map(prompt => <button key={prompt} onClick={() => send(prompt)}>{prompt}</button>)}</div><form className="chat-compose" onSubmit={event => { event.preventDefault(); send() }}><input aria-label="Ask a recruitment question" value={question} onChange={e => setQuestion(e.target.value)} placeholder="Ask a recruitment question…" /><button className="send-button" aria-label="Send message" disabled={!question.trim() || busy}><Send size={18} /></button></form></div>
}
