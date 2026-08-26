"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  AlertOctagon, 
  RotateCw, 
  Loader2,
  Trash2
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Misplacement {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  detected_shelf_map_id: number;
  detected_shelf_name: string;
  expected_shelf_map_id?: number;
  expected_shelf_name?: string;
  detected_position: string;
  expected_position: string;
  severity: string;
  created_at: string;
}

export default function MisplacedProductsPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [misplacements, setMisplacements] = useState<Misplacement[]>([]);
  const [filterSeverity, setFilterSeverity] = useState("ALL");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadMisplacements();
  }, [router]);

  const loadMisplacements = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/location/misplaced");
      if (res.ok) {
        setMisplacements(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const filteredMisp = misplacements.filter(m => {
    if (filterSeverity === "ALL") return true;
    return m.severity === filterSeverity;
  });

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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Misplaced Products</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Lists layout violations such as wrong category/brand shelf coordinates or slot placement deviations.
            </p>
          </div>

          <div className="flex gap-2">
            <select
              className="px-3 py-2 rounded-xl border border-neutral-850 bg-neutral-900 text-neutral-400 text-xs focus:outline-none"
              value={filterSeverity}
              onChange={e => setFilterSeverity(e.target.value)}
            >
              <option value="ALL">All Severity Levels</option>
              <option value="High">High Severity</option>
              <option value="Medium">Medium Severity</option>
              <option value="Low">Low Severity</option>
            </select>

            <button 
              onClick={loadMisplacements}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" /> Refresh
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Scanning wrong shelf layouts...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">Item Name</th>
                  <th className="px-6 py-4 text-center">Detected Location</th>
                  <th className="px-6 py-4 text-center">Expected Location</th>
                  <th className="px-6 py-4 text-center">Severity</th>
                  <th className="px-6 py-4 text-center">Scan Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300 font-mono">
                {filteredMisp.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-neutral-500 font-mono text-xs">
                      No misplaced products detected on shelves. Planograms are compliant!
                    </td>
                  </tr>
                ) : (
                  filteredMisp.map(m => {
                    let severityColor = "bg-neutral-900 text-neutral-450 border-neutral-800";
                    if (m.severity === "High") severityColor = "bg-red-950/20 text-red-400 border-red-500/20";
                    if (m.severity === "Medium") severityColor = "bg-yellow-950/20 text-yellow-400 border-yellow-500/20";
                    if (m.severity === "Low") severityColor = "bg-blue-950/20 text-blue-400 border-blue-500/20";

                    return (
                      <tr key={m.id} className="hover:bg-neutral-900/10 transition-colors">
                        <td className="px-6 py-4 font-sans font-bold text-neutral-200">
                          {m.product_name}
                          <span className="block text-[9px] text-neutral-500 font-mono mt-0.5">SKU: {m.sku}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="block text-neutral-250 font-sans font-bold">{m.detected_shelf_name}</span>
                          <span className="block text-[9px] text-neutral-500 mt-0.5">Detected: {m.detected_position}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className="block text-neutral-250 font-sans font-bold">{m.expected_shelf_name || "Wrong aisle/area"}</span>
                          <span className="block text-[9px] text-neutral-500 mt-0.5">Expected: {m.expected_position}</span>
                        </td>
                        <td className="px-6 py-4 text-center">
                          <span className={`px-2.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border ${severityColor}`}>
                            {m.severity}
                          </span>
                        </td>
                        <td className="px-6 py-4 text-center text-neutral-450">
                          {new Date(m.created_at).toLocaleDateString()}
                        </td>
                        <td className="px-6 py-4 text-right">
                          <Link 
                            href={`/location/shelf?id=${m.detected_shelf_map_id}`}
                            className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-800 hover:border-emerald-500/20 text-[10px] font-bold font-mono text-neutral-350 hover:text-emerald-400 transition-colors"
                          >
                            Inspect Shelf
                          </Link>
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
