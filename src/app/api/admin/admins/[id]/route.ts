import { NextResponse } from "next/server";
import { deleteAdmin } from "@/lib/db";
import { verifyAdminToken } from "@/lib/adminAuth";

async function verifyToken(request: Request) {
  const authHeader = request.headers.get("Authorization");
  if (!authHeader?.startsWith("Bearer ")) return null;

  const token = authHeader.substring(7);
  return await verifyAdminToken(token);
}

export async function DELETE(
  request: Request,
  { params }: { params: Promise<{ id: string }> }
) {
  const session = await verifyToken(request);

  if (!session) {
    return NextResponse.json({ error: "Unauthorized" }, { status: 401 });
  }

  if (!session.canManageAdmins) {
    return NextResponse.json({ error: "Permission denied" }, { status: 403 });
  }

  try {
    const { id } = await params;
    deleteAdmin(parseInt(id));
    return NextResponse.json({ success: true });
  } catch (error) {
    console.error("Error deleting admin:", error);
    const message = error instanceof Error ? error.message : "Internal server error";
    return NextResponse.json({ error: message }, { status: 500 });
  }
}
