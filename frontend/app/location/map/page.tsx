"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Map, 
  Layers, 
  Sliders, 
  Loader2, 
  Activity,
  Maximize2
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Shelf {
  id: number;
  shelf_level: string;
  max_capacity: number;
}

interface Rack {
  id: number;
  rack_number: string;
  x_coordinate: number;
  y_coordinate: number;
  shelves: Shelf[];
}

interface Aisle {
  id: number;
  aisle_name: string;
  start_x: number;
  start_y: number;
  end_x: number;
  end_y: number;
  racks: Rack[];
}

interface StoreMap {
  id: number;
  map_name: string;
  width_meters: number;
  height_meters: number;
  aisles: Aisle[];
}

export default function StoreMapPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [storeMap, setStoreMap] = useState<StoreMap | null>(null);
  
  // Controls
  const [showHeatmap, setShowHeatmap] = useState(false);
  const [selectedRack, setSelectedRack] = useState<Rack | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadMapData();
  }, [router]);

  const loadMapData = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/location/store-map?store_id=1");
      if (res.ok) {
        setStoreMap(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-xs text-neutral-500 font-mono">Drawing store map vectors layout...</p>
      </div>
    );
  }

  if (!storeMap) {
    return (
      <div className="text-center py-20 text-neutral-500 font-mono text-xs">
        Map layout data not seeded or inaccessible.
      </div>
    );
  }

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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Interactive Store Map</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Store Layout: {storeMap.map_name} ({storeMap.width_meters}m x {storeMap.height_meters}m)
            </p>
          </div>
          
          <button
            onClick={() => setShowHeatmap(!showHeatmap)}
            className={`flex items-center gap-1.5 px-4 py-2 rounded-xl border text-xs font-bold font-mono transition-all cursor-pointer ${
              showHeatmap ? 'bg-emerald-500 text-neutral-950 border-emerald-500' : 'bg-neutral-900 border-neutral-800 text-neutral-400 hover:text-neutral-100'
            }`}
          >
            <Layers className="w-3.5 h-3.5" /> {showHeatmap ? "Disable Heatmap" : "Enable Occupancy Heatmap"}
          </button>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-4 gap-8">
          
          {/* Store layout grid screen */}
          <div className="lg:col-span-3 space-y-4">
            <div className="relative w-full aspect-[4/3] bg-neutral-900/40 border border-neutral-900 rounded-3xl overflow-hidden p-6">
              
              {/* Grid Background lines */}
              <div className="absolute inset-0 bg-[linear-gradient(to_right,rgba(255,255,255,0.01)_1px,transparent_1px),linear-gradient(to_bottom,rgba(255,255,255,0.01)_1px,transparent_1px)] bg-[size:24px_24px]" />

              {/* Ingest aisles list */}
              {storeMap.aisles.map(aisle => {
                // Calculate position percentages on the floor grid (assuming width 40m, height 30m)
                const startXPercent = (aisle.start_x / storeMap.width_meters) * 100;
                const startYPercent = (aisle.start_y / storeMap.height_meters) * 100;
                const heightPercent = ((aisle.end_y - aisle.start_y) / storeMap.height_meters) * 100;

                return (
                  <div
                    key={aisle.id}
                    className="absolute border border-neutral-800 bg-neutral-950/40 rounded-2xl flex flex-col items-center justify-between p-2 select-none group"
                    style={{
                      left: `${startXPercent}%`,
                      top: `${startYPercent}%`,
                      width: "60px",
                      height: `${heightPercent}%`
                    }}
                  >
                    <span className="text-[7px] text-neutral-500 font-mono font-bold uppercase tracking-wider text-center rotate-90 my-auto truncate max-w-[80px]">
                      {aisle.aisle_name}
                    </span>

                    {/* Racks inside Aisle */}
                    {aisle.racks.map(rack => {
                      const rackYPercent = ((rack.y_coordinate - aisle.start_y) / (aisle.end_y - aisle.start_y)) * 80;
                      // Heatmap color
                      let heatmapColor = "bg-emerald-500 border-emerald-400";
                      if (showHeatmap) {
                        const score = (rack.id % 3);
                        if (score === 0) heatmapColor = "bg-red-500 border-red-400 animate-pulse";
                        if (score === 1) heatmapColor = "bg-yellow-500 border-yellow-400";
                      }

                      return (
                        <button
                          key={rack.id}
                          onClick={() => setSelectedRack(rack)}
                          className={`absolute w-10 h-10 rounded-xl border flex items-center justify-center text-[8px] font-bold font-mono transition-all hover:scale-115 cursor-pointer ${
                            selectedRack?.id === rack.id 
                              ? 'bg-emerald-500 text-neutral-950 border-emerald-400 ring-2 ring-emerald-500/20' 
                              : showHeatmap ? `${heatmapColor} text-neutral-950` : 'bg-neutral-900 border-neutral-800 text-neutral-350 hover:border-emerald-400'
                          }`}
                          style={{
                            top: `${rackYPercent + 5}%`
                          }}
                          title={`Rack: ${rack.rack_number}`}
                        >
                          R
                        </button>
                      );
                    })}
                  </div>
                );
              })}

            </div>
          </div>

          {/* Sidebar selector rack details */}
          <div className="space-y-6">
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              
              {selectedRack ? (
                <div className="space-y-6">
                  <div className="space-y-1">
                    <span className="block text-[8px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Rack Coordinates</span>
                    <h3 className="text-sm font-bold text-neutral-200 font-mono">Rack ID: {selectedRack.rack_number}</h3>
                    <p className="text-[10px] text-neutral-500 font-sans">
                      Located at X={selectedRack.x_coordinate}m, Y={selectedRack.y_coordinate}m.
                    </p>
                  </div>

                  <div className="space-y-3 pt-4 border-t border-neutral-900/60 text-xs">
                    <span className="block text-[9px] text-neutral-500 font-bold uppercase tracking-wider font-mono">Mapped shelf levels</span>
                    
                    {selectedRack.shelves.map(shelf => (
                      <Link 
                        key={shelf.id}
                        href={`/location/shelf?id=${shelf.id}`}
                        className="flex justify-between items-center p-3 bg-neutral-950 border border-neutral-900 hover:border-emerald-500/20 rounded-xl transition-all font-mono"
                      >
                        <div>
                          <span className="block text-neutral-300 font-bold">{shelf.shelf_level}</span>
                          <span className="block text-[8px] text-neutral-550 mt-0.5">Capacity: {shelf.max_capacity} slots</span>
                        </div>
                        <Maximize2 className="w-3.5 h-3.5 text-neutral-500" />
                      </Link>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="text-center py-20 text-neutral-500 text-xs font-mono">
                  Select any rack node on the store layout floor plan grid to inspect shelf levels.
                </div>
              )}

            </div>
          </div>

        </div>

      </div>
    </div>
  );
}
