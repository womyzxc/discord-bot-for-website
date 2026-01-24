"use client";

import { useEffect, useState, useMemo } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from "recharts";

interface User {
  id: number;
  email: string;
  name: string;
  image: string;
  provider: string;
  role: string;
  created_at: string;
  last_login: string;
  banned: boolean;
  ban_reason: string | null;
}

interface Admin {
  id: number;
  username: string;
  can_manage_users: number;
  can_manage_admins: number;
  created_at: string;
}

interface CurrentAdmin {
  id: number;
  username: string;
  canManageUsers: boolean;
  canManageAdmins: boolean;
}

interface ActivityLog {
  id: number;
  user_id: number | null;
  admin_id: number | null;
  action: string;
  details: string;
  created_at: string;
}

interface Stats {
  last7Days: { date: string; count: number }[];
  providerStats: { discord: number; google: number };
  totalUsers: number;
  bannedUsers: number;
  activeToday: number;
}

const COLORS = ["#8b5cf6", "#06b6d4"];

export default function AdminDashboard() {
  const [users, setUsers] = useState<User[]>([]);
  const [admins, setAdmins] = useState<Admin[]>([]);
  const [logs, setLogs] = useState<ActivityLog[]>([]);
  const [stats, setStats] = useState<Stats | null>(null);
  const [currentAdmin, setCurrentAdmin] = useState<CurrentAdmin | null>(null);
  const [activeTab, setActiveTab] = useState<"dashboard" | "users" | "admins" | "logs">("dashboard");
  const [isLoading, setIsLoading] = useState(true);
  const [showAddAdmin, setShowAddAdmin] = useState(false);
  const [showBanModal, setShowBanModal] = useState<User | null>(null);
  const [banReason, setBanReason] = useState("");
  const [newAdmin, setNewAdmin] = useState({ username: "", password: "", canManageUsers: false, canManageAdmins: false });
  const router = useRouter();

  // Search and filter state
  const [searchQuery, setSearchQuery] = useState("");
  const [providerFilter, setProviderFilter] = useState<"all" | "discord" | "google">("all");
  const [statusFilter, setStatusFilter] = useState<"all" | "active" | "banned">("all");
  const [sortBy, setSortBy] = useState<"newest" | "oldest" | "name">("newest");

  // Filtered users
  const filteredUsers = useMemo(() => {
    let result = [...users];
    if (searchQuery) {
      const query = searchQuery.toLowerCase();
      result = result.filter(
        (u) => u.name?.toLowerCase().includes(query) || u.email?.toLowerCase().includes(query)
      );
    }
    if (providerFilter !== "all") {
      result = result.filter((u) => u.provider === providerFilter);
    }
    if (statusFilter === "active") {
      result = result.filter((u) => !u.banned);
    } else if (statusFilter === "banned") {
      result = result.filter((u) => u.banned);
    }
    result.sort((a, b) => {
      if (sortBy === "newest") return new Date(b.created_at).getTime() - new Date(a.created_at).getTime();
      if (sortBy === "oldest") return new Date(a.created_at).getTime() - new Date(b.created_at).getTime();
      return (a.name || "").localeCompare(b.name || "");
    });
    return result;
  }, [users, searchQuery, providerFilter, statusFilter, sortBy]);

  useEffect(() => {
    const token = localStorage.getItem("adminToken");
    const adminUser = localStorage.getItem("adminUser");
    if (!token || !adminUser) {
      router.push("/admin/login");
      return;
    }
    setCurrentAdmin(JSON.parse(adminUser));

    const loadData = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const [usersRes, adminsRes, statsRes, logsRes] = await Promise.all([
          fetch("/api/admin/users", { headers }),
          fetch("/api/admin/admins", { headers }),
          fetch("/api/admin/stats", { headers }),
          fetch("/api/admin/logs", { headers }),
        ]);
        if (!usersRes.ok) {
          localStorage.removeItem("adminToken");
          localStorage.removeItem("adminUser");
          router.push("/admin/login");
          return;
        }
        const [usersData, adminsData, statsData, logsData] = await Promise.all([
          usersRes.json(), adminsRes.json(), statsRes.json(), logsRes.json(),
        ]);
        setUsers(usersData.users || []);
        setAdmins(adminsData.admins || []);
        setStats(statsData.stats || null);
        setLogs(logsData.logs || []);
      } catch (error) {
        console.error("Error fetching data:", error);
      } finally {
        setIsLoading(false);
      }
    };
    loadData();
  }, [router]);

  const handleDeleteUser = async (userId: number) => {
    if (!confirm("Are you sure you want to delete this user?")) return;
    const token = localStorage.getItem("adminToken");
    await fetch(`/api/admin/users/${userId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    setUsers(users.filter((u) => u.id !== userId));
  };

  const handleBanUser = async () => {
    if (!showBanModal) return;
    const token = localStorage.getItem("adminToken");
    await fetch(`/api/admin/users/${showBanModal.id}/ban`, {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify({ reason: banReason }),
    });
    setUsers(users.map((u) => u.id === showBanModal.id ? { ...u, banned: true, ban_reason: banReason } : u));
    setShowBanModal(null);
    setBanReason("");
  };

  const handleUnbanUser = async (userId: number) => {
    const token = localStorage.getItem("adminToken");
    await fetch(`/api/admin/users/${userId}/ban`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    setUsers(users.map((u) => u.id === userId ? { ...u, banned: false, ban_reason: null } : u));
  };

  const handleDeleteAdmin = async (adminId: number) => {
    if (!confirm("Are you sure you want to delete this admin?")) return;
    const token = localStorage.getItem("adminToken");
    const res = await fetch(`/api/admin/admins/${adminId}`, {
      method: "DELETE",
      headers: { Authorization: `Bearer ${token}` },
    });
    if (res.ok) {
      setAdmins(admins.filter((a) => a.id !== adminId));
    } else {
      const data = await res.json();
      alert(data.error || "Failed to delete admin");
    }
  };

  const handleAddAdmin = async (e: React.FormEvent) => {
    e.preventDefault();
    const token = localStorage.getItem("adminToken");
    const res = await fetch("/api/admin/admins", {
      method: "POST",
      headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
      body: JSON.stringify(newAdmin),
    });
    if (res.ok) {
      const data = await res.json();
      setAdmins([...admins, data.admin]);
      setShowAddAdmin(false);
      setNewAdmin({ username: "", password: "", canManageUsers: false, canManageAdmins: false });
    } else {
      const data = await res.json();
      alert(data.error || "Failed to add admin");
    }
  };

  const handleExportCSV = () => {
    const headers = ["ID", "Name", "Email", "Provider", "Role", "Status", "Joined", "Last Login"];
    const csvData = filteredUsers.map((u) => [
      u.id, u.name || "Unknown", u.email || "No email", u.provider, u.role,
      u.banned ? "Banned" : "Active",
      new Date(u.created_at).toLocaleDateString(),
      u.last_login ? new Date(u.last_login).toLocaleDateString() : "Never",
    ]);
    const csvContent = [headers.join(","), ...csvData.map((row) => row.map((cell) => `"${cell}"`).join(","))].join("\n");
    const blob = new Blob([csvContent], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `users_export_${new Date().toISOString().split("T")[0]}.csv`;
    link.click();
  };

  const handleLogout = () => {
    localStorage.removeItem("adminToken");
    localStorage.removeItem("adminUser");
    router.push("/admin/login");
  };

  const getActionColor = (action: string) => {
    if (action.includes("banned")) return "text-red-400";
    if (action.includes("unbanned")) return "text-green-400";
    if (action.includes("deleted")) return "text-orange-400";
    if (action.includes("login")) return "text-blue-400";
    if (action.includes("signup")) return "text-purple-400";
    return "text-gray-400";
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#040405] flex items-center justify-center">
        <div className="w-8 h-8 border-2 border-purple-500/30 border-t-purple-500 rounded-full animate-spin" />
      </div>
    );
  }

  const pieData = stats ? [
    { name: "Discord", value: stats.providerStats.discord },
    { name: "Google", value: stats.providerStats.google },
  ] : [];

  return (
    <main className="min-h-screen bg-[#040405]">
      {/* Header */}
      <header className="bg-[#0a0a0b] border-b border-purple-900/20 px-6 py-4">
        <div className="max-w-7xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-4">
            <Link href="/" className="flex items-center gap-2">
              <img src="/logo.jpg" alt="Logo" className="w-8 h-8 rounded-lg" />
              <span className="font-orbitron font-bold text-white text-xl">Offcialx</span>
            </Link>
            <span className="text-gray-500">|</span>
            <span className="text-purple-400 font-semibold">Admin Panel</span>
          </div>
          <div className="flex items-center gap-4">
            <span className="text-gray-400 text-sm hidden sm:block">
              Logged in as <span className="text-purple-400">{currentAdmin?.username}</span>
            </span>
            <button onClick={handleLogout} className="text-gray-400 hover:text-white transition text-sm">
              Logout
            </button>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 py-6">
        {/* Tabs */}
        <div className="flex flex-wrap gap-2 mb-6">
          {[
            { id: "dashboard", label: "Dashboard", icon: "M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6z" },
            { id: "users", label: `Users (${users.length})`, icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197" },
            { id: "admins", label: `Admins (${admins.length})`, icon: "M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z", hide: !currentAdmin?.canManageAdmins },
            { id: "logs", label: "Activity Logs", icon: "M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" },
          ].filter(t => !t.hide).map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as typeof activeTab)}
              className={`px-4 py-2 rounded-xl font-semibold transition flex items-center gap-2 text-sm ${
                activeTab === tab.id ? "bg-purple-600 text-white" : "bg-[#1a1a1b] text-gray-400 hover:text-white"
              }`}
            >
              <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={tab.icon} />
              </svg>
              {tab.label}
            </button>
          ))}
        </div>

        {/* Dashboard Tab */}
        {activeTab === "dashboard" && (
          <div className="space-y-6">
            {/* Stats Cards */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
              {[
                { label: "Total Users", value: stats?.totalUsers || 0, color: "green", icon: "M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197" },
                { label: "Active Today", value: stats?.activeToday || 0, color: "cyan", icon: "M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" },
                { label: "Banned", value: stats?.bannedUsers || 0, color: "red", icon: "M18.364 18.364A9 9 0 005.636 5.636m12.728 12.728A9 9 0 015.636 5.636m12.728 12.728L5.636 5.636" },
                { label: "Discord", value: stats?.providerStats.discord || 0, color: "purple", isDiscord: true },
                { label: "Google", value: stats?.providerStats.google || 0, color: "orange", isGoogle: true },
              ].map((stat, i) => (
                <div key={i} className="gradient-border rounded-xl p-4 bg-[#0a0a0b]">
                  <div className="flex items-center gap-3">
                    <div className={`w-10 h-10 rounded-xl bg-${stat.color}-900/30 border border-${stat.color}-500/30 flex items-center justify-center`}
                      style={{ backgroundColor: `rgb(${stat.color === 'green' ? '34 197 94' : stat.color === 'cyan' ? '6 182 212' : stat.color === 'red' ? '239 68 68' : stat.color === 'purple' ? '139 92 246' : '249 115 22'} / 0.1)`, borderColor: `rgb(${stat.color === 'green' ? '34 197 94' : stat.color === 'cyan' ? '6 182 212' : stat.color === 'red' ? '239 68 68' : stat.color === 'purple' ? '139 92 246' : '249 115 22'} / 0.3)` }}>
                      {stat.isDiscord ? (
                        <svg className="w-5 h-5 text-[#5865F2]" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M20.317 4.3698a19.7913 19.7913 0 00-4.8851-1.5152.0741.0741 0 00-.0785.0371c-.211.3753-.4447.8648-.6083 1.2495-1.8447-.2762-3.68-.2762-5.4868 0-.1636-.3933-.4058-.8742-.6177-1.2495a.077.077 0 00-.0785-.037 19.7363 19.7363 0 00-4.8852 1.515.0699.0699 0 00-.0321.0277C.5334 9.0458-.319 13.5799.0992 18.0578a.0824.0824 0 00.0312.0561c2.0528 1.5076 4.0413 2.4228 5.9929 3.0294a.0777.0777 0 00.0842-.0276c.4616-.6304.8731-1.2952 1.226-1.9942a.076.076 0 00-.0416-.1057c-.6528-.2476-1.2743-.5495-1.8722-.8923a.077.077 0 01-.0076-.1277c.1258-.0943.2517-.1923.3718-.2914a.0743.0743 0 01.0776-.0105c3.9278 1.7933 8.18 1.7933 12.0614 0a.0739.0739 0 01.0785.0095c.1202.099.246.1981.3728.2924a.077.077 0 01-.0066.1276 12.2986 12.2986 0 01-1.873.8914.0766.0766 0 00-.0407.1067c.3604.698.7719 1.3628 1.225 1.9932a.076.076 0 00.0842.0286c1.961-.6067 3.9495-1.5219 6.0023-3.0294a.077.077 0 00.0313-.0552c.5004-5.177-.8382-9.6739-3.5485-13.6604a.061.061 0 00-.0312-.0286z" />
                        </svg>
                      ) : stat.isGoogle ? (
                        <svg className="w-5 h-5 text-orange-400" viewBox="0 0 24 24" fill="currentColor">
                          <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" />
                          <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" />
                        </svg>
                      ) : (
                        <svg className={`w-5 h-5`} style={{ color: stat.color === 'green' ? '#4ade80' : stat.color === 'cyan' ? '#22d3ee' : '#f87171' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d={stat.icon} />
                        </svg>
                      )}
                    </div>
                    <div>
                      <p className="text-xl font-orbitron font-bold text-white">{stat.value}</p>
                      <p className="text-gray-500 text-xs">{stat.label}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* Charts */}
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              <div className="lg:col-span-2 gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
                <h3 className="font-orbitron font-bold text-lg text-white mb-4">User Growth (Last 7 Days)</h3>
                <div className="h-64">
                  <ResponsiveContainer width="100%" height="100%">
                    <AreaChart data={stats?.last7Days || []}>
                      <defs>
                        <linearGradient id="colorUsers" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#8b5cf6" stopOpacity={0.3} />
                          <stop offset="95%" stopColor="#8b5cf6" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <CartesianGrid strokeDasharray="3 3" stroke="#2a2a2b" />
                      <XAxis dataKey="date" stroke="#666" tick={{ fill: "#888", fontSize: 12 }} tickFormatter={(v) => new Date(v).toLocaleDateString('en-US', { month: 'short', day: 'numeric' })} />
                      <YAxis stroke="#666" tick={{ fill: "#888", fontSize: 12 }} />
                      <Tooltip contentStyle={{ backgroundColor: "#1a1a1b", border: "1px solid #8b5cf6", borderRadius: "8px" }} />
                      <Area type="monotone" dataKey="count" stroke="#8b5cf6" strokeWidth={2} fill="url(#colorUsers)" name="New Users" />
                    </AreaChart>
                  </ResponsiveContainer>
                </div>
              </div>

              <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
                <h3 className="font-orbitron font-bold text-lg text-white mb-4">Auth Providers</h3>
                <div className="h-48">
                  <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                      <Pie data={pieData} cx="50%" cy="50%" innerRadius={50} outerRadius={70} paddingAngle={5} dataKey="value">
                        {pieData.map((_, index) => <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />)}
                      </Pie>
                      <Tooltip contentStyle={{ backgroundColor: "#1a1a1b", border: "1px solid #8b5cf6", borderRadius: "8px" }} />
                    </PieChart>
                  </ResponsiveContainer>
                </div>
                <div className="flex justify-center gap-6 mt-2">
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-purple-500"></div><span className="text-gray-400 text-sm">Discord</span></div>
                  <div className="flex items-center gap-2"><div className="w-3 h-3 rounded-full bg-cyan-500"></div><span className="text-gray-400 text-sm">Google</span></div>
                </div>
              </div>
            </div>

            {/* Recent Activity */}
            <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
              <h3 className="font-orbitron font-bold text-lg text-white mb-4">Recent Activity</h3>
              <div className="space-y-3 max-h-64 overflow-y-auto">
                {logs.slice(0, 10).map((log) => (
                  <div key={log.id} className="flex items-start gap-3 p-3 bg-[#1a1a1b] rounded-xl">
                    <div className={`mt-1 ${getActionColor(log.action)}`}>
                      <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-gray-300 text-sm truncate">{log.details}</p>
                      <p className="text-gray-500 text-xs mt-1">{new Date(log.created_at).toLocaleString()}</p>
                    </div>
                  </div>
                ))}
                {logs.length === 0 && <p className="text-gray-500 text-center py-4">No activity yet</p>}
              </div>
            </div>
          </div>
        )}

        {/* Users Tab */}
        {activeTab === "users" && (
          <div className="space-y-4">
            {/* Search and Filter */}
            <div className="gradient-border rounded-xl p-4 bg-[#0a0a0b]">
              <div className="flex flex-wrap gap-3">
                <div className="flex-1 min-w-[200px]">
                  <div className="relative">
                    <svg className="w-5 h-5 absolute left-3 top-1/2 -translate-y-1/2 text-gray-500" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                    </svg>
                    <input type="text" value={searchQuery} onChange={(e) => setSearchQuery(e.target.value)} placeholder="Search by name or email..." className="w-full bg-[#1a1a1b] border border-purple-900/30 rounded-xl pl-10 pr-4 py-2.5 text-white placeholder:text-gray-500 focus:outline-none focus:border-purple-500" />
                  </div>
                </div>
                <select value={providerFilter} onChange={(e) => setProviderFilter(e.target.value as typeof providerFilter)} className="bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-purple-500">
                  <option value="all">All Providers</option>
                  <option value="discord">Discord</option>
                  <option value="google">Google</option>
                </select>
                <select value={statusFilter} onChange={(e) => setStatusFilter(e.target.value as typeof statusFilter)} className="bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-purple-500">
                  <option value="all">All Status</option>
                  <option value="active">Active</option>
                  <option value="banned">Banned</option>
                </select>
                <select value={sortBy} onChange={(e) => setSortBy(e.target.value as typeof sortBy)} className="bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-2.5 text-white focus:outline-none focus:border-purple-500">
                  <option value="newest">Newest First</option>
                  <option value="oldest">Oldest First</option>
                  <option value="name">By Name</option>
                </select>
                <button onClick={handleExportCSV} className="bg-green-600 hover:bg-green-500 text-white px-4 py-2.5 rounded-xl transition flex items-center gap-2">
                  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                  </svg>
                  Export CSV
                </button>
              </div>
              <div className="mt-3 text-gray-500 text-sm">Showing {filteredUsers.length} of {users.length} users</div>
            </div>

            {/* Users Table */}
            <div className="gradient-border rounded-2xl overflow-hidden">
              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead className="bg-purple-900/20">
                    <tr>
                      <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">User</th>
                      <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Provider</th>
                      <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Status</th>
                      <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm hidden md:table-cell">Joined</th>
                      <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-purple-900/20">
                    {filteredUsers.length === 0 ? (
                      <tr><td colSpan={5} className="px-6 py-12 text-center text-gray-500">{searchQuery || providerFilter !== "all" || statusFilter !== "all" ? "No users match your filters" : "No users yet"}</td></tr>
                    ) : filteredUsers.map((user) => (
                      <tr key={user.id} className={`hover:bg-purple-900/10 transition-colors ${user.banned ? 'opacity-60' : ''}`}>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            {user.image ? <img src={user.image} alt="" className="w-10 h-10 rounded-full" /> : (
                              <div className="w-10 h-10 rounded-full bg-purple-900/30 flex items-center justify-center">
                                <span className="text-purple-400 font-semibold">{user.name?.[0] || user.email?.[0] || "?"}</span>
                              </div>
                            )}
                            <div>
                              <p className="text-white font-semibold">{user.name || "Unknown"}</p>
                              <p className="text-gray-500 text-sm">{user.email || "No email"}</p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <span className={`px-3 py-1 rounded-full text-xs font-semibold ${user.provider === "discord" ? "bg-[#5865F2]/20 text-[#5865F2]" : "bg-orange-500/20 text-orange-400"}`}>{user.provider}</span>
                        </td>
                        <td className="px-6 py-4">
                          {user.banned ? (
                            <div>
                              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-red-500/20 text-red-400">Banned</span>
                              {user.ban_reason && <p className="text-gray-500 text-xs mt-1 max-w-[150px] truncate" title={user.ban_reason}>{user.ban_reason}</p>}
                            </div>
                          ) : <span className="px-3 py-1 rounded-full text-xs font-semibold bg-green-500/20 text-green-400">Active</span>}
                        </td>
                        <td className="px-6 py-4 text-gray-400 text-sm hidden md:table-cell">{new Date(user.created_at).toLocaleDateString()}</td>
                        <td className="px-6 py-4">
                          {currentAdmin?.canManageUsers && (
                            <div className="flex items-center gap-2">
                              {user.banned ? (
                                <button onClick={() => handleUnbanUser(user.id)} className="text-green-400 hover:text-green-300 transition text-sm">Unban</button>
                              ) : (
                                <button onClick={() => setShowBanModal(user)} className="text-orange-400 hover:text-orange-300 transition text-sm">Ban</button>
                              )}
                              <button onClick={() => handleDeleteUser(user.id)} className="text-red-400 hover:text-red-300 transition text-sm">Delete</button>
                            </div>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {/* Admins Tab */}
        {activeTab === "admins" && currentAdmin?.canManageAdmins && (
          <div>
            <div className="mb-4">
              <button onClick={() => setShowAddAdmin(true)} className="bg-purple-600 hover:bg-purple-500 text-white px-4 py-2 rounded-xl transition flex items-center gap-2">
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" /></svg>
                Add Admin
              </button>
            </div>
            <div className="gradient-border rounded-2xl overflow-hidden">
              <table className="w-full">
                <thead className="bg-purple-900/20">
                  <tr>
                    <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Username</th>
                    <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Permissions</th>
                    <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm hidden md:table-cell">Created</th>
                    <th className="text-left px-6 py-4 text-purple-400 font-orbitron text-sm">Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-purple-900/20">
                  {admins.map((admin) => (
                    <tr key={admin.id} className="hover:bg-purple-900/10 transition-colors">
                      <td className="px-6 py-4">
                        <span className="text-white font-semibold">{admin.username}</span>
                        {admin.username === "womy1621" && <span className="ml-2 text-xs bg-yellow-500/20 text-yellow-400 px-2 py-1 rounded-full">Owner</span>}
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex gap-2">
                          {admin.can_manage_users === 1 && <span className="text-xs bg-green-500/20 text-green-400 px-2 py-1 rounded-full">Users</span>}
                          {admin.can_manage_admins === 1 && <span className="text-xs bg-purple-500/20 text-purple-400 px-2 py-1 rounded-full">Admins</span>}
                        </div>
                      </td>
                      <td className="px-6 py-4 text-gray-400 text-sm hidden md:table-cell">{new Date(admin.created_at).toLocaleDateString()}</td>
                      <td className="px-6 py-4">
                        {admin.username !== "womy1621" && <button onClick={() => handleDeleteAdmin(admin.id)} className="text-red-400 hover:text-red-300 transition text-sm">Delete</button>}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Activity Logs Tab */}
        {activeTab === "logs" && (
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b]">
            <div className="flex items-center justify-between mb-6">
              <h3 className="font-orbitron font-bold text-lg text-white">Activity Logs</h3>
              <span className="text-gray-500 text-sm">{logs.length} entries</span>
            </div>
            <div className="space-y-3 max-h-[600px] overflow-y-auto">
              {logs.map((log) => (
                <div key={log.id} className="flex items-start gap-4 p-4 bg-[#1a1a1b] rounded-xl border border-purple-900/20 hover:border-purple-900/40 transition">
                  <div className={`mt-1 p-2 rounded-lg ${getActionColor(log.action)}`}>
                    <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                    </svg>
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="text-white text-sm font-medium">{log.details}</p>
                    <div className="flex items-center gap-4 mt-2">
                      <span className={`text-xs px-2 py-0.5 rounded-full ${getActionColor(log.action)} bg-current/10`}>{log.action.replace(/_/g, " ")}</span>
                      <span className="text-gray-500 text-xs">{new Date(log.created_at).toLocaleString()}</span>
                    </div>
                  </div>
                </div>
              ))}
              {logs.length === 0 && <p className="text-gray-500 text-center py-12">No activity logs yet</p>}
            </div>
          </div>
        )}
      </div>

      {/* Add Admin Modal */}
      {showAddAdmin && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] max-w-md w-full">
            <h3 className="font-orbitron font-bold text-xl text-white mb-4">Add New Admin</h3>
            <form onSubmit={handleAddAdmin} className="space-y-4">
              <div>
                <label className="block text-gray-400 text-sm mb-2">Username</label>
                <input type="text" value={newAdmin.username} onChange={(e) => setNewAdmin({ ...newAdmin, username: e.target.value })} className="w-full bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-3 text-white" required />
              </div>
              <div>
                <label className="block text-gray-400 text-sm mb-2">Password</label>
                <input type="password" value={newAdmin.password} onChange={(e) => setNewAdmin({ ...newAdmin, password: e.target.value })} className="w-full bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-3 text-white" required />
              </div>
              <div className="space-y-2">
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={newAdmin.canManageUsers} onChange={(e) => setNewAdmin({ ...newAdmin, canManageUsers: e.target.checked })} className="w-5 h-5 rounded" />
                  <span className="text-gray-300">Can manage users</span>
                </label>
                <label className="flex items-center gap-3 cursor-pointer">
                  <input type="checkbox" checked={newAdmin.canManageAdmins} onChange={(e) => setNewAdmin({ ...newAdmin, canManageAdmins: e.target.checked })} className="w-5 h-5 rounded" />
                  <span className="text-gray-300">Can manage admins</span>
                </label>
              </div>
              <div className="flex gap-3">
                <button type="button" onClick={() => setShowAddAdmin(false)} className="flex-1 bg-[#1a1a1b] text-gray-400 px-4 py-3 rounded-xl transition hover:bg-[#252527]">Cancel</button>
                <button type="submit" className="flex-1 bg-purple-600 hover:bg-purple-500 text-white px-4 py-3 rounded-xl transition">Add Admin</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Ban User Modal */}
      {showBanModal && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
          <div className="gradient-border rounded-2xl p-6 bg-[#0a0a0b] max-w-md w-full">
            <h3 className="font-orbitron font-bold text-xl text-white mb-2">Ban User</h3>
            <p className="text-gray-400 text-sm mb-4">Are you sure you want to ban <span className="text-white">{showBanModal.name || showBanModal.email}</span>?</p>
            <div className="mb-4">
              <label className="block text-gray-400 text-sm mb-2">Reason (optional)</label>
              <textarea value={banReason} onChange={(e) => setBanReason(e.target.value)} placeholder="Enter reason for ban..." className="w-full bg-[#1a1a1b] border border-purple-900/30 rounded-xl px-4 py-3 text-white resize-none h-24" />
            </div>
            <div className="flex gap-3">
              <button onClick={() => { setShowBanModal(null); setBanReason(""); }} className="flex-1 bg-[#1a1a1b] text-gray-400 px-4 py-3 rounded-xl transition hover:bg-[#252527]">Cancel</button>
              <button onClick={handleBanUser} className="flex-1 bg-red-600 hover:bg-red-500 text-white px-4 py-3 rounded-xl transition">Ban User</button>
            </div>
          </div>
        </div>
      )}
    </main>
  );
}
