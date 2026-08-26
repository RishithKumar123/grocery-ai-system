"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Sliders, 
  RotateCw, 
  Loader2,
  TrendingDown
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface EmptySpot {
  id: number;
  shelf_map_id: number;
  empty_start_x: number;
  empty_end_x: number;
  estimated_vacant_slots: number;
  created_at: string;
}

export default function EmptyShelfPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [spots, setSpots] = useState<EmptySpot[]>([]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadEmptySpots();
  }, [router]);

  const loadEmptySpots = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/location/empty-space");
      if (res.ok) {
        setSpots(await res.json());
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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Vacant Space Tracker</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Identifies empty shelf spaces and estimates how many stock item slot placements can be filled in gaps.
            </p>
          </div>

          <button 
            onClick={loadEmptySpots}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Gaps
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Mapping horizontal shelf gaps...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                  <th className="px-6 py-4">Spot ID</th>
                  <th className="px-6 py-4">Shelf Map Level Target</th>
                  <th className="px-6 py-4 text-center">Gap Span (m)</th>
                  <th className="px-6 py-4 text-center">Estimated Vacant Slots</th>
                  <th className="px-6 py-4 text-center">Scan Date</th>
                  <th className="px-6 py-4 text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300 font-mono">
                {spots.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="text-center py-20 text-neutral-500 font-mono text-xs">
                      No vacant gaps detected on shelves. Store spaces are fully occupied!
                    </td>
                  </tr>
                ) : (
                  spots.map(spot => (
                    <tr key={spot.id} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="px-6 py-4 text-neutral-400">
                        #{spot.id}
                      </td>
                      <td className="px-6 py-4 font-bold text-neutral-200">
                        Shelf Map ID: {spot.shelf_map_id}
                      </td>
                      <td className="px-6 py-4 text-center text-neutral-250">
                        {spot.empty_start_x.toFixed(2)}m to {spot.empty_end_x.toFixed(2)}m
                      </td>
                      <td className="px-6 py-4 text-center font-bold text-yellow-400">
                        ~ {spot.estimated_vacant_slots} slots
                      </td>
                      <td className="px-6 py-4 text-center text-neutral-450">
                        {new Date(spot.created_at).toLocaleDateString()}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <Link 
                          href={`/location/shelf?id=${spot.shelf_map_id}`}
                          className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-800 hover:border-emerald-500/20 text-[10px] font-bold font-mono text-neutral-350 hover:text-emerald-400 transition-colors"
                        >
                          View Shelf overlays
                        </Link>
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
