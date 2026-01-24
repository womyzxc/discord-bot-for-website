# Discord Security Bot - Improvement Recommendations

## Overview
Your bot has a solid foundation with comprehensive security features. Below are specific improvements categorized by priority.

---

## CRITICAL Priority Improvements

### 1. Race Condition in Anti-Nuke (antinuke.py)

**Problem**: The `instant_punish` function has a race condition. If multiple events trigger punishment simultaneously, users could be punished multiple times or the punishment could fail.

**Current Code Issue** (lines 903-907):
```python
if user_id in self.recently_punished.get(guild.id, set()):
    return
self.recently_punished[guild.id].add(user_id)
asyncio.get_event_loop().call_later(60, lambda: ...)
```

**Improvement**:
```python
async def instant_punish(self, guild: discord.Guild, user_id: int, reason: str):
    # Use a lock per-guild to prevent race conditions
    if not hasattr(self, '_punish_locks'):
        self._punish_locks = defaultdict(asyncio.Lock)

    async with self._punish_locks[guild.id]:
        if user_id in self.recently_punished.get(guild.id, set()):
            return
        self.recently_punished[guild.id].add(user_id)

    # Remove after 60 seconds (use asyncio.create_task for cleaner code)
    async def cleanup():
        await asyncio.sleep(60)
        self.recently_punished.get(guild.id, set()).discard(user_id)
    asyncio.create_task(cleanup())

    # ... rest of punishment logic
```

### 2. Audit Log Rate Limiting (antinuke.py)

**Problem**: Multiple event handlers fetch audit logs simultaneously, which can hit Discord's rate limits and cause delays in protection.

**Current Issue**: Each `on_guild_channel_delete`, `on_guild_role_delete`, etc. fetches audit logs independently.

**Improvement**: Create an audit log cache with debouncing:
```python
class AuditLogCache:
    def __init__(self, bot):
        self.bot = bot
        self.cache: Dict[int, List[discord.AuditLogEntry]] = {}
        self.cache_time: Dict[int, datetime] = {}
        self.lock = asyncio.Lock()
        self.CACHE_DURATION = 2  # seconds

    async def get_recent_entries(self, guild_id: int, action: discord.AuditLogAction, limit: int = 5):
        async with self.lock:
            now = datetime.utcnow()
            if guild_id in self.cache_time:
                if (now - self.cache_time[guild_id]).total_seconds() < self.CACHE_DURATION:
                    return [e for e in self.cache.get(guild_id, []) if e.action == action][:limit]

            guild = self.bot.get_guild(guild_id)
            if not guild:
                return []

            try:
                entries = [entry async for entry in guild.audit_logs(limit=20)]
                self.cache[guild_id] = entries
                self.cache_time[guild_id] = now
                return [e for e in entries if e.action == action][:limit]
            except:
                return []
```

### 3. Missing Error Handling in Webhook Deletion (antinuke.py)

**Problem**: Bare `except:` clauses hide actual errors and make debugging difficult.

**Current Code** (line 278, 543, 548, etc.):
```python
except:
    pass
```

**Improvement**: Add specific exception handling:
```python
except discord.NotFound:
    pass  # Webhook already deleted
except discord.Forbidden:
    logger.warning(f"No permission to delete webhook in {channel.name}")
except discord.HTTPException as e:
    if e.status != 429:  # Not a rate limit
        logger.error(f"Failed to delete webhook: {e}")
except Exception as e:
    logger.exception(f"Unexpected error deleting webhook: {e}")
```

---

## HIGH Priority Improvements

### 4. Anti-Selfbot Detection Improvements (antiselfbot.py)

**Problem**: Current detection can have false positives on fast human responders.

**Improvements**:

a) **Add context-aware detection**:
```python
async def check_response_context(self, message: discord.Message):
    """Check if response makes contextual sense"""
    if not message.reference:
        return

    try:
        original = await message.channel.fetch_message(message.reference.message_id)

        # Check if response is contextually appropriate
        # Selfbots often respond with generic/templated messages

        # 1. Check for unusually fast response to complex messages
        if len(original.content) > 200:  # Long message
            response_time = (message.created_at - original.created_at).total_seconds()
            if response_time < 1.0:  # Under 1 second for complex content
                return 50  # High suspicion score

        # 2. Check for pattern matching in responses
        if self._is_templated_response(message.content):
            return 30

    except:
        pass
    return 0

def _is_templated_response(self, content: str) -> bool:
    """Detect templated selfbot responses"""
    templates = [
        r"^(lol|lmao|haha|ok|yes|no|sure|nice|cool)$",
        r"^\+\d+$",  # +1, +rep patterns
        r"^[a-z]{1,3}$",  # Very short responses
    ]
    for pattern in templates:
        if re.match(pattern, content.strip(), re.IGNORECASE):
            return True
    return False
```

b) **Add typing indicator tracking**:
```python
@commands.Cog.listener()
async def on_typing(self, channel, user, when):
    """Track typing events - selfbots rarely trigger typing"""
    if user.bot or not hasattr(channel, 'guild') or not channel.guild:
        return

    tracker = self.get_tracker(channel.guild.id, user.id)
    if not hasattr(tracker, 'typing_events'):
        tracker.typing_events = []

    tracker.typing_events.append(datetime.utcnow())
    # Keep last 20
    tracker.typing_events = tracker.typing_events[-20:]

async def on_message(self, message):
    # ... existing code ...

    # Check if user typed before sending
    tracker = self.get_tracker(message.guild.id, message.author.id)
    if hasattr(tracker, 'typing_events') and tracker.typing_events:
        recent_type = max(tracker.typing_events)
        if (message.created_at.replace(tzinfo=None) - recent_type).total_seconds() < 30:
            # User typed recently - reduce suspicion
            tracker.suspicion_score = max(0, tracker.suspicion_score - 5)
    else:
        # No typing event before message - slightly suspicious
        if len(message.content) > 50:  # Long message without typing
            tracker.suspicion_score += 5
```

### 5. Mass Ban Detection Improvements (antinuke.py)

**Problem**: Current detection triggers after the first ban, which is good, but doesn't track ban velocity.

**Improvement**: Add velocity-based detection:
```python
class BanVelocityTracker:
    def __init__(self):
        self.bans: Dict[int, Dict[int, List[datetime]]] = defaultdict(lambda: defaultdict(list))
        # guild_id -> user_id -> list of ban timestamps

    def record_ban(self, guild_id: int, actor_id: int) -> int:
        """Record a ban and return velocity (bans per minute by this user)"""
        now = datetime.utcnow()
        cutoff = now - timedelta(minutes=1)

        # Clean old entries
        self.bans[guild_id][actor_id] = [
            t for t in self.bans[guild_id][actor_id] if t > cutoff
        ]

        # Add new ban
        self.bans[guild_id][actor_id].append(now)

        return len(self.bans[guild_id][actor_id])

    def get_total_bans(self, guild_id: int, seconds: int = 60) -> int:
        """Get total bans across all actors in timeframe"""
        cutoff = datetime.utcnow() - timedelta(seconds=seconds)
        total = 0
        for actor_bans in self.bans[guild_id].values():
            total += len([t for t in actor_bans if t > cutoff])
        return total
```

### 6. Anti-Raid Improvements (antiraid.py)

**Problem**: Current detection uses simple thresholds. Add ML-inspired pattern detection.

**Improvements**:

a) **Name similarity detection** for coordinated raids:
```python
import difflib

def detect_coordinated_names(self, recent_joins: List[Dict]) -> float:
    """Detect if recent joins have suspiciously similar names"""
    if len(recent_joins) < 3:
        return 0.0

    names = [j['name'] for j in recent_joins[-10:]]
    similarities = []

    for i, name1 in enumerate(names):
        for name2 in names[i+1:]:
            ratio = difflib.SequenceMatcher(None, name1.lower(), name2.lower()).ratio()
            similarities.append(ratio)

    if not similarities:
        return 0.0

    avg_similarity = sum(similarities) / len(similarities)

    # High similarity suggests coordinated raid
    if avg_similarity > 0.7:
        return 100  # Definite raid
    elif avg_similarity > 0.5:
        return 60
    elif avg_similarity > 0.3:
        return 30
    return 0
```

b) **Account creation time clustering**:
```python
def detect_account_clustering(self, recent_joins: List[Dict]) -> float:
    """Detect if accounts were created around the same time"""
    if len(recent_joins) < 5:
        return 0.0

    creation_times = [j['created'] for j in recent_joins[-15:]]

    # Calculate time differences between adjacent creation times
    sorted_times = sorted(creation_times)
    diffs = []
    for i in range(1, len(sorted_times)):
        diff = (sorted_times[i] - sorted_times[i-1]).total_seconds()
        diffs.append(diff)

    if not diffs:
        return 0.0

    # If accounts were created within minutes of each other
    close_creations = sum(1 for d in diffs if d < 300)  # 5 minutes

    if close_creations >= len(diffs) * 0.6:
        return 80  # Likely raid bot accounts
    elif close_creations >= len(diffs) * 0.3:
        return 40
    return 0
```

---

## MEDIUM Priority Improvements

### 7. Database Connection Pooling (postgres.py)

**Problem**: Current implementation may not efficiently handle concurrent database operations.

**Improvement**: Use connection pooling with asyncpg:
```python
import asyncpg

class PostgresDatabase:
    def __init__(self, url: str):
        self.url = url
        self.pool: Optional[asyncpg.Pool] = None

    async def connect(self):
        self.pool = await asyncpg.create_pool(
            self.url,
            min_size=5,
            max_size=20,
            command_timeout=60
        )

    async def execute(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.execute(query, *args)

    async def fetchone(self, query: str, *args):
        async with self.pool.acquire() as conn:
            return await conn.fetchrow(query, *args)
```

### 8. Honeypot Persistence (advanced_security.py)

**Problem**: Honeypot channels/roles are not persisted to database. They're lost on restart.

**Improvement**: Add database persistence for honeypots:
```python
async def load_honeypots(self, guild_id: int):
    """Load honeypots from database"""
    if self.db:
        channels = await self.db.get_honeypot_channels(guild_id)
        roles = await self.db.get_honeypot_roles(guild_id)

        for ch_id in channels:
            self.honeypot.honeypot_channels[guild_id].append(ch_id)
        for r_id in roles:
            self.honeypot.honeypot_roles[guild_id].append(r_id)

async def save_honeypot(self, guild_id: int, item_id: int, item_type: str):
    """Save honeypot to database"""
    if self.db:
        await self.db.add_honeypot(guild_id, item_id, item_type)
```

### 9. Add Captcha/Verification System for Raids

**Improvement**: Add a CAPTCHA-like verification for new members during raids:
```python
class VerificationSystem:
    def __init__(self, bot):
        self.bot = bot
        self.pending_verification: Dict[int, Dict[int, Dict]] = defaultdict(dict)
        # guild_id -> user_id -> {code, expires, attempts}

    async def create_verification(self, guild: discord.Guild, member: discord.Member):
        """Create a verification challenge for a member"""
        import random
        import string

        # Generate simple code
        code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=6))

        self.pending_verification[guild.id][member.id] = {
            'code': code,
            'expires': datetime.utcnow() + timedelta(minutes=5),
            'attempts': 0
        }

        # DM the user
        try:
            embed = discord.Embed(color=0x2b2d31)
            embed.description = (
                f"**Verification Required**\n\n"
                f"Please reply with this code to verify:\n"
                f"```{code}```\n"
                f"You have 5 minutes and 3 attempts."
            )
            await member.send(embed=embed)
            return True
        except:
            return False
```

### 10. Add Rate Limit Awareness

**Improvement**: Track Discord rate limits to avoid hitting them:
```python
class RateLimitTracker:
    def __init__(self):
        self.requests: Dict[str, List[datetime]] = defaultdict(list)
        self.limits = {
            'audit_log': (10, 10),      # 10 requests per 10 seconds
            'guild_edit': (5, 60),       # 5 edits per minute
            'channel_edit': (10, 60),    # 10 edits per minute
            'role_edit': (10, 60),       # 10 role edits per minute
            'ban': (30, 60),             # 30 bans per minute
            'kick': (30, 60),            # 30 kicks per minute
        }

    async def can_request(self, action: str) -> bool:
        """Check if we can make a request without hitting rate limit"""
        if action not in self.limits:
            return True

        max_requests, timeframe = self.limits[action]
        cutoff = datetime.utcnow() - timedelta(seconds=timeframe)

        # Clean old entries
        self.requests[action] = [t for t in self.requests[action] if t > cutoff]

        return len(self.requests[action]) < max_requests

    def record_request(self, action: str):
        """Record a request"""
        self.requests[action].append(datetime.utcnow())
```

---

## LOW Priority / Nice-to-Have

### 11. Add Command Cooldowns

```python
from discord.ext.commands import cooldown, BucketType

@commands.hybrid_command()
@cooldown(1, 5, BucketType.user)  # 1 use per 5 seconds per user
async def trust(self, ctx, member: discord.Member):
    # ...
```

### 12. Add Metrics/Statistics Dashboard Data

```python
class SecurityMetrics:
    def __init__(self):
        self.metrics = {
            'attacks_blocked': 0,
            'bans_prevented': 0,
            'channels_restored': 0,
            'webhooks_deleted': 0,
            'selfbots_detected': 0,
            'raids_stopped': 0,
        }
        self.hourly_stats: Dict[str, Dict[int, int]] = defaultdict(lambda: defaultdict(int))

    def record(self, metric: str, guild_id: int, amount: int = 1):
        self.metrics[metric] += amount
        hour = datetime.utcnow().hour
        self.hourly_stats[metric][hour] += amount

    def get_stats(self, guild_id: int = None):
        return self.metrics.copy()
```

### 13. Add Webhook Message Deduplication

**Problem**: Multiple webhook messages might be processed before deletion.

```python
class WebhookMessageDedup:
    def __init__(self, max_size: int = 1000):
        self.seen_hashes: Set[str] = set()
        self.max_size = max_size

    def is_duplicate(self, content: str, author_name: str) -> bool:
        """Check if we've seen this message before"""
        msg_hash = hashlib.md5(f"{content}{author_name}".encode()).hexdigest()

        if msg_hash in self.seen_hashes:
            return True

        self.seen_hashes.add(msg_hash)

        # Cleanup if too large
        if len(self.seen_hashes) > self.max_size:
            self.seen_hashes = set(list(self.seen_hashes)[-500:])

        return False
```

### 14. Add Threat Intelligence Sharing

```python
async def share_threat_intel(self, threat_type: str, threat_data: dict):
    """Share threat intelligence with other servers using the bot"""
    if threat_type == 'mass_ban_actor':
        # Add to global bad actors list
        self.global_bad_actors.add(threat_data['user_id'])
    elif threat_type == 'raid_pattern':
        # Share raid pattern signatures
        self.known_raid_patterns.append(threat_data)
```

---

## Code Quality Improvements

### 15. Type Hints Throughout

Add proper type hints to all functions for better IDE support and code documentation:
```python
from typing import Optional, Dict, List, Set, Tuple, Union

async def get_settings(self, guild_id: int) -> Dict[str, Any]:
    """Get guild settings"""
    ...

def is_trusted(self, guild: discord.Guild, user_id: int) -> bool:
    """Check if user is trusted"""
    ...
```

### 16. Centralized Constants

Create a constants file:
```python
# constants.py
class Thresholds:
    MASS_BAN = 1
    MASS_KICK = 1
    MASS_CHANNEL_DELETE = 1
    WEBHOOK_SPAM = 5
    REACTION_TIME_MS = 50
    SELFBOT_RESPONSE_TIME = 0.5

class Permissions:
    DANGEROUS = [
        'administrator',
        'ban_members',
        'kick_members',
        'manage_channels',
        'manage_guild',
        'manage_roles',
        'manage_webhooks',
    ]
```

### 17. Add Unit Tests

Create tests for critical functions:
```python
# tests/test_antinuke.py
import pytest
from bot.cogs.antinuke import AntiNuke

class TestAntiNuke:
    def test_is_suspicious_webhook_name(self):
        cog = AntiNuke(None)
        assert cog._is_suspicious_webhook_name("nuke") == True
        assert cog._is_suspicious_webhook_name("raider") == True
        assert cog._is_suspicious_webhook_name("MyBot") == False

    def test_has_dangerous_permissions(self):
        # ...
```

---

## Summary

| Priority | Count | Key Areas |
|----------|-------|-----------|
| Critical | 3 | Race conditions, Rate limiting, Error handling |
| High | 3 | Selfbot detection, Mass ban velocity, Raid patterns |
| Medium | 4 | DB pooling, Honeypot persistence, Verification, Rate limits |
| Low | 4 | Cooldowns, Metrics, Dedup, Threat sharing |
| Code Quality | 3 | Types, Constants, Tests |

The most impactful improvements would be:
1. **Fix race conditions** in punishment logic
2. **Add audit log caching** to prevent rate limits
3. **Improve selfbot detection** with typing indicators and context
4. **Add coordinated raid detection** with name similarity and account clustering
