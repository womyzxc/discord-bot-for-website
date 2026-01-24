"use client";

import { useState, useEffect } from "react";
import { useSession } from "next-auth/react";
import { redirect } from "next/navigation";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import RealTimeThreatMonitor from "@/components/RealTimeThreatMonitor";
import { useWebSocket } from "@/hooks/useWebSocket";

export default function ThreatMonitorPage() {
  const { data: session, status } = useSession();
  const [selectedGuild, setSelectedGuild] = useState<string | undefined>();
  const { isConnected, threats, securityEvents, moderationEvents } = useWebSocket({
    guildId: selectedGuild,
  });

  useEffect(() => {
    if (status === "unauthenticated") {
      redirect("/auth");
    }
  }, [status]);

  if (status === "loading") {
    return (
      <main className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-t-2 border-b-2 border-purple-500" />
      </main>
    );
  }

  const totalThreats = threats.length;
  const criticalThreats = threats.filter((t) => t.threat_score >= 80).length;
  const recentEvents = securityEvents.length + moderationEvents.length;

  return (
    <main className="min-h-screen">
      <Navigation />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-7xl mx-auto">
          {/* Header */}
          <div className="mb-8">
            <div className="flex items-center gap-4 mb-4">
              <a
                href="/dashboard"
                className="text-gray-400 hover:text-white transition"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
                </svg>
              </a>
              <h1 className="font-orbitron font-bold text-3xl text-white">
                Live Threat Monitor
              </h1>
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                isConnected ? "bg-green-900/30 border border-green-500/30" : "bg-red-900/30 border border-red-500/30"
              }`}>
                <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
                <span className={`text-sm font-medium ${isConnected ? "text-green-400" : "text-red-400"}`}>
                  {isConnected ? "LIVE" : "DISCONNECTED"}
                </span>
              </div>
            </div>
            <p className="text-gray-400">
              Real-time security monitoring and threat detection for your Discord servers
            </p>
          </div>

          {/* Stats Cards */}
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Connection Status</span>
                <div className={`w-3 h-3 rounded-full ${isConnected ? "bg-green-500" : "bg-red-500"}`} />
              </div>
              <p className={`text-2xl font-bold ${isConnected ? "text-green-400" : "text-red-400"}`}>
                {isConnected ? "Online" : "Offline"}
              </p>
            </div>

            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Total Threats</span>
                <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-orange-400">{totalThreats}</p>
            </div>

            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Critical Threats</span>
                <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M20.618 5.984A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-red-400">{criticalThreats}</p>
            </div>

            <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
              <div className="flex items-center justify-between mb-2">
                <span className="text-gray-400 text-sm">Recent Events</span>
                <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
              <p className="text-2xl font-bold text-blue-400">{recentEvents}</p>
            </div>
          </div>

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Threat Monitor - Takes 2 columns */}
            <div className="lg:col-span-2">
              <RealTimeThreatMonitor
                guildId={selectedGuild}
                showConnection={false}
                maxEvents={20}
              />
            </div>

            {/* Sidebar */}
            <div className="space-y-6">
              {/* Threat Level Indicator */}
              <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
                <h3 className="font-orbitron font-bold text-lg text-white mb-4">Threat Level</h3>
                <div className="relative h-4 bg-gray-800 rounded-full overflow-hidden mb-4">
                  <div
                    className={`absolute inset-y-0 left-0 rounded-full transition-all duration-500 ${
                      criticalThreats > 5 ? "bg-red-500" :
                      totalThreats > 10 ? "bg-orange-500" :
                      totalThreats > 0 ? "bg-yellow-500" :
                      "bg-green-500"
                    }`}
                    style={{
                      width: `${Math.min(100, totalThreats * 5)}%`,
                    }}
                  />
                </div>
                <div className="flex justify-between text-sm">
                  <span className={`font-medium ${
                    criticalThreats > 5 ? "text-red-400" :
                    totalThreats > 10 ? "text-orange-400" :
                    totalThreats > 0 ? "text-yellow-400" :
                    "text-green-400"
                  }`}>
                    {criticalThreats > 5 ? "CRITICAL" :
                     totalThreats > 10 ? "HIGH" :
                     totalThreats > 0 ? "MODERATE" :
                     "LOW"}
                  </span>
                  <span className="text-gray-500">
                    {totalThreats} active threats
                  </span>
                </div>
              </div>

              {/* Quick Actions */}
              <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
                <h3 className="font-orbitron font-bold text-lg text-white mb-4">Quick Actions</h3>
                <div className="space-y-3">
                  <button className="w-full flex items-center gap-3 p-3 bg-red-900/20 hover:bg-red-900/30 border border-red-500/30 rounded-lg text-red-400 transition">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                    </svg>
                    Emergency Lockdown
                  </button>
                  <button className="w-full flex items-center gap-3 p-3 bg-yellow-900/20 hover:bg-yellow-900/30 border border-yellow-500/30 rounded-lg text-yellow-400 transition">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
                    </svg>
                    Enable Raid Mode
                  </button>
                  <button className="w-full flex items-center gap-3 p-3 bg-purple-900/20 hover:bg-purple-900/30 border border-purple-500/30 rounded-lg text-purple-400 transition">
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                    </svg>
                    Export Logs
                  </button>
                </div>
              </div>

              {/* Detection Stats */}
              <div className="gradient-border rounded-xl p-6 bg-[#0a0a0b]">
                <h3 className="font-orbitron font-bold text-lg text-white mb-4">Detection Types</h3>
                <div className="space-y-3">
                  {[
                    { type: "Nuke Attempts", count: threats.filter(t => t.threat_type.includes("nuke")).length, color: "text-red-400" },
                    { type: "Raid Activity", count: threats.filter(t => t.threat_type.includes("raid")).length, color: "text-orange-400" },
                    { type: "Spam Detected", count: threats.filter(t => t.threat_type.includes("spam")).length, color: "text-yellow-400" },
                    { type: "Phishing Links", count: threats.filter(t => t.threat_type.includes("phish")).length, color: "text-blue-400" },
                    { type: "Other", count: threats.filter(t => !["nuke", "raid", "spam", "phish"].some(k => t.threat_type.includes(k))).length, color: "text-gray-400" },
                  ].map((item, index) => (
                    <div key={index} className="flex items-center justify-between">
                      <span className="text-gray-400">{item.type}</span>
                      <span className={`font-bold ${item.color}`}>{item.count}</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Info Box */}
              <div className="bg-blue-900/20 border border-blue-500/30 rounded-xl p-4">
                <div className="flex items-start gap-3">
                  <svg className="w-5 h-5 text-blue-400 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                  <div>
                    <p className="text-blue-400 font-medium text-sm">WebSocket Connection</p>
                    <p className="text-blue-300/70 text-xs mt-1">
                      Events are streamed in real-time from the bot API. Make sure your bot is running and the API server is enabled.
                    </p>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
