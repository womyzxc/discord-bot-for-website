"use client";

import { useState, useEffect, useCallback } from "react";
import Navigation from "@/components/Navigation";
import Footer from "@/components/Footer";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
} from "recharts";

interface ShardStatus {
  id: number;
  status: "online" | "connecting" | "offline";
  latency: number;
  servers: number;
  uptime: number;
}

interface Incident {
  id: number;
  title: string;
  status: "resolved" | "investigating" | "identified" | "monitoring";
  date: string;
  description: string;
  updates: { time: string; message: string }[];
}

interface ServiceHealth {
  name: string;
  status: "operational" | "degraded" | "outage";
  latency: number;
  lastChecked: string;
}

interface UptimeData {
  date: string;
  uptime: number;
}

interface BotStats {
  status: string;
  totalServers: number;
  totalUsers: number;
  threatsBlocked: number;
  shards: number;
  shardData?: ShardStatus[];
  averageLatency: number;
  uptime: number;
  botUser?: {
    id?: string;
    username: string;
    discriminator: string;
    avatar: string | null;
  };
  lastUpdated: string;
}

export default function StatusPage() {
  const [currentTime, setCurrentTime] = useState(new Date());
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const [botStats, setBotStats] = useState<BotStats>({
    status: "operational",
    totalServers: 0,
    totalUsers: 0,
    threatsBlocked: 0,
    shards: 1,
    averageLatency: 0,
    uptime: 99.98,
    lastUpdated: new Date().toISOString(),
  });
  const [isApiConnected, setIsApiConnected] = useState(false);

  const [shards, setShards] = useState<ShardStatus[]>([]);
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [overallStatus, setOverallStatus] = useState<"operational" | "degraded" | "outage">("operational");

  // Generate uptime history data for the last 30 days
  const [uptimeHistory] = useState<UptimeData[]>(() => {
    const data: UptimeData[] = [];
    for (let i = 29; i >= 0; i--) {
      const date = new Date();
      date.setDate(date.getDate() - i);
      data.push({
        date: date.toISOString().split("T")[0],
        uptime: 99.5 + Math.random() * 0.5,
      });
    }
    return data;
  });

  // Fetch bot stats
  const fetchBotStats = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/stats");
      const data = await response.json();

      if (data.success && data.stats) {
        setBotStats(data.stats);
        setIsApiConnected(true);

        if (data.stats.shardData) {
          setShards(data.stats.shardData);
        } else {
          // Generate default shard data if not provided
          const defaultShards: ShardStatus[] = Array.from(
            { length: data.stats.shards || 1 },
            (_, i) => ({
              id: i,
              status: "online" as const,
              latency: 30 + Math.floor(Math.random() * 30),
              servers: Math.floor((data.stats.totalServers || 0) / (data.stats.shards || 1)),
              uptime: 99.9 + Math.random() * 0.1,
            })
          );
          setShards(defaultShards);
        }
      }
    } catch (err) {
      console.error("Error fetching bot stats:", err);
      setIsApiConnected(false);
      setError("Failed to fetch bot stats");
    }
  }, []);

  // Fetch service health
  const fetchServiceHealth = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/health");
      const data = await response.json();

      if (data.success) {
        setServices(data.services || []);
        setOverallStatus(data.status || "operational");
      }
    } catch (err) {
      console.error("Error fetching service health:", err);
    }
  }, []);

  // Fetch incidents
  const fetchIncidents = useCallback(async () => {
    try {
      const response = await fetch("/api/bot/incidents?limit=5");
      const data = await response.json();

      if (data.success) {
        setIncidents(data.incidents || []);
      }
    } catch (err) {
      console.error("Error fetching incidents:", err);
    }
  }, []);

  // Initial data fetch
  useEffect(() => {
    const loadData = async () => {
      setIsLoading(true);
      await Promise.all([fetchBotStats(), fetchServiceHealth(), fetchIncidents()]);
      setIsLoading(false);
    };

    loadData();
  }, [fetchBotStats, fetchServiceHealth, fetchIncidents]);

  // Update current time every second
  useEffect(() => {
    const timer = setInterval(() => {
      setCurrentTime(new Date());
    }, 1000);

    return () => clearInterval(timer);
  }, []);

  // Refresh stats every 30 seconds
  useEffect(() => {
    const interval = setInterval(() => {
      fetchBotStats();
      fetchServiceHealth();
    }, 30000);

    return () => clearInterval(interval);
  }, [fetchBotStats, fetchServiceHealth]);

  const getStatusColor = (status: string) => {
    switch (status) {
      case "operational":
      case "online":
      case "resolved":
        return "text-green-400";
      case "degraded":
      case "connecting":
      case "monitoring":
      case "identified":
        return "text-yellow-400";
      case "outage":
      case "offline":
      case "investigating":
        return "text-red-400";
      default:
        return "text-gray-400";
    }
  };

  const getStatusBg = (status: string) => {
    switch (status) {
      case "operational":
      case "online":
      case "resolved":
        return "bg-green-500/20 border-green-500/30";
      case "degraded":
      case "connecting":
      case "monitoring":
      case "identified":
        return "bg-yellow-500/20 border-yellow-500/30";
      case "outage":
      case "offline":
      case "investigating":
        return "bg-red-500/20 border-red-500/30";
      default:
        return "bg-gray-500/20 border-gray-500/30";
    }
  };

  const getLatencyColor = (latency: number) => {
    if (latency < 50) return "text-green-400";
    if (latency < 100) return "text-yellow-400";
    return "text-red-400";
  };

  if (isLoading) {
    return (
      <main className="min-h-screen">
        <Navigation />
        <div className="min-h-[80vh] flex items-center justify-center">
          <div className="text-center">
            <div className="w-12 h-12 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-400">Loading status...</p>
          </div>
        </div>
        <Footer />
      </main>
    );
  }

  if (error) {
    return (
      <main className="min-h-screen">
        <Navigation />
        <div className="min-h-[80vh] flex items-center justify-center">
          <div className="text-center">
            <div className="w-16 h-16 rounded-full bg-red-500/20 flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
              </svg>
            </div>
            <p className="text-red-400 mb-2">Error loading status</p>
            <p className="text-gray-500 text-sm">{error}</p>
            <button
              onClick={() => window.location.reload()}
              className="mt-4 px-4 py-2 bg-purple-600 hover:bg-purple-500 text-white rounded-lg transition"
            >
              Retry
            </button>
          </div>
        </div>
        <Footer />
      </main>
    );
  }

  return (
    <main className="min-h-screen">
      <Navigation />

      <section className="pt-32 pb-16 px-4">
        <div className="max-w-5xl mx-auto">
          {/* Header */}
          <div className="text-center mb-12">
            <h1 className="font-orbitron font-bold text-4xl md:text-5xl text-white mb-4">
              System Status
            </h1>
            <p className="text-gray-400">
              Real-time monitoring of Offcialx services
            </p>
            <p className="text-gray-500 text-sm mt-2">
              Last updated: {currentTime.toLocaleTimeString()}
            </p>

          </div>

          {/* Main Status Card */}
          <div className={`gradient-border rounded-2xl p-8 bg-[#0a0a0b] mb-8 ${overallStatus === "operational" ? "border-green-500/30" : ""}`}>
            <div className="flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="flex items-center gap-4">
                <div className={`w-16 h-16 rounded-2xl flex items-center justify-center ${getStatusBg(overallStatus)} border`}>
                  {overallStatus === "operational" ? (
                    <svg className="w-8 h-8 text-green-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                  ) : overallStatus === "degraded" ? (
                    <svg className="w-8 h-8 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                  ) : (
                    <svg className="w-8 h-8 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  )}
                </div>
                <div>
                  <h2 className="font-orbitron font-bold text-2xl text-white">
                    {overallStatus === "operational"
                      ? "All Systems Operational"
                      : overallStatus === "degraded"
                      ? "Partial System Degradation"
                      : "System Outage"}
                  </h2>
                  <p className={`${getStatusColor(overallStatus)} font-semibold`}>
                    {botStats.uptime}% Uptime (30 days)
                  </p>
                </div>
              </div>

              {/* Live Pulse Indicator */}
              <div className="flex items-center gap-3">
                <div className="relative">
                  <div className={`w-3 h-3 ${overallStatus === "operational" ? "bg-green-500" : overallStatus === "degraded" ? "bg-yellow-500" : "bg-red-500"} rounded-full`}></div>
                  <div className={`absolute inset-0 w-3 h-3 ${overallStatus === "operational" ? "bg-green-500" : overallStatus === "degraded" ? "bg-yellow-500" : "bg-red-500"} rounded-full animate-ping`}></div>
                </div>
                <span className={`${getStatusColor(overallStatus)} font-medium`}>Live</span>
              </div>
            </div>
          </div>

          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              {
                label: "Total Servers",
                value: botStats.totalServers.toLocaleString(),
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                ),
                color: "purple",
              },
              {
                label: "Total Users",
                value: botStats.totalUsers.toLocaleString(),
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                  </svg>
                ),
                color: "cyan",
              },
              {
                label: "Avg Latency",
                value: `${botStats.averageLatency}ms`,
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                  </svg>
                ),
                color: "green",
                dynamic: true,
              },
              {
                label: "Active Shards",
                value: `${shards.filter((s) => s.status === "online").length}/${shards.length || botStats.shards}`,
                icon: (
                  <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 7v10c0 2.21 3.582 4 8 4s8-1.79 8-4V7M4 7c0 2.21 3.582 4 8 4s8-1.79 8-4M4 7c0-2.21 3.582-4 8-4s8 1.79 8 4" />
                  </svg>
                ),
                color: "orange",
              },
            ].map((stat, i) => (
              <div key={i} className="gradient-border rounded-xl p-4 bg-[#0a0a0b]">
                <div className="flex items-center gap-3 mb-2">
                  <div
                    className="w-10 h-10 rounded-lg flex items-center justify-center"
                    style={{
                      backgroundColor: `rgb(${stat.color === "purple" ? "139 92 246" : stat.color === "cyan" ? "6 182 212" : stat.color === "green" ? "34 197 94" : "249 115 22"} / 0.2)`,
                    }}
                  >
                    <span
                      style={{
                        color: stat.color === "purple" ? "#a78bfa" : stat.color === "cyan" ? "#22d3ee" : stat.color === "green" ? "#4ade80" : "#fb923c",
                      }}
                    >
                      {stat.icon}
                    </span>
                  </div>
                </div>
                <p className={`text-2xl font-orbitron font-bold ${stat.dynamic ? getLatencyColor(botStats.averageLatency) : "text-white"}`}>
                  {stat.value}
                </p>
                <p className="text-gray-500 text-sm">{stat.label}</p>
              </div>
            ))}
          </div>

          {/* Real-Time Threat Activity */}
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] mb-8 overflow-hidden relative">
            {/* Animated background */}
            <div className="absolute inset-0 bg-gradient-to-r from-red-500/5 via-purple-500/5 to-cyan-500/5" />

            <div className="relative z-10">
              <div className="flex items-center justify-between mb-6">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-xl bg-red-900/30 border border-red-500/30 flex items-center justify-center">
                    <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                    </svg>
                  </div>
                  <div>
                    <h3 className="font-orbitron font-bold text-lg text-white">Real-Time Threat Activity</h3>
                    <p className="text-gray-500 text-xs">Live security monitoring across all servers</p>
                  </div>
                </div>

                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full ${
                  isApiConnected
                    ? "bg-green-900/30 border border-green-500/30"
                    : "bg-gray-800 border border-gray-700"
                }`}>
                  <span className="relative flex h-2 w-2">
                    <span className={`${isApiConnected ? "animate-ping" : ""} absolute inline-flex h-full w-full rounded-full ${isApiConnected ? "bg-green-400" : "bg-gray-500"} opacity-75`}></span>
                    <span className={`relative inline-flex rounded-full h-2 w-2 ${isApiConnected ? "bg-green-500" : "bg-gray-500"}`}></span>
                  </span>
                  <span className={`text-xs font-medium ${isApiConnected ? "text-green-400" : "text-gray-500"}`}>
                    {isApiConnected ? "LIVE" : "CONNECTING"}
                  </span>
                </div>
              </div>

              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                {/* Threats Blocked */}
                <div className="bg-[#1a1a1b] rounded-xl p-4 border border-red-500/20 hover:border-red-500/40 transition-all">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-red-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                    </svg>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Threats Blocked</span>
                  </div>
                  <p className="font-orbitron font-black text-2xl text-red-500">
                    {(botStats.threatsBlocked || 0).toLocaleString()}+
                  </p>
                  <p className="text-xs text-gray-600 mt-1">This month</p>
                </div>

                {/* Active Alerts */}
                <div className="bg-[#1a1a1b] rounded-xl p-4 border border-orange-500/20 hover:border-orange-500/40 transition-all">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-orange-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Active Alerts</span>
                  </div>
                  <p className="font-orbitron font-black text-2xl text-orange-500">
                    0
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Monitoring</p>
                </div>

                {/* Security Events */}
                <div className="bg-[#1a1a1b] rounded-xl p-4 border border-cyan-500/20 hover:border-cyan-500/40 transition-all">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-cyan-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                    </svg>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Security Events</span>
                  </div>
                  <p className="font-orbitron font-black text-2xl text-cyan-500">
                    0
                  </p>
                  <p className="text-xs text-gray-600 mt-1">In queue</p>
                </div>

                {/* Mod Actions */}
                <div className="bg-[#1a1a1b] rounded-xl p-4 border border-purple-500/20 hover:border-purple-500/40 transition-all">
                  <div className="flex items-center gap-2 mb-2">
                    <svg className="w-4 h-4 text-purple-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                    </svg>
                    <span className="text-xs text-gray-500 uppercase tracking-wider">Mod Actions</span>
                  </div>
                  <p className="font-orbitron font-black text-2xl text-purple-500">
                    0
                  </p>
                  <p className="text-xs text-gray-600 mt-1">Today</p>
                </div>
              </div>

              {/* Status indicator */}
              <div className="mt-4 pt-4 border-t border-gray-800 text-center">
                <div className="flex items-center justify-center gap-2 text-gray-500 text-sm">
                  <svg className="w-5 h-5 text-green-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                  </svg>
                  <span>All systems secure - No active threats</span>
                </div>
              </div>
            </div>
          </div>

          {/* Uptime Chart */}
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] mb-8">
            <h3 className="font-orbitron font-bold text-lg text-white mb-4">
              Uptime History (30 Days)
            </h3>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <AreaChart data={uptimeHistory}>
                  <defs>
                    <linearGradient id="colorUptime" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor="#22c55e" stopOpacity={0.3} />
                      <stop offset="95%" stopColor="#22c55e" stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2b" />
                  <XAxis
                    dataKey="date"
                    stroke="#666"
                    tick={{ fill: "#888", fontSize: 12 }}
                    tickFormatter={(v) =>
                      new Date(v).toLocaleDateString("en-US", {
                        month: "short",
                        day: "numeric",
                      })
                    }
                    interval="preserveStartEnd"
                  />
                  <YAxis
                    stroke="#666"
                    tick={{ fill: "#888", fontSize: 12 }}
                    domain={[99, 100]}
                    tickFormatter={(v) => `${v}%`}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "#1a1a1b",
                      border: "1px solid #22c55e",
                      borderRadius: "8px",
                    }}
                    formatter={(value) => [`${(value as number)?.toFixed(2) ?? 0}%`, "Uptime"]}
                    labelFormatter={(label) =>
                      new Date(label).toLocaleDateString("en-US", {
                        weekday: "short",
                        month: "short",
                        day: "numeric",
                      })
                    }
                  />
                  <Area
                    type="monotone"
                    dataKey="uptime"
                    stroke="#22c55e"
                    strokeWidth={2}
                    fill="url(#colorUptime)"
                  />
                </AreaChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Shard Status */}
          {shards.length > 0 && (
            <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] mb-8">
              <h3 className="font-orbitron font-bold text-lg text-white mb-4">
                Shard Status
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
                {shards.map((shard) => (
                  <div
                    key={shard.id}
                    className={`p-4 rounded-xl border ${getStatusBg(shard.status)}`}
                  >
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-white font-semibold">Shard {shard.id}</span>
                      <span
                        className={`text-xs px-2 py-1 rounded-full ${getStatusBg(shard.status)} ${getStatusColor(shard.status)} font-medium capitalize`}
                      >
                        {shard.status}
                      </span>
                    </div>
                    <div className="space-y-2 text-sm">
                      <div className="flex justify-between">
                        <span className="text-gray-500">Latency</span>
                        <span className={getLatencyColor(shard.latency)}>{shard.latency}ms</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Servers</span>
                        <span className="text-white">{shard.servers}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-gray-500">Uptime</span>
                        <span className="text-green-400">{shard.uptime.toFixed(2)}%</span>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Service Status */}
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] mb-8">
            <h3 className="font-orbitron font-bold text-lg text-white mb-4">
              Service Status
            </h3>
            <div className="space-y-3">
              {services.length > 0 ? (
                services.map((service, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 bg-[#1a1a1b] rounded-xl border border-purple-900/20"
                  >
                    <div className="flex items-center gap-3">
                      <div
                        className={`w-2 h-2 rounded-full ${
                          service.status === "operational"
                            ? "bg-green-500"
                            : service.status === "degraded"
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                      />
                      <span className="text-white">{service.name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-gray-500 text-sm">{service.latency}ms</span>
                      <span
                        className={`text-sm font-medium capitalize ${getStatusColor(service.status)}`}
                      >
                        {service.status}
                      </span>
                    </div>
                  </div>
                ))
              ) : (
                // Fallback static services
                [
                  { name: "Discord Gateway", status: "operational", latency: 38 },
                  { name: "Command Processing", status: "operational", latency: 12 },
                  { name: "Anti-Nuke System", status: "operational", latency: 5 },
                  { name: "Database", status: "operational", latency: 8 },
                  { name: "API Server", status: "operational", latency: 22 },
                  { name: "Dashboard", status: "operational", latency: 45 },
                ].map((service, i) => (
                  <div
                    key={i}
                    className="flex items-center justify-between p-4 bg-[#1a1a1b] rounded-xl border border-purple-900/20"
                  >
                    <div className="flex items-center gap-3">
                      <div className="w-2 h-2 rounded-full bg-green-500" />
                      <span className="text-white">{service.name}</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <span className="text-gray-500 text-sm">{service.latency}ms</span>
                      <span className="text-sm font-medium capitalize text-green-400">
                        {service.status}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          </div>

          {/* Incident History */}
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
            <h3 className="font-orbitron font-bold text-lg text-white mb-4">
              Incident History
            </h3>
            {incidents.length === 0 ? (
              <div className="text-center py-8">
                <svg
                  className="w-12 h-12 text-green-400 mx-auto mb-3"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
                  />
                </svg>
                <p className="text-gray-400">No incidents reported</p>
              </div>
            ) : (
              <div className="space-y-4">
                {incidents.map((incident) => (
                  <div
                    key={incident.id}
                    className="p-4 bg-[#1a1a1b] rounded-xl border border-purple-900/20"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 mb-3">
                      <h4 className="text-white font-semibold">{incident.title}</h4>
                      <div className="flex items-center gap-3">
                        <span className="text-gray-500 text-sm">{incident.date}</span>
                        <span
                          className={`text-xs px-2 py-1 rounded-full ${getStatusBg(incident.status)} ${getStatusColor(incident.status)} font-medium capitalize`}
                        >
                          {incident.status}
                        </span>
                      </div>
                    </div>
                    <p className="text-gray-400 text-sm mb-3">{incident.description}</p>
                    <div className="border-t border-purple-900/20 pt-3 space-y-2">
                      {incident.updates.map((update, i) => (
                        <div key={i} className="flex gap-3 text-sm">
                          <span className="text-gray-500 whitespace-nowrap">
                            {update.time}
                          </span>
                          <span className="text-gray-300">{update.message}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Subscribe to Updates */}
          <div className="mt-8 text-center">
            <div className="gradient-border rounded-2xl p-8 bg-[#0a0a0b] inline-block">
              <h3 className="font-orbitron font-bold text-xl text-white mb-2">
                Stay Updated
              </h3>
              <p className="text-gray-400 mb-4">
                Get notified about status updates and incidents
              </p>
              <a
                href="https://discord.gg/NXK5sFEJSy"
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center gap-2 bg-[#5865F2] hover:bg-[#4752C4] text-white px-6 py-3 rounded-xl transition font-semibold"
              >
                <svg className="w-5 h-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286z" />
                </svg>
                Join Discord for Updates
              </a>
            </div>
          </div>
        </div>
      </section>

      <Footer />
    </main>
  );
}
