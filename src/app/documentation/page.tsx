import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import Link from "next/link";

const categories = [
  {
    title: "Getting Started",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
      </svg>
    ),
    description: "Learn how to set up Offcialx on your Discord server in just a few minutes.",
    articles: [
      { title: "Quick Start Guide", href: "#quick-start" },
      { title: "Bot Permissions", href: "#permissions" },
      { title: "Initial Configuration", href: "#config" },
    ],
  },
  {
    title: "Security Features",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
      </svg>
    ),
    description: "Configure anti-raid, anti-nuke, and other protection features.",
    articles: [
      { title: "Anti-Raid Protection", href: "#anti-raid" },
      { title: "Anti-Nuke System", href: "#anti-nuke" },
      { title: "Auto-Moderation", href: "#automod" },
    ],
  },
  {
    title: "Commands",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 9l3 3-3 3m5 0h3M5 20h14a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
      </svg>
    ),
    description: "Complete list of all available commands and their usage.",
    articles: [
      { title: "Moderation Commands", href: "#mod-commands" },
      { title: "Security Commands", href: "#security-commands" },
      { title: "Utility Commands", href: "#utility-commands" },
    ],
  },
  {
    title: "Dashboard",
    icon: (
      <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
      </svg>
    ),
    description: "Navigate and customize your bot through the web dashboard.",
    articles: [
      { title: "Dashboard Overview", href: "#dashboard-overview" },
      { title: "Server Settings", href: "#server-settings" },
      { title: "Logs & Analytics", href: "#logs" },
    ],
  },
];

const commands = [
  { name: "/setup", description: "Initialize Offcialx on your server", category: "Admin" },
  { name: "/antinuke enable", description: "Enable anti-nuke protection", category: "Security" },
  { name: "/antiraid enable", description: "Enable anti-raid protection", category: "Security" },
  { name: "/automod config", description: "Configure auto-moderation settings", category: "Moderation" },
  { name: "/ban", description: "Ban a user from the server", category: "Moderation" },
  { name: "/kick", description: "Kick a user from the server", category: "Moderation" },
  { name: "/mute", description: "Mute a user temporarily", category: "Moderation" },
  { name: "/warn", description: "Issue a warning to a user", category: "Moderation" },
  { name: "/logs set", description: "Set the logging channel", category: "Admin" },
  { name: "/welcome setup", description: "Configure welcome messages", category: "Utility" },
];

export default function DocumentationPage() {
  return (
    <main className="min-h-screen">
      <Navigation />

      {/* Hero */}
      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto text-center">
          <span className="inline-flex items-center gap-2 bg-purple-900/30 px-4 py-2 rounded-full border border-purple-500/30 text-purple-400 text-sm mb-6">
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
            </svg>
            Documentation
          </span>
          <h1 className="font-orbitron font-bold text-4xl md:text-6xl text-white mb-6">
            Learn How to Use <span className="text-purple-500">Offcialx</span>
          </h1>
          <p className="text-gray-400 text-lg max-w-2xl mx-auto">
            Everything you need to know about setting up, configuring, and managing Offcialx on your Discord server.
          </p>
        </div>
      </section>

      {/* Categories */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="grid md:grid-cols-2 gap-6">
            {categories.map((category, index) => (
              <div
                key={index}
                className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] hover:bg-[#0f0f10] transition-colors"
              >
                <div className="flex items-center gap-3 mb-4">
                  <div className="w-12 h-12 rounded-xl bg-purple-900/30 border border-purple-500/30 flex items-center justify-center text-purple-400">
                    {category.icon}
                  </div>
                  <h3 className="font-orbitron font-bold text-xl text-white">{category.title}</h3>
                </div>
                <p className="text-gray-400 text-sm mb-4">{category.description}</p>
                <ul className="space-y-2">
                  {category.articles.map((article, idx) => (
                    <li key={idx}>
                      <Link
                        href={article.href}
                        className="flex items-center gap-2 text-purple-400 hover:text-purple-300 transition text-sm"
                      >
                        <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                        </svg>
                        {article.title}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Commands Reference */}
      <section className="py-16 px-4">
        <div className="max-w-5xl mx-auto">
          <div className="text-center mb-12">
            <h2 className="font-orbitron font-bold text-3xl text-white mb-4">
              Command <span className="text-purple-500">Reference</span>
            </h2>
            <p className="text-gray-400">Quick reference for commonly used commands</p>
          </div>

          <div className="gradient-border rounded-2xl overflow-hidden">
            <table className="w-full">
              <thead className="bg-purple-900/20">
                <tr>
                  <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Command</th>
                  <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm hidden md:table-cell">Description</th>
                  <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Category</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-purple-900/20">
                {commands.map((cmd, index) => (
                  <tr key={index} className="hover:bg-purple-900/10 transition-colors">
                    <td className="px-6 py-4">
                      <code className="text-cyan-400 bg-[#1a1a1b] px-2 py-1 rounded text-sm">{cmd.name}</code>
                    </td>
                    <td className="px-6 py-4 text-gray-400 text-sm hidden md:table-cell">{cmd.description}</td>
                    <td className="px-6 py-4">
                      <span className="text-xs bg-purple-900/30 text-purple-400 px-2 py-1 rounded-full border border-purple-500/30">
                        {cmd.category}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </section>

      {/* Need Help */}
      <section className="py-16 px-4">
        <div className="max-w-3xl mx-auto text-center">
          <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b]">
            <h3 className="font-orbitron font-bold text-2xl text-white mb-4">Need More Help?</h3>
            <p className="text-gray-400 mb-6">
              Join our Discord server for personalized support from our team and community.
            </p>
            <a
              href="https://discord.gg/NXK5sFEJSy"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white px-6 py-3 rounded-xl transition font-semibold"
            >
              <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286zM8.02 15.3312c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9555-2.4189 2.157-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.9555 2.4189-2.1569 2.4189zm7.9748 0c-1.1825 0-2.1569-1.0857-2.1569-2.419 0-1.3332.9554-2.4189 2.1569-2.4189 1.2108 0 2.1757 1.0952 2.1568 2.419 0 1.3332-.946 2.4189-2.1568 2.4189Z" />
              </svg>
              Join Discord Server
            </a>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
