# Stitch brief: Recruiter AI workspace

Design a polished, responsive web application for an AI-powered recruiter assistant. The implementation target is a React frontend with a Python FastAPI backend, deployed as one public web app. Create complete desktop and mobile screens in both light and dark modes. The interface should feel like a trustworthy professional hiring tool: clear, warm, calm, and visually engaging. Use synthetic candidate data only.

## Product promise and core journey

A recruiter should be able to open the link and, within two minutes, select or paste a job description, add one or more CVs, inspect an evidence-based ranked shortlist, understand one candidate's fit through charts and a skill table, ask an open-ended question in a floating chat window, and generate interview questions or a recruitment email draft. Include sample data so the experience works before any upload. The reviewer needs no login or API key.

## Navigation and layout

- Desktop: 240 px left navigation rail, central content up to 1440 px, compact top bar. Nav items: Overview, Jobs & CVs, Compare, Drafts. A persistent round Assistant button floats at the bottom-right of every workspace screen.
- Mobile: compact top bar and bottom navigation; cards stack vertically. The floating Assistant button remains above bottom navigation. Chat opens as a nearly full-screen sheet on mobile and a 420 px right drawer on desktop.
- Top bar: product mark `Recruiter AI`, active job selector, light/dark toggle, sample-data badge, and an AI status chip (`AI connected` or `Basic mode`). Do not imply that basic mode can answer arbitrary questions.
- Use a clear page heading, one sentence of guidance, and a prominent next action on each screen. Provide breadcrumbs when opening a candidate detail view.

## Screen 1: Overview / demo landing

- Hero: `Find the evidence behind every shortlist.` Subtext: `Compare CVs with a job, ask questions, and prepare the next conversation.`
- Primary action: `Explore sample candidates`; secondary action: `Add a job description`.
- Show three small preview stats from synthetic data: Jobs, Candidates, Drafts ready. Show a 3-step visual (`Add documents → Compare evidence → Prepare outreach`).
- Below the hero, show two sample job cards with role title, required skill chips, candidate count, and `Open comparison` action.
- Footer note: `Sample data is synthetic. Uploaded documents stay in this session.`
- Transition: sample job card opens Screen 3 with that JD selected. Add-job action opens Screen 2.

## Screen 2: Jobs & CVs / input workspace

Use two clearly separated panels with equal visual weight on desktop, stacked on mobile.

### Job description panel

- Heading `1. Job description`.
- Tabs: `Upload file`, `Paste text`, `Use sample`.
- Upload accepts one PDF, DOCX, or TXT file; show a drop zone, file name, size, replacement action, and extraction status.
- Paste tab has `Role title` field and a large multiline JD text box with character count and `Use this JD` action. Retain pasted text when switching tabs until explicitly cleared.
- Sample tab lists the synthetic JDs. Selecting one shows a read-only preview and `Use sample` action.
- After processing, show extracted role title, required and preferred skill chips, and an `Edit requirements` action. The recruiter can correct parsed requirements before scoring.

### Candidate CV panel

- Heading `2. Candidate CVs`.
- Tabs: `Upload files`, `Paste CV`, `Use samples`.
- Upload accepts multiple PDF, DOCX, or TXT files; show one row per candidate with extraction status and remove/replace actions.
- Paste tab has `Candidate display name` and multiline CV text box; `Add candidate` appends it to the current list. Display names are synthetic or entered by the recruiter.
- Sample tab adds all or selected sample CVs. The list shows source (`Sample`, `Upload`, `Pasted`), extracted-text preview, and a remove action.
- Bottom sticky action: `Compare candidates`, enabled only when there is one active JD and at least one readable CV. Explain disabled states inline.
- Error states: unsupported file, empty text, oversized file, and scanned PDF with no extractable text. Keep successfully processed files even if one file fails.
- Transition: `Compare candidates` opens Screen 3.

## Screen 3: Compare / ranked shortlist

- Header: selected role, candidate count, last analysis timestamp for the current session, and `Change documents` action.
- A one-line method note: `ATS-style JD alignment is this app's evidence-based comparison, not a score from an external ATS.` Link `How is this calculated?` opens an explanation popover.
- Summary strip: number with strong alignment, number with possible alignment, and number with limited evidence. Label all counts in text, not only color.
- Ranked candidate cards or table: rank, display name, ATS-style JD alignment percentage, alignment band, matched required skills count, requirements without CV evidence count, and `View evidence` action. Sort by score by default; allow sorting by name or required skills.
- Score bands: `Strong alignment` 80–100%, `Possible alignment` 60–79%, `Limited evidence` 0–59%. Avoid labels such as `bad candidate` or `rejected`.
- Hover or focus on a skill chip reveals a short evidence snippet. Clicking a candidate opens Screen 4. Clicking `Ask Assistant` opens chat with the current JD in context and a suggested comparison prompt.
- Empty state explains the minimum documents needed and links back to Screen 2.

## Screen 4: Candidate detail / evidence dashboard

### Header

- Breadcrumb `Compare / Candidate name`; candidate name, selected job, source label, alignment band, and large percentage score.
- Actions: `Generate summary`, `Create interview questions`, `Draft email`, and `Ask Assistant`.

### Visual comparison

- An overall donut chart shows the ATS-style JD alignment percentage. Center label includes percentage and `JD alignment`; a nearby plain-text sentence explains it.
- A grouped horizontal bar chart compares `Required skills`, `Preferred skills`, and `JD language similarity` for this CV. For required and preferred skills show `found` and `not evidenced` portions. For language similarity show a single 0–100 bar. Include exact values and tooltips.
- A compact score-breakdown panel explains the weighting: 70% required-skill coverage, 20% preferred-skill coverage, 10% JD/CV text similarity. If a category is empty, explain that its weight is redistributed. Avoid a mystery score.
- Chart interactions: selecting a bar filters the skills table to that category; clicking the donut clears the filter. The charts never replace the table or evidence.
- Add a `JD terminology` strip beneath the bars: the most relevant non-skill terms extracted from the JD, split into `Seen in CV` and `Not seen in CV`, with a short source excerpt on click. Explain that term overlap contributes to the text-similarity component and a missing word can be expressed differently in a CV.

### Skills and evidence table

- Columns: `JD requirement`, `Priority`, `CV status`, `Evidence`, `Action`.
- Status values: `Found in CV` and `No evidence found`. Show the matched phrase and source location for found skills. For no-evidence rows, state `Not found in this CV` and offer `Ask interview follow-up`.
- Filter chips: All, Required, Preferred, Found, No evidence. Search by skill name. Each found row expands to the exact CV excerpt and JD requirement text. Never infer proficiency from a mere mention.
- Add a small note: `No evidence found does not mean the candidate lacks this skill.`

### Preparation area

- Tabs: `Summary`, `Interview questions`, `Email draft`.
- Summary: concise, grounded paragraphs: relevant experience, matching evidence, points to verify. Show source chips.
- Interview questions: 5–7 questions grouped by strengths to explore and gaps to verify. Each question shows the JD requirement that prompted it. Allow regenerate and copy.
- Email draft: choose `Interview invitation` or `Assessment instructions`. Fields for date/time, meeting link, assessment details, and deadline appear only when relevant. Generated content is editable, copyable, and downloadable as text; there is no Send button.
- Transition: `Ask Assistant` opens the chat drawer with this candidate and job selected. `Back to shortlist` returns to Screen 3 without losing state.

## Persistent floating Assistant

- Closed: circular 56 px button at bottom-right with a chat/spark icon, accessible label `Open recruiter assistant`, soft shadow, and a subtle online/status dot. No distracting continuous animation.
- Open on desktop: right drawer about 420 px wide, full viewport height beneath the top bar, with a visible close control. Open on mobile: full-height sheet. Preserve the underlying page and selection.
- Header shows `Recruiter Assistant`, context chips (`Current job`, `Selected candidate`), and status (`AI connected` or `Basic mode`). Allow changing context without closing the drawer.
- First-open prompts: `Why is the top candidate ranked first?`, `Compare two candidates`, `What should I ask in an interview?`, `Draft an invitation`.
- Chat turns show readable text, expandable evidence citations linking to the relevant CV/JD passage or recruitment record, and action cards when a generated draft can be opened in Screen 4. Candidate-specific factual answers must cite supplied data. General recruiter advice should be labeled `General advice`.
- Input placeholder: `Ask about candidates, this job, interviews, or outreach…`. Enter sends; Shift+Enter adds a line break. Show typing/loading state, retry on failure, and a clear notice when the AI service is temporarily unavailable. In basic mode, suggest supported example questions.
- Out-of-scope questions receive a polite redirect to recruitment work. Never state an unknown candidate fact as certain.

## Theme and visual tokens

Use the same information hierarchy in both themes, with a visible theme toggle and system preference as initial default. Palette should be professional with teal as the action color, indigo as the insight color, and amber for items to verify. Use color with text labels and icons, never as the sole status signal.

| Token | Light | Dark | Use |
|---|---|---|---|
| Canvas | `#F7F9FC` | `#0B1220` | Page background |
| Surface | `#FFFFFF` | `#141E2E` | Cards, drawers, modals |
| Raised surface | `#EDF3F7` | `#1B2A3D` | Hover and nested panels |
| Primary text | `#172338` | `#F1F6FC` | Headings and body |
| Secondary text | `#526277` | `#A9B9CC` | Explanatory text |
| Brand/action | `#087E83` | `#37C6BE` | Primary buttons, links, selected states |
| Insight | `#5146B9` | `#A79BFF` | Charts and AI cues |
| Positive | `#087F59` | `#48D6A0` | Found evidence |
| Verify | `#9A6700` | `#F5C76A` | No evidence / follow-up |
| Border | `#DCE5EC` | `#314258` | Dividers, input outlines |
| Focus ring | `#0B8F92` | `#7CE4DC` | Keyboard focus |

- Typography: use Inter or a similar highly legible sans-serif. Headings 28–32 px desktop and 24 px mobile; body 15–16 px; labels 13–14 px. Use tabular numerals for scores.
- Spacing: 8 px grid, 16–24 px card padding, 12–16 px corner radii, restrained shadows. Make the charts colorful but keep data labels high contrast.
- Motion: 150–220 ms transitions for drawer, tabs, hover, and chart filtering. Respect reduced-motion preference. Avoid parallax and celebratory effects for candidate ranking.
- Accessibility: aim for WCAG AA contrast, visible focus, keyboard navigation, screen-reader labels for charts and upload controls, chart text alternatives, and touch targets at least 44 px.

## Responsive behavior and states

- At tablet widths, collapse the navigation rail to icons and stack input panels. At mobile widths, use bottom navigation, one-column cards, a full-screen chat sheet, and horizontally scrollable skills table or equivalent stacked rows.
- Show skeleton/loading states during extraction, scoring, and AI generation. Preserve current data on recoverable errors.
- Distinguish `No CVs added`, `No extractable text`, `AI quota reached`, and `No evidence in supplied data` states. Give a direct next action in each.
- Never auto-send emails or silently discard pasted text. Confirm only destructive clearing of a full session.

## Synthetic content for mockups

Use a `Senior Data Engineer` JD requiring Python, SQL, Airflow, and data pipelines, with AWS preferred. Use synthetic candidates `Maya Shah`, `Arjun Rao`, and `Neha Iyer`; their CVs should have deliberately different evidence so charts and missing-skill rows are meaningful. Use fictional email domains and avoid real personal details. Sample chat prompt: `Maya mentions Airflow. What should I ask to check whether she owned a production pipeline?` Sample answer must distinguish CV evidence from what needs verifying.

## Stitch delivery request

Produce all listed screens in light and dark desktop views plus mobile versions of input, candidate detail, and open chat. Show the closed/open floating assistant, upload and paste tabs, an error state, a ranking view, expanded evidence rows, charts, and an editable email draft. Include a clickable transition map connecting the actions above. Keep chart components and design tokens consistent across every screen. Do not add hiring decisions, automatic rejection, or an email Send action.
