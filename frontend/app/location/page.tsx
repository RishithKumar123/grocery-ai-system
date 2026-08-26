"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Map, 
  Layers, 
  Search, 
  Sliders, 
  ShieldAlert, 
  Clock, 
  Grid, 
  AlertOctagon, 
  RotateCw, 
  Loader2,
  Trash2,
  ListOrdered
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface Occupancy {
  id: number;
  shelf_map_id: number;
  shelf_name: string;
  occupancy_percentage: number;
  unassigned_space_percentage: number;
}

interface Misplacement {
  id: number;
  product_name: string;
  severity: string;
}

interface EmptySpot {
  id: number;
  estimated_vacant_slots: number;
}

export default function LocationDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  
  // Mapped Data telemetry
  const [occupancyList, setOccupancyList] = useState<Occupancy[]>([]);
  const [misplacedCount, setMisplacedCount] = useState(0);
  const [emptySpotCount, setEmptySpotCount] = useState(0);
  const [avgOccupancy, setAvgOccupancy] = useState(0.0);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadData();
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Store occupancy metrics
      const resOcc = await fetchWithAuth("/api/v1/location/occupancy");
      if (resOcc.ok) {
        const occData = await resOcc.json();
        setOccupancyList(occData);

        if (occData.length > 0) {
          const total = occData.reduce((acc: number, item: Occupancy) => acc + item.occupancy_percentage, 0);
          setAvgOccupancy(Math.round((total / occData.length) * 100) / 100);
        }
      }

      // 2. Fetch Misplaced items count
      const resMisp = await fetchWithAuth("/api/v1/location/misplaced");
      if (resMisp.ok) {
        const mispData = await resMisp.json();
        setMisplacedCount(mispData.length);
      }

      // 3. Fetch Empty spaces spots count
      const resEmp = await fetchWithAuth("/api/v1/location/empty-space");
      if (resEmp.ok) {
        const empData = await resEmp.json();
        setEmptySpotCount(empData.length);
      }

    } catch (err) {
      console.error("Failed to load location intelligence telemetry metrics", err);
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
              <Link href="/dashboard" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Location Intelligence Desk</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Identifies the physical slot coordinates of every shelf product and tracks misplaced items and empty space allocations.
            </p>
          </div>
          <button 
            onClick={loadData}
            className="self-start md:self-auto flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Layout metrics
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading coordinates transformation maps...</p>
          </div>
        ) : (
          <>
            {/* 1. Analytics Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Average Shelf Occupancy</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{avgOccupancy}%</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Misplaced Products</span>
                <span className="block text-2xl font-bold text-red-400 font-mono mt-1">{misplacedCount} items</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Empty Shelf Gaps</span>
                <span className="block text-2xl font-bold text-yellow-400 font-mono mt-1">{emptySpotCount} spots</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Mapped Shelf Areas</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{occupancyList.length} levels</span>
              </div>
            </div>

            {/* Visual Action cards links */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <Link href="/location/map" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Map className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Interactive Store Map</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    View full store department zoning layout coordinates, aisles, racks, and hotspots mapping details.
                  </p>
                </div>
              </Link>

              <Link href="/location/locator" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Search className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Product Locator</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Search for any product name, SKU, or category to find its exact aisle rack level placement coordinate.
                  </p>
                </div>
              </Link>

              <Link href="/location/planogram" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Grid className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Planogram Compliance</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Inspect expected sequencing layouts, product facecounts targets, and deviations mapping details.
                  </p>
                </div>
              </Link>

              <Link href="/location/misplacement" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <AlertOctagon className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Misplaced Products</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Review wrong category placement logs, wrong brand placement alerts, and severity meters.
                  </p>
                </div>
              </Link>

              <Link href="/location/empty-shelf" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Sliders className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Vacant Space Tracker</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Locate completely empty or partially empty shelf sections to optimize store space allocation.
                  </p>
                </div>
              </Link>

              <Link href="/location/history" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Location History</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    View timeline audit history log of stock movement and shelf reassignments within the store.
                  </p>
                </div>
              </Link>

            </div>

            {/* Occupancy stats listings */}
            <div className="space-y-4">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">Shelf Utilization Ratios</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {occupancyList.map(occ => (
                  <div key={occ.id} className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl space-y-3 font-mono text-xs text-neutral-400">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-neutral-200 truncate max-w-[200px]">{occ.shelf_name}</span>
                      <span className="text-emerald-400 font-bold">{occ.occupancy_percentage}% Used</span>
                    </div>
                    <div className="w-full bg-neutral-950 h-2 border border-neutral-900 rounded-full overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${occ.occupancy_percentage}%` }} />
                    </div>
                    <div className="flex justify-between items-center text-[10px] text-neutral-550">
                      <span>Occupied: {occ.occupancy_percentage}%</span>
                      <span>Vacant: {occ.unassigned_space_percentage}%</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </>
        )}
      </div>
    </div>
  );
}
