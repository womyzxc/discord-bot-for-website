import { NextResponse } from "next/server";
import { getUserStats } from "@/lib/db";
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
    const stats = getUserStats();
    return NextResponse.json({ stats });
  } catch (error) {
    console.error("Error fetching stats:", error);
    return NextResponse.json({ error: "Internal server error" }, { status: 500 });
  }
}
