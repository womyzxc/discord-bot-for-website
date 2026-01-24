import { NextResponse } from "next/server";
import { verifyAdmin } from "@/lib/db";
import { createAdminToken } from "@/lib/adminAuth";

export async function POST(request: Request) {
  try {
    const { username, password } = await request.json();

    if (!username || !password) {
      return NextResponse.json(
        { error: "Username and password are required" },
        { status: 400 }
      );
    }

    const admin = verifyAdmin(username, password);

    if (!admin) {
      return NextResponse.json(
        { error: "Invalid username or password" },
        { status: 401 }
      );
    }

    // Generate JWT token
    const token = await createAdminToken({
      adminId: admin.id,
      username: admin.username,
      canManageUsers: admin.canManageUsers,
      canManageAdmins: admin.canManageAdmins,
    });

    return NextResponse.json({
      token,
      admin: {
        id: admin.id,
        username: admin.username,
        canManageUsers: admin.canManageUsers,
        canManageAdmins: admin.canManageAdmins,
      },
    });
  } catch (error) {
    console.error("Admin login error:", error);
    return NextResponse.json(
      { error: "Internal server error" },
      { status: 500 }
    );
  }
}
