# Discord Bot Command Permissions

## Permission Levels

| Level | Description |
|-------|-------------|
| **Bot Owner** | Users in OWNER_IDS environment variable |
| **Bot Developer** | Same as Bot Owner |
| **Server Owner** | The owner of the Discord server |
| **Admin** | Users with Administrator permission |
| **Moderator** | Users with Manage Messages, Kick, or Ban permissions |
| **Member** | Regular server members |

---

## Anti-Nuke Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/antinuke` | Admin | Server Owner, Bot Owner |
| `/setlog` | Admin | Server Owner, Bot Owner |
| `/antinuke_enable` | Admin | Server Owner, Bot Owner |
| `/antinuke_disable` | Admin | Server Owner, Bot Owner |
| `/trust @user` | Admin | Server Owner, Bot Owner |
| `/untrust @user` | Admin | Server Owner, Bot Owner |
| `/trusted` | Admin | Server Owner, Bot Owner, Admin |
| `/trustbot @bot` | Admin | Server Owner, Bot Owner |
| `/untrustbot @bot` | Admin | Server Owner, Bot Owner |
| `/trustedbots` | Admin | Server Owner, Bot Owner, Admin |
| `/serverlock [seconds]` | Admin | Server Owner, Bot Owner, Admin |
| `/serverunlock` | Admin | Server Owner, Bot Owner, Admin |
| `/nukewebhooks` | Admin | Server Owner, Bot Owner |
| `/attackstats` | Admin | Server Owner, Bot Owner, Admin |
| `/ancommands` | None | Everyone |
| `/test_antinuke` | Admin | Server Owner, Bot Owner |
| `/restore` | Admin | Server Owner, Bot Owner |
| `/restore_channel` | Admin | Server Owner, Bot Owner |
| `/restore_clear` | Admin | Server Owner, Bot Owner |

---

## Whitelist Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/wlist` | Admin | Server Owner, Bot Owner |
| `/wlist add @user [level]` | Admin | Server Owner, Bot Owner |
| `/wlist remove @user` | Admin | Server Owner, Bot Owner |
| `/wlist check @user` | Admin | Server Owner, Bot Owner |
| `/wlist update @user level` | Admin | Server Owner, Bot Owner |
| `/wlist clear [level]` | Admin | Server Owner, Bot Owner |
| `/wlist setlog #channel` | Admin | Server Owner, Bot Owner |
| `/wlist role @role` | Admin | Server Owner, Bot Owner |
| `/wlist unrole @role` | Admin | Server Owner, Bot Owner |
| `/wlist roles` | Admin | Server Owner, Bot Owner |
| `/wlist clearroles` | Admin | Server Owner, Bot Owner |

---

## Anti-Selfbot Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/antiselfbot` | Admin | Server Owner, Bot Owner |
| `/antiselfbot enable` | Admin | Server Owner, Bot Owner |
| `/antiselfbot disable` | Admin | Server Owner, Bot Owner |
| `/antiselfbot action` | Admin | Server Owner, Bot Owner |
| `/antiselfbot check @user` | Admin | Server Owner, Bot Owner |
| `/antiselfbot clear @user` | Admin | Server Owner, Bot Owner |
| `/antiselfbot setlog #channel` | Admin | Server Owner, Bot Owner |
| `/antiselfbot threshold` | Admin | Server Owner, Bot Owner |

---

## Moderation Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/kick @user [reason]` | Kick Members | Moderator, Admin, Server Owner |
| `/ban @user [reason]` | Ban Members | Moderator, Admin, Server Owner |
| `/unban user_id` | Ban Members | Moderator, Admin, Server Owner |
| `/mute @user [duration]` | Moderate Members | Moderator, Admin, Server Owner |
| `/unmute @user` | Moderate Members | Moderator, Admin, Server Owner |
| `/warn @user [reason]` | Manage Messages | Moderator, Admin, Server Owner |
| `/warnings @user` | Manage Messages | Moderator, Admin, Server Owner |
| `/clearwarns @user` | Manage Messages | Moderator, Admin, Server Owner |
| `/purge [amount]` | Manage Messages | Moderator, Admin, Server Owner |
| `/slowmode [seconds]` | Manage Channels | Moderator, Admin, Server Owner |

---

## Utility Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/help [category]` | None | Everyone |
| `/ping` | None | Everyone |
| `/avatar [@user]` | None | Everyone |
| `/banner [@user]` | None | Everyone |
| `/userinfo [@user]` | None | Everyone |
| `/serverinfo` | None | Everyone |
| `/servericon` | None | Everyone |
| `/serverbanner` | None | Everyone |
| `/serverprofile` | None | Everyone |

---

## Role Commands

| Command | Permission | Who Can Use |
|---------|------------|-------------|
| `/role @user @role` | Manage Roles | Admin, Server Owner |
| `/unrole @user @role` | Manage Roles | Admin, Server Owner |

---

## Database Persistence

The following data is **automatically saved** and **loads on bot restart**:

| Data Type | Persisted |
|-----------|-----------|
| Anti-Nuke settings (enabled, log channel, etc.) | Yes |
| Trusted users (`/trust`) | Yes |
| Trusted bots (`/trustbot`) | Yes |
| Whitelisted users (`/wlist add`) | Yes |
| Whitelisted roles (`/wlist role`) | Yes |
| Anti-Selfbot settings | Yes |
| Whitelist settings | Yes |
| Warnings | Yes |
| Security logs | Yes |

**No need to re-enable or re-configure after bot restart!**
