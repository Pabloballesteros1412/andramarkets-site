---
target: homepage prototype, light and dark
total_score: 23
max_score: 32
na_heuristics: 7,10
p0_count: 0
p1_count: 2
target_identity: "file:/home/user/andramarkets-site/prototypes/index.html"
target_fingerprint: "sha256:159795abbb3dc69fc67937d37cb4e5915a1b9315717f1e70535157e2964c7708"
target_path: /home/user/andramarkets-site/prototypes/index.html
timestamp: 2026-10-12T14-04-27Z
slug: prototypes-index-html
---
Method: dual-agent (A: design review sub-agent, B: detector + browser sub-agent). Target prototypes/index.html, light and dark themes.

| # | Heuristic | Score | Key issue |
|---|---|---|---|
| 1 | Visibility of system status | 3 | Filter status and form status work; nav shows no current section |
| 2 | Match system / real world | 3 | Right vocabulary; calendar not grouped by day; mobile "Cons." label |
| 3 | User control and freedom | 3 | Mobile menu button pushed off-screen when header turns solid |
| 4 | Consistency and standards | 2 | Tile headings misaligned; keys on 6 of 12 tiles; Illustrative stamp only on Lab |
| 5 | Error prevention | 3 | Typed email input, clear hint |
| 6 | Recognition rather than recall | 3 | Keys hidden on mobile |
| 7 | Flexibility and efficiency | n/a | Persuade surface |
| 8 | Aesthetic and minimalist design | 3 | Watch frames dead grey slabs; repetition of "markets research platform" |
| 9 | Error recovery | 3 | Error looks like focus state |
| 10 | Help and documentation | n/a | Persuade surface |
| Total | | 23/32 | Good |

Detector: static 10 warnings (cramped-padding 9, tight-leading 1), false positives; rendered URL scans clean in both themes at 1280 and 390. 0 contrast failures in 268 text elements; heatmap low-magnitude cells under 3:1; webfont loads; no serif; no dashes; no console errors; theme toggle, filters, menu, form and redirects all pass.

Priority issues:
- [P1] Today's note not one tap away for social visitors.
- [P1] Mobile solid header pushes the menu button off-screen.
- [P2] Filtered grid states show solid grey cells.
- [P2] Dashboard tiles lack keys, Illustrative stamp, source line; headings misaligned.
- [P2] Calendar mobile layout and placeholder walls read as broken.
- [P2] Keyboard: focus not moved into open menu; chip focus ring clipped.
