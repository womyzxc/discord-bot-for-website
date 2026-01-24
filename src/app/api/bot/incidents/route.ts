import { NextRequest, NextResponse } from "next/server";

interface IncidentUpdate {
  time: string;
  message: string;
}

interface Incident {
  id: number;
  title: string;
  status: "resolved" | "investigating" | "identified" | "monitoring";
  date: string;
  description: string;
  updates: IncidentUpdate[];
  createdAt: string;
  updatedAt: string;
}

// In-memory storage for incidents (in production, use a database)
let incidents: Incident[] = [
  {
    id: 1,
    title: "API Response Delays",
    status: "resolved",
    date: "2026-01-15",
    description: "Some users experienced delayed responses from the bot.",
    updates: [
      { time: "14:30 UTC", message: "Issue resolved. All systems operational." },
      { time: "14:00 UTC", message: "Identified the root cause. Implementing fix." },
      { time: "13:45 UTC", message: "Investigating reports of slow responses." },
    ],
    createdAt: "2026-01-15T13:45:00Z",
    updatedAt: "2026-01-15T14:30:00Z",
  },
  {
    id: 2,
    title: "Scheduled Maintenance",
    status: "resolved",
    date: "2026-01-10",
    description: "Planned maintenance for database optimization.",
    updates: [
      { time: "06:00 UTC", message: "Maintenance completed successfully." },
      { time: "04:00 UTC", message: "Maintenance started as scheduled." },
    ],
    createdAt: "2026-01-10T04:00:00Z",
    updatedAt: "2026-01-10T06:00:00Z",
  },
];

let nextIncidentId = 3;

// GET - Fetch all incidents
export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url);
  const limit = parseInt(searchParams.get("limit") || "10");
  const status = searchParams.get("status");

  let filteredIncidents = [...incidents];

  if (status) {
    filteredIncidents = filteredIncidents.filter((i) => i.status === status);
  }

  // Sort by date descending
  filteredIncidents.sort(
    (a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
  );

  return NextResponse.json({
    success: true,
    incidents: filteredIncidents.slice(0, limit),
    total: filteredIncidents.length,
  });
}

// POST - Create a new incident (requires admin auth)
export async function POST(request: NextRequest) {
  try {
    const authHeader = request.headers.get("Authorization");

    if (!authHeader?.startsWith("Bearer ")) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { title, description, status = "investigating" } = body;

    if (!title || !description) {
      return NextResponse.json(
        { success: false, error: "Title and description are required" },
        { status: 400 }
      );
    }

    const now = new Date();
    const newIncident: Incident = {
      id: nextIncidentId++,
      title,
      description,
      status,
      date: now.toISOString().split("T")[0],
      updates: [
        {
          time: now.toLocaleTimeString("en-US", {
            hour: "2-digit",
            minute: "2-digit",
            timeZone: "UTC"
          }) + " UTC",
          message: `Incident created: ${description}`,
        },
      ],
      createdAt: now.toISOString(),
      updatedAt: now.toISOString(),
    };

    incidents.unshift(newIncident);

    return NextResponse.json({
      success: true,
      incident: newIncident,
    });
  } catch (error) {
    console.error("Error creating incident:", error);
    return NextResponse.json(
      { success: false, error: "Failed to create incident" },
      { status: 500 }
    );
  }
}

// PATCH - Update an incident
export async function PATCH(request: NextRequest) {
  try {
    const authHeader = request.headers.get("Authorization");

    if (!authHeader?.startsWith("Bearer ")) {
      return NextResponse.json(
        { success: false, error: "Unauthorized" },
        { status: 401 }
      );
    }

    const body = await request.json();
    const { id, status, updateMessage } = body;

    const incidentIndex = incidents.findIndex((i) => i.id === id);

    if (incidentIndex === -1) {
      return NextResponse.json(
        { success: false, error: "Incident not found" },
        { status: 404 }
      );
    }

    const now = new Date();

    if (status) {
      incidents[incidentIndex].status = status;
    }

    if (updateMessage) {
      incidents[incidentIndex].updates.unshift({
        time: now.toLocaleTimeString("en-US", {
          hour: "2-digit",
          minute: "2-digit",
          timeZone: "UTC"
        }) + " UTC",
        message: updateMessage,
      });
    }

    incidents[incidentIndex].updatedAt = now.toISOString();

    return NextResponse.json({
      success: true,
      incident: incidents[incidentIndex],
    });
  } catch (error) {
    console.error("Error updating incident:", error);
    return NextResponse.json(
      { success: false, error: "Failed to update incident" },
      { status: 500 }
    );
  }
}
