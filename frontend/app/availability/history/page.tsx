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

interface HistoryLog {
  id: number;
  product_id?: number;
  product_name?: string;
  store_id: number;
  search_query: string;
  search_method: string;
  status: string;
  reason?: string;
  created_at: string;
}

export default function AvailabilityHistoryPage() {
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
    loadHistory();
  }, [router]);

  const loadHistory = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/availability/history?store_id=1");
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
              <Link href="/availability" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Availability Search History</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Audits historical user availability checks, search methods, and YES/NO verification outcomes.
            </p>
          </div>

          <button 
            onClick={loadHistory}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh History Logs
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading search history logs...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse font-mono">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] bg-neutral-950/40">
                  <th className="px-6 py-4">Search Query</th>
                  <th className="px-6 py-4 text-center">Search Method</th>
                  <th className="px-6 py-4 font-sans font-bold">Catalog Product</th>
                  <th className="px-6 py-4 text-center">Status</th>
                  <th className="px-6 py-4">Reason / Notes</th>
                  <th className="px-6 py-4 text-right">Timestamp</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-neutral-550 font-mono text-xs">
                      No availability search history logged yet.
                    </td>
                  </tr>
                ) : (
                  logs.map(log => (
                    <tr key={log.id} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="px-6 py-4 font-bold text-neutral-100">{log.search_query}</td>
                      <td className="px-6 py-4 text-center text-neutral-400">{log.search_method}</td>
                      <td className="px-6 py-4 font-sans text-neutral-200">{log.product_name || log.search_query}</td>
                      <td className="px-6 py-4 text-center">
                        <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${
                          log.status === 'YES' ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' : 'bg-red-950/20 text-red-400 border-red-500/20'
                        }`}>
                          {log.status}
                        </span>
                      </td>
                      <td className="px-6 py-4 text-neutral-450">{log.reason || "Product Available"}</td>
                      <td className="px-6 py-4 text-right text-neutral-500">
                        {new Date(log.created_at).toLocaleString()}
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
