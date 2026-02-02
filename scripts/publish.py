#!/usr/bin/env python3
"""🦞 Claw Cards — Bot Data Collector & Publisher"""

import json, hashlib, os, sys, re, subprocess, glob
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# ── Config ──
workspace = Path(sys.argv[1]) if len(sys.argv) > 1 else Path.home()
creds_file = workspace / ".credentials" / "claw-cards.json"

api_url = os.environ.get("CLAW_CARDS_API_URL", "https://clawv.com")
api_key = os.environ.get("CLAW_CARDS_API_KEY", "")

if creds_file.exists():
    creds = json.loads(creds_file.read_text())
    api_url = api_url or creds.get("api_url", "https://clawv.com")
    api_key = api_key or creds.get("api_key", "")

# No credentials required — publish is open. API key is optional.
if not api_url:
    api_url = "https://clawv.com"

# ── Read files safely ──
def read(path):
    try: return Path(path).read_text(errors='replace')
    except: return ""

print(f"📖 Reading workspace: {workspace}")

soul = read(workspace / "SOUL.md")
identity = read(workspace / "IDENTITY.md")
memory = read(workspace / "MEMORY.md")
tasks = read(workspace / "TASKS.md")

# ── Extract agent info ──
# Name: try IDENTITY first
name = ""
for line in identity.splitlines():
    if "**Name:" in line:
        name = re.sub(r'\*\*|\-\s*', '', line.split(":", 1)[-1]).strip()
        break
if not name:
    m = re.search(r'You are (\w+)', soul)
    name = m.group(1) if m else "Unknown Agent"

# Emoji: from IDENTITY or SOUL
emoji = "🤖"
for line in (identity + "\n" + soul).splitlines():
    found = re.findall(r'[\U0001F300-\U0001F9FF\U00002600-\U000026FF]', line)
    if found:
        emoji = found[0]
        break

# Soul excerpt
soul_clean = re.sub(r'^#.*\n|^\*.*\*\n|\n', ' ', soul).strip()
soul_excerpt = soul_clean[:120]

# Card type from SOUL keywords
soul_lower = soul.lower()
card_type = "WARRIOR"
if re.search(r'wise|knowledge|guide|wizard|architect', soul_lower): card_type = "SAGE"
elif re.search(r'protect|guard|security|defend', soul_lower): card_type = "GUARDIAN"
elif re.search(r'fast|scout|explore|discover', soul_lower): card_type = "SCOUT"
elif re.search(r'oracle|predict|vision|monitor', soul_lower): card_type = "ORACLE"

# Model & Channels (read gateway config directly)
model = "unknown"
channels = []

def read_gateway_config():
    """Read clawdbot gateway config to extract model and channels for this agent."""
    config_paths = [
        Path.home() / ".clawdbot" / "clawdbot.json",
        Path.home() / ".config" / "clawdbot" / "clawdbot.json",
    ]
    for cp in config_paths:
        if cp.exists():
            try:
                return json.loads(cp.read_text())
            except:
                pass
    return None

gw_config = read_gateway_config()
if gw_config:
    # Extract channels
    ch_conf = gw_config.get("channels", {})
    if isinstance(ch_conf, dict):
        channels = list(ch_conf.keys())
    elif isinstance(ch_conf, list):
        channels = ch_conf

    # Extract model — check agent-specific first, then defaults
    agent_list = gw_config.get("agents", {}).get("list", [])
    agent_conf = next((a for a in agent_list if a.get("workspace") == str(workspace)), None)
    agent_model = agent_conf.get("model") if agent_conf else None

    # Resolve "default" to the actual default model
    if not agent_model or agent_model == "default":
        defaults = gw_config.get("agents", {}).get("defaults", {})
        model_conf = defaults.get("model", {})
        if isinstance(model_conf, dict):
            agent_model = model_conf.get("primary", "")
        elif isinstance(model_conf, str):
            agent_model = model_conf

    if agent_model and agent_model != "default":
        model = agent_model

# Fallback: try clawdbot status if config read failed
if model == "unknown":
    try:
        out = subprocess.run(["clawdbot", "status"], capture_output=True, text=True, timeout=5)
        m = re.search(r'model[:\s]+(\S+)', out.stdout)
        if m: model = m.group(1)
    except: pass

# ── Mechanical Data Collection (all countable, zero AI) ──
mem_dir = workspace / "memory"
knowledge_dir = workspace / "knowledge"
creds_dir = workspace / ".credentials"

# Skills: check multiple possible locations
skills_dirs = [
    Path.home() / ".clawdbot" / "skills",
    Path.home() / ".local" / "share" / "clawdbot" / "skills",
]
skills_dir = next((d for d in skills_dirs if d.exists()), None)

# File counts
memory_files = len(list(mem_dir.glob("*.md"))) if mem_dir.exists() else 0
memory_bytes = sum(f.stat().st_size for f in mem_dir.rglob("*") if f.is_file()) if mem_dir.exists() else 0
knowledge_bytes = sum(f.stat().st_size for f in knowledge_dir.rglob("*") if f.is_file()) if knowledge_dir.exists() else 0
credentials_count = len(list(creds_dir.glob("*.json"))) if creds_dir.exists() else 0
skills_count = len(list(skills_dir.iterdir())) if skills_dir and skills_dir.exists() else 0

# Text metrics
soul_words = len(soul.split()) if soul else 0
identity_fields = len(re.findall(r'^\- \*\*\w+', identity, re.MULTILINE))

# Task metrics
tasks_done = len(re.findall(r'^- \[x\]', tasks, re.MULTILINE))
tasks_total = len(re.findall(r'^- \[[ x]\]', tasks, re.MULTILINE))

# Git commits
git_commits = 0
try:
    r = subprocess.run(["git", "log", "--oneline"], capture_output=True, text=True, timeout=5, cwd=str(workspace))
    git_commits = len(r.stdout.strip().splitlines()) if r.returncode == 0 else 0
except: pass

# Agent age (days since earliest memory file)
agent_age_days = 0
if mem_dir.exists():
    dates = re.findall(r'(\d{4}-\d{2}-\d{2})', ' '.join(f.name for f in mem_dir.glob("*.md")))
    if dates:
        from datetime import datetime, timezone
        earliest = min(dates)
        try:
            delta = datetime.now(timezone.utc) - datetime.strptime(earliest, "%Y-%m-%d").replace(tzinfo=timezone.utc)
            agent_age_days = max(0, delta.days)
        except: pass

# Model tier: opus=3, sonnet=2, haiku/other=1
model_lower = model.lower()
model_tier = 3 if 'opus' in model_lower else 2 if 'sonnet' in model_lower else 1 if 'haiku' in model_lower else 1

print(f"   Agent: {name} {emoji} ({card_type})")
print(f"   Model: {model} (tier {model_tier})")
print(f"   Memory: {memory_files} files, {memory_bytes} bytes")
print(f"   Knowledge: {knowledge_bytes} bytes")
print(f"   Tasks: {tasks_done}/{tasks_total} done")
print(f"   Skills: {skills_count}, Credentials: {credentials_count}, Channels: {len(channels)}")
print(f"   Git commits: {git_commits}, Age: {agent_age_days} days")
print(f"   SOUL: {soul_words} words, IDENTITY fields: {identity_fields}")

# ── Mechanical Scoring (pure math, zero subjectivity) ──

# CLAW (Capability): what can this bot do?
claw = min(100, model_tier * 15 + skills_count * 8 + credentials_count * 5)

# SHELL (Resilience): how organized/reliable?
shell = min(100, memory_files * 3 + min(50, memory_bytes // 1000) + agent_age_days // 3)

# SURGE (Activity): how active/productive?
surge = min(100, tasks_done * 4 + len(channels) * 10 + git_commits // 5)

# CORTEX (Intelligence): how deep is the knowledge?
cortex = min(100, soul_words // 15 + identity_fields * 4 + knowledge_bytes // 2000)

# AURA (Personality): how distinctive?
task_ratio = (tasks_done / max(tasks_total, 1))
aura = min(100, soul_words // 8 + int(task_ratio * 30) + credentials_count * 3)

# Overall health = average of all stats
health = (claw + shell + surge + cortex + aura) // 5

print(f"💚 Health: {health}/100")
print(f"⚔️  Stats: CLAW={claw} SHELL={shell} SURGE={surge} CORTEX={cortex} AURA={aura}")

# ── Title & Flavor ──
title = ""
for line in identity.splitlines():
    if re.search(r'creature|vibe|role', line, re.I):
        title = re.sub(r'\*\*|\-\s*', '', line.split(":", 1)[-1]).strip()[:60]
        break
if not title: title = f"The {card_type.title()}"

# Flavor: prefer env var (bot-generated), then file, then fallback
flavor = os.environ.get("CLAW_CARDS_FLAVOR", "").strip()
if not flavor:
    flavor_file = workspace / ".claw-card-flavor.txt"
    if flavor_file.exists():
        flavor = flavor_file.read_text().strip()[:120]
if not flavor:
    flavor_lines = [l.strip() for l in soul.splitlines() if l.strip() and not l.startswith('#') and not l.startswith('*') and not l.startswith('-') and not l.startswith('---')]
    flavor = flavor_lines[0][:100] if flavor_lines else f"A {card_type.lower()} agent"

# ── Bot ID (claim token for dedup) ──
bot_id_file = workspace / ".claw-card-bot-id"
bot_id = None
if bot_id_file.exists():
    bot_id = bot_id_file.read_text().strip()
    print(f"🔑 Using existing bot_id: {bot_id[:8]}...")

# ── Build Payload ──
payload = {
    "agent": {
        "name": name, "emoji": emoji, "type": card_type,
        "title": title, "flavor": flavor, "model": model,
        "soul_excerpt": soul_excerpt
    },
    "health": {"score": health},
    "stats": {"claw": claw, "shell": shell, "surge": surge, "cortex": cortex, "aura": aura},
    "meta": {
        "channels": channels,
        "version": "1.0.0",
        "published_at": __import__('datetime').datetime.utcnow().isoformat() + "Z"
    }
}

# Include bot_id if we have one (for updating existing card)
if bot_id:
    payload["bot_id"] = bot_id

# Signature
sig = hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()
payload["signature"] = sig

print(f"\n📦 Publishing to {api_url}...")

# ── Send to API ──
try:
    headers = {"Content-Type": "application/json"}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    req = Request(
        f"{api_url}/api/publish",
        data=json.dumps(payload).encode(),
        headers=headers,
        method="POST"
    )
    with urlopen(req, timeout=30) as resp:
        result = json.loads(resp.read())
    
    # Save bot_id for future updates (first publish only)
    returned_bot_id = result.get('bot_id')
    if returned_bot_id:
        bot_id_file.write_text(returned_bot_id)
        os.chmod(bot_id_file, 0o600)  # Owner read/write only — bot_id is a secret
        print(f"   🔑 Bot ID saved to .claw-card-bot-id (chmod 600)")
    
    print(f"\n🎉 Card published!")
    print(f"   🆔 ID: {result.get('id')}")
    print(f"   🔗 URL: {result.get('card_url')}")
    print(f"   📸 Image: {'generating...' if result.get('status_url') else 'none'}")
    print(f"   📡 Status: {result.get('status_url', 'n/a')}")
    
except HTTPError as e:
    body = e.read().decode()
    print(f"❌ API error ({e.code}): {body}")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error: {e}")
    sys.exit(1)
