# Discord Security Bot - TODO List

## Completed
- [x] Ultra-aggressive anti-nuke protection for channel rename/delete/webhook events
- [x] Instant punishment on first unauthorized action within 1 second
- [x] Backup and restore system with database persistence
- [x] Proper permission overwrite serialization/deserialization
- [x] Lockdown bypass for trusted users and roles
- [x] Lockdown permission backup and restore (preserves custom channel permissions)
- [x] Push all code to GitHub

## New Lockdown Features Added
- [x] `!trustrole @Role` - Add role to trusted (can send during lockdown)
- [x] `!untrustrole @Role` - Remove role from trusted
- [x] `!trustedroles` - View all trusted roles
- [x] `!lockdownstatus` - View lockdown status and bypass config
- [x] Admins and mods automatically bypass lockdown
- [x] Original channel permissions backed up before lockdown
- [x] Original permissions properly restored after lockdown ends

## Pending / Future Enhancements
- [ ] Add lockdown schedule (auto-lock at specific times)
- [ ] Add per-channel lockdown bypass settings
- [ ] Add lockdown history logging
- [ ] Add lockdown notification to a specific channel
- [ ] Test all lockdown features in production
