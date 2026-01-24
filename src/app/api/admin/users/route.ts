import { NextResponse } from "next/server";
import { getAllUsers } from "@/lib/db";
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
    const users = getAllUsers();
    return NextResponse.json({ users });
  } catch (error) {
    console.error("Error fetching users:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
