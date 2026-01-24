import { NextResponse } from "next/server";
import { banUser, unbanUser } from "@/lib/db";
import { verifyAdminToken } from "@/lib/adminAuth";

async function verifyToken(request: Request) {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) return null;

  const token = authHeader.substring(7);
  return await verifyAdminToken(token);
}

export async function POST(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await verifyToken(request);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!session.canManageUsers) {
    return NextResponse.json({ error: "Permission denied" }, { status: 403 });
  }

  try {
    const { id } = await params;
    const { reason } = await request.json();
    banUser(parseInt(id), reason || "No reason provided");
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error banning user:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await verifyToken(request);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!session.canManageUsers) {
    return NextResponse.json({ error: "Permission denied" }, { status: 403 });
  }

  try {
    const { id } = await params;
    unbanUser(parseInt(id));
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error unbanning user:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
