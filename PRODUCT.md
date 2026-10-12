# Product

<!-- impeccable:product-schema 1 -->

## Platform

web

## Stack

Design phase: plain static HTML/CSS/JS prototypes in `/prototypes`, deployed to
GitHub Pages by a GitHub Actions workflow (owner's brief). The production stack
for the real site is undecided.

## Users

Two audiences in equal measure:

- Finance recruiters and professionals judging the quality and seriousness of
  the research, usually on a laptop and often from a link on a CV or LinkedIn.
- Social media followers (LinkedIn, TikTok, YouTube) arriving on a phone after
  a post or a clip, who want today's note and a reason to subscribe.

## Product Purpose

Andra Markets is an automated research desk. Every US trading day it publishes
a market close note. It also maintains interactive dashboards and publishes
quantitative studies. Success: visitors read the latest note, explore a
dashboard or study, and subscribe to the daily note by email.

## Positioning

The research is produced by an automated pipeline on a fixed daily cadence, so
the output is consistent, dated and on the record every trading day.

## Operating Context

- The close note is tied to the US market close and published per trading day.
- Visitors arrive from LinkedIn, TikTok and YouTube as well as direct links.

## Capabilities and Constraints

- Outputs: daily US market close note, interactive dashboards, quantitative
  studies (first featured study: momentum regimes).
- Undecided: dashboard names and count, study list, data sources, publication
  time, email provider, social handles. Prototypes use labelled placeholders.

## Brand Commitments

- Name: Andra Markets. All copy in English.
- `andra-horse.png` is the brand mark (engraved rearing horse on black). Do not
  redraw, recolor, crop or replace it without owner approval. The owner
  approved showing it on light grounds via a CSS invert + multiply treatment
  that leaves the file untouched (prototype stage).
- Sans-serif only, everywhere, including fallbacks (CLAUDE.md rule 2).
- Owner approves visual decisions before real pages are built (CLAUDE.md rule 1).
- Tone: premium and serious, never playful. References the owner likes for
  their principles (not their look): spacex.com, canyon.com, quartr.com.
- Red and green appear only inside charts.

## Evidence on Hand

- `andra-horse.png` (brand mark).
- No market data, report text, subscriber counts, testimonials or press exist
  yet. Never invent numbers: use placeholders such as `[live]` and `[date]`.

## Product Principles

1. On the record: every number is dated and sourced, or it is a placeholder.
2. Cadence is the product: the daily note is always one click away.
3. Serve both readers: a recruiter judges rigor in seconds; a follower finds
   today's note in one tap.
4. Restraint signals seriousness: little text per screen, no hype.

## Accessibility & Inclusion

WCAG 2.2 AA contrast; full keyboard support; motion honors
`prefers-reduced-motion`; must work well on phones.
