"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  History, 
  RotateCw, 
  Loader2
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface UpdateLog {
  id: number;
  product_name: string;
  sku: string;
  previous_quantity: number;
  new_quantity: number;
  variance: number;
  status: string;
  confidence: number;
  created_at: string;
}

export default function UpdateHistoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<UpdateLog[]>([]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadHistoryLogs();
  }, [router]);

  const loadHistoryLogs = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/history?store_id=1");
      if (res.ok) {
        setLogs(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/inventory-update" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Update History</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Timeline log auditing applied, rejected, or rolled back stock updates.
            </p>
          </div>

          <button 
            onClick={loadHistoryLogs}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Logs
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading update history ledger logs...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">Sync ID</th>
                  <th className="px-6 py-4">Product Catalog Item</th>
                  <th className="px-6 py-4 text-center">Previous Qty</th>
                  <th className="px-6 py-4 text-center">New Qty</th>
                  <th className="px-6 py-4 text-center">Variance</th>
                  <th className="px-6 py-4 text-center">Status</th>
                  <th className="px-6 py-4 text-right">Applied Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300 font-mono">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="text-center py-20 text-neutral-550 font-mono text-xs">
                      No stock sync updates recorded.
                    </td>
                  </tr>
                ) : (
                  logs.map(log => {
                    let statusColor = "bg-neutral-900 text-neutral-450 border-neutral-800";
                    if (log.status === "Applied") statusColor = "bg-emerald-950/20 text-emerald-400 border-emerald-500/20";
                    if (log.status === "Pending") statusColor = "bg-yellow-950/20 text-yellow-400 border-yellow-500/20";
                    if (log.status === "Rejected") statusColor = "bg-red-950/20 text-red-400 border-red-500/20";
                    if (log.status === "Rolled Back") statusColor = "bg-blue-950/20 text-blue-400 border-blue-500/20";

                    return (
                      <tr key={log.id} className="hover:bg-neutral-900/10 transition-colors">
                        <td className="px-6 py-4 text-neutral-450">
                          #{log.id}
                        </td>
                        <td className="px-6 py-4 font-sans font-bold text-neutral-200">
                          {log.product_name}
                          <span className="block text-[9px] text-neutral-550 font-mono mt-0.5">SKU: {log.sku} - Confidence: {Math.round(log.confidence * 100)}%</span>
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-450">
                          {log.previous_quantity} items
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-100 font-bold">
                          {log.new_quantity} items
                        </td>
                        <td className="px-6 py-4 text-center font-bold">
                          <span className={log.variance === 0 ? 'text-neutral-400' : log.variance >= 0 ? 'text-emerald-400' : 'text-red-400'}>
                            {log.variance === 0 ? '0' : log.variance >= 0 ? `+${log.variance}` : log.variance}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border ${statusColor}`}>
                            {log.status}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-right text-neutral-450">
                          {new Date(log.created_at).toLocaleString()}
                        </td>
                      </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
}
