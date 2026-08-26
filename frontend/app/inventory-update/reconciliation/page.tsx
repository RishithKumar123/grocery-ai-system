"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  RotateCw, 
  Loader2, 
  Activity,
  FolderSync
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface ReconciliationMetrics {
  id: number;
  total_items_db: number;
  total_items_ai: number;
  variance_count: number;
  accuracy_rate: number;
  scanned_at: string;
}

export default function ReconciliationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [recon, setRecon] = useState<ReconciliationMetrics | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadReconciliation();
  }, [router]);

  const loadReconciliation = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/preview?store_id=1");
      if (res.ok) {
        const diffData = await res.json();
        // Compute statistics aggregations on client
        const dbTotal = diffData.reduce((acc: number, item: any) => acc + item.database_stock, 0);
        const aiTotal = diffData.reduce((acc: number, item: any) => acc + item.physical_scan, 0);
        const variance = aiTotal - dbTotal;
        const rate = dbTotal > 0 ? Math.max(100.0 - (Math.abs(variance) / dbTotal * 100), 0.0) : 100.0;

        setRecon({
          id: 1,
          total_items_db: dbTotal,
          total_items_ai: aiTotal,
          variance_count: variance,
          accuracy_rate: Math.round(rate * 100) / 100,
          scanned_at: new Date().toISOString()
        });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-3xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
          <Link href="/inventory-update" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Reconciliation Metrics</h1>
            <p className="text-xs text-neutral-500 font-sans mt-0.5">Telemetry reports comparing inventory registry vs scan records.</p>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Reconciliation telemetry processing...</p>
          </div>
        ) : recon ? (
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h4 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <FolderSync className="w-5 h-5 text-emerald-400" />
              Consolidated Summary Metrics
            </h4>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 font-mono text-xs text-neutral-450 pt-4 border-t border-neutral-900/60">
              <div className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="block text-[8px] text-neutral-500 font-bold uppercase">System Accuracy rate</span>
                <span className="block text-xl font-bold text-emerald-450 text-emerald-400">{recon.accuracy_rate}% Aligned</span>
              </div>
              <div className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="block text-[8px] text-neutral-500 font-bold uppercase">Net stock Variance</span>
                <span className={`block text-xl font-bold ${recon.variance_count >= 0 ? 'text-emerald-400' : 'text-red-405 text-red-400'}`}>
                  {recon.variance_count >= 0 ? `+${recon.variance_count}` : recon.variance_count} items
                </span>
              </div>
              <div className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="block text-[8px] text-neutral-500 font-bold uppercase">Total Database Stock</span>
                <span>{recon.total_items_db} items</span>
              </div>
              <div className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="block text-[8px] text-neutral-500 font-bold uppercase">Total Scanner verified count</span>
                <span>{recon.total_items_ai} items</span>
              </div>
            </div>

            <div className="p-4 rounded-xl border border-emerald-500/10 bg-emerald-950/10 text-emerald-400 text-[10px] leading-relaxed font-sans">
              Reconciliation completed successfully. Accuracy indicates stock levels compliance against recent visual scan outputs.
            </div>
          </div>
        ) : (
          <div className="text-center py-20 text-neutral-550 font-mono text-xs">
            Failed to build reconciliation report.
          </div>
        )}

      </div>
    </div>
  );
}
