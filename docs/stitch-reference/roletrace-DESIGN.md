---
name: RoleTrace — Cobalt & Jade
colors:
  background: '#F6F8FC'
  surface: '#FFFFFF'
  surface-container: '#EEF2FA'
  on-surface: '#15233B'
  on-surface-variant: '#51617A'
  outline: '#D8E1ED'
  primary: '#3157C6'
  on-primary: '#FFFFFF'
  secondary: '#7553C7'
  tertiary: '#1B8069'
  warning: '#9A5B13'
  error: '#B42332'
---

# RoleTrace design system

RoleTrace is an evidence-based recruiter workspace. The visual style is calm, precise, welcoming, and professional. Use cobalt as the main action color, jade for CV evidence, violet for assistant insights, and amber for points to verify. Avoid the previous teal-heavy appearance. Do not make the interface look like a gaming dashboard or a generic AI chat product.

## Theme colors

Use these exact semantic colors across all screens. Theme values in the Stitch Theme tab should match this document.

| Role | Light mode | Dark mode | Application |
|---|---|---|---|
| Canvas | `#F6F8FC` | `#0C1425` | Page background |
| Surface | `#FFFFFF` | `#152039` | Cards, navigation, chat drawer, forms |
| Raised surface | `#EEF2FA` | `#1D2B49` | Nested panels, hover states, table headers |
| Main text | `#15233B` | `#F4F7FF` | Headings and body |
| Secondary text | `#51617A` | `#AFBDD3` | Supporting copy and labels |
| Border | `#D8E1ED` | `#334560` | Inputs, dividers, cards |
| Primary cobalt | `#3157C6` | `#9AB0FF` | Primary buttons, links, active navigation, chatbot launcher |
| Primary hover | `#2446A5` | `#B8C7FF` | Hover on primary controls |
| On primary | `#FFFFFF` | `#101B34` | Text and icons on primary buttons |
| Selected background | `#E8EDFF` | `#27345E` | Active navigation and selected tabs |
| Evidence jade | `#1B8069` | `#56D7AE` | Found-in-CV states and matching chart segments |
| Verification amber | `#9A5B13` | `#F6BF69` | No-evidence states and interview follow-ups |
| Insight violet | `#7553C7` | `#B9A2FF` | Chat insights, generated content, secondary chart series |
| Decorative coral | `#E78370` | `#FFAB98` | Tiny hero or illustration accent only |
| Error red | `#B42332` | `#FF8E95` | Form and upload errors |

Light mode uses an airy off-white canvas with white cards. Dark mode uses layered navy surfaces, never pure black. The two modes must have the same hierarchy and functionality. Do not use gradients behind tables or body text. A subtle cobalt-to-violet wash may appear only in the landing-page hero.

## Semantic rules

- Cobalt means an action the recruiter can take. Use it for the primary CTA, active navigation, links, and the floating chatbot icon.
- Jade means evidence was found in the supplied CV. It does not mean a skill was independently verified.
- Amber means the supplied CV did not establish a JD requirement. Label it `No evidence found`, not `Skill missing` or `Rejected`.
- Violet means an assistant-generated suggestion or explanation. It does not imply factual certainty.
- Red is reserved for actual errors. Never use it to label a candidate's rank or fit.
- Coral is decorative. Do not use coral for small text or controls.
- Every status has a readable text label and icon; color alone must not carry meaning.

## Typography

Use Inter for headings, body, labels, forms, charts, and data tables. Use 32 px / 600 for major desktop headings, 24 px / 600 for major mobile headings, 20 px / 600 for card titles, 16 px / 400 for body text, and 14 px / 500 for labels. Use tabular numerals for scores and percentages. Avoid all-caps body copy.

## Layout and components

Use an 8 px spacing grid, 16–24 px card padding, 12–16 px corner radius, thin borders, and restrained shadows. The desktop app has a left navigation rail and a roomy content area. On mobile, stack content into one column and keep all primary actions reachable.

Primary buttons are filled cobalt with the matching on-primary text color. Secondary buttons are light or dark raised surfaces with cobalt text and a visible border. Inputs have a visible focus ring in cobalt. Keep hover, active, disabled, loading, error, and success states consistent in every component.

The floating chatbot icon must sit above the page without covering other buttons. Clicking it opens the chat drawer or mobile sheet; clicking it must not trigger another action. The chat drawer uses the surface color with a subtle border and contains readable cited answers.

Charts use cobalt for overall JD alignment, jade for found evidence, amber for no evidence, and violet for assistant/contextual information. Include direct numbers, labels, and accessible text alternatives. Donut charts are paired with a breakdown table so the data remains understandable without color.

## Accuracy of product copy

Use `ATS-style JD alignment` for the app's own percentage. Do not claim that an external ATS produced it. Do not show invented `0 hallucinations`, `verified credentials`, `OCR`, `ATS export`, or fixed production metrics. Use synthetic sample data and label examples. A CV mention is document evidence, not independent skill verification.

## Motion and accessibility

Use subtle 150–220 ms transitions for menus, tabs, drawers, and chart filters. Respect reduced-motion preferences. Keep normal text at least 4.5:1 contrast and meaningful UI boundaries at least 3:1 where applicable. Show visible keyboard focus and use touch targets at least 44 px. Do not rely on color alone for any chart, status, or validation error.
