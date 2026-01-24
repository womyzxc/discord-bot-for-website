import { SignJWT, jwtVerify } from 'jose';

const SECRET_KEY = new TextEncoder().encode(
  process.env.AUTH_SECRET || 'offcialx-admin-secret-key-2024'
);

export interface AdminSession {
  adminId: number;
  username: string;
  canManageUsers: boolean;
  canManageAdmins: boolean;
}

export async function createAdminToken(data: AdminSession): Promise<string> {
  const token = await new SignJWT({ ...data })
    .setProtectedHeader({ alg: 'HS256' })
    .setIssuedAt()
    .setExpirationTime('24h')
    .sign(SECRET_KEY);

  return token;
}

export async function verifyAdminToken(token: string): Promise<AdminSession | null> {
  try {
    const { payload } = await jwtVerify(token, SECRET_KEY);
    return {
      adminId: payload.adminId as number,
      username: payload.username as string,
      canManageUsers: payload.canManageUsers as boolean,
      canManageAdmins: payload.canManageAdmins as boolean,
    };
  } catch {
    return null;
  }
}
