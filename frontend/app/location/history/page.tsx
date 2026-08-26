"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Clock, 
  RotateCw, 
  Loader2,
  TrendingDown
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface HistoryLog {
  id: number;
  product_name: string;
  sku: string;
  previous_shelf_name: string;
  new_shelf_name: string;
  moved_at: string;
}

export default function LocationHistoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [logs, setLogs] = useState<HistoryLog[]>([]);

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
      const res = await fetchWithAuth("/api/v1/location/history");
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
              <Link href="/location" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Location History</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Timeline audit logs tracking stock physical movements, relocations, and shelf placements.
            </p>
          </div>

          <button 
            onClick={loadHistoryLogs}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Audit Logs
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Scanning movement history database...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">Transaction ID</th>
                  <th className="px-6 py-4">Product Mapped</th>
                  <th className="px-6 py-4 text-center">Previous Shelf Location</th>
                  <th className="px-6 py-4 text-center">New Shelf Location</th>
                  <th className="px-6 py-4 text-right">Movement Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-350 font-mono">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={5} className="text-center py-20 text-neutral-500 font-mono text-xs">
                      No stock physical movement logs recorded.
                    </td>
                  </tr>
                ) : (
                  logs.map(log => (
                    <tr key={log.id} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="px-6 py-4 text-neutral-400">
                        #{log.id}
                      </td>
                      <td className="px-6 py-4 font-sans font-bold text-neutral-200">
                        {log.product_name}
                        <span className="block text-[9px] text-neutral-500 font-mono mt-0.5">SKU: {log.sku}</span>
                      </td>
                      <td className="px-6 py-4 text-center text-neutral-450">
                        {log.previous_shelf_name}
                      </td>
                      <td className="px-6 py-4 text-center text-neutral-100 font-bold">
                        {log.new_shelf_name}
                      </td>
                      <td className="px-6 py-4 text-right text-neutral-450">
                        {new Date(log.moved_at).toLocaleString()}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
}
