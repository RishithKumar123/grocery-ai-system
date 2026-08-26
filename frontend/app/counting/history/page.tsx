"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Search, 
  RotateCw, 
  Loader2, 
  FileText, 
  TrendingUp 
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface HistoryEntry {
  id: number;
  product_id?: number;
  product_name: string;
  shelf_id?: number;
  shelf_aisle?: string;
  shelf_level?: string;
  count: number;
  verified_at: string;
  job_id: number;
}

export default function CountHistoryPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const [search, setSearch] = useState("");

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
      const res = await fetchWithAuth("/api/v1/counting/history");
      if (res.ok) {
        setHistory(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredHistory = history.filter(h => {
    const term = search.toLowerCase();
    return (
      h.product_name.toLowerCase().includes(term) ||
      (h.shelf_aisle && h.shelf_aisle.toLowerCase().includes(term)) ||
      (h.shelf_level && h.shelf_level.toLowerCase().includes(term)) ||
      h.job_id.toString().includes(term)
    );
  });

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/counting" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Count History Ledger</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Auditing timeline records of verified products counts. Use these logs for inventory validation reports.
            </p>
          </div>

          <button 
            onClick={loadHistory}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh History
          </button>
        </div>

        {/* Filter Toolbar */}
        <div className="relative max-w-md">
          <Search className="absolute left-3.5 top-3 w-4 h-4 text-neutral-500" />
          <input
            type="text"
            className="w-full pl-10 pr-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-900/60 text-xs text-neutral-300 focus:outline-none focus:border-emerald-500/20"
            placeholder="Search by product, SKU, aisle, or Job ID..."
            value={search}
            onChange={e => setSearch(e.target.value)}
          />
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Retrieving count validation history logs...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">History Log ID</th>
                  <th className="px-6 py-4">Product Name</th>
                  <th className="px-6 py-4 text-center">Shelf Location</th>
                  <th className="px-6 py-4 text-center">Verified Count</th>
                  <th className="px-6 py-4 text-center">Audit Source Job</th>
                  <th className="px-6 py-4 text-right">Verification Date</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                {filteredHistory.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-neutral-500 font-mono text-xs">
                      No matching verified count records logged in database.
                    </td>
                  </tr>
                ) : (
                  filteredHistory.map(h => (
                    <tr key={h.id} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="px-6 py-4 font-mono text-neutral-400">
                        #{h.id}
                      </td>
                      <td className="px-6 py-4 font-bold text-neutral-200">
                        {h.product_name}
                      </td>
                      <td className="px-6 py-4 text-center font-mono text-neutral-450">
                        {h.shelf_aisle ? `${h.shelf_aisle} / ${h.shelf_level || 'General'}` : "Store Floor Placement"}
                      </td>
                      <td className="px-6 py-4 text-center">
                        <span className="px-3 py-1 rounded-xl bg-emerald-950/30 border border-emerald-500/10 text-emerald-400 font-bold font-mono">
                          {h.count} pcs
                        </span>
                      </td>
                      <td className="px-6 py-4 text-center font-mono font-bold text-neutral-100">
                        Job Record: #{h.job_id}
                      </td>
                      <td className="px-6 py-4 text-right font-mono text-neutral-450">
                        {new Date(h.verified_at).toLocaleDateString()} {new Date(h.verified_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
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
