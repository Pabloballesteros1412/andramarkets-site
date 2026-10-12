---
target: cream homepage prototype
total_score: 23
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 3
target_identity: "file:/home/user/andramarkets-site/prototypes/cream/index.html"
target_fingerprint: "sha256:d9e6855342a120cf08e1b39bd70724b19f943c5fdb64ea345e547aafe6cb3cbd"
target_path: /home/user/andramarkets-site/prototypes/cream/index.html
timestamp: 2026-10-12T12-43-14Z
slug: prototypes-cream-index-html
---
Method: dual-agent (A: design review sub-agent, B: detector + browser sub-agent). Covers prototypes/cream and prototypes/dark (identical markup, theme differs).

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 2 | Transparent header collided with hero copy on scroll; no active nav state |
| 2 | Match system / real world | 3 | Momentum chart contradicted its regime legend |
| 3 | User control and freedom | 3 | Skip link, Esc closes menu |
| 4 | Consistency and standards | 3 | Red used for form error outside charts |
| 5 | Error prevention | 3 | Email input typed, helper sets expectations |
| 6 | Recognition rather than recall | 3 | Study/Close-note type hidden on mobile; curve chart lacked legend |
| 7 | Flexibility and efficiency | n/a | Persuade surface |
| 8 | Aesthetic and minimalist design | 3 | Strong restraint; long mobile page, dead air |
| 9 | Error recovery | 3 | Specific messages, focus returns |
| 10 | Help and documentation | n/a | Persuade surface |
| Total | | 23/32 | Good |

Specificity: hero authored (engraved horse + "Every close, on the record."); below the fold drifted toward a generic section stack.
Detector: static 10 warnings (cramped-padding x6, tight-leading x4), all false positives; rendered URL scans at 1280 and 390 clean in both themes; contrast all AA; no overflow, no serif, no dashes, no console errors; tap targets under 44px on mobile footer links and "All notes and studies".

Priority issues:
- [P1] Header collision and brand-mark patch occluding content on scroll.
- [P1] Full-bleed plates promised by the brief existed only in the hero.
- [P1] Red used outside charts (form error).
- [P2] Illustrative charts contradicted their labels (momentum bands, curve legend, single-line volatility).
- [P2] Mobile weaker: tape without peek, squashed study chart, 240px gaps, no Subscribe after scroll, small tap targets.
Cream vs dark: dark wins the hero, cream wins the scroll (dark ground steps too small, inverse tile became a white slab; cream horse washed out).
