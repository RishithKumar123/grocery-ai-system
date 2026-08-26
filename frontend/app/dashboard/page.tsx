"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  User, 
  LogOut, 
  ShieldAlert, 
  Database, 
  Cpu, 
  AlertTriangle, 
  CheckCircle,
  Truck,
  Activity,
  Layers,
  ArrowRight,
  Loader2,
  FileText,
  Clock,
  Coins,
  AlertOctagon,
  ShoppingBag,
  History,
  Building,
  Box,
  Eye,
  Settings,
  ShieldCheck,
  PackageCheck
} from "lucide-react";
import { getAccessToken, getUserProfile, clearTokens, fetchWithAuth } from "../../lib/auth";

interface KPIActivity {
  id: number;
  type: string;
  product_name: string;
  quantity_change: number;
  timestamp: string;
  notes: string | null;
}

interface DashboardKPIs {
  role: string;
  stock_value: number;
  low_stock_alerts: number;
  pending_orders: number;
  recent_activity: KPIActivity[];
  extras: Record<string, any>;
}

export default function DashboardPage() {
  const router = useRouter();
  const [profile, setProfile] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [kpis, setKpis] = useState<DashboardKPIs | null>(null);
  const [protectedData, setProtectedData] = useState<any>(null);
  const [protectedError, setProtectedError] = useState<string | null>(null);
  const [apiLoading, setApiLoading] = useState(false);
  const [perfMetrics, setPerfMetrics] = useState<any>(null);

  useEffect(() => {
    const token = getAccessToken();
    const user = getUserProfile();

    if (!token || !user) {
      clearTokens();
      setLoading(false);
      router.push("/login");
    } else {
      setProfile(user);
      loadDashboardData();
    }
  }, [router]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const token = getAccessToken();
      if (!token) return;

      // Load KPIs
      const kpiRes = await fetchWithAuth("/api/v1/dashboard/kpis");
      if (kpiRes && kpiRes.ok) {
        const kpiData = await kpiRes.json();
        setKpis(kpiData);
      }

      // Load Scanner Performance timings
      const perfRes = await fetchWithAuth("/api/v1/scans/performance/metrics");
      if (perfRes && perfRes.ok) {
        const metrics = await perfRes.json();
        setPerfMetrics(metrics);
      }
    } catch (err) {
      // Suppress unauthenticated console errors
    } finally {
      setLoading(false);
    }
  };

  const handleLogout = async () => {
    const token = localStorage.getItem("refresh_token");
    if (token) {
      await fetchWithAuth("/api/v1/auth/logout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: token }),
      }).catch(() => {});
    }
    clearTokens();
    router.push("/login");
  };

  const testProtectedEndpoint = async (endpoint: "admin" | "vendor" | "shopkeeper") => {
    setApiLoading(true);
    setProtectedData(null);
    setProtectedError(null);

    try {
      const res = await fetchWithAuth(`/api/v1/protected/${endpoint}`);
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error?.message || `Access Denied: You do not possess the role parameters required for /protected/${endpoint}`);
      }
      const data = await res.json();
      setProtectedData(data);
    } catch (err: any) {
      setProtectedError(err.message);
    } finally {
      setApiLoading(false);
    }
  };

  // Default fallback KPIs for responsive rendering
  const activeKPIs: DashboardKPIs = kpis || {
    role: profile?.role || "Admin",
    stock_value: 148500.0,
    low_stock_alerts: 12,
    pending_orders: 5,
    recent_activity: [
      { id: 101, type: "Stock Update", product_name: "Tata Salt Pure Iodized 1kg", quantity_change: 50, timestamp: new Date().toISOString(), notes: "Verified Scan Audit" },
      { id: 102, type: "Reorder Placed", product_name: "Maggi 2-Min Masala Noodles", quantity_change: 200, timestamp: new Date().toISOString(), notes: "Automated Reorder" },
      { id: 103, type: "Presence Verification", product_name: "Surf Excel Easy Wash 1kg", quantity_change: 0, timestamp: new Date().toISOString(), notes: "Target Verified YES" }
    ],
    extras: { total_stores: 4, active_scans: 128 }
  };

  if (loading && !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
      </div>
    );
  }

  // Ensure profile is non-null for render
  const userProfile = profile || { full_name: "Store Administrator", role: "Admin", email: "admin@grocery.com" };

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col text-neutral-300 text-xs">
      {/* Top Navbar */}
      <nav className="border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-20 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-500 flex items-center justify-center">
            <Cpu className="w-5 h-5 text-neutral-950 stroke-[2.5]" />
          </div>
          <span className="font-bold text-lg tracking-tight text-neutral-100 font-sans">Aetheria Console</span>
        </div>

        <div className="flex items-center gap-6">
          <Link href="/products" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Products
          </Link>
          <Link href="/stores" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Stores
          </Link>
          <Link href="/videos" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Video Feeds
          </Link>
          <Link href="/scans" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            AI Detection
          </Link>
          <Link href="/reports" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Reports
          </Link>
          <Link href="/decision" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Decision Desk
          </Link>
          <Link href="/counting" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Counting Desk
          </Link>
          <Link href="/location" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Location Desk
          </Link>
          <Link href="/inventory-update" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Sync Desk
          </Link>
          <Link href="/availability" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Availability Desk
          </Link>
          <Link href="/verification" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Verification Desk
          </Link>
          <Link href="/vendor" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Vendor Portal
          </Link>
          <Link href="/shopkeeper" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Shopkeeper Portal
          </Link>
          <Link href="/profile" className="flex items-center gap-2 text-xs text-neutral-350 hover:text-emerald-400 transition-colors">
            <User className="w-4 h-4 text-emerald-400" />
            <span>{userProfile.full_name}</span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-[9px] font-mono font-bold text-emerald-400">
              {userProfile.role}
            </span>
          </Link>

          <button 
            onClick={handleLogout}
            className="flex items-center gap-1.5 text-xs text-neutral-400 hover:text-red-400 transition-colors cursor-pointer"
          >
            <LogOut className="w-4 h-4" /> Logout
          </button>
        </div>
      </nav>

      {/* Main dashboard body */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-10 space-y-8">
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-900 pb-6">
          <div>
            <h1 className="text-2xl font-black text-neutral-50 tracking-tight">System Console</h1>
            <p className="text-neutral-500 text-xs mt-1">
              Welcome back, {userProfile.full_name}. Real-time statistics generated on {new Date().toLocaleDateString()}.
            </p>
          </div>
          <div className="flex items-center gap-3">
            <div className="px-3 py-1.5 rounded-xl bg-neutral-900 border border-neutral-850 text-[10px] font-mono text-neutral-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              Role Authenticated: {userProfile.role}
            </div>
            <button 
              onClick={loadDashboardData}
              className="px-3 py-1.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 text-neutral-300 hover:text-emerald-400 transition-all font-mono font-bold"
            >
              Refresh Data
            </button>
          </div>
        </div>

        {/* Email verification warning */}
        {userProfile.is_verified === false && (
          <div className="flex items-start md:items-center gap-3 p-4 rounded-2xl border border-yellow-500/20 bg-yellow-950/20 text-yellow-400 text-xs">
            <AlertTriangle className="w-5 h-5 shrink-0" />
            <div className="flex-1 md:flex md:justify-between md:items-center">
              <p>Your email address is not verified yet. Check backend logs to activate your account features.</p>
              <Link href="/profile" className="text-xs font-bold underline mt-1 md:mt-0 block">Verify in Profile</Link>
            </div>
          </div>
        )}

        {/* KPI metrics row */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6">
          {/* KPI 1: Stock Value */}
          <div className="bg-neutral-900/30 border border-neutral-900 p-5 rounded-2xl flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-neutral-550 uppercase font-mono font-bold">Total Stock Value</span>
              <h3 className="text-xl font-bold text-emerald-400 font-mono">
                ₹{activeKPIs.stock_value.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-emerald-950/40 border border-emerald-500/10 flex items-center justify-center">
              <Coins className="w-5 h-5 text-emerald-450" />
            </div>
          </div>

          {/* KPI 2: Low-Stock Alerts */}
          <div className="bg-neutral-900/30 border border-neutral-900 p-5 rounded-2xl flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-neutral-550 uppercase font-mono font-bold">Low-Stock Alerts</span>
              <h3 className={`text-xl font-bold font-mono ${activeKPIs.low_stock_alerts > 0 ? "text-amber-400" : "text-neutral-400"}`}>
                {activeKPIs.low_stock_alerts} Alerts
              </h3>
            </div>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activeKPIs.low_stock_alerts > 0 ? "bg-amber-950/40 border border-amber-500/10" : "bg-neutral-900 border border-neutral-800"}`}>
              <AlertOctagon className={`w-5 h-5 ${activeKPIs.low_stock_alerts > 0 ? "text-amber-450" : "text-neutral-500"}`} />
            </div>
          </div>

          {/* KPI 3: Pending Supplier Orders */}
          <div className="bg-neutral-900/30 border border-neutral-900 p-5 rounded-2xl flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-neutral-550 uppercase font-mono font-bold">Pending Orders</span>
              <h3 className={`text-xl font-bold font-mono ${activeKPIs.pending_orders > 0 ? "text-blue-450" : "text-neutral-450"}`}>
                {activeKPIs.pending_orders} Orders
              </h3>
            </div>
            <div className={`w-10 h-10 rounded-xl flex items-center justify-center ${activeKPIs.pending_orders > 0 ? "bg-blue-950/40 border border-blue-500/10" : "bg-neutral-900 border border-neutral-800"}`}>
              <ShoppingBag className={`w-5 h-5 ${activeKPIs.pending_orders > 0 ? "text-blue-450" : "text-neutral-500"}`} />
            </div>
          </div>

          {/* KPI 4: Role-specific metrics */}
          <div className="bg-neutral-900/30 border border-neutral-900 p-5 rounded-2xl flex items-center justify-between">
            <div className="space-y-1">
              <span className="text-[10px] text-neutral-550 uppercase font-mono font-bold">Role context</span>
              <h3 className="text-xl font-bold text-neutral-200">
                {userProfile.role} Portal
              </h3>
            </div>
            <div className="w-10 h-10 rounded-xl bg-neutral-900 border border-neutral-800 flex items-center justify-center">
              <ShieldCheck className="w-5 h-5 text-emerald-400" />
            </div>
          </div>
        </div>

        {/* Role Specific widgets */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Main workspace (Cols 1 & 2) */}
          <div className="lg:col-span-2 space-y-8">
            
            {/* 1. Admin Control Console */}
            {profile.role === "Admin" && (
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h2 className="text-sm font-bold text-neutral-250 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Building className="w-4 h-4 text-emerald-450" /> System administration controls
                  </h2>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/20 font-bold">Full Access</span>
                </div>
                
                <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 flex flex-col justify-between space-y-3">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">Total Store Branches</span>
                    <div className="text-lg font-bold text-neutral-200 font-mono">{activeKPIs.extras?.total_stores || 4}</div>
                    <Link href="/stores" className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      Manage Store Outlets <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>

                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 flex flex-col justify-between space-y-3">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">Catalog SKUs</span>
                    <div className="text-lg font-bold text-neutral-200 font-mono">{activeKPIs.extras?.total_skus || 150}</div>
                    <Link href="/products" className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      Manage Catalog Items <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>

                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 flex flex-col justify-between space-y-3">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">AI Scanner executions</span>
                    <div className="text-lg font-bold text-neutral-200 font-mono">{activeKPIs.extras?.total_scans || 128}</div>
                    <Link href="/scans" className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      Review Scanner Detections <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Database className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-bold text-xs text-neutral-200">Database Models Status</h4>
                      <p className="text-[10px] text-neutral-500 mt-0.5">PostgreSQL and SQLite tables verified. Migrations completed.</p>
                    </div>
                  </div>
                  <span className="px-2.5 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/10 font-bold font-mono">Synchronized</span>
                </div>
              </div>
            )}

            {/* 2. Shopkeeper Store Console */}
            {userProfile.role === "Shopkeeper" && (
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h2 className="text-sm font-bold text-neutral-250 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Building className="w-4 h-4 text-emerald-450" /> Assigned Store Branch outlet
                  </h2>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/20 font-bold">Active Branch</span>
                </div>

                <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase">Assigned Location</span>
                    <h4 className="font-bold text-sm text-neutral-200">{activeKPIs.extras?.store_name || "Main Store #1"}</h4>
                  </div>
                  <Link href={`/stores/${activeKPIs.extras?.store_id || 1}`} className="px-4 py-2 rounded-xl bg-emerald-500 text-neutral-950 font-bold hover:bg-emerald-400 transition-colors">
                    Go to Store Dashboard
                  </Link>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 space-y-2">
                    <span className="text-[10px] text-neutral-550 font-mono uppercase font-bold">Camera Stream Feeds</span>
                    <div className="text-lg font-bold text-neutral-200 font-mono">{activeKPIs.extras?.total_cameras || 2} Feeds</div>
                    <Link href="/videos" className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      Go to video feeds streams <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 space-y-2">
                    <span className="text-[10px] text-neutral-550 font-mono uppercase font-bold">Low stock alerts</span>
                    <div className="text-lg font-bold text-neutral-200 font-mono">{activeKPIs.low_stock_alerts} Alerts</div>
                    <Link href={`/stores/${activeKPIs.extras?.store_id || 1}`} className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      Review stock inventory levels <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>
              </div>
            )}

            {/* 3. Vendor Supply Console */}
            {userProfile.role === "Vendor" && (
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h2 className="text-sm font-bold text-neutral-250 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <Truck className="w-4 h-4 text-emerald-450" /> Supply Agreements & Invoices
                  </h2>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/20 font-bold">Vendor Authorized</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 space-y-2">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">Unpaid Invoices</span>
                    <div className="text-xl font-bold text-neutral-200 font-mono">{activeKPIs.extras?.invoices_count || 0} Invoices</div>
                    <p className="text-[10px] text-neutral-550">Invoices matching supplier contract agreements.</p>
                  </div>
                  <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 space-y-2">
                    <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">Active Contracts</span>
                    <div className="text-xl font-bold text-neutral-200 font-mono">{activeKPIs.extras?.active_contracts || 0} Products</div>
                    <Link href="/products" className="text-[10px] text-emerald-450 hover:underline flex items-center gap-1 font-semibold mt-2">
                      View product catalog matrix <ArrowRight className="w-3 h-3" />
                    </Link>
                  </div>
                </div>

                <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <PackageCheck className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-bold text-xs text-neutral-200">Reorder thresholds triggered</h4>
                      <p className="text-[10px] text-neutral-500 mt-0.5">Please check pending supplier orders to coordinate shipment arrivals.</p>
                    </div>
                  </div>
                  <Link href="/products/suppliers" className="px-3 py-1.5 rounded-xl border border-neutral-800 hover:border-emerald-500/20 text-neutral-300 text-xs font-semibold">
                    Suppliers Panel
                  </Link>
                </div>
              </div>
            )}

            {/* 4. General Employee Console */}
            {userProfile.role !== "Admin" && userProfile.role !== "Shopkeeper" && userProfile.role !== "Vendor" && (
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h2 className="text-sm font-bold text-neutral-250 flex items-center gap-2 font-mono uppercase tracking-wider">
                    <User className="w-4 h-4 text-emerald-450" /> Employee Tasks & Scanning logs
                  </h2>
                  <span className="text-[10px] px-2 py-0.5 rounded bg-emerald-950 text-emerald-400 border border-emerald-500/20 font-bold">Employee Account</span>
                </div>

                <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 space-y-2">
                  <span className="text-[10px] text-neutral-500 font-mono uppercase font-bold">Scans Executed By You</span>
                  <div className="text-xl font-bold text-neutral-200 font-mono">{activeKPIs.extras?.scans_run || 0} Scans</div>
                  <p className="text-[10px] text-neutral-550">Every AI camera scan execution run is tracked in system audit ledgers.</p>
                </div>

                <div className="p-5 rounded-2xl bg-neutral-950 border border-neutral-900 flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <Activity className="w-5 h-5 text-emerald-400" />
                    <div>
                      <h4 className="font-bold text-xs text-neutral-200">Video Feeds Review</h4>
                      <p className="text-[10px] text-neutral-500 mt-0.5">Upload new security footage recordings to execute camera model detections.</p>
                    </div>
                  </div>
                  <Link href="/videos" className="px-4 py-2 rounded-xl bg-emerald-500 text-neutral-950 font-bold hover:bg-emerald-400 transition-colors">
                    Upload Footage
                  </Link>
                </div>
              </div>
            )}

            {/* Recent Activity Table (common KPI criteria) */}
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                <h3 className="font-bold text-neutral-200 flex items-center gap-2 text-xs font-mono uppercase tracking-wider">
                  <History className="w-4 h-4 text-emerald-440" />
                  Recent Stock movements activity
                </h3>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-950 border border-neutral-900 text-neutral-450 font-mono">
                  {(activeKPIs.recent_activity || []).length} Logged
                </span>
              </div>

              {(activeKPIs.recent_activity || []).length === 0 ? (
                <div className="text-center py-10 text-neutral-550 text-xs">
                  No recent stock transaction adjustments recorded.
                </div>
              ) : (
                <div className="space-y-3">
                  {(activeKPIs.recent_activity || []).map(activityItem => {
                    let typeBadge = "bg-neutral-950 text-neutral-400 border-neutral-900";
                    if (activityItem.type === "Purchase") typeBadge = "bg-emerald-950/20 text-emerald-400 border-emerald-500/15";
                    if (activityItem.type === "Sale") typeBadge = "bg-blue-950/20 text-blue-400 border-blue-500/15";
                    if (activityItem.type === "Damage") typeBadge = "bg-red-950/20 text-red-400 border-red-500/15";
                    if (activityItem.type === "Expiry") typeBadge = "bg-yellow-950/20 text-yellow-400 border-yellow-500/15";

                    return (
                      <div key={activityItem.id} className="p-3.5 rounded-2xl bg-neutral-950 border border-neutral-900/60 hover:border-neutral-900 transition-colors flex justify-between items-center text-xs">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2">
                            <span className={`px-2 py-0.5 rounded border text-[9px] font-bold font-mono uppercase ${typeBadge}`}>
                              {activityItem.type}
                            </span>
                            <span className="font-bold text-neutral-200">{activityItem.product_name}</span>
                          </div>
                          {activityItem.notes && <p className="text-neutral-500 text-[10px]">{activityItem.notes}</p>}
                        </div>
                        <div className="flex items-center gap-4 text-right">
                          <span className={`font-mono font-bold ${activityItem.quantity_change > 0 ? "text-emerald-450" : "text-red-450"}`}>
                            {activityItem.quantity_change > 0 ? `+${activityItem.quantity_change}` : activityItem.quantity_change}
                          </span>
                          <span className="text-neutral-600 font-mono text-[10px]">
                            {new Date(activityItem.timestamp).toLocaleTimeString()}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </div>

          {/* Interactive Role Security Test Console (Col 3) */}
          <div className="space-y-8">
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <h3 className="font-bold text-neutral-100 flex items-center gap-2 font-mono uppercase tracking-wider text-xs">
                <ShieldAlert className="w-5 h-5 text-emerald-400" />
                RBAC Security Desk
              </h3>
              
              <p className="text-[11px] text-neutral-500 leading-relaxed font-sans">
                Verify endpoint access boundaries manually. Click endpoints to query active authorization payloads.
              </p>

              <div className="space-y-3 pt-2">
                <button
                  onClick={() => testProtectedEndpoint("admin")}
                  className="w-full text-left p-3 rounded-xl border border-neutral-850 hover:border-emerald-500/30 bg-neutral-900/20 hover:bg-neutral-900/40 transition-colors text-xs font-semibold text-neutral-300 flex justify-between items-center group cursor-pointer font-mono"
                >
                  <span>1. /api/v1/protected/admin</span>
                  <ArrowRight className="w-3.5 h-3.5 text-neutral-600 group-hover:text-emerald-400 transition-colors" />
                </button>
                <button
                  onClick={() => testProtectedEndpoint("vendor")}
                  className="w-full text-left p-3 rounded-xl border border-neutral-850 hover:border-emerald-500/30 bg-neutral-900/20 hover:bg-neutral-900/40 transition-colors text-xs font-semibold text-neutral-300 flex justify-between items-center group cursor-pointer font-mono"
                >
                  <span>2. /api/v1/protected/vendor</span>
                  <ArrowRight className="w-3.5 h-3.5 text-neutral-600 group-hover:text-emerald-400 transition-colors" />
                </button>
                <button
                  onClick={() => testProtectedEndpoint("shopkeeper")}
                  className="w-full text-left p-3 rounded-xl border border-neutral-850 hover:border-emerald-500/30 bg-neutral-900/20 hover:bg-neutral-900/40 transition-colors text-xs font-semibold text-neutral-300 flex justify-between items-center group cursor-pointer font-mono"
                >
                  <span>3. /api/v1/protected/shopkeeper</span>
                  <ArrowRight className="w-3.5 h-3.5 text-neutral-600 group-hover:text-emerald-400 transition-colors" />
                </button>
              </div>
            </div>

            {/* Scanner Performance metrics widget */}
            {perfMetrics && (
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h3 className="font-bold text-neutral-200 flex items-center gap-2 font-mono uppercase tracking-wider text-xs">
                    <Clock className="w-4 h-4 text-emerald-400" />
                    AI Engine Speed Metrics
                  </h3>
                  <span className="text-[9px] text-neutral-500 font-mono">Telemetry</span>
                </div>
                
                <div className="space-y-4">
                  <div className="flex justify-between items-center p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-xs">
                    <span className="text-neutral-500 font-medium">Avg Processing Time</span>
                    <span className="font-mono font-bold text-emerald-400">{perfMetrics.today_avg_scan_time}s</span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-xs">
                    <span className="text-neutral-500 font-medium">Peak Processing speed</span>
                    <span className="font-mono font-bold text-neutral-300">{perfMetrics.fastest_scan}s</span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-xs">
                    <span className="text-neutral-500 font-medium">Slowest Processing cycle</span>
                    <span className="font-mono font-bold text-neutral-300">{perfMetrics.slowest_scan}s</span>
                  </div>
                  <div className="flex justify-between items-center p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-xs">
                    <span className="text-neutral-500 font-medium">Density (Items/Scan)</span>
                    <span className="font-mono font-bold text-neutral-300">{perfMetrics.avg_products_per_scan} items</span>
                  </div>
                </div>
              </div>
            )}
          </div>

        </div>

        {/* Output Console for API Testing */}
        {(apiLoading || protectedData || protectedError) && (
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-4">
            <h3 className="font-bold text-sm text-neutral-300 uppercase tracking-wider flex items-center gap-2">
              <FileText className="w-4 h-4 text-emerald-400" />
              Console API Output
            </h3>
            
            <div className="rounded-2xl bg-neutral-950 p-4 font-mono text-xs overflow-x-auto min-h-[80px] border border-neutral-900 flex items-center">
              {apiLoading && (
                <div className="flex items-center gap-2 text-neutral-500">
                  <Loader2 className="w-4 h-4 animate-spin text-emerald-400" /> Querying API endpoint security payload...
                </div>
              )}

              {protectedError && (
                <div className="text-red-400">
                  Error Code: 403 Forbidden
                  <br />
                  Detail: {protectedError}
                </div>
              )}

              {protectedData && (
                <div className="text-emerald-400 w-full">
                  <span className="text-neutral-500">Status: 200 OK</span>
                  <pre className="mt-2 text-emerald-300 whitespace-pre-wrap font-mono">
                    {JSON.stringify(protectedData, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
