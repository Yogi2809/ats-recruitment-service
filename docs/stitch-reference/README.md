# Extracted Stitch design reference

Source: private Stitch project `Recruiter AI Workspace`, project ID `4475403551809078684`, read on 6 November 2026 with the owner's supplied key. The key is not stored here.

| Screen | Screenshot | Generated HTML | Relevant design |
|---|---|---|---|
| Overview & Demo Landing | [overview.png](overview.png) | [overview.html](overview.html) | Navigation, hero, sample job cards, assistant launcher |
| Jobs & CVs Workspace | [inputs.png](inputs.png) | [inputs.html](inputs.html) | Separate JD/CV panels; upload, paste, and sample tabs; extraction states |
| Compare & Shortlist | [compare.png](compare.png) | [compare.html](compare.html) | Ranking bands, candidate cards, skill evidence overview |
| Candidate Detail & Evidence Dashboard | [candidate.png](candidate.png) | [candidate.html](candidate.html) | Donut, score breakdown, evidence table, preparation panel, chat drawer |

The project theme is in [design-system.md](design-system.md). These files are visual and markup references, not a functional app. The generated HTML uses Tailwind's CDN and static sample content. Rebuild components with real app state, responsive behavior, accessibility, and connected Python services.

## Adaptation notes

- The Stitch project currently has four desktop screens. It does not include mobile variants, dark variants, or a standalone Drafts screen. Follow `docs/stitch-ui-brief.md` for those states.
- Keep the left navigation, comparison cards, evidence table, and floating assistant. Replace Stitch's original teal/indigo palette with the Paper & Ember colors and Manrope/Source Sans 3 typography in `roletrace-DESIGN.md`.
- Replace hard-coded 91%, 74%, and 52% mock scores with scores actually calculated from the sample CV/JD data. The mockup's `70% required / 30% preferred` text conflicts with the approved `70% required / 20% preferred / 10% text similarity` formula.
- Remove unsupported statements such as `0 hallucinations`, `verified credentials`, `AI semantic parser`, `audit guarantee`, `Engine v2.4`, `evaluation locked`, and `1-click export to ATS`. Evidence from a CV supports a claim only about what the CV says, not independent verification.
- Do not offer OCR unless implemented. A scanned PDF should show a text-extraction failure and suggest pasting text.
- Change the upload privacy copy: documents are session-local in our app, but relevant excerpts may be sent to the configured AI provider when AI chat or drafting is used. Only synthetic data should be used in the public demo.
- The chat drawer in the Stitch candidate screenshot is much wider than the 380–420 px design target and obscures much of the evidence table. On desktop, keep it resizable or use a narrower drawer; on mobile, use a full-screen sheet.
- Ensure the `Drafts` navigation leads to a real screen or remove it. The implementation should include a working drafts view because the assignment requires email drafting.
