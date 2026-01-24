"use client";

import { useState, useEffect } from "react";
import { useWebSocket, ThreatEvent, SecurityEvent, ModerationEvent } from "@/hooks/useWebSocket";

interface RealTimeThreatMonitorProps {
  guildId?: string;
  showConnection?: boolean;
  maxEvents?: number;
  compact?: boolean;
}

export default function RealTimeThreatMonitor({
  guildId,
  showConnection = true,
  maxEvents = 10,
  compact = false,
}: RealTimeThreatMonitorProps) {
  const {
    isConnected,
    threats,
    securityEvents,
    moderationEvents,
    clearEvents,
  } = useWebSocket({ guildId });

  const [activeTab, setActiveTab] = useState<"threats" | "security" | "moderation">("threats");
  const [isLive, setIsLive] = useState(true);

  // Combine all events for timeline view
  const allEvents = [
    ...threats.map((t) => ({ ...t, eventCategory: "threat" as const })),
    ...securityEvents.map((e) => ({ ...e, eventCategory: "security" as const })),
    ...moderationEvents.map((m) => ({ ...m, eventCategory: "moderation" as const })),
  ]
    .sort((a, b) => {
      const timeA = ("detected_at" in a ? a.detected_at : a.timestamp) || "";
      const timeB = ("detected_at" in b ? b.detected_at : b.timestamp) || "";
      return new Date(timeB).getTime() - new Date(timeA).getTime();
    })
    .slice(0, maxEvents);

  const getThreatColor = (score: number) => {
    if (score >= 80) return "text-red-500 bg-red-900/20 border-red-500/30";
    if (score >= 60) return "text-orange-500 bg-orange-900/20 border-orange-500/30";
    if (score >= 40) return "text-yellow-500 bg-yellow-900/20 border-yellow-500/30";
    return "text-green-500 bg-green-900/20 border-green-500/30";
  };

  const getEventIcon = (category: string, type?: string) => {
    if (category === "threat") {
      return (
        <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
        </svg>
      );
    }
    if (category === "security") {
      if (type?.includes("lockdown")) {
        return (
          <svg className="w-5 h-5 text-orange-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
          </svg>
        );
      }
      return (
        <svg className="w-5 h-5 text-yellow-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-blue-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
      </svg>
    );
  };

  const formatTime = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString("en-US", {
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
    });
  };

  const formatTimeDiff = (timestamp: string) => {
    const diff = Date.now() - new Date(timestamp).getTime();
    if (diff < 60000) return "Just now";
    if (diff < 3600000) return `${Math.floor(diff / 60000)}m ago`;
    if (diff < 86400000) return `${Math.floor(diff / 3600000)}h ago`;
    return `${Math.floor(diff / 86400000)}d ago`;
  };

  if (compact) {
    return (
      <div className="gradient-border rounded-xl p-4 bg-[#0a0a0b]">
        <div className="flex items-center justify-between mb-4">
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
            <span className="text-sm text-gray-400">
              {isConnected ? "Live" : "Disconnected"}
            </span>
          </div>
          <span className="text-xs text-gray-500">
            {allEvents.length} events
          </span>
        </div>

        {allEvents.length === 0 ? (
          <div className="text-center py-8 text-gray-500">
            <svg className="w-12 h-12 mx-auto mb-2 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
            <p className="text-sm">No recent events</p>
          </div>
        ) : (
          <div className="space-y-2">
            {allEvents.slice(0, 5).map((event, index) => (
              <div
                key={index}
                className="flex items-center gap-3 p-2 bg-[#1a1a1b] rounded-lg"
              >
                {getEventIcon(event.eventCategory, "event_type" in event ? event.event_type : undefined)}
                <div className="flex-1 min-w-0">
                  <p className="text-sm text-white truncate">
                    {"threat_type" in event ? event.threat_type : "action" in event ? event.action : event.event_type}
                  </p>
                  <p className="text-xs text-gray-500">
                    {formatTimeDiff("detected_at" in event ? event.detected_at : event.timestamp)}
                  </p>
                </div>
                {"threat_score" in event && (
                  <span className={`text-xs px-2 py-0.5 rounded-full ${getThreatColor(event.threat_score)}`}>
                    {event.threat_score}%
                  </span>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="gradient-border rounded-2xl bg-[#0a0a0b] overflow-hidden">
      {/* Header */}
      <div className="p-4 border-b border-gray-800">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-red-900/30 border border-red-500/30 flex items-center justify-center">
              <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
              </svg>
            </div>
            <div>
              <h3 className="font-orbitron font-bold text-lg text-white">Real-Time Threat Monitor</h3>
              <p className="text-sm text-gray-500">Live security events from your servers</p>
            </div>
          </div>

          {showConnection && (
            <div className="flex items-center gap-4">
              <button
                onClick={() => setIsLive(!isLive)}
                className={`px-3 py-1.5 rounded-lg text-sm font-medium transition ${
                  isLive
                    ? "bg-green-900/30 text-green-400 border border-green-500/30"
                    : "bg-gray-800 text-gray-400 border border-gray-700"
                }`}
              >
                {isLive ? "LIVE" : "PAUSED"}
              </button>
              <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${isConnected ? "bg-green-500 animate-pulse" : "bg-red-500"}`} />
                <span className="text-sm text-gray-400">
                  {isConnected ? "Connected" : "Disconnected"}
                </span>
              </div>
            </div>
          )}
        </div>

        {/* Tabs */}
        <div className="flex gap-1 mt-4 bg-[#1a1a1b] rounded-lg p-1">
          {[
            { id: "threats", label: "Threats", count: threats.length },
            { id: "security", label: "Security", count: securityEvents.length },
            { id: "moderation", label: "Moderation", count: moderationEvents.length },
          ].map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`flex-1 px-4 py-2 rounded-md text-sm font-medium transition flex items-center justify-center gap-2 ${
                activeTab === tab.id
                  ? "bg-purple-900/50 text-purple-400"
                  : "text-gray-400 hover:text-white hover:bg-gray-800"
              }`}
            >
              {tab.label}
              {tab.count > 0 && (
                <span className={`px-1.5 py-0.5 rounded-full text-xs ${
                  activeTab === tab.id ? "bg-purple-500/30" : "bg-gray-700"
                }`}>
                  {tab.count}
                </span>
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Event List */}
      <div className="p-4 max-h-96 overflow-y-auto">
        {activeTab === "threats" && (
          <div className="space-y-3">
            {threats.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
                </svg>
                <p className="text-lg font-medium">No threats detected</p>
                <p className="text-sm">Your servers are secure</p>
              </div>
            ) : (
              threats.slice(0, maxEvents).map((threat, index) => (
                <div
                  key={index}
                  className={`p-4 rounded-xl border ${getThreatColor(threat.threat_score)}`}
                >
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      <div className="w-10 h-10 rounded-full bg-red-900/50 flex items-center justify-center">
                        <svg className="w-5 h-5 text-red-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
                        </svg>
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          {threat.threat_type.replace(/_/g, " ").toUpperCase()}
                        </p>
                        <p className="text-sm text-gray-400">User ID: {threat.user_id}</p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-2xl font-bold">{threat.threat_score}%</p>
                      <p className="text-xs text-gray-500">{formatTime(threat.detected_at)}</p>
                    </div>
                  </div>
                  {threat.details && (
                    <p className="mt-3 text-sm text-gray-400 bg-black/30 p-2 rounded-lg">
                      {threat.details}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "security" && (
          <div className="space-y-3">
            {securityEvents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
                </svg>
                <p className="text-lg font-medium">No security events</p>
                <p className="text-sm">All systems operational</p>
              </div>
            ) : (
              securityEvents.slice(0, maxEvents).map((event, index) => (
                <div
                  key={index}
                  className="p-4 rounded-xl border border-yellow-500/30 bg-yellow-900/10"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      {getEventIcon("security", event.event_type)}
                      <div>
                        <p className="font-semibold text-white">
                          {event.event_type.replace(/_/g, " ").toUpperCase()}
                        </p>
                        {event.details && (
                          <p className="text-sm text-gray-400">{event.details}</p>
                        )}
                      </div>
                    </div>
                    <div className="text-right">
                      <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                        event.severity === "critical" ? "bg-red-900/50 text-red-400" :
                        event.severity === "high" ? "bg-orange-900/50 text-orange-400" :
                        event.severity === "medium" ? "bg-yellow-900/50 text-yellow-400" :
                        "bg-gray-800 text-gray-400"
                      }`}>
                        {event.severity?.toUpperCase()}
                      </span>
                      <p className="text-xs text-gray-500 mt-1">{formatTime(event.timestamp)}</p>
                    </div>
                  </div>
                </div>
              ))
            )}
          </div>
        )}

        {activeTab === "moderation" && (
          <div className="space-y-3">
            {moderationEvents.length === 0 ? (
              <div className="text-center py-12 text-gray-500">
                <svg className="w-16 h-16 mx-auto mb-4 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" />
                </svg>
                <p className="text-lg font-medium">No moderation actions</p>
                <p className="text-sm">Community is behaving</p>
              </div>
            ) : (
              moderationEvents.slice(0, maxEvents).map((event, index) => (
                <div
                  key={index}
                  className="p-4 rounded-xl border border-blue-500/30 bg-blue-900/10"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-3">
                      <div className={`w-10 h-10 rounded-full flex items-center justify-center ${
                        event.action === "ban" ? "bg-red-900/50" :
                        event.action === "kick" ? "bg-orange-900/50" :
                        event.action === "mute" ? "bg-yellow-900/50" :
                        "bg-blue-900/50"
                      }`}>
                        {getEventIcon("moderation")}
                      </div>
                      <div>
                        <p className="font-semibold text-white">
                          User {event.action.toUpperCase()}
                        </p>
                        <p className="text-sm text-gray-400">
                          Target: {event.user_id}
                        </p>
                      </div>
                    </div>
                    <div className="text-right">
                      <p className="text-xs text-gray-500">{formatTime(event.timestamp)}</p>
                    </div>
                  </div>
                  {event.reason && (
                    <p className="mt-2 text-sm text-gray-400">
                      Reason: {event.reason}
                    </p>
                  )}
                </div>
              ))
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-gray-800 flex items-center justify-between">
        <p className="text-xs text-gray-500">
          Showing latest {maxEvents} events
        </p>
        <button
          onClick={clearEvents}
          className="text-xs text-gray-400 hover:text-white transition"
        >
          Clear All
        </button>
      </div>
    </div>
  );
}
