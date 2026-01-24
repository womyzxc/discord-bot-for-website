# 🛡️ Offcialx Security Bot - Complete Documentation

## 📋 Table of Contents
1. [Permission Levels](#permission-levels)
2. [Anti-Nuke Protection](#anti-nuke-protection)
3. [Anti-Raid Protection](#anti-raid-protection)
4. [Anti-Spam Protection](#anti-spam-protection)
5. [Anti-Selfbot Detection](#anti-selfbot-detection)
6. [Whitelist Management](#whitelist-management)
7. [Moderation Commands](#moderation-commands)
8. [Lockdown System](#lockdown-system)
9. [Backup System](#backup-system)
10. [Ban Sync System](#ban-sync-system)
11. [VPN Detection](#vpn-detection)
12. [Utility Commands](#utility-commands)
13. [Bot Admin Commands](#bot-admin-commands)
14. [All Thresholds](#all-thresholds)

---

## 🔐 Permission Levels

| Level | Who | Description |
|-------|-----|-------------|
| **Bot Developer** | Users in `OWNER_IDS` env variable | Full control over bot, can use all commands in any server |
| **Server Owner** | Guild owner | Full control over bot settings in their server |
| **Administrator** | Users with Administrator permission | Can use most moderation commands |
| **Moderator** | Users with Manage Messages/Kick/Ban | Can use basic moderation |
| **Trusted User** | Users added via `!trust` | Immune to anti-nuke actions |
| **Trusted Bot** | Bots added via `!trustbot` | Immune to anti-bot protection |
| **User** | Regular server member | Can use utility commands only |

---

## 🛡️ Anti-Nuke Protection

### Features (All Enabled by Default)

| Feature | Setting | Description |
|---------|---------|-------------|
| **Anti-Channel Create** | `anti_channel_create` | Deletes channels created by untrusted users |
| **Anti-Channel Delete** | `anti_channel_delete` | Bans attacker + auto-restores deleted channels |
| **Anti-Channel Rename** | `anti_channel_rename` | Reverts channel renames by untrusted users |
| **Anti-Webhook** | `anti_webhook` | Instantly deletes unauthorized webhooks |
| **Anti-Role Create** | `anti_role_create` | Deletes dangerous roles created by untrusted users |
| **Anti-Role Delete** | `anti_role_delete` | Punishes role deletion by untrusted users |
| **Anti-Role Update** | `anti_role_update` | Reverts dangerous permission changes |
| **Anti-Ban** | `anti_ban` | Unbans victims + punishes unauthorized banners |
| **Anti-Bot** | `anti_bot` | Kicks unauthorized bots + punishes adders |
| **Anti-Permissions** | `anti_permissions` | Blocks dangerous role grants |
| **Anti-Integration** | `anti_integration` | Blocks unauthorized apps/integrations |
| **Anti-Vanity** | `anti_vanity` | Protects vanity URL changes |

### Commands

| Command | Aliases | Description | Who Can Use |
|---------|---------|-------------|-------------|
| `/antinuke` | - | View protection status | Server Owner, Bot Dev |
| `/setlog #channel` | - | Set security log channel | Server Owner, Bot Dev |
| `/antinuke_enable` | `an-on` | Enable anti-nuke | Server Owner, Bot Dev |
| `/antinuke_disable` | `an-off` | Disable anti-nuke (DANGEROUS) | Server Owner, Bot Dev |
| `/punishment ban/kick` | `anpunish` | Set punishment type | Server Owner, Bot Dev |
| `/trust @user` | - | Add user to trusted list | Server Owner, Bot Dev |
| `/untrust @user` | - | Remove user from trusted | Server Owner, Bot Dev |
| `/trusted` | - | View all trusted users | Server Owner, Bot Dev |
| `/trustbot @bot` | - | Trust a bot | Server Owner, Bot Dev |
| `/untrustbot @bot` | - | Untrust a bot | Server Owner, Bot Dev |
| `/trustedbots` | - | View all trusted bots | Server Owner, Bot Dev |
| `/serverlock [seconds]` | - | Lock server (default 60s) | Server Owner, Bot Dev |
| `/serverunlock` | - | Unlock server immediately | Server Owner, Bot Dev |
| `/nukewebhooks` | - | Delete ALL webhooks (emergency) | Server Owner, Bot Dev |
| `/attackstats` | - | View attack statistics | Server Owner, Bot Dev |
| `/ancommands` | - | List all anti-nuke commands | Everyone |
| `/test_antinuke` | `an-test` | Test security logging | Server Owner, Bot Dev |
| `/restore` | - | View deleted channels | Server Owner, Bot Dev |
| `/restore_channel <num>` | `rc` | Restore a channel | Server Owner, Bot Dev |
| `/restore_clear` | - | Clear restore list | Server Owner, Bot Dev |

### Dangerous Permissions (Triggers Protection)
```
- administrator
- ban_members
- kick_members
- manage_channels
- manage_guild
- manage_roles
- manage_webhooks
- mention_everyone
```

---

## ⚔️ Anti-Raid Protection

### Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `True` | Protection status |
| `join_threshold` | `10` | Max joins in timeframe |
| `join_timeframe` | `10` seconds | Detection window |
| `min_account_age` | `7` days | Minimum account age |
| `auto_raid_mode` | `True` | Auto-enable raid mode |
| `raid_mode_duration` | `300` seconds | Raid mode duration |
| `verification_level` | `medium` | Verification during raid |
| `action` | `kick` | Action on raiders (kick/ban/quarantine) |
| `smart_detection` | `True` | Detect suspicious patterns |

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!antiraid` / `/antiraid` | View anti-raid status | Server Owner, Bot Dev |
| `!antiraid enable` | Enable anti-raid | Server Owner, Bot Dev |
| `!antiraid disable` | Disable anti-raid | Server Owner, Bot Dev |
| `!antiraid threshold <num>` | Set join threshold | Server Owner, Bot Dev |
| `!antiraid timeframe <sec>` | Set detection timeframe | Server Owner, Bot Dev |
| `!antiraid accountage <days>` | Set minimum account age | Server Owner, Bot Dev |
| `!antiraid action <kick/ban>` | Set raid action | Server Owner, Bot Dev |
| `!antiraid raidmode` | Manually toggle raid mode | Server Owner, Bot Dev |

### Detection Features
- Mass join detection (10+ joins in 10 seconds)
- New account detection (< 7 days old)
- Similar username pattern detection
- Coordinated join pattern detection
- Smart profile analysis

---

## 📝 Anti-Spam Protection

### Default Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `enabled` | `False` | Off by default |
| `action` | `warn` | warn/mute/kick/ban |
| `message_limit` | `5` | Max messages in timeframe |
| `message_timeframe` | `5` seconds | Detection window |
| `allow_links` | `True` | Allow URL links |
| `allow_invites` | `False` | Block Discord invites |
| `block_shorteners` | `True` | Block URL shorteners |
| `block_phishing` | `True` | Block phishing domains |
| `exempt_roles` | `[]` | Roles immune to spam check |
| `exempt_channels` | `[]` | Channels without spam check |

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!antispam` / `/antispam` | View anti-spam status | Server Owner, Bot Dev |
| `!antispam enable` | Enable anti-spam | Server Owner, Bot Dev |
| `!antispam disable` | Disable anti-spam | Server Owner, Bot Dev |
| `!antispam action <type>` | Set spam action | Server Owner, Bot Dev |
| `!antispam limit <num>` | Set message limit | Server Owner, Bot Dev |
| `!antispam links on/off` | Toggle links | Server Owner, Bot Dev |
| `!antispam invites on/off` | Toggle invites | Server Owner, Bot Dev |
| `!antispam exempt @role` | Exempt a role | Server Owner, Bot Dev |
| `!antispam unexempt @role` | Remove exemption | Server Owner, Bot Dev |

### Blocked Domains
- **URL Shorteners:** bit.ly, tinyurl.com, t.co, goo.gl, ow.ly, is.gd, buff.ly, adf.ly, tiny.cc, j.mp
- **Phishing:** discord-nitro.com, discordgift.com, free-nitro.com, discord-app.com, steamnity.com

---

## 🤖 Anti-Selfbot Detection

### Features
- Message timing analysis (detects inhuman response speeds)
- Behavioral pattern detection
- API abuse detection
- Automated response detection

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!antiselfbot` / `/antiselfbot` | View status | Server Owner, Bot Dev |
| `!antiselfbot enable` | Enable detection | Server Owner, Bot Dev |
| `!antiselfbot disable` | Disable detection | Server Owner, Bot Dev |
| `!antiselfbot action <type>` | Set action (warn/kick/ban) | Server Owner, Bot Dev |
| `!antiselfbot sensitivity <level>` | Set detection level | Server Owner, Bot Dev |

---

## 📋 Whitelist Management

### Whitelist Levels
| Level | Value | Description |
|-------|-------|-------------|
| `trusted` | 1 | Basic immunity |
| `admin` | 2 | Admin-level trust |
| `owner` | 3 | Owner-level trust |

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!wlist` / `/wlist` | View whitelist status | Server Owner, Bot Dev |
| `!wlist add @user [level]` | Add user to whitelist | Server Owner, Bot Dev |
| `!wlist remove @user` | Remove from whitelist | Server Owner, Bot Dev |
| `!wlist list` | View all whitelisted | Server Owner, Bot Dev |
| `!wlist addrole @role` | Whitelist entire role | Server Owner, Bot Dev |
| `!wlist removerole @role` | Remove role whitelist | Server Owner, Bot Dev |
| `!wlist roles` | View whitelisted roles | Server Owner, Bot Dev |

---

## 🔨 Moderation Commands

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `/ban @user [reason]` | Ban a user | Admin (Ban Members perm) |
| `/unban <user_id>` | Unban a user | Admin (Ban Members perm) |
| `/massban <ids...>` | Ban multiple users | Server Owner, Bot Dev |
| `/kick @user [reason]` | Kick a user | Admin (Kick Members perm) |
| `/mute @user [duration] [reason]` | Timeout a user | Admin (Moderate Members perm) |
| `/unmute @user` | Remove timeout | Admin (Moderate Members perm) |
| `/warn @user [reason]` | Warn a user | Admin (Kick Members perm) |
| `/warnings @user` | View user's warnings | Admin |
| `/clearwarns @user` | Clear all warnings | Admin |
| `/purge <amount>` | Delete messages | Admin (Manage Messages perm) |
| `/purgeuser @user <amount>` | Delete user's messages | Admin (Manage Messages perm) |
| `/slowmode <seconds>` | Set channel slowmode | Admin (Manage Channels perm) |
| `/modlog #channel` | Set moderation log | Server Owner, Bot Dev |

### Moderation Settings

| Setting | Default | Description |
|---------|---------|-------------|
| `warn_threshold` | `3` | Warnings before auto-action |
| `warn_action` | `mute` | Action on threshold (mute/kick/ban) |
| `warn_mute_duration` | `3600` | Mute duration in seconds (1 hour) |
| `default_mute_duration` | `3600` | Default mute duration |
| `dm_on_action` | `True` | DM user on moderation |

---

## 🔒 Lockdown System

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!lockdown` / `/lockdown` | View lockdown status | Server Owner, Bot Dev |
| `!lockdown enable` | Lock entire server | Server Owner, Bot Dev |
| `!lockdown disable` | Unlock entire server | Server Owner, Bot Dev |
| `!lockdown channel #ch` | Lock specific channel | Admin |
| `!lockdown unlock #ch` | Unlock specific channel | Admin |
| `!lockdown all` | Lock all channels | Server Owner, Bot Dev |
| `!lockdown panic` | Emergency lockdown | Server Owner, Bot Dev |

### Default Settings
| Setting | Default |
|---------|---------|
| `lockdown_duration` | `300` seconds (5 minutes) |

---

## 💾 Backup System

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!backup` / `/backup` | View backup status | Server Owner, Bot Dev |
| `!backup create` | Create server backup | Server Owner, Bot Dev |
| `!backup list` | View all backups | Server Owner, Bot Dev |
| `!backup load <id>` | Load/preview backup | Server Owner, Bot Dev |
| `!backup restore <id>` | Restore from backup | Server Owner, Bot Dev |
| `!backup delete <id>` | Delete a backup | Server Owner, Bot Dev |
| `!backup auto on/off` | Toggle auto-backup | Server Owner, Bot Dev |

### What Gets Backed Up
- Server settings (name, icon, region)
- All channels (with permissions)
- All roles (with permissions)
- Channel categories
- Webhook configurations

---

## 🔗 Ban Sync System

Cross-server ban synchronization.

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!bansync` / `/bansync` | View ban sync status | Server Owner, Bot Dev |
| `!bansync enable` | Enable ban syncing | Server Owner, Bot Dev |
| `!bansync disable` | Disable ban syncing | Server Owner, Bot Dev |
| `!bansync link <server_id>` | Link to another server | Server Owner, Bot Dev |
| `!bansync unlink <server_id>` | Unlink server | Server Owner, Bot Dev |
| `!bansync list` | View linked servers | Server Owner, Bot Dev |
| `!bansync import <server_id>` | Import bans from server | Server Owner, Bot Dev |

---

## 🌐 VPN Detection

Block VPN/Proxy users from joining.

### Commands

| Command | Description | Who Can Use |
|---------|-------------|-------------|
| `!vpn` / `/vpn` | View VPN detection status | Server Owner, Bot Dev |
| `!vpn enable` | Enable VPN detection | Server Owner, Bot Dev |
| `!vpn disable` | Disable VPN detection | Server Owner, Bot Dev |
| `!vpn action <kick/ban>` | Set action on VPN users | Server Owner, Bot Dev |
| `!vpn check @user` | Check if user is on VPN | Admin |
| `!vpn whitelist <ip>` | Whitelist an IP | Server Owner, Bot Dev |

---

## 🔧 Utility Commands

| Command | Aliases | Description | Who Can Use |
|---------|---------|-------------|-------------|
| `/avatar @user` | `av`, `pfp` | Get user's avatar | Everyone |
| `/banner @user` | `userbanner`, `ub` | Get user's banner | Everyone |
| `/userinfo @user` | `ui`, `whois` | Get user information | Everyone |
| `/serverinfo` | `si`, `server` | Get server information | Everyone |
| `/servericon` | `sicon`, `icon` | Get server icon | Everyone |
| `/serverbanner` | `sb` | Get server banner | Everyone |
| `/serverprofile` | `sp` | Full server profile | Everyone |
| `/ping` | - | Check bot latency | Everyone |
| `/invite` | - | Get bot invite link | Everyone |
| `/info` | `about`, `botinfo` | Bot information | Everyone |
| `/help` | `h`, `cmds` | Help menu | Everyone |
| `/botstats` | `stats` | Bot statistics | Everyone |
| `/support` | - | Support server link | Everyone |

---

## 👑 Bot Admin Commands (Bot Dev Only)

| Command | Aliases | Description | Who Can Use |
|---------|---------|-------------|-------------|
| `!botstatus <status>` | `setstatus` | Set bot status | Bot Dev Only |
| `!servers` | `servercount` | View server count | Bot Dev Only |
| `!serverlist` | `listservers` | List all servers | Bot Dev Only |
| `!setjoinlog #channel` | - | Set bot join/leave log | Bot Dev Only |
| `!leaveserver <id>` | `leave` | Leave a server | Bot Dev Only |
| `!ownerinfo <server_id>` | `oi` | Get server owner info | Bot Dev Only |
| `!sync` | - | Sync slash commands globally | Bot Dev Only |
| `!syncguild` | - | Sync slash commands to guild | Bot Dev Only |
| `!clearsync` | - | Clear and resync commands | Bot Dev Only |
| `!listcmds` | - | List registered commands | Bot Dev Only |

---

## 📊 All Thresholds

### Anti-Nuke Protection (INSTANT PUNISHMENT)

**Rule: Untrusted User + 1 Action = INSTANT Punishment**

| Action | Behavior | Response |
|--------|----------|----------|
| Channel Delete | 1 delete = instant | Ban + Auto-restore channel |
| Channel Create | 1 create = instant | Ban + Delete channel |
| Channel Rename | 1 rename = instant | Ban + Revert name |
| Role Delete | 1 delete = instant | Ban |
| Role Create (dangerous perms) | 1 create = instant | Ban + Delete role |
| Role Update (add dangerous perms) | 1 update = instant | Ban + Revert permissions |
| Webhook Create | 1 create = instant | Ban + Delete webhook |
| Unauthorized Ban | 1 ban = instant | Ban attacker + Unban victim |
| Unauthorized Kick | 1 kick = instant | Ban attacker |
| Bot Add | 1 bot = instant | Kick bot + Ban adder |
| Dangerous Role Grant | 1 grant = instant | Ban + Remove roles |
| Integration Add | 1 integration = instant | Ban + Delete integration |
| Server Settings Change | 1 change = instant | Ban + Revert settings |
| Member Prune | 1 prune = instant | Ban attacker |

**No timeframe needed** - punishment is immediate on first action by untrusted user.

### Anti-Spam Thresholds

| Threshold | Default | Description |
|-----------|---------|-------------|
| `MESSAGE_THRESHOLD` | `10` | Messages to trigger |
| `MESSAGE_TIMEFRAME` | `5` seconds | Detection window |
| `DUPLICATE_THRESHOLD` | `5` | Duplicate messages to trigger |
| `MENTION_THRESHOLD` | `10` | Mentions to trigger |
| `EMOJI_THRESHOLD` | `20` | Emojis to trigger |

### Anti-Raid Thresholds

| Threshold | Default | Description |
|-----------|---------|-------------|
| `JOIN_THRESHOLD` | `10` | Joins to trigger raid mode |
| `JOIN_TIMEFRAME` | `10` seconds | Detection window |
| `NEW_ACCOUNT_DAYS` | `7` days | Min account age |
| `RAID_MODE_DURATION` | `300` seconds | Auto raid mode duration |

### Command Cooldowns

| Cooldown | Value | Description |
|----------|-------|-------------|
| All antinuke commands | `5` seconds | Per user cooldown |

---

## ⏱️ Timing & Intervals

| Timer | Value | Description |
|-------|-------|-------------|
| Webhook scan interval | `1` second | Continuous webhook check |
| Fast webhook scan | `0.5` seconds | Blacklist check |
| Periodic cleanup | `300` seconds | Cache cleanup |
| Mass restore delay | `3` seconds | Wait before restoring |
| Auto-lockdown duration | `30` seconds | Emergency lockdown |
| Punishment cooldown | `60` seconds | Prevent re-punishing |

---

## 🚨 Punishment Actions

| Action | Description |
|--------|-------------|
| `ban` | Ban user permanently |
| `kick` | Kick user from server |
| `mute` | Timeout user |
| `warn` | Issue warning |
| `quarantine` | Strip roles + add quarantine role |

---

## 📝 Notes

1. **Bot Developer** has access to ALL commands in ALL servers
2. **Server Owner** can configure everything for their own server
3. **Trusted Users** (added via `!trust`) are immune to anti-nuke actions
4. **Administrators** can use moderation commands but NOT security configuration
5. **Regular Users** can only use utility commands (avatar, userinfo, etc.)

---

*Documentation generated for Offcialx Security Bot v3.0.0*
