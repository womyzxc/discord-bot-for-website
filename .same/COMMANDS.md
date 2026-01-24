# Offcialx Bot - Command Reference

All commands work with both **prefix** (`!`) and **slash** (`/`)

---

## 🔑 WHO CAN USE OWNER COMMANDS?

**Only these people can use owner-only commands:**
1. **Server Owner** - The person who created the server
2. **Bot Owner** - ID: `1226754207051153428`
3. **Developer** - ID: `1184454687865438218`

---

## 👑 OWNER-ONLY COMMANDS

These commands can ONLY be used by server owner, bot owner, or developer.

### Anti-Nuke Configuration
| Command | Description |
|---------|-------------|
| `!antinuke` / `/antinuke` | View anti-nuke status |
| `!antinuke_enable` | Enable anti-nuke protection |
| `!antinuke_disable` | Disable anti-nuke protection |
| `!setlog #channel` | Set security log channel |
| `!trust @user` | Add user to trusted whitelist |
| `!untrust @user` | Remove user from whitelist |
| `!trustbot @bot` | Add bot to trusted bots |
| `!trusted` | View all trusted users |
| `!trustedbots` | View all trusted bots |
| `!attackstats` | View blocked attacks |
| `!nukewebhooks` | Delete ALL webhooks (emergency) |

### Server Protection
| Command | Description |
|---------|-------------|
| `!serverlock [secs]` | Lock entire server |
| `!serverunlock` | Unlock entire server |
| `!lockdown [duration]` | Lock down server |
| `!lockdown end` | End server lockdown |

### Anti-Spam
| Command | Description |
|---------|-------------|
| `!antispam` | View anti-spam status |
| `!antispam enable` | Enable anti-spam |
| `!antispam disable` | Disable anti-spam |
| `!antispam action <warn/mute/kick/ban>` | Set spam action |
| `!antispam setlog #channel` | Set spam log channel |

### Anti-Raid
| Command | Description |
|---------|-------------|
| `!antiraid` | View anti-raid status |
| `!antiraid enable` | Enable anti-raid |
| `!antiraid disable` | Disable anti-raid |
| `!antiraid action <kick/ban/quarantine>` | Set raid action |

### VPN Detection
| Command | Description |
|---------|-------------|
| `!vpn` | View VPN detection status |
| `!vpn enable` | Enable VPN detection |
| `!vpn disable` | Disable VPN detection |
| `!vpn action <kick/ban/alert>` | Set VPN action |

### Whitelist
| Command | Description |
|---------|-------------|
| `!whitelist` | View all whitelisted users |
| `!whitelist add @user` | Add user to whitelist |
| `!whitelist remove @user` | Remove user |
| `!whitelist clear` | Clear entire whitelist |

### Backup
| Command | Description |
|---------|-------------|
| `!backup` | View server backups |
| `!backup create` | Create new backup |
| `!backup list` | List all backups |
| `!backup clear` | Delete all backups |

### Channel Management
| Command | Description |
|---------|-------------|
| `!lock` | Lock current channel |
| `!unlockc` | Unlock current channel |
| `!slowmode [secs]` | Set channel slowmode |

### Mass Moderation
| Command | Description |
|---------|-------------|
| `!massban <ids>` | Mass ban (comma-separated) |

### Bot Links
| Command | Description |
|---------|-------------|
| `!invite` | Get bot invite link |
| `!support` | Support server link |
| `!setup` | Run setup wizard |

---

## 🟢 MODERATOR COMMANDS

These can be used by anyone with the required Discord permissions.

### Ban/Kick (Requires: `Ban Members` / `Kick Members`)
| Command | Description |
|---------|-------------|
| `!ban @user [reason]` | Ban a member |
| `!unban <user_id>` | Unban a user |
| `!kick @user [reason]` | Kick a member |

### Timeout (Requires: `Moderate Members`)
| Command | Description |
|---------|-------------|
| `!mute @user [duration]` | Timeout member (10m, 1h, 1d) |
| `!unmute @user` | Remove timeout |
| `!warn @user [reason]` | Warn a member |
| `!warnings @user` | View warnings |
| `!clearwarns @user` | Clear warnings |

### Messages (Requires: `Manage Messages`)
| Command | Description |
|---------|-------------|
| `!purge [amount]` | Delete messages (1-1000) |
| `!purgeuser @user [amount]` | Delete user's messages |

### Roles (Requires: `Manage Roles`)
| Command | Description |
|---------|-------------|
| `!role @user @role` | Toggle role |
| `!addrole @user @role` | Add role |
| `!removerole @user @role` | Remove role |

### Nicknames (Requires: `Manage Nicknames`)
| Command | Description |
|---------|-------------|
| `!nick @user [name]` | Set nickname |

---

## 🟡 ALL MEMBERS

Anyone can use these commands.

### Help & Info
| Command | Description |
|---------|-------------|
| `!help` / `/help` | Main help menu |
| `!help antinuke` | Anti-nuke commands |
| `!help mod` | Moderation commands |
| `!help whitelist` | Whitelist commands |
| `!help raid` | Anti-raid commands |
| `!help spam` | Anti-spam commands |
| `!ping` | Check bot latency |
| `!info` | Bot information |
| `!botstats` | Bot statistics |

### User Info
| Command | Description |
|---------|-------------|
| `!userinfo [@user]` | Get user info |
| `!serverinfo` | Get server info |
| `!avatar [@user]` | Get avatar |

---

## ⚠️ Role Hierarchy Rules

Moderation commands check role hierarchy:
- ❌ Cannot moderate yourself
- ❌ Cannot moderate the bot
- ❌ Cannot moderate server owner
- ❌ Cannot moderate someone with higher/equal role
- ✅ Server owner bypasses all checks
- ✅ Bot owner/Developer bypasses all checks

---

## 🛡️ What Anti-Nuke Protects Against

- ✅ Mass channel create/delete/rename
- ✅ Mass role create/delete/modify
- ✅ Webhook spam (selfbot nukes)
- ✅ Unauthorized bot additions
- ✅ Mass bans/kicks
- ✅ Permission escalation
- ✅ Dangerous role grants

**Untrusted users are instantly BANNED!**
