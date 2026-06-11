# Mozi-Copy

A Claude **Agent Skill** that writes sales copy and persuasion scripts using Alex Hormozi's sales system — built from full transcripts of the Gym Launch 2.0 course (30 videos) and his core sales trainings on YouTube (6 videos).

It covers: cold calls, WhatsApp/SMS/DM sequences, emails, appointment reminders, full sales conversations, objection handling (organized by his three-distortions taxonomy), the 3A reframing method, negotiation, pricing/guarantee presentation, and the voice/tonality rules — generalized to any industry while preserving the original verbatim scripts and the reasoning behind them.

## Structure

```
mozi-copy/
├── SKILL.md            # router: laws, workflow, routing table
├── references/         # the distilled system (10 files, zero duplication)
└── sources/            # cleaned verbatim transcripts + INDEX.md coverage matrix
```

Progressive disclosure: Claude reads `SKILL.md` when the skill triggers, loads only the `references/` files the task needs, and greps `sources/` when verbatim wording or extra nuance matters.

## Install

**claude.ai (web/app):** zip the skill folder and upload it under **Settings → Capabilities → Skills** (the zip must contain `mozi-copy/SKILL.md` at its root — use `dist/mozi-copy.zip` or rebuild below). Then just ask for copy in any chat or Project: *"write a 5-touch WhatsApp follow-up for leads who booked but didn't confirm."*

**Claude Code:** `cp -r mozi-copy ~/.claude/skills/` — invoke with `/mozi-copy` or let it trigger automatically.

## Rebuild the zip

```bash
cd <repo-root> && rm -f dist/mozi-copy.zip && mkdir -p dist && zip -r dist/mozi-copy.zip mozi-copy -x "*.DS_Store"
```

## Regenerating sources

The Gym Launch sources were split from the raw upload by `tools/clean_transcripts.py`. The YouTube sources are full transcripts re-sourced from YouTube's own captions (via yt-dlp, 2026-06-12), which replaced the original lossy whisper transcripts; occasional odd words are caption artifacts, not edits. Raw uploads are not stored in this repo.

## Fidelity notes

- Reference files preserve scripts verbatim (lightly cleaned), each with the stated mechanism, a generalized template, and channel adaptation notes.
- Every technique has exactly one home; other files cross-reference it. The only intentional redundancy is `sources/` (the verbatim archive).
