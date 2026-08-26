"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Building2, 
  ArrowLeft, 
  FileText, 
  FileDown, 
  Loader2, 
  Cpu, 
  User, 
  LogOut, 
  TrendingUp, 
  Package, 
  Truck, 
  Percent, 
  Layers, 
  Award, 
  Coins 
} from "lucide-react";
import { getAccessToken, getUserProfile, clearTokens, fetchWithAuth } from "../../lib/auth";
import { useToast } from "../../components/ui/toast";

interface Store {
  id: number;
  name: string;
  location: string | null;
}

export default function ReportsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [profile, setProfile] = useState<any>(null);
  const [stores, setStores] = useState<Store[]>([]);
  const [selectedStoreId, setSelectedStoreId] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [downloadingReport, setDownloadingReport] = useState<string | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    const user = getUserProfile();

    if (!token || !user) {
      clearTokens();
      router.push("/login");
      return;
    }

    setProfile(user);
    loadStores();
  }, [router]);

  const loadStores = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/stores");
      if (res.ok) {
        const data = await res.json();
        setStores(data);
        if (data.length > 0) {
          setSelectedStoreId(data[0].id.toString());
        }
      }
    } catch (err) {
      console.error("Failed to load stores list", err);
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

  const handleDownload = async (reportType: string, format: "pdf" | "excel") => {
    if (!selectedStoreId) {
      alert("Please select a store branch to generate the report.");
      return;
    }

    const actionKey = `${reportType}-${format}`;
    setDownloadingReport(actionKey);

    try {
      const res = await fetchWithAuth("/api/v1/reports/operational", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: parseInt(selectedStoreId),
          report_type: reportType,
          format: format
        })
      });

      if (res.ok) {
        const data = await res.json();
        if (data.file_url) {
          window.open(`${data.file_url}`, "_blank");
          toast({ title: "Report Downloaded", description: `Exported ${reportType} report successfully.`, type: "success" });
        }
      } else {
        const err = await res.json().catch(() => ({}));
        alert(err.detail || `Failed to export operational ${reportType} report.`);
      }
    } catch (err) {
      console.error(err);
      alert("An unexpected error occurred during export.");
    } finally {
      setDownloadingReport(null);
    }
  };

  const reportsList = [
    {
      id: "stock",
      title: "Current Stock Report",
      description: "Inventory levels, location mappings, safety limits, and status flags across shelves.",
      icon: <Package className="w-6 h-6 text-emerald-450" />,
    },
    {
      id: "purchase",
      title: "Purchase Replenishments",
      description: "Chronological ledger tracking purchase arrivals, quantities received, and log notes.",
      icon: <TrendingUp className="w-6 h-6 text-blue-450" />,
    },
    {
      id: "sales",
      title: "Sales Outflows",
      description: "Chronological ledger tracking items sold, item prices, and estimated revenue totals.",
      icon: <Coins className="w-6 h-6 text-yellow-450" />,
    },
    {
      id: "supplier",
      title: "Supplier Directory",
      description: "Supplier contacts, payment agreements, active states, and localized region tax IDs.",
      icon: <Truck className="w-6 h-6 text-indigo-450" />,
    },
    {
      id: "category",
      title: "Valuation by Category",
      description: "Aggregated stock counts and financial assets classified by product categories.",
      icon: <Layers className="w-6 h-6 text-pink-450" />,
    },
    {
      id: "brand",
      title: "Valuation by Brand",
      description: "Aggregated stock counts and financial assets classified by product brands.",
      icon: <Award className="w-6 h-6 text-purple-450" />,
    },
    {
      id: "valuation",
      title: "Inventory Valuation",
      description: "Inventory sheet detailing margin spreads, cost metrics, and market valuation assets.",
      icon: <Percent className="w-6 h-6 text-teal-450" />,
    }
  ];

  if (loading || !profile) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

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
          <Link href="/reports" className="text-xs font-semibold text-emerald-400 transition-colors">
            Reports
          </Link>
          <Link href="/vendor" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Vendor Portal
          </Link>
          <Link href="/shopkeeper" className="text-xs font-semibold text-neutral-400 hover:text-emerald-400 transition-colors">
            Shopkeeper Portal
          </Link>
          <Link href="/profile" className="flex items-center gap-2 text-xs text-neutral-355 hover:text-emerald-400 transition-colors">
            <User className="w-4 h-4 text-emerald-400" />
            <span>{profile.full_name}</span>
            <span className="px-2 py-0.5 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-[9px] font-mono font-bold text-emerald-400">
              {profile.role}
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

      {/* Main Content */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-4 py-12 space-y-8">
        
        {/* Back Link & Title */}
        <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-neutral-900 pb-6">
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/50 text-neutral-400 hover:text-emerald-400 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <h2 className="text-2xl font-black text-neutral-50 tracking-tight">Operational Reports</h2>
              <p className="text-neutral-500 text-xs mt-0.5">Select store branch to export operational spreadsheets and PDF files</p>
            </div>
          </div>
          
          {/* Store Selector */}
          <div className="flex items-center gap-3 shrink-0">
            <Building2 className="w-4 h-4 text-emerald-400" />
            <select
              value={selectedStoreId}
              onChange={(e) => setSelectedStoreId(e.target.value)}
              className="px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-900 text-neutral-200 text-xs focus:ring-1 focus:ring-emerald-500 focus:outline-none"
            >
              <option value="">Select Branch...</option>
              {stores.map((s) => (
                <option key={s.id} value={s.id}>{s.name} ({s.location || "No coords"})</option>
              ))}
            </select>
          </div>
        </div>

        {/* Reports Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {reportsList.map((report) => {
            const isPdfLoading = downloadingReport === `${report.id}-pdf`;
            const isExcelLoading = downloadingReport === `${report.id}-excel`;

            return (
              <div key={report.id} className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6 flex flex-col justify-between hover:border-neutral-850 hover:bg-neutral-900/30 transition-all">
                <div className="space-y-3">
                  <div className="flex items-center gap-3">
                    <div className="p-3 rounded-2xl bg-neutral-950 border border-neutral-900">
                      {report.icon}
                    </div>
                    <h3 className="font-bold text-neutral-200 text-sm">{report.title}</h3>
                  </div>
                  <p className="text-neutral-500 leading-relaxed text-[11px]">{report.description}</p>
                </div>

                <div className="pt-4 border-t border-neutral-900/60 grid grid-cols-2 gap-3">
                  <button
                    onClick={() => handleDownload(report.id, "pdf")}
                    disabled={downloadingReport !== null}
                    className="flex items-center justify-center gap-2 py-2.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 text-neutral-350 hover:text-emerald-400 font-semibold hover:bg-emerald-950/10 transition-all cursor-pointer disabled:opacity-50 text-[11px]"
                  >
                    {isPdfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileText className="w-3.5 h-3.5 text-emerald-450" />} PDF Export
                  </button>

                  <button
                    onClick={() => handleDownload(report.id, "excel")}
                    disabled={downloadingReport !== null}
                    className="flex items-center justify-center gap-2 py-2.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 text-neutral-350 hover:text-emerald-400 font-semibold hover:bg-emerald-950/10 transition-all cursor-pointer disabled:opacity-50 text-[11px]"
                  >
                    {isExcelLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <FileDown className="w-3.5 h-3.5 text-emerald-450" />} Excel Export
                  </button>
                </div>
              </div>
            );
          })}
        </div>

      </main>
    </div>
  );
}
