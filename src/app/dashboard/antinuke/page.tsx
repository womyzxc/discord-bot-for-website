import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Link from "next/link";

export default async function AntiNukePage() {
  const session = await auth();

  if (!session?.user) {
    redirect("/auth");
  }

  const commands = [
    {
      category: "Protection",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      color: "green",
      commands: [
        {
          name: "!antinuke [on/off]",
          description: "Enable or disable anti-nuke protection for your server",
          example: "!antinuke on",
        },
        {
          name: "!punish [ban/kick]",
          description: "Set the punishment method for detected threats",
          example: "!punish ban",
        },
        {
          name: "!restore [on/off]",
          description: "Toggle manual channel restoration after an attack",
          example: "!restore on",
        },
        {
          name: "!drestore [count]",
          description: "Restore a specified number of deleted channels",
          example: "!drestore 5",
        },
      ],
    },
    {
      category: "Vanity & Status",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      ),
      color: "purple",
      commands: [
        {
          name: "!vanity [on/off]",
          description: "Toggle vanity URL restoration if changed by attacker",
          example: "!vanity on",
        },
        {
          name: "!status [type] [message]",
          description: "Change the bot's status (playing, watching, listening)",
          example: "!status playing Protecting servers",
        },
      ],
    },
    {
      category: "Logging",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
        </svg>
      ),
      color: "cyan",
      commands: [
        {
          name: "!setlogs [#channel]",
          description: "Set the channel where security logs will be sent",
          example: "!setlogs #security-logs",
        },
      ],
    },
    {
      category: "Whitelist Management",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: "yellow",
      commands: [
        {
          name: "!whiterole [@role]",
          description: "Add a role to the whitelist (bypasses anti-nuke)",
          example: "!whiterole @Admin",
        },
        {
          name: "!unwhiterole [@role]",
          description: "Remove a role from the whitelist",
          example: "!unwhiterole @Admin",
        },
        {
          name: "!protect [@user]",
          description: "Add a user to the protected list",
          example: "!protect @username",
        },
        {
          name: "!unprotect [@user]",
          description: "Remove a user from the protected list",
          example: "!unprotect @username",
        },
      ],
    },
    {
      category: "Trust Level System",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 20h5v-2a3 3 0 00-5.356-1.857M17 20H7m10 0v-2c0-.656-.126-1.283-.356-1.857M7 20H2v-2a3 3 0 015.356-1.857M7 20v-2c0-.656.126-1.283.356-1.857m0 0a5.002 5.002 0 019.288 0M15 7a3 3 0 11-6 0 3 3 0 016 0zm6 3a2 2 0 11-4 0 2 2 0 014 0zM7 10a2 2 0 11-4 0 2 2 0 014 0z" />
        </svg>
      ),
      color: "blue",
      commands: [
        {
          name: "!antinuke trust",
          description: "Show trust level system info and hierarchy",
          example: "!antinuke trust",
        },
        {
          name: "!antinuke trust add [level] [@user]",
          description: "Add user to trust level (owner/admin/mod)",
          example: "!antinuke trust add admin @TrustedUser",
        },
        {
          name: "!antinuke trust remove [@user]",
          description: "Remove user from trust levels",
          example: "!antinuke trust remove @User",
        },
        {
          name: "!antinuke trust list",
          description: "Show all trusted users in the server",
          example: "!antinuke trust list",
        },
        {
          name: "!antinuke trust check [@user]",
          description: "Check a user's trust level and permissions",
          example: "!antinuke trust check @User",
        },
      ],
    },
    {
      category: "Recovery Commands",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
        </svg>
      ),
      color: "orange",
      commands: [
        {
          name: "!antinuke recover [@attacker]",
          description: "Undo ALL actions by an attacker (unbans, restores channels/roles, deletes webhooks)",
          example: "!antinuke recover @BadUser",
        },
        {
          name: "!antinuke scan [@user]",
          description: "Preview what actions a user has done without recovering",
          example: "!antinuke scan @SuspiciousUser",
        },
        {
          name: "!antinuke unbanall [@attacker]",
          description: "Unban all users that were banned by a specific attacker",
          example: "!antinuke unbanall @Attacker",
        },
        {
          name: "!antinuke nukerevert CONFIRM",
          description: "Full server restore from the last backup",
          example: "!antinuke nukerevert CONFIRM",
        },
      ],
    },
    {
      category: "Server Management",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
      color: "red",
      commands: [
        {
          name: "!wlserver [guild_id]",
          description: "Whitelist a server (bot owner only)",
          example: "!wlserver 123456789012345678",
        },
        {
          name: "!blserver [guild_id]",
          description: "Blacklist a server and make the bot leave",
          example: "!blserver 123456789012345678",
        },
        {
          name: "!rmblserver [guild_id]",
          description: "Remove a server from the blacklist",
          example: "!rmblserver 123456789012345678",
        },
      ],
    },
    {
      category: "Advanced Security",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
      color: "red",
      commands: [
        {
          name: "!security honeypot create channel",
          description: "Create a hidden trap channel that catches attackers",
          example: "!security honeypot create channel",
        },
        {
          name: "!security honeypot create role",
          description: "Create a hidden trap role that catches attackers",
          example: "!security honeypot create role",
        },
        {
          name: "!security honeypot list",
          description: "List all honeypot channels and roles",
          example: "!security honeypot list",
        },
        {
          name: "!security profile [@user]",
          description: "View a user's behavioral fingerprint and anomaly score",
          example: "!security profile @SuspiciousUser",
        },
        {
          name: "!security scan [@user]",
          description: "Scan a user for selfbot behavior and suspicious activity",
          example: "!security scan @User",
        },
      ],
    },
    {
      category: "Cross-Server Ban Sync",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
        </svg>
      ),
      color: "cyan",
      commands: [
        {
          name: "!bansync create",
          description: "Create a ban sync network for your servers",
          example: "!bansync create",
        },
        {
          name: "!bansync join [@owner]",
          description: "Join an existing ban sync network",
          example: "!bansync join @NetworkOwner",
        },
        {
          name: "!bansync list",
          description: "List all servers in your network",
          example: "!bansync list",
        },
        {
          name: "!bansync bans",
          description: "View the global ban list",
          example: "!bansync bans",
        },
        {
          name: "!bansync import",
          description: "Import current server bans to the global list",
          example: "!bansync import",
        },
      ],
    },
    {
      category: "VPN/Proxy Detection",
      icon: (
        <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3.055 11H5a2 2 0 012 2v1a2 2 0 002 2 2 2 0 012 2v2.945M8 3.935V5.5A2.5 2.5 0 0010.5 8h.5a2 2 0 012 2 2 2 0 104 0 2 2 0 012-2h1.064M15 20.488V18a2 2 0 012-2h3.064M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
      color: "green",
      commands: [
        {
          name: "!vpn enable/disable",
          description: "Toggle VPN/Proxy detection",
          example: "!vpn enable",
        },
        {
          name: "!vpn action [kick/ban/alert]",
          description: "Set action for VPN users",
          example: "!vpn action kick",
        },
        {
          name: "!vpn check [ip]",
          description: "Manually check an IP address",
          example: "!vpn check 1.2.3.4",
        },
        {
          name: "!vpn raidmode [on/off]",
          description: "Enable aggressive checking during raids",
          example: "!vpn raidmode on",
        },
        {
          name: "!vpn whitelist [@user]",
          description: "Whitelist a user from VPN checks",
          example: "!vpn whitelist @TrustedUser",
        },
      ],
    },
  ];

  const getColorClasses = (color: string) => {
    const colors: Record<string, { bg: string; border: string; text: string }> = {
      green: { bg: "bg-green-900/20", border: "border-green-500/30", text: "text-green-400" },
      purple: { bg: "bg-purple-900/20", border: "border-purple-500/30", text: "text-purple-400" },
      cyan: { bg: "bg-cyan-900/20", border: "border-cyan-500/30", text: "text-cyan-400" },
      yellow: { bg: "bg-yellow-900/20", border: "border-yellow-500/30", text: "text-yellow-400" },
      orange: { bg: "bg-orange-900/20", border: "border-orange-500/30", text: "text-orange-400" },
      blue: { bg: "bg-blue-900/20", border: "border-blue-500/30", text: "text-blue-400" },
      red: { bg: "bg-red-900/20", border: "border-red-500/30", text: "text-red-400" },
    };
    return colors[color] || colors.purple;
  };

  return (
    <main className="min-h-screen">
      <Navigation />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <Link
              href="/dashboard"
              className="inline-flex items-center gap-2 text-gray-400 hover:text-white transition mb-4"
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
              </svg>
              Back to Dashboard
            </Link>
            <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
              <div className="flex items-center gap-4 mb-4">
                <div className="w-14 h-14 rounded-xl bg-red-900/30 border border-red-500/30 flex items-center justify-center">
                  <svg className="w-7 h-7 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <h1 className="font-orbitron font-bold text-3xl text-white">Anti-Nuke Configuration</h1>
                  <p className="text-gray-400">Configure your server's anti-nuke protection settings</p>
                </div>
              </div>

              {/* Quick Setup Guide */}
              <div className="bg-[#1a1a1b] rounded-xl p-4 border border-purple-500/20">
                <h3 className="text-purple-400 font-semibold mb-2 flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  Quick Setup
                </h3>
                <p className="text-gray-400 text-sm">
                  1. Add the bot to your server → 2. Run <code className="text-cyan-400 bg-[#0a0a0b] px-2 py-0.5 rounded">!antinuke on</code> →
                  3. Set logs with <code className="text-cyan-400 bg-[#0a0a0b] px-2 py-0.5 rounded">!setlogs #channel</code> →
                  4. Whitelist trusted roles with <code className="text-cyan-400 bg-[#0a0a0b] px-2 py-0.5 rounded">!whiterole @role</code>
                </p>
              </div>
            </div>
          </div>

          {/* Commands Grid */}
          <div className="space-y-6">
            {commands.map((category) => {
              const colors = getColorClasses(category.color);
              return (
                <div key={category.category} className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
                  <div className="flex items-center gap-3 mb-6">
                    <div className={`w-10 h-10 rounded-xl ${colors.bg} border ${colors.border} flex items-center justify-center ${colors.text}`}>
                      {category.icon}
                    </div>
                    <h2 className="font-orbitron font-bold text-xl text-white">{category.category}</h2>
                  </div>

                  <div className="grid gap-4">
                    {category.commands.map((cmd) => (
                      <div
                        key={cmd.name}
                        className="bg-[#1a1a1b] rounded-xl p-4 border border-purple-900/20 hover:border-purple-500/30 transition"
                      >
                        <div className="flex flex-col md:flex-row md:items-center gap-3 mb-2">
                          <code className={`text-lg font-mono font-bold ${colors.text}`}>
                            {cmd.name}
                          </code>
                        </div>
                        <p className="text-gray-400 text-sm mb-3">{cmd.description}</p>
                        <div className="flex items-center gap-2">
                          <span className="text-gray-500 text-xs">Example:</span>
                          <code className="text-cyan-400 bg-[#0a0a0b] px-3 py-1 rounded-lg text-sm">
                            {cmd.example}
                          </code>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              );
            })}
          </div>

          {/* Security Thresholds - ULTRA STRICT MODE */}
          <div className="mt-8 gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-xl bg-red-900/30 border border-red-500/30 flex items-center justify-center">
                <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
              </div>
              <div>
                <h2 className="font-orbitron font-bold text-xl text-white">Security Thresholds</h2>
                <p className="text-gray-500 text-sm">ULTRA STRICT MODE - Instant punishment</p>
              </div>
              <span className="ml-auto px-3 py-1 bg-red-900/30 border border-red-500/30 rounded-full text-red-400 text-xs font-bold animate-pulse">
                INSTANT
              </span>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {[
                { action: "Channel Delete", threshold: 1, color: "red", icon: "🗑️" },
                { action: "Channel Create", threshold: 1, color: "red", icon: "➕" },
                { action: "Channel Rename", threshold: 1, color: "red", icon: "✏️" },
                { action: "Webhook Create", threshold: 1, color: "red", icon: "🔗" },
                { action: "Role Delete", threshold: 1, color: "red", icon: "🎭" },
                { action: "Role Create", threshold: 1, color: "red", icon: "👤" },
                { action: "Mass Ban", threshold: 1, color: "red", icon: "🔨" },
                { action: "Mass Kick", threshold: 1, color: "red", icon: "👢" },
                { action: "Bot Add", threshold: 1, color: "red", icon: "🤖" },
                { action: "Emoji Delete", threshold: 1, color: "red", icon: "😀" },
                { action: "Sticker Delete", threshold: 1, color: "red", icon: "🎨" },
                { action: "Thread Delete", threshold: 1, color: "red", icon: "🧵" },
                { action: "Member Prune", threshold: 1, color: "red", icon: "🧹" },
                { action: "Invite Spam", threshold: 1, color: "red", icon: "📨" },
              ].map((item) => (
                <div
                  key={item.action}
                  className={`bg-[#1a1a1b] rounded-xl p-4 border ${
                    item.color === "red"
                      ? "border-red-500/30"
                      : item.color === "orange"
                      ? "border-orange-500/30"
                      : "border-yellow-500/30"
                  }`}
                >
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-2xl">{item.icon}</span>
                    <span
                      className={`text-2xl font-orbitron font-black ${
                        item.color === "red"
                          ? "text-red-500"
                          : item.color === "orange"
                          ? "text-orange-500"
                          : "text-yellow-500"
                      }`}
                    >
                      {item.threshold}
                    </span>
                  </div>
                  <p className="text-white font-medium text-sm">{item.action}</p>
                  <p className="text-gray-500 text-xs">
                    INSTANT - Triggers in 3 seconds
                  </p>
                </div>
              ))}
            </div>

            <div className="bg-[#1a1a1b] rounded-xl p-4 border border-green-500/20">
              <div className="flex items-center gap-2 text-green-400 mb-2">
                <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                <span className="font-semibold text-sm">Customize with Commands</span>
              </div>
              <p className="text-gray-400 text-sm">
                Use <code className="text-cyan-400 bg-[#0a0a0b] px-2 py-0.5 rounded">!antinuke threshold channel_delete 1</code> to adjust thresholds.
                Valid types: <code className="text-purple-400">ban</code>, <code className="text-purple-400">kick</code>,
                <code className="text-purple-400">channel_delete</code>, <code className="text-purple-400">channel_create</code>,
                <code className="text-purple-400">channel_rename</code>, <code className="text-purple-400">role</code>,
                <code className="text-purple-400">webhook</code>
              </p>
            </div>
          </div>

          {/* Protection Features */}
          <div className="mt-8 gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
            <h2 className="font-orbitron font-bold text-xl text-white mb-6">What Does Anti-Nuke Protect Against?</h2>

            {/* Core Protections */}
            <h3 className="text-purple-400 font-semibold mb-3 text-sm uppercase tracking-wider">Core Protections</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {[
                { icon: "🛡️", title: "Mass Ban Protection", desc: "Detects and prevents mass banning of members" },
                { icon: "👢", title: "Mass Kick Protection", desc: "Stops mass kicking attacks" },
                { icon: "🗑️", title: "Channel Deletion", desc: "Prevents channel deletion (1 action limit)" },
                { icon: "➕", title: "Channel Creation", desc: "Blocks mass channel creation (1 action limit)" },
                { icon: "✏️", title: "Channel Renaming", desc: "Stops mass rename attacks (1 action limit)" },
                { icon: "🎭", title: "Role Deletion", desc: "Protects roles from being deleted" },
                { icon: "🔗", title: "Webhook Spam", desc: "Blocks webhook creation (1 action limit)" },
                { icon: "🤖", title: "Bot Addition", desc: "Monitors unauthorized bot additions" },
                { icon: "⚡", title: "Permission Changes", desc: "Detects dangerous permission modifications" },
              ].map((feature) => (
                <div key={feature.title} className="bg-[#1a1a1b] rounded-xl p-4 border border-purple-900/20">
                  <div className="text-2xl mb-2">{feature.icon}</div>
                  <h3 className="text-white font-semibold mb-1">{feature.title}</h3>
                  <p className="text-gray-500 text-sm">{feature.desc}</p>
                </div>
              ))}
            </div>

            {/* Advanced Protections */}
            <h3 className="text-orange-400 font-semibold mb-3 text-sm uppercase tracking-wider">Advanced Protections</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-6">
              {[
                { icon: "😀", title: "Emoji Deletion", desc: "Detects mass emoji deletion attacks" },
                { icon: "🎨", title: "Sticker Deletion", desc: "Protects stickers from being deleted" },
                { icon: "🧵", title: "Thread Nuking", desc: "Detects mass thread deletion" },
                { icon: "🏠", title: "Server Edit", desc: "Monitors server name/icon/banner changes" },
                { icon: "🔒", title: "Vanity Steal", desc: "Detects vanity URL changes" },
                { icon: "✓", title: "Verification Change", desc: "Alerts on verification level changes" },
                { icon: "🧹", title: "Member Prune", desc: "Detects unauthorized member pruning" },
                { icon: "📨", title: "Invite Spam", desc: "Blocks mass invite creation" },
                { icon: "🎯", title: "Pattern Detection", desc: "Detects multi-vector coordinated attacks" },
              ].map((feature) => (
                <div key={feature.title} className="bg-[#1a1a1b] rounded-xl p-4 border border-orange-900/20">
                  <div className="text-2xl mb-2">{feature.icon}</div>
                  <h3 className="text-white font-semibold mb-1">{feature.title}</h3>
                  <p className="text-gray-500 text-sm">{feature.desc}</p>
                </div>
              ))}
            </div>

            {/* Military-Grade Security Features */}
            <h3 className="text-red-400 font-semibold mb-3 text-sm uppercase tracking-wider">Military-Grade Security</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {[
                { icon: "👑", title: "Role Hierarchy Protection", desc: "Prevents role manipulation above the bot" },
                { icon: "📊", title: "API Abuse Detection", desc: "Monitors abnormal API usage patterns" },
                { icon: "🔍", title: "Behavioral Fingerprinting", desc: "Tracks user behavior patterns for anomalies" },
                { icon: "⏱️", title: "Message Timing Analysis", desc: "Detects selfbots via inhuman response times" },
                { icon: "🔑", title: "Token Compromise Detection", desc: "Identifies potentially hijacked accounts" },
                { icon: "🍯", title: "Honeypot Traps", desc: "Hidden channels/roles that catch attackers instantly" },
                { icon: "🔗", title: "Cross-Server Ban Sync", desc: "Share bans across all your servers automatically" },
                { icon: "🌐", title: "VPN/Proxy Detection", desc: "Block users joining from VPNs, proxies, and datacenters" },
              ].map((feature) => (
                <div key={feature.title} className="bg-[#1a1a1b] rounded-xl p-4 border border-red-900/20">
                  <div className="text-2xl mb-2">{feature.icon}</div>
                  <h3 className="text-white font-semibold mb-1">{feature.title}</h3>
                  <p className="text-gray-500 text-sm">{feature.desc}</p>
                </div>
              ))}
            </div>
          </div>

          {/* CTA */}
          <div className="mt-8 text-center">
            <a
              href="https://discord.com/api/oauth2/authorize?client_id=1338739893035204628&permissions=8&scope=bot%20applications.commands"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-3 bg-purple-600 hover:bg-purple-500 text-white px-8 py-4 rounded-xl transition font-semibold"
            >
              <svg className="w-6 h-6" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286z" />
              </svg>
              Add Bot to Your Server
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
