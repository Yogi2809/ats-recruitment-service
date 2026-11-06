---
name: Evidence Precision
colors:
  surface: '#f9f9ff'
  surface-dim: '#d0daef'
  surface-bright: '#f9f9ff'
  surface-container-lowest: '#ffffff'
  surface-container-low: '#f0f3ff'
  surface-container: '#e7eeff'
  surface-container-high: '#dee8fe'
  surface-container-highest: '#d9e3f8'
  on-surface: '#121c2b'
  on-surface-variant: '#3e4949'
  inverse-surface: '#273141'
  inverse-on-surface: '#ebf1ff'
  outline: '#6e797a'
  outline-variant: '#bdc9c9'
  surface-tint: '#00696d'
  primary: '#006367'
  on-primary: '#ffffff'
  primary-container: '#087e83'
  on-primary-container: '#defdff'
  inverse-primary: '#79d5da'
  secondary: '#584dc0'
  on-secondary: '#ffffff'
  secondary-container: '#9087fd'
  on-secondary-container: '#26108f'
  tertiary: '#006646'
  on-tertiary: '#ffffff'
  tertiary-container: '#0e815b'
  on-tertiary-container: '#ddffeb'
  error: '#ba1a1a'
  on-error: '#ffffff'
  error-container: '#ffdad6'
  on-error-container: '#93000a'
  primary-fixed: '#96f1f7'
  primary-fixed-dim: '#79d5da'
  on-primary-fixed: '#002021'
  on-primary-fixed-variant: '#004f53'
  secondary-fixed: '#e4dfff'
  secondary-fixed-dim: '#c5c0ff'
  on-secondary-fixed: '#140067'
  on-secondary-fixed-variant: '#4033a7'
  tertiary-fixed: '#94f6c7'
  tertiary-fixed-dim: '#78d9ac'
  on-tertiary-fixed: '#002114'
  on-tertiary-fixed-variant: '#005137'
  background: '#f9f9ff'
  on-background: '#121c2b'
  surface-variant: '#d9e3f8'
typography:
  headline-xl:
    fontFamily: Inter
    fontSize: 32px
    fontWeight: '600'
    lineHeight: 40px
  headline-xl-mobile:
    fontFamily: Inter
    fontSize: 26px
    fontWeight: '600'
    lineHeight: 34px
  headline-lg:
    fontFamily: Inter
    fontSize: 24px
    fontWeight: '600'
    lineHeight: 32px
  headline-md:
    fontFamily: Inter
    fontSize: 20px
    fontWeight: '600'
    lineHeight: 28px
  headline-sm:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '600'
    lineHeight: 24px
  body-lg:
    fontFamily: Inter
    fontSize: 16px
    fontWeight: '400'
    lineHeight: 24px
  body-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '400'
    lineHeight: 20px
  body-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '400'
    lineHeight: 18px
  label-lg:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  label-md:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
  label-sm:
    fontFamily: Inter
    fontSize: 11px
    fontWeight: '600'
    lineHeight: 14px
  tabular-numeric-lg:
    fontFamily: Inter
    fontSize: 22px
    fontWeight: '600'
    lineHeight: 28px
  tabular-numeric-md:
    fontFamily: Inter
    fontSize: 14px
    fontWeight: '500'
    lineHeight: 20px
  tabular-numeric-sm:
    fontFamily: Inter
    fontSize: 12px
    fontWeight: '500'
    lineHeight: 16px
rounded:
  sm: 0.25rem
  DEFAULT: 0.5rem
  md: 0.75rem
  lg: 1rem
  xl: 1.5rem
  full: 9999px
spacing:
  gutter: 1rem
  gutter-desktop: 1.5rem
  margin: 1rem
  margin-desktop: 2rem
  space-xs: 0.25rem
  space-sm: 0.5rem
  space-md: 1rem
  space-lg: 1.5rem
  space-xl: 2rem
---

## Brand & Style

### Brand Personality & Philosophy
This design system sets the standard for an AI-native, evidence-based recruitment platform. It embodies calm authority, clinical precision, and analytical clarity. Rather than generating opaque "magic" hiring recommendations, the interface surfaces auditable facts, verifiable candidate data, and measurable skill alignments. The emotional goal is to transform recruiter cognitive fatigue into confident, defensible decision-making.

### Visual Aesthetic & Movement
The visual language merges **Corporate / Modern** utilitarian discipline with **Tactile Analytical Minimalist** accents:
- **Calm, High-Information Density:** Spatially structured workspaces that avoid decorative clutter to prioritize scanning speed, comparative reading, and tabular data consumption.
- **Auditable Visual Anchors:** Color and elevation are reserved strictly for semantic utility. Visual flourishes occur only as contextual signals: verified evidence states, AI reasoning traces, and risk signals.
- **Architectural Structure:** Strict grid alignment, hairline boundaries, and dedicated spatial lanes establish an environment reminiscent of high-end clinical instrumentation and advanced analytical suites.

## Colors

### Palette Architecture & Semantic Intent
The color strategy enforces distinct cognitive lanes across light and dark modes, ensuring non-ambiguous visual categorization and strict WCAG 2.1 AA compliance (minimum 4.5:1 for normal text, 3:1 for graphical indicators and large text).

#### Core Palette Roles
- **Primary Action (Deep Teal):** `#087E83` (Light) / `#37C6BE` (Dark). Guides the human-driven workflow: primary CTA buttons, selected navigation states, interactive slider controls, and candidate decision locks.
- **Insight & Reasoning (Insight Indigo):** `#5146B9` (Light) / `#A79BFF` (Dark). Denotes automated synthesis: algorithmic confidence scoring, copilot drawer affordances, data charts, and generative summary panels.
- **Verified Evidence (Positive Green):** `#087F59` (Light) / `#48D6A0` (Dark). Exclusively applied to confirmed candidate skills, validated work experience, reference matches, and authenticated credentials.
- **Pending Verification (Amber Warning):** `#9A6700` (Light) / `#F5C76A` (Dark). Reserved for flagged claims, unverified resume entries, missing references, and interview discrepancies requiring manual probe.
- **Critical Risk (Red Accent):** `#C92A2A` (Light) / `#FF8787` (Dark). Highlighted anomalies, compliance blockers, or strict job requirement mismatches.

#### Neutral & Surface Strategy
- **Light Theme Surfaces:**
  - App Canvas (Background): `#F7F9FC`
  - Base Surface (Cards, Rails, Drawers): `#FFFFFF`
  - Secondary Container (Filters, Inset panels): `#EEF2F6`
  - Outline / Divider (Subtle): `#D8E0EA`
  - Text Primary: `#0F172A`
  - Text Secondary: `#475569`
  - Text Muted: `#64748B`
- **Dark Theme Surfaces:**
  - App Canvas (Background): `#0B1220`
  - Base Surface (Cards, Rails, Drawers): `#141E2E`
  - Secondary Container (Filters, Inset panels): `#1C293D`
  - Outline / Divider (Subtle): `#283950`
  - Text Primary: `#F1F5F9`
  - Text Secondary: `#94A3B8`
  - Text Muted: `#64748B`

## Typography

### Structural Principles
The typography architecture is built entirely on `Inter` to leverage high x-height, extensive weight variations, and native OpenType tabular figures (`tnum`).

### Numerical & Tabular Data Execution
All match scores, match percentages, duration logs, and metric comparisons must explicitly enable:
- `font-feature-settings: "tnum" 1, "cv05" 1;`
This prevents horizontal jitter when values update in real-time, keeps decimal points and alignment bars strictly comparable across table columns, and guarantees instantaneous legibility.

### Hierarchy & Text Applications
- **Headlines (`headline-xl`, `headline-lg`):** Candidate profile names, job requisition titles, and high-level pipeline overviews.
- **Section Headers (`headline-md`, `headline-sm`):** Sub-panel headers, card group containers, and score category classifications.
- **Analytical & Body Copy (`body-lg`, `body-md`, `body-sm`):** Resume text extractions, interview transcript excerpts, AI summary blurbs, and user notes.
- **Labels & Micro-copy (`label-lg`, `label-md`, `label-sm`):** Metadata keys, pill tags, badge states, and action triggers. Uppercase transformations (`label-sm`) must use letter-spacing `0.05em`.

## Layout & Spacing

### Layout Architecture
The application layout uses an operational dashboard model composed of persistent layout regions, dual-panel workspaces, and overlay drawers:

1. **Primary Navigation Rail (Left):**
   - Desktop width: `240px` fixed.
   - Houses global product areas (Requisitions, Pipeline, Talent Database, Insights, Settings).
   - Collapses to a compact icon-rail (`64px`) on tablet screens and converts to a hidden off-canvas drawer on mobile.

2. **Dual-Panel Workspace (Main Viewport):**
   - Designed for simultaneous evidence evaluation and decision input.
   - **Left Panel (Evidence Viewer):** 60% standard width (min `560px`). Displays source resumes, verified work traces, and interview audio/video transcripts with inline citation anchors.
   - **Right Panel (Alignment & Analysis):** 40% standard width (min `420px`). Displays AI requirement rubrics, score cards, and verification task lists.
   - The boundary between panels supports an adjustable drag affordance (min constraint 35% / 65%).

3. **Floating AI Assistant Drawer (Right Overlay):**
   - Contextual assistant width: `380px` fixed.
   - Sits at `z-index: 40`, floating `1rem` off the right edge and bottom bar with an internal scrolling query history and prompt dock.

### Responsive Breakpoints & Reflow Rules
- **Desktop (>= 1280px):** Full dual-panel layout active. Navigation rail at 240px. Gutters at `1.5rem` (`24px`).
- **Tablet (768px - 1279px):** Navigation rail collapses to 64px icon dock. The dual-panel view switches to a segmented tabbed view ("Evidence Source" vs. "Analysis Rubric") with a sticky bottom switch bar. Assistant drawer behaves as an overlay modal.
- **Mobile (< 768px):** Single-column stack. Outer margins reduce to `1rem` (`16px`). High-density score summaries collapse to accordion headers.

## Elevation & Depth

### Philosophy: Tonal Surfaces & Structural Outlines
To ensure readability and prevent visual distraction during prolonged recruiter sessions, depth is communicated primarily through structural surface contrast and crisp 1px borders, rather than dramatic drop shadows.

### Surface Elevation Levels

1. **Level 0 (Base Canvas):**
   - Light: `#F7F9FC` | Dark: `#0B1220`
   - Flat canvas foundation. Zero elevation.

2. **Level 1 (Card & Content Containers):**
   - Light: `#FFFFFF` with `1px solid #D8E0EA`
   - Dark: `#141E2E` with `1px solid #283950`
   - Subtle ambient elevation: `0 1px 3px 0 rgba(15, 23, 42, 0.04)`.
   - Used for ATS candidate cards, alignment tables, and data containers.

3. **Level 2 (Interactive Floating Elements & Dropdowns):**
   - Light: `#FFFFFF` with `1px solid #CBD5E1`
   - Dark: `#1C293D` with `1px solid #334661`
   - Ambient drop shadow: `0 4px 12px -2px rgba(15, 23, 42, 0.08), 0 2px 6px -1px rgba(15, 23, 42, 0.04)`.
   - Used for filter menus, contextual action toolbars, and hover popovers.

4. **Level 3 (Assistant Drawer & Modal Overlays):**
   - Light: `#FFFFFF` with `1px solid #CBD5E1`
   - Dark: `#141E2E` with `1px solid #3A4D6B`
   - Directional shadow: `-4px 0 24px -4px rgba(15, 23, 42, 0.12), -2px 0 8px -2px rgba(15, 23, 42, 0.06)`.
   - Used for the slide-out conversational copilot and deep-dive verification dialogs.

## Shapes

### Corner Radii Guidelines
With `roundedness: 2`, the system utilizes balanced, geometric radii that project modern professionalism without feeling overly playful:
- **Base Geometry (`0.5rem` / `8px`):** Default for standard buttons, input fields, dropdown trigger buttons, and small metric containers.
- **Large Surface Geometry (`1rem` / `16px`):** ATS candidate cards, dual-panel container edges, modal shells, and chart wrappers.
- **Pill Geometry (`9999px`):** Reserved exclusively for semantic chips, evidence tags, status pills, and numeric score badges.
- **Micro Radii (`0.25rem` / `4px`):** Checkboxes, segmented data progress bars, chart bars, and tooltip frames.

## Components

### 1. Buttons
- **Primary Action:** Solid Deep Teal (`#087E83` light / `#37C6BE` dark) background with high-contrast text (`#FFFFFF` in light mode, `#0B1220` in dark mode). Border-radius `0.5rem`. Height: `36px` (compact) or `40px` (default).
- **Secondary / Ghost:** Transparent background with subtle border (`1px solid #D8E0EA` light, `#283950` dark). Hover state adopts container tint.
- **AI Action Button:** Subtle indigo gradient border with Insight Indigo text (`#5146B9` light / `#A79BFF` dark) accompanied by a spark icon; triggers copilot synthesis.

### 2. Multi-Tier Evidence Status Pills
Pills communicate verification state at a glance using a 3-part micro-anatomy: 
- `[Status Icon] [Verification Tier] [Count or Label]`
- **Verified Tier:** Light positive green background (`#E6F7F0` light, `#0D3325` dark), text `#087F59` / `#48D6A0`, border `1px solid #A3E3CB` / `#165A3F`. Icon: check-circle-solid.
- **To-Verify Tier:** Amber background (`#FFF8E6` light, `#362400` dark), text `#9A6700` / `#F5C76A`, border `1px solid #FADF9E` / `#5C4006`. Icon: alert-circle-outline.
- **AI Suggested / Inferred:** Insight Indigo tint (`#EEEDFA` light, `#201B4D` dark), text `#5146B9` / `#A79BFF`, border `1px solid #C9C4F7` / `#393183`. Icon: sparkle-outline.

### 3. ATS Alignment Cards
- Structural layout: 3-column card design.
  - Column 1: Candidate identity, source, current role, and match score badge.
  - Column 2: Core requirement checklist (evidence pills with matched vs. unmatched signals).
  - Column 3: Mini horizontal bar rubric and rapid-action menu (Shortlist, Verify, Reject).
- Visual Style: Level 1 surface, hover border shifts to Primary Deep Teal, interactive click reveals full workspace view.

### 4. Interactive Data Visualizations
- **Match Score Donut:** A high-contrast SVG circular indicator (size: `48px` small, `80px` large). Stroke width `6px`. Track color is surface container; fill stroke uses Insight Indigo (`#5146B9` / `#A79BFF`) or Deep Teal based on metric type. Center houses Tabular Numeric text (`94%`).
- **Grouped Horizontal Rubric Bars:** Stacked criterion bars (e.g., "System Architecture", "Leadership", "Domain Fit").
  - Background track: height `6px`, radius `3px`, neutral surface tint.
  - Foreground bar: split dynamically into verified segments (Positive Green) and unconfirmed claims (Amber). Interactive hover reveals specific line-item citations.

### 5. Input Fields & Search Bars
- Background `#FFFFFF` (light) / `#141E2E` (dark), surrounded by `1px solid #D8E0EA` / `#283950`.
- Focus ring: `2px solid #087E83` (light) / `#37C6BE` (dark) with `0px` shadow offset.
- Global Search Bar includes integrated keyboard shortcut indicator (`⌘K`) with monospace styling.

### 6. Navigation Rail (240px)
- Fixed left lane with company workspace switcher at top, main nav items grouped into Core Hiring, Sourcing, and Pipeline.
- Active item uses soft primary tint background (`#E6F3F3` light / `#132E32` dark) with a `3px` solid indicator bar on the left edge.
- Bottom docked area houses recruiter profile, light/dark mode switch, and background AI sync status.

### 7. Floating Assistant Drawer
- Anchored to bottom right. Collapsed state is a compact indigo pill (`"Ask AI Assistant"` with shortcut `⌘J`).
- Expanded state (`380px` wide, `640px` max height): Header features conversation controls, body presents chat threads containing clickable citation tags linked directly to document highlighted regions in the Evidence Panel.