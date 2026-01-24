import { NextResponse } from "next/server";
import { getAllAdmins, createAdmin } from "@/lib/db";
import { verifyAdminToken } from "@/lib/adminAuth";

async function verifyToken(request: Request) {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) return null;

  const token = authHeader.substring(7);
  return await verifyAdminToken(token);
}

export async function GET(request: Request) {
  const session = await verifyToken(request);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  try {
    const admins = getAllAdmins();
    return NextResponse.json({ admins });
  } catch (error) {
    console.error("Error fetching admins:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function POST(request: Request) {
  const session = await verifyToken(request);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!session.canManageAdmins) {
    return NextResponse.json({ error: "Permission denied" }, { status: 403 });
  }

  try {
    const { username, password, canManageUsers, canManageAdmins } = await request.json();

    if (!username || !password) {
      return NextResponse.json({ error: "Username and password are required" }, { status: 400 });
    }

    const result = createAdmin(username, password, canManageUsers, canManageAdmins);

    return NextResponse.json({
      admin: {
        id: result.lastInsertRowid,
        username,
        can_manage_users: canManageUsers ? 1 : 0,
        can_manage_admins: canManageAdmins ? 1 : 0,
        created_at: new Date().toISOString(),
      },
    });
  } catch (error) {
    console.error("Error creating admin:", error);
    if (error instanceof Error && error.message?.includes("UNIQUE constraint")) {
      return NextResponse.json({ error: "Username already exists" }, { status: 400 });
    }
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
