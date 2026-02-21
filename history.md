# OpenClaw Agent - Change History

---

## 2026-02-21 — Skills Migration to Go Binaries

### What changed
Migrated skills from Python scripts to pre-compiled Go binaries (v1.0.0 release). Added `tech-intel` as a new skill alongside the existing `market-overview`.

### Skills setup
Both skills pulled from: https://github.com/baladengale/claude-skills/releases/tag/v1.0.0

Each skill directory (`market-overview`, `tech-intel`) now contains:
- `*-linux-amd64` — compiled Go binary (executable)
- `SKILL.md` — agent instructions
- `template.html` — email HTML template
- `.env` — symlink to credentials (see below)

Installed to: `/home/bala/.openclaw/workspace/skills/`

### Credentials
Consolidated to a single file: `/home/bala/.openclaw/.env`

Contains: `GMAIL_USER`, `GMAIL_APP_PASSWORD`, `MARKET_RECIPIENTS`, `NEWSLETTER_RECIPIENTS`, `PERPLEXITY_API_KEY`

Each skill directory has a `.env` symlink pointing to this file so binaries can read credentials from their working directory without duplicating secrets.

No credentials stored in the repo. The `openclaw-agent/.env` references `~/.openclaw/.env` for documentation only.

### Sync script
`/home/bala/sync-skills.sh` — re-downloads binaries, SKILL.md, and template.html from GitHub and re-creates symlinks. Run this to upgrade skills when a new release is tagged. Update `RELEASE_TAG` at the top of the script.

### Verified working
- `market-overview-linux-amd64 --no-email` — live Yahoo Finance data for all markets
- `tech-intel-linux-amd64` — RSS aggregation and article scoring working
