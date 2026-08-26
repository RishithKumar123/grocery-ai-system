"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Building2, 
  Boxes, 
  UploadCloud, 
  FileDown, 
  AlertTriangle, 
  Bell, 
  History,
  FileSpreadsheet,
  CheckCircle,
  Clock,
  ArrowLeft,
  Loader2,
  Trash2,
  Eye,
  Info
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";
import { getApiBaseUrl } from "../../lib/config";

interface StoreInfo {
  id: number;
  name: string;
  location: string;
}

interface InventoryItem {
  id: number;
  name: string;
  sku: string;
  quantity: number;
  location_bin: string;
  status: string;
  expiry_date: string | null;
  updated_at: string;
}

interface AlertItem {
  type: string;
  severity: string;
  message: string;
}

interface ScanItem {
  id: number;
  status: string;
  created_at: string;
  detections_count: number;
}

interface ReportItem {
  id: number;
  type: string;
  file_url: string;
  created_at: string;
}

interface NotificationItem {
  id: number;
  title: string;
  message: string;
  type: string;
  created_at: string;
}

interface ShopkeeperDashboardData {
  store: StoreInfo;
  today_scans: {
    count: number;
    success_count: number;
    failed_count: number;
  };
  inventory: InventoryItem[];
  alerts: AlertItem[];
  scans_history: ScanItem[];
  reports: ReportItem[];
  notifications: NotificationItem[];
}

export default function ShopkeeperDashboardPage() {
  const router = useRouter();
  const [data, setData] = useState<ShopkeeperDashboardData | null>(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"inventory" | "scans" | "reports">("inventory");

  // Video Upload States
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const fileInputRef = useRef<HTMLInputElement>(null);

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
    try {
      const res = await fetchWithAuth("/api/v1/shopkeeper/dashboard");
      if (res.ok) {
        const payload = await res.json();
        setData(payload);
      } else {
        router.push("/dashboard");
      }
    } catch (err) {
      console.error("Failed to load shopkeeper dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleMarkRead = async (notificationId: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/shopkeeper/notifications/${notificationId}/read`, {
        method: "POST"
      });
      if (res.ok) {
        // Filter out read notification locally to prevent full reload flicker
        if (data) {
          setData({
            ...data,
            notifications: data.notifications.filter(n => n.id !== notificationId)
          });
        }
      }
    } catch (err) {
      console.error("Failed to mark notification read", err);
    }
  };

  const handleVideoUploadClick = () => {
    fileInputRef.current?.click();
  };

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setUploading(true);
    setUploadProgress(10);

    const CHUNK_SIZE = 5 * 1024 * 1024; // 5MB chunks
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const uploadId = `upload_${Date.now()}`;
    const cleanFileName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");

    try {
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("chunk", chunk);
        formData.append("chunkIndex", chunkIndex.toString());
        formData.append("totalChunks", totalChunks.toString());
        formData.append("uploadId", uploadId);
        formData.append("filename", cleanFileName);

        const token = getAccessToken();
        const headers: Record<string, string> = {};
        if (token) {
          headers["Authorization"] = `Bearer ${token}`;
        }

        const res = await fetch(`/api/v1/videos/upload/chunk?upload_id=${uploadId}&chunk_index=${chunkIndex}&total_chunks=${totalChunks}`, {
          method: "POST",
          headers,
          body: formData
        });

        if (!res.ok) {
          throw new Error(`Failed chunk: ${chunkIndex}`);
        }

        const progressPercent = Math.round(((chunkIndex + 1) / totalChunks) * 80) + 10;
        setUploadProgress(progressPercent);
      }

      // Upload complete request
      const completeRes = await fetch("/api/v1/videos/upload/complete", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(getAccessToken() ? { "Authorization": `Bearer ${getAccessToken()}` } : {})
        },
        body: JSON.stringify({
          upload_id: uploadId,
          filename: cleanFileName,
          store_id: data?.store.id || 1,
          camera_name: "Store Camera 1"
        })
      });

      if (completeRes.ok) {
        setUploadProgress(100);
        setTimeout(() => {
          setUploading(false);
          setUploadProgress(0);
          loadDashboardData();
          alert("Video upload successful! Shelf scanning started.");
        }, 1000);
      } else {
        throw new Error("Complete upload trigger failed.");
      }

    } catch (err) {
      console.error(err);
      alert("An error occurred during video upload station processing.");
      setUploading(false);
      setUploadProgress(0);
    }
  };

  const triggerBranchReport = async () => {
    if (!data) return;
    try {
      const res = await fetchWithAuth(`/api/v1/reports/store/${data.store.id}`, {
        method: "POST"
      });
      if (res.ok) {
        const payload = await res.json();
        if (payload.file_url) {
          window.open(`${payload.file_url}`, "_blank");
          loadDashboardData();
        }
      }
    } catch (err) {
      console.error("Report generation failed", err);
    }
  };

  if (loading || !data) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
      </div>
    );
  }

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
              <span className="font-bold text-neutral-100 block">{data.store.name}</span>
              <span className="text-[10px] text-neutral-500 font-mono block">Location: {data.store.location}</span>
            </div>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <button
            onClick={triggerBranchReport}
            className="flex items-center gap-1.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 hover:bg-emerald-950/10 px-4 py-2 text-sm font-semibold text-neutral-300 hover:text-emerald-400 transition-all cursor-pointer"
          >
            <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
            Generate Excel Report
          </button>
        </div>
      </nav>

      {/* Main Container */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-8 space-y-8">

        {/* Dashboard Metric Overview Rows */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-6">
          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <History className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Today's Scans</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">{data.today_scans.count} Scans</span>
            </div>
          </div>

          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <Boxes className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Total Inventory</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">{data.inventory.length} SKUs</span>
            </div>
          </div>

          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <AlertTriangle className="w-6 h-6 text-yellow-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">Active Alerts</span>
              <span className="text-xl font-black text-neutral-100 mt-1 block">{data.alerts.length} Warnings</span>
            </div>
          </div>

          <div className="glass p-5 rounded-2xl text-center flex flex-col justify-between">
            <Bell className="w-6 h-6 text-emerald-400 mx-auto" />
            <div>
              <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-3 block">New Notices</span>
              <span className="text-xl font-black text-emerald-400 mt-1 block">{data.notifications.length} Unread</span>
            </div>
          </div>
        </div>

        {/* Upload Station and Live Alerts section */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
          
          {/* Upload Video Station card */}
          <div className="glass p-6 rounded-3xl border border-neutral-900 flex flex-col justify-between space-y-6 md:col-span-1">
            <div>
              <h3 className="font-bold text-sm text-neutral-200 uppercase tracking-wider mb-2">
                Shelf Video Scanner
              </h3>
              <p className="text-xs text-neutral-400">
                Upload raw shelf MP4 video records to start auto-counting, OCR parameter alignment, and matching engine checks.
              </p>
            </div>

            <div 
              onClick={!uploading ? handleVideoUploadClick : undefined}
              className={`border-2 border-dashed rounded-2xl p-6 text-center flex flex-col items-center justify-center gap-3 transition-all cursor-pointer ${
                uploading 
                  ? "border-emerald-500/20 bg-emerald-950/5 cursor-not-allowed" 
                  : "border-neutral-800 hover:border-emerald-500/30 hover:bg-neutral-900/20"
              }`}
            >
              <input 
                type="file" 
                ref={fileInputRef} 
                onChange={handleFileChange} 
                accept="video/*" 
                className="hidden" 
              />
              
              {uploading ? (
                <>
                  <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                  <div className="w-full space-y-1">
                    <div className="text-xs text-neutral-300 font-semibold">Uploading: {uploadProgress}%</div>
                    <div className="h-1.5 w-full bg-neutral-950 rounded-full overflow-hidden border border-neutral-900">
                      <div className="h-full bg-emerald-500 transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <UploadCloud className="w-8 h-8 text-neutral-500 hover:text-emerald-400 transition-colors" />
                  <div className="text-xs text-neutral-400">
                    <span className="text-emerald-400 font-semibold underline">Select file</span> or drop MP4 here
                  </div>
                </>
              )}
            </div>
          </div>

          {/* Active Alerts List */}
          <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-4 md:col-span-2 max-h-[300px] overflow-y-auto">
            <h3 className="font-bold text-sm text-neutral-200 uppercase tracking-wider">
              Real-time Shelf alerts ({data.alerts.length})
            </h3>
            
            {data.alerts.length === 0 ? (
              <div className="text-center py-12 text-neutral-555 text-xs">
                Perfect! All stock configurations are normal with no warning reports.
              </div>
            ) : (
              <div className="space-y-2">
                {data.alerts.map((alert, index) => {
                  let alertTheme = "bg-yellow-950/20 border-yellow-500/20 text-yellow-400";
                  if (alert.severity === "High") {
                    alertTheme = "bg-red-950/20 border-red-500/20 text-red-400";
                  }
                  return (
                    <div key={index} className={`p-3 rounded-xl border flex items-start gap-2.5 text-xs ${alertTheme}`}>
                      <AlertTriangle className="w-4 h-4 shrink-0 mt-0.5" />
                      <div>
                        <span className="font-bold uppercase text-[9px] block mb-0.5">{alert.type} Alert</span>
                        <p className="text-neutral-200 leading-relaxed">{alert.message}</p>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>

        </div>

        {/* Live Notices / Notifications Center */}
        {data.notifications.length > 0 && (
          <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-4">
            <h3 className="font-bold text-sm text-neutral-200 uppercase tracking-wider flex items-center gap-2">
              <Bell className="w-4 h-4 text-emerald-400" />
              Store Notifications
            </h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.notifications.map((notif, index) => (
                <div key={index} className="p-3.5 rounded-2xl bg-neutral-950 border border-neutral-900/60 flex justify-between items-start gap-4">
                  <div className="space-y-1 text-xs">
                    <span className="font-bold text-neutral-200 block">{notif.title}</span>
                    <p className="text-neutral-400 leading-relaxed">{notif.message}</p>
                  </div>
                  <button
                    onClick={() => handleMarkRead(notif.id)}
                    className="p-1 rounded bg-neutral-900 border border-neutral-800 hover:border-emerald-500/40 text-neutral-500 hover:text-emerald-400 transition-colors cursor-pointer shrink-0"
                    title="Mark as read"
                  >
                    <CheckCircle className="w-3.5 h-3.5" />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Tab worksheets details segment */}
        <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-6">
          <div className="flex gap-2 border-b border-neutral-900 pb-4">
            <button
              onClick={() => setActiveTab("inventory")}
              className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "inventory"
                  ? "bg-emerald-500 text-neutral-950 shadow"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
              }`}
            >
              Current Inventory catalog
            </button>
            <button
              onClick={() => setActiveTab("scans")}
              className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "scans"
                  ? "bg-emerald-500 text-neutral-950 shadow"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
              }`}
            >
              Scans History logs
            </button>
            <button
              onClick={() => setActiveTab("reports")}
              className={`py-1.5 px-3 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                activeTab === "reports"
                  ? "bg-emerald-500 text-neutral-950 shadow"
                  : "text-neutral-400 hover:text-neutral-200 hover:bg-neutral-900/40"
              }`}
            >
              Excel Reports index
            </button>
          </div>

          {/* TAB 1: Inventory catalog */}
          {activeTab === "inventory" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-400 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="pb-3">Product Name</th>
                    <th className="pb-3">SKU</th>
                    <th className="pb-3">Shelf Bin</th>
                    <th className="pb-3 text-center">Stock Qty</th>
                    <th className="pb-3">Expiry Date</th>
                    <th className="pb-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                  {data.inventory.map((item, index) => {
                    let textClass = "text-neutral-300";
                    if (item.quantity === 0) {
                      textClass = "text-red-400 font-semibold";
                    } else if (item.quantity <= 5) {
                      textClass = "text-yellow-400 font-semibold";
                    }
                    return (
                      <tr key={index} className="hover:bg-neutral-900/10 transition-colors">
                        <td className="py-3.5 font-bold text-neutral-200">{item.name}</td>
                        <td className="py-3.5 font-mono text-neutral-450">{item.sku}</td>
                        <td className="py-3.5">{item.location_bin}</td>
                        <td className={`py-3.5 text-center font-mono font-bold ${textClass}`}>
                          {item.quantity} units
                        </td>
                        <td className="py-3.5 font-mono text-neutral-400">
                          {item.expiry_date || "N/A"}
                        </td>
                        <td className="py-3.5 text-right font-medium">
                          <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold ${
                            item.status === "In Stock" 
                              ? "bg-emerald-950/20 text-emerald-400 border border-emerald-500/10" 
                              : "bg-red-950/20 text-red-400 border border-red-500/10"
                          }`}>
                            {item.status}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 2: Scans History */}
          {activeTab === "scans" && (
            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-400 font-semibold uppercase tracking-wider text-[10px]">
                    <th className="pb-3">Scan ID</th>
                    <th className="pb-3">Detections count</th>
                    <th className="pb-3 text-center">Execution status</th>
                    <th className="pb-3 text-right">Scanned Date</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                  {data.scans_history.map((scan, index) => (
                    <tr key={index} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="py-3.5 font-mono text-neutral-200 font-bold">#SCN-{scan.id}</td>
                      <td className="py-3.5 font-mono font-bold text-neutral-300">
                        {scan.detections_count} Items
                      </td>
                      <td className="py-3.5 text-center">
                        <span className={`px-2 py-0.5 rounded text-[9px] font-bold ${
                          scan.status === "Completed" || scan.status === "Success"
                            ? "bg-emerald-500/10 text-emerald-400"
                            : "bg-yellow-500/10 text-yellow-450"
                        }`}>
                          {scan.status}
                        </span>
                      </td>
                      <td className="py-3.5 text-right font-mono text-neutral-400">
                        {new Date(scan.created_at).toLocaleString()}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}

          {/* TAB 3: Reports catalog */}
          {activeTab === "reports" && (
            <div className="space-y-3">
              {data.reports.length === 0 ? (
                <div className="text-center py-10 text-neutral-500 text-xs">
                  No Excel reports available yet. Click "Generate Excel Report" in the header to compile one.
                </div>
              ) : (
                data.reports.map((report, index) => (
                  <div key={index} className="p-3.5 rounded-2xl bg-neutral-950 border border-neutral-900/60 flex justify-between items-center text-xs">
                    <div className="flex items-center gap-3">
                      <div className="w-8 h-8 rounded-lg bg-emerald-500/5 border border-emerald-500/10 flex items-center justify-center">
                        <FileSpreadsheet className="w-4 h-4 text-emerald-400" />
                      </div>
                      <div>
                        <div className="font-bold text-neutral-200">{report.type} Status Report</div>
                        <div className="text-[10px] text-neutral-500 font-mono">
                          Generated: {new Date(report.created_at).toLocaleString()}
                        </div>
                      </div>
                    </div>
                    <button
                      onClick={() => window.open(`${report.file_url}`, "_blank")}
                      className="flex items-center gap-1 text-[10px] font-bold rounded-lg border border-neutral-800 hover:border-emerald-500/30 hover:bg-emerald-950/10 px-3 py-1.5 text-neutral-300 hover:text-emerald-400 transition-all cursor-pointer"
                    >
                      <FileDown className="w-3 h-3" /> Download
                    </button>
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
