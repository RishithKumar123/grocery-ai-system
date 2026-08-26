"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  RotateCw, 
  Loader2, 
  Activity, 
  Grid, 
  AlertTriangle,
  FileText
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Difference {
  product_id: number;
  product_name: string;
  sku: string;
  database_stock: number;
  physical_scan: number;
  difference: number;
  variance_percentage: number;
  recommendation: string;
}

export default function DifferenceViewerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [differences, setDifferences] = useState<Difference[]>([]);
  const [showDiscrepanciesOnly, setShowDiscrepanciesOnly] = useState(true);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadDifferences();
  }, [router]);

  const loadDifferences = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/preview?store_id=1");
      if (res.ok) {
        setDifferences(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredDiffs = differences.filter(d => {
    if (showDiscrepanciesOnly) return d.difference !== 0;
    return true;
  });

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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Stock Difference Viewer</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Compares physical stock counting scans side-by-side with database records to isolate discrepancies.
            </p>
          </div>

          <div className="flex gap-2">
            <button
              onClick={() => setShowDiscrepanciesOnly(!showDiscrepanciesOnly)}
              className={`px-4 py-2 rounded-xl border text-xs font-bold font-mono transition-all cursor-pointer ${
                showDiscrepanciesOnly ? 'bg-emerald-500 text-neutral-950 border-emerald-500' : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-neutral-100'
              }`}
            >
              {showDiscrepanciesOnly ? "Show All Items" : "Show Discrepancies Only"}
            </button>

            <button 
              onClick={loadDifferences}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" /> Refresh Previews
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Calculating differences parameters...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">Catalog Product</th>
                  <th className="px-6 py-4 text-center">Database Stock</th>
                  <th className="px-6 py-4 text-center">Verified Scan</th>
                  <th className="px-6 py-4 text-center">Variance Diff</th>
                  <th className="px-6 py-4 text-center">Variance %</th>
                  <th className="px-6 py-4 text-right">Action Recommendation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300 font-mono">
                {filteredDiffs.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-neutral-500 font-mono text-xs">
                      No stock differences detected. Database is fully aligned with physical shelf counts.
                    </td>
                  </tr>
                ) : (
                  filteredDiffs.map(diff => {
                    const isPositive = diff.difference >= 0;

                    return (
                      <tr key={diff.product_id} className="hover:bg-neutral-900/10 transition-colors">
                        <td className="px-6 py-4 font-sans font-bold text-neutral-200">
                          {diff.product_name}
                          <span className="block text-[9px] text-neutral-550 font-mono mt-0.5">SKU: {diff.sku}</span>
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-100 font-bold">
                          {diff.database_stock} items
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-100 font-bold">
                          {diff.physical_scan} items
                        </td>
                        <td className="px-6 py-4 text-center font-bold">
                          <span className={diff.difference === 0 ? 'text-neutral-400' : isPositive ? 'text-emerald-400' : 'text-red-400'}>
                            {diff.difference === 0 ? '0' : isPositive ? `+${diff.difference}` : diff.difference}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-450">
                          {diff.variance_percentage}%
                        </td>
                        <td className="px-6 py-4 text-right text-neutral-450 font-sans font-semibold">
                          {diff.recommendation}
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
