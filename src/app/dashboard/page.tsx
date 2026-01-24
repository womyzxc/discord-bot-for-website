import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import { SignOutButton } from "./SignOutButton";

export default async function DashboardPage() {
  const session = await auth();

  if (!session?.user) {
    redirect("/auth");
  }

  return (
    <main className="min-h-screen">
      <Navigation />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-4xl mx-auto">
          {/* Welcome Header */}
          <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b] mb-8">
            <div className="flex items-center gap-6">
              {session.user.image ? (
                <img
                  src={session.user.image}
                  alt={session.user.name || "User"}
                  className="w-20 h-20 rounded-full border-4 border-purple-500/30"
                />
              ) : (
                <div className="w-20 h-20 rounded-full bg-purple-900/30 border-4 border-purple-500/30 flex items-center justify-center">
                  <span className="text-purple-400 font-bold text-2xl">
                    {session.user.name?.[0] || session.user.email?.[0] || "?"}
                  </span>
                </div>
              )}
              <div>
                <h1 className="font-orbitron font-bold text-3xl text-white mb-2">
                  Welcome back, {session.user.name || "User"}!
                </h1>
                <p className="text-gray-400">{session.user.email}</p>
              </div>
            </div>
          </div>

          {/* Dashboard Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            {/* Server Protection Card */}
            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="w-12 h-12 rounded-xl bg-green-900/30 border border-green-500/30 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-lg text-white mb-2">Protected Servers</h3>
              <p className="text-3xl font-bold text-green-400 mb-1">0</p>
              <p className="text-gray-500 text-sm">Add the bot to start protecting</p>
            </div>

            {/* Threats Blocked Card */}
            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="w-12 h-12 rounded-xl bg-red-900/30 border border-red-500/30 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-lg text-white mb-2">Threats Blocked</h3>
              <p className="text-3xl font-bold text-red-400 mb-1">0</p>
              <p className="text-gray-500 text-sm">Total threats neutralized</p>
            </div>

            {/* Account Status Card */}
            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="w-12 h-12 rounded-xl bg-purple-900/30 border border-purple-500/30 flex items-center justify-center mb-4">
                <svg className="w-6 h-6 text-purple-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5.121 17.804A13.937 13.937 0 0112 16c2.5 0 4.847.655 6.879 1.804M15 10a3 3 0 11-6 0 3 3 0 016 0zm6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
              <h3 className="font-orbitron font-bold text-lg text-white mb-2">Account Status</h3>
              <p className="text-lg font-bold text-purple-400 mb-1">Free Plan</p>
              <p className="text-gray-500 text-sm">Upgrade for more features</p>
            </div>
          </div>

          {/* Quick Actions */}
          <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b] mb-8">
            <h2 className="font-orbitron font-bold text-xl text-white mb-6">Quick Actions</h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Anti-Nuke Configuration */}
              <a
                href="/dashboard/antinuke"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-red-900/20 hover:border-red-500/30"
              >
                <div className="w-12 h-12 rounded-xl bg-red-900/20 flex items-center justify-center">
                  <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold">Anti-Nuke Configuration</p>
                  <p className="text-gray-500 text-sm">Configure protection settings & commands</p>
                </div>
              </a>

              <a
                href="https://discord.com/api/oauth2/authorize?client_id=1338739893035204628&permissions=8&scope=bot%20applications.commands"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-purple-900/20"
              >
                <div className="w-12 h-12 rounded-xl bg-[#5865F2]/20 flex items-center justify-center">
                  <svg className="w-6 h-6 text-[#5865F2]" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286z" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold">Add Bot to Server</p>
                  <p className="text-gray-500 text-sm">Start protecting your Discord server</p>
                </div>
              </a>

              <a
                href="/documentation"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-purple-900/20"
              >
                <div className="w-12 h-12 rounded-xl bg-cyan-900/20 flex items-center justify-center">
                  <svg className="w-6 h-6 text-cyan-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold">View Documentation</p>
                  <p className="text-gray-500 text-sm">Learn how to use Offcialx</p>
                </div>
              </a>

              <a
                href="https://discord.gg/NXK5sFEJSy"
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-purple-900/20"
              >
                <div className="w-12 h-12 rounded-xl bg-green-900/20 flex items-center justify-center">
                  <svg className="w-6 h-6 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 8h2a2 2 0 012 2v6a2 2 0 01-2 2h-2v4l-4-4H9a1.994 1.994 0 01-1.414-.586m0 0L11 14h4a2 2 0 002-2V6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2v4l.586-.586z" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold">Join Support Server</p>
                  <p className="text-gray-500 text-sm">Get help from our community</p>
                </div>
              </a>

              <a
                href="/dashboard/threats"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-red-900/20 hover:border-red-500/30"
              >
                <div className="w-12 h-12 rounded-xl bg-red-900/20 flex items-center justify-center relative">
                  <svg className="w-6 h-6 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                  <span className="absolute -top-1 -right-1 w-3 h-3 bg-green-500 rounded-full animate-pulse" />
                </div>
                <div>
                  <p className="text-white font-semibold">Live Threat Monitor</p>
                  <p className="text-gray-500 text-sm">Real-time security events</p>
                </div>
              </a>

              <a
                href="/themes"
                className="flex items-center gap-4 p-4 bg-[#1a1a1b] hover:bg-[#252527] rounded-xl transition border border-purple-900/20"
              >
                <div className="w-12 h-12 rounded-xl bg-orange-900/20 flex items-center justify-center">
                  <svg className="w-6 h-6 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 21a4 4 0 01-4-4V5a2 2 0 012-2h4a2 2 0 012 2v12a4 4 0 01-4 4zm0 0h12a2 2 0 002-2v-4a2 2 0 00-2-2h-2.343M11 7.343l1.657-1.657a2 2 0 012.828 0l2.829 2.829a2 2 0 010 2.828l-8.486 8.485M7 17h.01" />
                  </svg>
                </div>
                <div>
                  <p className="text-white font-semibold">Customize Theme</p>
                  <p className="text-gray-500 text-sm">Personalize your dashboard</p>
                </div>
              </a>
            </div>
          </div>

          {/* Sign Out */}
          <div className="text-center">
            <SignOutButton />
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
