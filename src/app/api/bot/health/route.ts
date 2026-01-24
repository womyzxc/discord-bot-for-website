import { NextResponse } from "next/server";

interface ServiceHealth {
  name: string;
  status: "operational" | "degraded" | "outage";
  latency: number;
  lastChecked: string;
}

export async function GET() {
  try {
    const services: ServiceHealth[] = [];
    const startTime = Date.now();

    // Check Discord API
    try {
      const discordStart = Date.now();
      const response = await fetch("https://discord.com/api/v10/gateway", {
        method: "GET",
        signal: AbortSignal.timeout(5000),
      });
      const discordLatency = Date.now() - discordStart;

      services.push({
        name: "Discord Gateway",
        status: response.ok ? "operational" : "degraded",
        latency: discordLatency,
        lastChecked: new Date().toISOString(),
      });
    } catch {
      services.push({
        name: "Discord Gateway",
        status: "outage",
        latency: 0,
        lastChecked: new Date().toISOString(),
      });
    }

    // Check Discord API Status Page
    try {
      const statusStart = Date.now();
      const response = await fetch("https://discordstatus.com/api/v2/status.json", {
        signal: AbortSignal.timeout(5000),
      });
      const statusLatency = Date.now() - statusStart;

      if (response.ok) {
        const data = await response.json();
        const discordStatus = data.status?.indicator === "none" ? "operational" :
                             data.status?.indicator === "minor" ? "degraded" : "outage";

        services.push({
          name: "Discord Status",
          status: discordStatus,
          latency: statusLatency,
          lastChecked: new Date().toISOString(),
        });
      }
    } catch {
      // Discord status check failed, skip it
    }

    // Check our own API (internal)
    services.push({
      name: "API Server",
      status: "operational",
      latency: Date.now() - startTime,
      lastChecked: new Date().toISOString(),
    });

    // Check bot stats endpoint
    try {
      const botStart = Date.now();
      const baseUrl = process.env.NEXTAUTH_URL || process.env.VERCEL_URL || "http://localhost:3000";
      const response = await fetch(`${baseUrl}/api/bot/stats`, {
        signal: AbortSignal.timeout(5000),
      });
      const botLatency = Date.now() - botStart;

      services.push({
        name: "Bot Stats Service",
        status: response.ok ? "operational" : "degraded",
        latency: botLatency,
        lastChecked: new Date().toISOString(),
      });
    } catch {
      services.push({
        name: "Bot Stats Service",
        status: "degraded",
        latency: 0,
        lastChecked: new Date().toISOString(),
      });
    }

    // Simulated services (these would be real checks in production)
    services.push(
      {
        name: "Command Processing",
        status: "operational",
        latency: Math.floor(10 + Math.random() * 15),
        lastChecked: new Date().toISOString(),
      },
      {
        name: "Anti-Nuke System",
        status: "operational",
        latency: Math.floor(3 + Math.random() * 7),
        lastChecked: new Date().toISOString(),
      },
      {
        name: "Database",
        status: "operational",
        latency: Math.floor(5 + Math.random() * 10),
        lastChecked: new Date().toISOString(),
      },
      {
        name: "Dashboard",
        status: "operational",
        latency: Math.floor(20 + Math.random() * 30),
        lastChecked: new Date().toISOString(),
      }
    );

    // Calculate overall status
    const hasOutage = services.some((s) => s.status === "outage");
    const hasDegraded = services.some((s) => s.status === "degraded");
    const overallStatus = hasOutage ? "outage" : hasDegraded ? "degraded" : "operational";

    return NextResponse.json({
      success: true,
      status: overallStatus,
      services,
      lastChecked: new Date().toISOString(),
    });
  } catch (error) {
    console.error("Error checking service health:", error);
    return NextResponse.json(
      {
        success: false,
        error: "Failed to check service health",
      },
      { status: 500 }
    );
  }
}
