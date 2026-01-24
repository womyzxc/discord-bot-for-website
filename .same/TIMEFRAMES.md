# Discord Security Bot - Timeframes & Thresholds

## Overview
Complete reference for all detection thresholds, timeframes, and scoring systems.

---

## ANTI-NUKE PROTECTION (`antinuke.py`)

### Detection Thresholds (from `main.py` BotConfig)

| Action | Threshold | Response |
|--------|-----------|----------|
| **Ban by untrusted** | **1** | Instant ban attacker + unban victim |
| **Kick by untrusted** | **1** | Instant ban attacker |
| **Channel Delete** | **1** | Instant ban + restore channel |
| **Channel Create** | **1** | Delete channel + ban creator |
| **Channel Rename** | **1** | Revert channel name + ban |
| **Role Delete** | **1** | Instant ban attacker |
| **Role Create** (with admin perms) | **1** | Delete role + ban creator |
| **Role Update** (add dangerous perms) | **1** | Revert permissions + ban |
| **Webhook Create** | **1** | Delete webhook + ban creator |
| **Member Prune** | **1** | Instant ban attacker |
| **Server Settings Change** | **1** | Revert changes + ban |
| **Dangerous Role Grant** | **1** | Remove role + ban granter |

### Dangerous Permissions (instant punishment if granted)
```python
DANGEROUS_PERMISSIONS = [
    'administrator',
    'ban_members',
    'kick_members',
    'manage_channels',
    'manage_guild',
    'manage_roles',
    'manage_webhooks',
    'mention_everyone',
]
```

### Suspicious Webhook Names (auto-delete + ban)
```python
SUSPICIOUS_WEBHOOK_NAMES = [
    'nuke', 'nuked', 'nuker', 'nuk3',
    'raid', 'raided', 'raider', 'ra1d',
    'hacked', 'hack', 'h4ck', 'pwned',
    'destroyed', 'destroy', 'rekt',
    'owned', '0wned', 'fucked', 'fuck',
    'deleted', 'delete', 'boom', 'dead',
    'selfbot', 'self-bot', 'token', 'logger',
    'spam', 'spammer', 'bot', 'attack',
    'revenge', 'die', 'kill', 'death',
]
```

### Timing Constants

| Constant | Value | Description |
|----------|-------|-------------|
| Audit Log Max Age | **5 sec** | Only check audit entries from last 5 seconds |
| Webhook Scan Interval | **1 sec** | Continuous scan for unauthorized webhooks |
| Fast Webhook Scan | **0.5 sec** | Ultra-fast scan for blacklisted webhooks |
| Cleanup Interval | **300 sec** | Clean old processed entries every 5 minutes |
| Punishment Cooldown | **60 sec** | Don't re-punish same user within 60 seconds |
| Emergency Lockdown | **30 sec** | Auto-unlock after 30 seconds |
| Mass Restore Delay | **3 sec** | Wait for nuke to complete before restoring |

### Punishment Types
```python
# Configurable via !punishment command
'punishment': 'ban'   # Default: ban attacker
'punishment': 'kick'  # Alternative: kick attacker
```

### Protected Server Settings
- Server name
- Server icon
- Server banner
- Vanity URL
- Verification level
- Description
- Default notifications
- Explicit content filter
- AFK channel/timeout
- System channel

---

## ANTI-SELFBOT DETECTION (`antiselfbot.py`)

### Suspicion Scoring System

| Detection Type | Points | Description |
|----------------|--------|-------------|
| Fast Reaction | **+20** | Reaction under 50ms after message |
| Multiple Fast Reactions | **FLAG** | 3+ fast reactions in 10 minutes → immediate flag |
| Nitro Snipe Attempt | **+15** | Posting nitro gift links |
| Multiple Nitro Attempts | **FLAG** | 5+ attempts in 1 hour → immediate flag |
| Selfbot Command | **+25** | Using known selfbot commands (`.snipe`, `.steal`) |
| Automation Pattern | **+30** | Suspiciously consistent message timing |
| Rich Embed (User) | **+50** | Users can't send rich embeds - only bots can |
| Embed Spam | **+30** | 5+ embeds in 1 minute |

### Detection Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| `suspicion_threshold` | **100** | Score needed to trigger action |
| `reaction_threshold_ms` | **50** | Reactions faster than this are suspicious |
| `automation_interval_variance` | **0.1** | Low timing variance = bot-like |

### Selfbot Command Patterns (auto-delete + flag)
```python
SELFBOT_PATTERNS = [
    r'^\.(?:snipe|editsnipe|reactionsnipe)',  # .snipe commands
    r'^\.(?:steal|yoink|grab)',                # .steal commands
    r'^\.(?:nitro|token|grab)',                # .nitro commands
    r'^\.(?:afk|status|activity)',             # .afk commands
    r'^\?(?:snipe|steal|grab)',                # ?snipe commands
]
```

### Nitro Gift Pattern (suspicious if posted by user)
```python
NITRO_PATTERN = r'(?:https?://)?(?:www\.)?discord(?:app)?\.(?:com|gift)/gifts?/[\w-]+'
```

### Action Types
```python
'action': 'alert'  # Default: just log to channel
'action': 'mute'   # Timeout for 1 hour
'action': 'kick'   # Kick from server
'action': 'ban'    # Ban from server
```

### Timing Windows

| Window | Duration | Description |
|--------|----------|-------------|
| Fast Reaction Tracking | **10 min** | Track fast reactions for 10 minutes |
| Nitro Attempt Tracking | **1 hour** | Track nitro attempts for 1 hour |
| Message Interval Analysis | **20 msgs** | Analyze last 20 message intervals |
| Embed Spam Window | **1 min** | Count embeds in rolling 1-minute window |

---

## ANTI-RAID PROTECTION (`antiraid.py`)

### Join Thresholds

| Setting | Default | Description |
|---------|---------|-------------|
| `join_threshold` | **10** | Joins needed to trigger raid mode |
| `join_timeframe` | **10 sec** | Window to count joins |
| `min_account_age` | **7 days** | Accounts newer than this are suspicious |

### Raid Score Calculation

| Factor | Points | Description |
|--------|--------|-------------|
| New Account | **+30** | Account under 7 days old |
| No Avatar | **+20** | Default avatar |
| Suspicious Name | **+15 each** | Matches raid name patterns |
| Very New (24h) | **+25** | Created within last day |

**Total Score ≥ 60** = Flagged as suspicious

### Suspicious Name Patterns
```python
PATTERNS = [
    r'^[a-zA-Z]+\d{4,}$',   # user1234
    r'^.{1,3}$',             # Very short (1-3 chars)
    r'^\d+$',                # Numbers only
    r'(.)\1{4,}',            # Repeated chars (aaaaa)
    r'raid|nuke|destroy',    # Keywords
    r'^[A-Z]{5,}$',          # ALL CAPS
]
```

### Raid Mode Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `auto_raid_mode` | **True** | Auto-enable when threshold hit |
| `raid_mode_duration` | **300 sec** | Auto-disable after 5 minutes |
| `verification_level` | **medium** | Set during raid mode |

### Action Types
```python
'action': 'kick'       # Default: kick raiders
'action': 'ban'        # Ban raiders
'action': 'quarantine' # Strip all roles
```

---

## ANTI-SPAM PROTECTION (from `main.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| `MESSAGE_THRESHOLD` | **10** | Messages to trigger |
| `MESSAGE_TIMEFRAME` | **5 sec** | Window for messages |
| `DUPLICATE_THRESHOLD` | **5** | Same message count |
| `MENTION_THRESHOLD` | **10** | Max mentions per message |
| `EMOJI_THRESHOLD` | **20** | Max emojis per message |

---

## ADVANCED SECURITY (`advanced_security.py`)

### API Abuse Thresholds (per minute)

| Action | Limit | Description |
|--------|-------|-------------|
| Message Edit | **5** | Edits per minute |
| Message Delete | **8** | Deletes per minute |
| Reaction Add/Remove | **10** | Reactions per minute |
| Channel Edit | **2** | VERY STRICT |
| Role Edit | **2** | VERY STRICT |
| Nickname Change | **3** | Changes per minute |
| Webhook Action | **1** | INSTANT detection |
| **Total Actions** | **25** | Combined per minute |

### Selfbot Detection (Advanced)

| Threshold | Value | Description |
|-----------|-------|-------------|
| Min Response Time | **500ms** | Faster = suspicious |
| Suspicious Response | **800ms** | Triggers warning |
| Timing Variance | **200ms** | Low variance = bot |
| Max Msgs/Second | **2** | Speed limit |
| Min Typing Time | **500ms** | Before message |

---

## AUDIT LOG CACHE (`utils/audit_cache.py`)

| Setting | Value | Description |
|---------|-------|-------------|
| `CACHE_DURATION` | **2 sec** | Cache lifetime |
| `MAX_ENTRIES` | **25** | Entries per fetch |
| Cleanup Age | **60 sec** | Remove old cache |

---

## DATABASE PERSISTENCE

### Tables for Security Data

| Table | Purpose |
|-------|---------|
| `guild_settings` | All module settings (JSON) |
| `whitelist` | Trusted users per guild |
| `trusted_users` | Anti-nuke trusted users |
| `trusted_bots` | Anti-nuke trusted bots |
| `trusted_roles` | Anti-nuke trusted roles |
| `whitelisted_roles` | Whitelist module roles |
| `honeypots` | Trap channels/roles |
| `honeypot_triggers` | Who triggered traps |
| `selfbot_tracking` | Suspicion scores |
| `ban_velocity` | Ban rate tracking |
| `channel_backups` | For restoration |
| `server_settings_backup` | Server config backup |
| `security_logs` | Event history |
| `threat_intel` | Known bad actors |
| `warnings` | User warnings |

---

## Quick Reference Commands

### Anti-Nuke
```
!antinuke          - View status
!antinuke_enable   - Enable protection
!antinuke_disable  - Disable protection
!punishment ban/kick - Set punishment
!setlog #channel   - Set log channel
!trust @user       - Add trusted user
!trustbot @bot     - Add trusted bot
!trustrole @role   - Add trusted role
!recover           - Restore all channels
```

### Anti-Selfbot
```
!antiselfbot              - View status
!antiselfbot enable       - Enable detection
!antiselfbot disable      - Disable detection
!antiselfbot action ban   - Set action
!antiselfbot threshold 80 - Set score threshold
!antiselfbot check @user  - Check user score
!antiselfbot clear @user  - Reset user tracking
```

### Anti-Raid
```
!antiraid              - View status
!antiraid enable       - Enable protection
!antiraid disable      - Disable protection
!antiraid raidmode on  - Manual raid mode
!antiraid action kick  - Set action
!antiraid threshold 10 5 - 10 joins in 5 seconds
!antiraid minage 7     - Min account age (days)
```
