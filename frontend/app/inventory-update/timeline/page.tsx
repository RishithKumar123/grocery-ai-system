"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Clock, 
  RotateCw, 
  Loader2, 
  TrendingUp, 
  TrendingDown, 
  HelpCircle
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
  created_at: string;
}

export default function TimelineTrackerPage() {
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
    loadTimelineLogs();
  }, [router]);

  const loadTimelineLogs = async () => {
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
      <div className="max-w-4xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/inventory-update" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Inventory Timeline</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Chronological visual tracker monitoring stock modifications.
            </p>
          </div>

          <button 
            onClick={loadTimelineLogs}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Timeline
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading transaction timeline nodes...</p>
          </div>
        ) : (
          <div className="relative pl-6 border-l-2 border-neutral-900 space-y-8 font-mono text-xs">
            {logs.length === 0 ? (
              <div className="text-center py-20 text-neutral-550">
                No inventory changes logged in timeline.
              </div>
            ) : (
              logs.map(log => {
                const isPositive = log.variance >= 0;

                return (
                  <div key={log.id} className="relative space-y-2">
                    
                    {/* Circle Node indicator */}
                    <span className={`absolute -left-[31px] top-1.5 w-4 h-4 rounded-full border-4 border-neutral-950 flex items-center justify-center ${
                      log.status === 'Applied' ? 'bg-emerald-400' : 'bg-yellow-400'
                    }`} />

                    <div className="flex justify-between items-center text-[10px] text-neutral-500">
                      <span>{new Date(log.created_at).toLocaleString()}</span>
                      <span className="font-bold uppercase tracking-wider text-[8px]">Update ID #{log.id}</span>
                    </div>

                    <div className="p-4 bg-neutral-900/10 border border-neutral-900 rounded-2xl flex items-center justify-between">
                      <div className="space-y-1">
                        <span className="block font-sans text-neutral-250 font-bold">{log.product_name}</span>
                        <span className="block text-[10px] text-neutral-500">SKU: {log.sku} - Status: {log.status}</span>
                      </div>
                      
                      <div className="flex items-center gap-2">
                        {isPositive ? (
                          <TrendingUp className="w-4 h-4 text-emerald-450 text-emerald-400" />
                        ) : (
                          <TrendingDown className="w-4 h-4 text-red-405 text-red-400" />
                        )}
                        <span className={`font-bold ${isPositive ? 'text-emerald-400' : 'text-red-400'}`}>
                          {isPositive ? `+${log.variance}` : log.variance} items
                        </span>
                      </div>
                    </div>

                  </div>
                );
              })
            )}
          </div>
        )}

      </div>
    </div>
  );
}
