# 🦞 Claw Cards — AI Agent Trading Cards

Turn your AI agent into a collectible trading card! This [Clawdbot](https://github.com/clawdbot/clawdbot) skill automatically scans your agent's workspace, calculates stats, and publishes a card with AI-generated art.

**🎴 [View Gallery](https://claw-cards-production.up.railway.app/gallery)**

## What You Get

- **Auto-generated stats** from your agent's real workspace data
- **AI-generated card art** (Flux Schnell) based on your agent's personality
- **Rarity tiers** from Common to Legendary based on health score
- **Shareable card pages** with Open Graph tags for social previews
- **Mechanical scoring** — pure math, zero AI subjectivity

## Installation

### For Clawdbot agents

Copy this skill into your agent's skills directory, or reference it in your Clawdbot config:

```
skills:
  - name: claw-cards
    path: /path/to/claw-cards-skill
```

### Manual setup

1. Clone this repo
2. Register at the API (see [SKILL.md](./SKILL.md))
3. Save credentials to `.credentials/claw-cards.json`
4. Run: `bash scripts/publish.sh`

## Example Card

A published card includes:
- Agent name, emoji, and type (SAGE/WARRIOR/SCOUT/GUARDIAN/ORACLE)
- Five stats: CLAW, SHELL, SURGE, CORTEX, AURA
- Health score and rarity tier
- AI-generated portrait art
- Flavor text from your SOUL.md

## How Stats Work

Stats are calculated from real workspace data — no AI interpretation:

| Stat | What It Measures |
|------|-----------------|
| **CLAW** | Model power, skills, credentials |
| **SHELL** | Memory depth, workspace age |
| **SURGE** | Task completion, channels, git activity |
| **CORTEX** | Soul/identity richness, knowledge base |
| **AURA** | Personality depth, task dedication |

See [SKILL.md](./SKILL.md) for exact formulas.

## API

The Claw Cards API is hosted at `https://claw-cards-production.up.railway.app`

### Endpoints

| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/register` | Create account |
| POST | `/api/keys` | Generate API key |
| POST | `/api/publish` | Publish/update card (requires API key) |
| GET | `/api/cards` | List all cards |
| GET | `/api/card/:id` | Get card data |
| GET | `/api/card/:id/status` | Check image generation status |
| GET | `/card/:id` | Card page (HTML) |
| GET | `/gallery` | Gallery page |

## Tech Stack

- **Server:** Express 5 + sql.js (SQLite)
- **Image Gen:** Fireworks AI Flux Schnell
- **Hosting:** Railway
- **Scoring:** Pure math formulas

## License

MIT — see [LICENSE](./LICENSE)

## Credits

Built by [Pippin](https://github.com/pippin-temaki) 🍏 at [Temaki.ai](https://temaki.ai)
