import bcrypt from 'bcryptjs';

// In-memory storage for serverless environments (Netlify, Vercel, etc.)
// For production, use a real database like Neon, PlanetScale, or Turso

interface User {
  id: number;
  email: string | null;
  name: string | null;
  image: string | null;
  provider: string;
  provider_id: string | null;
  role: string;
  created_at: string;
  last_login: string | null;
  banned: boolean;
  ban_reason: string | null;
}

interface Admin {
  id: number;
  username: string;
  password_hash: string;
  can_manage_users: number;
  can_manage_admins: number;
  created_at: string;
}

interface ActivityLog {
  id: number;
  user_id: number | null;
  admin_id: number | null;
  action: string;
  details: string;
  ip_address: string | null;
  created_at: string;
}

// In-memory storage
const users: User[] = [];
const admins: Admin[] = [];
const activityLogs: ActivityLog[] = [];
let userIdCounter = 1;
let adminIdCounter = 1;
let activityLogIdCounter = 1;

// Initialize default admin
const defaultAdminHash = bcrypt.hashSync('womy1621', 10);
admins.push({
  id: adminIdCounter++,
  username: 'womy1621',
  password_hash: defaultAdminHash,
  can_manage_users: 1,
  can_manage_admins: 1,
  created_at: new Date().toISOString(),
});

// Add some sample users for demo
const sampleUsers = [
  { name: 'John Doe', email: 'john@example.com', provider: 'discord', daysAgo: 7 },
  { name: 'Jane Smith', email: 'jane@example.com', provider: 'google', daysAgo: 5 },
  { name: 'Mike Johnson', email: 'mike@example.com', provider: 'discord', daysAgo: 3 },
  { name: 'Sarah Wilson', email: 'sarah@example.com', provider: 'discord', daysAgo: 2 },
  { name: 'Alex Brown', email: 'alex@example.com', provider: 'google', daysAgo: 1 },
];

sampleUsers.forEach((sample) => {
  const date = new Date();
  date.setDate(date.getDate() - sample.daysAgo);
  users.push({
    id: userIdCounter++,
    email: sample.email,
    name: sample.name,
    image: null,
    provider: sample.provider,
    provider_id: `${sample.provider}_${userIdCounter}`,
    role: 'user',
    created_at: date.toISOString(),
    last_login: date.toISOString(),
    banned: false,
    ban_reason: null,
  });
});

// User functions
export function createUser(data: {
  email?: string;
  name?: string;
  image?: string;
  provider: string;
  providerId?: string;
}) {
  const newUser: User = {
    id: userIdCounter++,
    email: data.email || null,
    name: data.name || null,
    image: data.image || null,
    provider: data.provider,
    provider_id: data.providerId || null,
    role: 'user',
    created_at: new Date().toISOString(),
    last_login: new Date().toISOString(),
    banned: false,
    ban_reason: null,
  };
  users.push(newUser);

  // Log activity
  addActivityLog(null, null, 'user_signup', `New user signed up: ${newUser.name || newUser.email}`);

  return newUser.id;
}

export function getUserByEmail(email: string) {
  return users.find(u => u.email === email) || null;
}

export function getUserByProviderId(provider: string, providerId: string) {
  return users.find(u => u.provider === provider && u.provider_id === providerId) || null;
}

export function updateUserLogin(userId: number) {
  const user = users.find(u => u.id === userId);
  if (user) {
    user.last_login = new Date().toISOString();
    addActivityLog(userId, null, 'user_login', `User logged in: ${user.name || user.email}`);
  }
}

export function getAllUsers() {
  return users.map(u => ({
    id: u.id,
    email: u.email,
    name: u.name,
    image: u.image,
    provider: u.provider,
    role: u.role,
    created_at: u.created_at,
    last_login: u.last_login,
    banned: u.banned,
    ban_reason: u.ban_reason,
  }));
}

export function deleteUser(userId: number) {
  const index = users.findIndex(u => u.id === userId);
  if (index !== -1) {
    const user = users[index];
    addActivityLog(null, null, 'user_deleted', `User deleted: ${user.name || user.email}`);
    users.splice(index, 1);
  }
}

export function updateUserRole(userId: number, role: string) {
  const user = users.find(u => u.id === userId);
  if (user) {
    user.role = role;
  }
}

export function banUser(userId: number, reason: string) {
  const user = users.find(u => u.id === userId);
  if (user) {
    user.banned = true;
    user.ban_reason = reason;
    addActivityLog(userId, null, 'user_banned', `User banned: ${user.name || user.email}. Reason: ${reason}`);
  }
}

export function unbanUser(userId: number) {
  const user = users.find(u => u.id === userId);
  if (user) {
    user.banned = false;
    user.ban_reason = null;
    addActivityLog(userId, null, 'user_unbanned', `User unbanned: ${user.name || user.email}`);
  }
}

// Activity Log functions
export function addActivityLog(userId: number | null, adminId: number | null, action: string, details: string, ipAddress: string | null = null) {
  activityLogs.push({
    id: activityLogIdCounter++,
    user_id: userId,
    admin_id: adminId,
    action,
    details,
    ip_address: ipAddress,
    created_at: new Date().toISOString(),
  });
}

export function getActivityLogs(limit: number = 50) {
  return activityLogs
    .slice(-limit)
    .reverse()
    .map(log => ({
      id: log.id,
      user_id: log.user_id,
      admin_id: log.admin_id,
      action: log.action,
      details: log.details,
      created_at: log.created_at,
    }));
}

// Analytics functions
export function getUserStats() {
  const now = new Date();
  const last7Days = [];

  for (let i = 6; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    const dateStr = date.toISOString().split('T')[0];

    const count = users.filter(u => {
      const userDate = new Date(u.created_at).toISOString().split('T')[0];
      return userDate === dateStr;
    }).length;

    last7Days.push({
      date: dateStr,
      count,
    });
  }

  const providerStats = {
    discord: users.filter(u => u.provider === 'discord').length,
    google: users.filter(u => u.provider === 'google').length,
  };

  const totalUsers = users.length;
  const bannedUsers = users.filter(u => u.banned).length;
  const activeToday = users.filter(u => {
    if (!u.last_login) return false;
    const today = new Date().toISOString().split('T')[0];
    return u.last_login.split('T')[0] === today;
  }).length;

  return {
    last7Days,
    providerStats,
    totalUsers,
    bannedUsers,
    activeToday,
  };
}

// Admin functions
export function verifyAdmin(username: string, password: string) {
  const admin = admins.find(a => a.username === username);
  if (!admin) return null;

  const isValid = bcrypt.compareSync(password, admin.password_hash);
  if (!isValid) return null;

  return {
    id: admin.id,
    username: admin.username,
    canManageUsers: admin.can_manage_users === 1,
    canManageAdmins: admin.can_manage_admins === 1,
  };
}

export function getAllAdmins() {
  return admins.map(a => ({
    id: a.id,
    username: a.username,
    can_manage_users: a.can_manage_users,
    can_manage_admins: a.can_manage_admins,
    created_at: a.created_at,
  }));
}

export function createAdmin(username: string, password: string, canManageUsers: boolean, canManageAdmins: boolean) {
  // Check if admin already exists
  if (admins.find(a => a.username === username)) {
    throw new Error('UNIQUE constraint failed: admin_users.username');
  }

  const hashedPassword = bcrypt.hashSync(password, 10);
  const newAdmin: Admin = {
    id: adminIdCounter++,
    username,
    password_hash: hashedPassword,
    can_manage_users: canManageUsers ? 1 : 0,
    can_manage_admins: canManageAdmins ? 1 : 0,
    created_at: new Date().toISOString(),
  };
  admins.push(newAdmin);
  return { lastInsertRowid: newAdmin.id };
}

export function deleteAdmin(adminId: number) {
  const admin = admins.find(a => a.id === adminId);
  if (admin?.username === 'womy1621') {
    throw new Error('Cannot delete the main admin');
  }
  const index = admins.findIndex(a => a.id === adminId);
  if (index !== -1) {
    admins.splice(index, 1);
  }
}

export function updateAdminPermissions(adminId: number, canManageUsers: boolean, canManageAdmins: boolean) {
  const admin = admins.find(a => a.id === adminId);
  if (admin) {
    admin.can_manage_users = canManageUsers ? 1 : 0;
    admin.can_manage_admins = canManageAdmins ? 1 : 0;
  }
}

const db = { users, admins, activityLogs };
export default db;
