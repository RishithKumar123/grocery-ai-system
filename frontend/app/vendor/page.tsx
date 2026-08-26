"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Building2, 
  Boxes, 
  TrendingUp, 
  Coins, 
  FileDown, 
  Activity, 
  Award, 
  ArrowLeft,
  Loader2,
  Trash2,
  CheckCircle,
  Clock,
  Package,
  Layers,
  HelpCircle
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface SupplierDetails {
  id: number;
  name: string;
  contact_email: string;
  phone: string;
  address: string;
}

interface InventoryDetailItem {
  product_id: number;
  name: string;
  sku: string;
  category: string;
  price: number;
  total_stock: number;
  stock_value: number;
}

interface OrderDetailItem {
  id: number;
  store_name: string;
  created_at: string;
  status: string;
  total_amount: number;
  items_count: number;
}

interface ScanDetailItem {
  product_name: string;
  product_sku: string;
  store_name: string;
  confidence: number;
  scanned_at: string;
}

interface ChartDataItem {
  name: string;
  value: number;
}

interface VendorDashboardData {
  supplier: SupplierDetails;
  metrics: {
    stock_value: number;
    total_stock_units: number;
    revenue: number;
    orders_count: number;
    ai_confidence: number;
  };
  inventory: InventoryDetailItem[];
  orders: OrderDetailItem[];
  recent_scans: ScanDetailItem[];
  charts: {
    categories: ChartDataItem[];
    order_statuses: ChartDataItem[];
    stock_levels: ChartDataItem[];
  };
}

export default function VendorDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<VendorDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [exportLoading, setExportLoading] = useState(false);
  const [activeTab, setActiveTab] = useState<"inventory" | "orders" | "scans">("inventory");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }

    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/vendor/dashboard");
      if (res.ok) {
        const payload = await res.json();
        setData(payload);
      } else {
        // Fallback or deny
        router.push("/dashboard");
      }
    } catch (err) {
      console.error("Failed to load vendor dashboard details", err);
    } finally {
      setLoading(false);
    }
  };

  const handleExportExcel = async () => {
    setExportLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/vendor/export", {
        method: "POST"
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.file_url) {
          window.open(`${payload.file_url}`, "_blank");
        }
      } else {
        alert("Failed to export vendor report.");
      }
    } catch (err) {
      console.error("Export error", err);
      alert("Error occurred during report export.");
    } finally {
      setExportLoading(false);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
      </div>
    );
  }

  // Categories colors map for SVG Donut chart
  const COLORS = ["#10B981", "#3B82F6", "#F59E0B", "#EC4899", "#8B5CF6", "#6B7280"];
  const totalCategoriesCount = data.charts.categories.reduce((acc, curr) => acc + curr.value, 0) || 1;

  // Let's compute SVG Donut arcs
  let accumulatedAngle = 0;
  const donutArcs = data.charts.categories.map((cat, idx) => {
    const percentage = cat.value / totalCategoriesCount;
    const angle = percentage * 360;
    const startAngle = accumulatedAngle;
    accumulatedAngle += angle;

    // Convert angles to polar coordinates for SVG arc paths
    const startRad = ((startAngle - 90) * Math.PI) / 180;
    const endRad = ((accumulatedAngle - 90) * Math.PI) / 180;

    const x1 = 100 + 70 * Math.cos(startRad);
    const y1 = 100 + 70 * Math.sin(startRad);
    const x2 = 100 + 70 * Math.cos(endRad);
    const y2 = 100 + 70 * Math.sin(endRad);

    const largeArcFlag = angle > 180 ? 1 : 0;

    return {
      path: `M ${x1} ${y1} A 70 70 0 ${largeArcFlag} 1 ${x2} ${y2}`,
      color: COLORS[idx % COLORS.length],
      name: cat.name,
      percentage: Math.round(percentage * 100)
    };
  });

  // Calculate max stock for scaling SVG Bar chart
  const maxStockVal = Math.max(...data.charts.stock_levels.map(s => s.value), 10);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col">
      {/* Top Navbar */}
      <nav className="border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-20 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/50 text-neutral-400 hover:text-emerald-400 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <span className="font-bold text-neutral-100 block">Vendor Control Panel</span>
              <span className="text-[10px] text-neutral-500 font-mono block">{data.supplier.name}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={handleExportExcel}
            disabled={exportLoading}
            className="flex items-center gap-1.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 hover:bg-emerald-950/10 px-4 py-2 text-sm font-semibold text-neutral-300 hover:text-emerald-400 transition-all cursor-pointer disabled:opacity-50"
          >
            {exportLoading ? (
              <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />
            ) : (
              <FileDown className="w-4 h-4 text-emerald-400" />
            )}
            {exportLoading ? "Exporting..." : "Export Excel Summary"}
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-8 space-y-8">
        
        {/* Profile Card Header */}
        <div className="glass p-6 rounded-3xl border border-neutral-900 flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
          <div className="space-y-2">
            <h2 className="text-xl font-bold text-neutral-100 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-400" />
              {data.supplier.name}
            </h2>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-x-6 gap-y-1 text-xs text-neutral-400">
              <p>Email: <span className="text-neutral-200 font-mono">{data.supplier.contact_email}</span></p>
              <p>Phone: <span className="text-neutral-200 font-mono">{data.supplier.phone}</span></p>
              <p className="md:col-span-2 mt-1">Warehouse Address: <span className="text-neutral-200">{data.supplier.address}</span></p>
            </div>
          </div>
          <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-xs font-semibold text-emerald-400 shrink-0">
            Fulfillment Vendor Profile Active
          </span>
        </div>

        {/* Core Metrics Summary Grid */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
          {/* Card 1: Supplied Stock Value */}
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <Coins className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Supplied Value</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">${data.metrics.stock_value.toFixed(2)}</span>
            </div>
          </div>

          {/* Card 2: Stock Units */}
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <Boxes className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Total Stock Units</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">{data.metrics.total_stock_units} units</span>
            </div>
          </div>

          {/* Card 3: Fulfill Revenue */}
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <TrendingUp className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Total Revenue</span>
              <span className="text-xl font-black text-emerald-400 mt-1 block">${data.metrics.revenue.toFixed(2)}</span>
            </div>
          </div>

          {/* Card 4: Orders */}
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <Package className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Supply Orders</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">{data.metrics.orders_count} orders</span>
            </div>
          </div>

          {/* Card 5: AI Scanner Accuracy */}
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between col-span-2 md:col-span-1">
            <Award className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">AI Scan Accuracy</span>
              <span className="text-xl font-black text-emerald-400 mt-1 block">{data.metrics.ai_confidence.toFixed(1)}%</span>
            </div>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          
          {/* Category Share Donut Chart */}
          <div className="glass p-6 rounded-3xl border border-neutral-900 flex flex-col items-center space-y-6">
            <h3 className="w-full text-left font-bold text-sm text-neutral-200 uppercase tracking-wider">
              Category Distribution of Products
            </h3>
            
            <div className="flex flex-col sm:flex-row items-center justify-around w-full gap-6">
              {/* SVG Donut render */}
              <div className="relative w-44 h-44">
                <svg className="w-full h-full" viewBox="0 0 200 200">
                  {/* Outer circle track */}
                  <circle cx="100" cy="100" r="70" fill="transparent" stroke="#171717" strokeWidth="20" />
                  
                  {/* Sector paths */}
                  {donutArcs.map((arc, index) => (
                    <path
                      key={index}
                      d={arc.path}
                      fill="transparent"
                      stroke={arc.color}
                      strokeWidth="20"
                    />
                  ))}
                  
                  {/* Inside hole details */}
                  <circle cx="100" cy="100" r="58" fill="#0A0A0A" />
                </svg>
                <div className="absolute inset-0 flex flex-col items-center justify-center text-center">
                  <span className="text-[10px] text-neutral-500 uppercase tracking-wider font-semibold">SKUs</span>
                  <span className="text-lg font-black text-neutral-100">{data.inventory.length} Categories</span>
                </div>
              </div>

              {/* Legend map */}
              <div className="space-y-2">
                {donutArcs.map((arc, index) => (
                  <div key={index} className="flex items-center gap-2 text-xs">
                    <div className="w-3 h-3 rounded" style={{ backgroundColor: arc.color }} />
                    <span className="text-neutral-300 font-medium">{arc.name}</span>
                    <span className="text-neutral-500 font-mono">({arc.percentage}%)</span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Product Stock Levels Bar Chart */}
          <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-6">
            <h3 className="font-bold text-sm text-neutral-200 uppercase tracking-wider">
              Stock Levels by Supplied Product
            </h3>

            <div className="space-y-4 pt-2">
              {data.charts.stock_levels.map((item, index) => {
                const percentage = Math.round((item.value / maxStockVal) * 100);
                return (
                  <div key={index} className="space-y-1.5">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-neutral-300 truncate max-w-[200px]">{item.name}</span>
                      <span className="text-neutral-400 font-mono font-bold">{item.value} units</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-neutral-950 overflow-hidden border border-neutral-900">
                      <div 
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500" 
                        style={{ width: `${percentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

        </div>

        {/* Tab worksheets details segment */}
        <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-6">
          <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
            <div className="flex gap-2">
              <button
                onClick={() => setActiveTab("inventory")}
                className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === "inventory"
                    ? "bg-emerald-500 text-neutral-950 shadow"
                    : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
                }`}
              >
                Supplied Catalog
              </button>
              <button
                onClick={() => setActiveTab("orders")}
                className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === "orders"
                    ? "bg-emerald-500 text-neutral-950 shadow"
                    : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
                }`}
              >
                Supply Orders ({data.orders.length})
              </button>
              <button
                onClick={() => setActiveTab("scans")}
                className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                  activeTab === "scans"
                    ? "bg-emerald-500 text-neutral-950 shadow"
                    : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
                }`}
              >
                Recent AI Scans ({data.recent_scans.length})
              </button>
            </div>
            <span className="text-[10px] text-neutral-500 font-mono uppercase">System Grid</span>
          </div>

          {/* TAB Content 1: Catalog */}
          {activeTab === "inventory" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-400 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="pb-3">Product Name</th>
                    <th className="pb-3">SKU</th>
                    <th className="pb-3">Category</th>
                    <th className="pb-3 text-center">FOB Price</th>
                    <th className="pb-3 text-center">Total Stock</th>
                    <th className="pb-3 text-right">Stock Value</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                  {data.inventory.map((item, index) => (
                    <tr key={index} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="py-3.5 font-bold text-neutral-200">{item.name}</td>
                      <td className="py-3.5 font-mono text-neutral-450">{item.sku}</td>
                      <td className="py-3.5">
                        <span className="px-2 py-0.5 rounded-full bg-neutral-900 border border-neutral-850 text-neutral-400 font-medium">
                          {item.category}
                        </span>
                      </td>
                      <td className="py-3.5 text-center font-bold font-mono text-neutral-200">
                        ${item.price.toFixed(2)}
                      </td>
                      <td className="py-3.5 text-center font-mono font-bold text-emerald-400">
                        {item.total_stock} units
                      </td>
                      <td className="py-3.5 text-right font-mono text-neutral-200 font-bold">
                        ${item.stock_value.toFixed(2)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB Content 2: Orders */}
          {activeTab === "orders" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-400 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="pb-3">Order ID</th>
                    <th className="pb-3">Destination Store</th>
                    <th className="pb-3">Order Date</th>
                    <th className="pb-3 text-center">Fulfillment Status</th>
                    <th className="pb-3 text-right">Order Amount</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                  {data.orders.map((order, index) => {
                    let badgeColor = "bg-neutral-900 text-neutral-400 border-neutral-800";
                    if (order.status === "Delivered") {
                      badgeColor = "bg-emerald-950/20 text-emerald-400 border-emerald-500/15";
                    } else if (order.status === "Pending") {
                      badgeColor = "bg-yellow-950/20 text-yellow-400 border-yellow-500/15";
                    }

                    return (
                      <tr key={index} className="hover:bg-neutral-900/10 transition-colors">
                        <td className="py-3.5 font-mono text-neutral-200 font-bold">#ORD-{order.id}</td>
                        <td className="py-3.5 font-bold text-neutral-300">{order.store_name}</td>
                        <td className="py-3.5 font-mono text-neutral-400">
                          {new Date(order.created_at).toLocaleDateString()}
                        </td>
                        <td className="py-3.5 text-center">
                          <span className={`px-2.5 py-0.5 rounded-full border text-[10px] font-bold ${badgeColor}`}>
                            {order.status}
                          </span>
                        </td>
                        <td className="py-3.5 text-right font-mono text-neutral-100 font-bold">
                          ${order.total_amount.toFixed(2)}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB Content 3: Scans Feed */}
          {activeTab === "scans" && (
            <div className="space-y-3">
              {data.recent_scans.length === 0 ? (
                <div className="text-center py-10 text-neutral-500 text-xs">
                  No scan logs matching supplied items detected recently.
                </div>
              ) : (
                data.recent_scans.map((scan, index) => (
                  <div key={index} className="p-3.5 rounded-2xl bg-neutral-950 border border-neutral-900/60 flex flex-col sm:flex-row justify-between sm:items-center text-xs gap-3">
                    <div className="space-y-1">
                      <div className="font-bold text-neutral-200">{scan.product_name}</div>
                      <div className="text-[10px] text-neutral-500 font-mono">
                        Location Branch: {scan.store_name} | SKU Code: {scan.product_sku}
                      </div>
                    </div>
                    <div className="flex items-center gap-4 shrink-0 font-mono text-[10px] sm:text-right sm:flex-col sm:items-end">
                      <span className="px-2 py-0.5 rounded bg-emerald-950/20 text-emerald-400 border border-emerald-500/10 font-bold">
                        AI Conf: {Math.round(scan.confidence * 100)}%
                      </span>
                      <span className="text-neutral-600">
                        {new Date(scan.scanned_at).toLocaleString()}
                      </span>
                    </div>
                  </div>
                ))
              )}
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
