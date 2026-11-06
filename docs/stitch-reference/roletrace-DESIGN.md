---
name: RoleTrace — Paper & Ember
colors:
  background: '#F7F4EE'
  surface: '#FFFDF8'
  surface-container: '#EFE9DF'
  on-surface: '#27352F'
  on-surface-variant: '#59655C'
  outline: '#D9D0C2'
  primary: '#9B5742'
  on-primary: '#FFFFFF'
  secondary: '#356B55'
  tertiary: '#705A78'
  warning: '#8A5A22'
  error: '#AD4148'
---

# RoleTrace design system — Paper & Ember

RoleTrace is a human-centered recruiter workspace. Its visual identity should resemble a thoughtful editorial tool: warm paper, grounded ink, natural clay, quiet sage, and a small touch of plum. It should feel welcoming, precise, and trustworthy without neon, glassmorphism, or generic AI-dashboard gradients.

## Light and dark palettes

| Role | Name | Light mode | Dark mode |
|---|---|---|---|
| Page canvas | Warm Porcelain / Night Olive | `#F7F4EE` | `#191F1B` |
| Card surface | Paper / Deep Moss | `#FFFDF8` | `#232B26` |
| Nested surface | Oat Linen / Moss Slate | `#EFE9DF` | `#303A32` |
| Main text | Forest Ink / Warm Ivory | `#27352F` | `#F5F0E8` |
| Secondary text | Stone Sage / Soft Sage | `#59655C` | `#BEC8BA` |
| Border | Sandstone / Muted Fern | `#D9D0C2` | `#455348` |
| Control border | Dark Stone / Soft Fern | `#8A8F82` | `#7E907F` |
| Primary action | Ember Clay / Apricot Clay | `#9B5742` | `#E7A58A` |
| Primary hover | Fired Clay / Light Apricot | `#834431` | `#F2BA9F` |
| Text on primary | White / Dark Ink | `#FFFFFF` | `#211D19` |
| Selected navigation | Blush Linen / Clay Shadow | `#F3E3D9` | `#45342F` |
| Evidence found | Forest Sage / Soft Mint | `#356B55` | `#9ACAAD` |
| Needs verification | Deep Ochre / Honey | `#8A5A22` | `#EEC384` |
| Assistant insight | Muted Plum / Dusty Lilac | `#705A78` | `#CBB3CF` |
| Error | Brick Red / Soft Rose | `#AD4148` | `#F2A0A4` |

Use the warm neutrals for at least 80% of each screen. Clay is the only dominant accent. Sage, ochre, and plum are reserved for meaning. Do not use all accent colors in one card. Light mode should look like crisp paper; dark mode should look like layered dark olive, never pure black.

## Semantic rules

- Clay marks actions: primary buttons, active controls, focused inputs, links, and the floating chatbot launcher.
- Sage marks CV evidence found. It does **not** imply independent verification of a skill or credential.
- Ochre marks a requirement for which the CV has no evidence. Use `No evidence found`; never label a person `Rejected` or `Unqualified`.
- Plum marks assistant-generated content and interview suggestions, not factual certainty.
- Red is for actual form, upload, or service errors only.
- Every chart and status includes a label and value. Color must never be the only explanation.

## Typography and character

Use **Manrope** for headings and **Source Sans 3** for body text and controls. This pairing is softer and more human than an all-Inter dashboard while remaining easy to scan. If Stitch does not offer Source Sans 3, use Inter for body text. Use 32 px / 600 for desktop page headings, 24 px / 600 on mobile, 20 px / 600 for card headings, 16 px / 400 for body text, and 14 px / 500 for labels. Use tabular numerals for percentages and chart values.

Use plain-language labels such as `Evidence in CV`, `Needs a follow-up`, and `How this score was calculated`. Avoid technical or robotic labels such as `telemetry`, `AI engine`, `algorithmic parity`, `verification protocol`, or `zero hallucinations`.

## Layout and components

Use an 8 px spacing grid, 16–24 px card padding, 12–16 px corner radii, subtle borders, and minimal shadows. The product should feel like a calm desk with well-organized documents. Use generous white space around important decisions and compact spacing within comparison tables.

Primary buttons use Clay with the matching on-primary text color. Secondary buttons use a neutral surface and a visible control border. Inputs use the stronger control-border color and show a clay focus ring. The softer border is for noninteractive card dividers. Cards should be mostly flat; use small changes in surface color and border instead of large drop shadows. No glossy effects, glass panels, glowing outlines, or oversized AI sparkles.

The floating chatbot icon stays clear of sticky actions and navigation. Clicking it only opens chat. Chat uses the Paper or Deep Moss surface, with plum used sparingly for generated suggestions and clay for send actions. The drawer is comfortable for reading and never hides the entire evidence table on desktop.

Charts use clay for overall JD alignment, sage for evidence found, ochre for no evidence, and plum for assistant/contextual information. Pair the donut and bars with direct numbers, a score breakdown, and an evidence table. Avoid bright traffic-light grading of people.

## Light and dark consistency

Every screen—including login, account creation, overview, JD/CV inputs, comparison, candidate detail, drafts, and chat—must have both themes. Keep layouts, hierarchy, and interactions the same. Dark cards must remain visually separate from the dark canvas, with legible borders and text. Use the visible theme toggle and respect the browser's initial light/dark preference.

## Content accuracy

Call the percentage `ATS-style JD alignment`; it is this app's own comparison, not a score from an external ATS. Do not include invented system metrics, fixed candidate percentages presented as real results, independent credential verification, OCR, ATS export, or email sending. Sample candidate data must be labeled synthetic. A CV mention supports only the statement that the CV mentions it.

## Motion and accessibility

Use gentle 150–220 ms transitions for drawers, menus, tabs, and filters. Respect reduced-motion preference. Aim for at least 4.5:1 contrast for normal text and 3:1 for meaningful interface graphics. Keep visible focus states, clear form errors, and touch targets of at least 44 px. Never convey a chart result or error through color alone.
