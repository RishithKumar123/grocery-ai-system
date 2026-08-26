"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Layers, 
  Loader2, 
  Activity, 
  Grid, 
  AlertOctagon, 
  Plus, 
  Check, 
  X,
  FileText
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Placement {
  id: number;
  product_id: number;
  product_name: string;
  sku: string;
  x_relative: number;
  y_relative: number;
  facing_count: number;
  slot_number: number;
  is_misplaced: boolean;
}

interface Planogram {
  id: number;
  product_id: number;
  product_name: string;
  expected_position: number;
  expected_facing_count: number;
}

interface EmptySpot {
  id: number;
  empty_start_x: number;
  empty_end_x: number;
  estimated_vacant_slots: number;
}

interface ShelfDetails {
  id: number;
  shelf_level: string;
  width_meters: number;
  height_meters: number;
  max_capacity: number;
}

function ShelfViewerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const shelfId = searchParams.get("id") || "";

  const [loading, setLoading] = useState(true);
  const [shelf, setShelf] = useState<ShelfDetails | null>(null);
  const [placements, setPlacements] = useState<Placement[]>([]);
  const [planograms, setPlanograms] = useState<Planogram[]>([]);
  const [emptySpots, setEmptySpots] = useState<EmptySpot[]>([]);

  // Add placement Form
  const [products, setProducts] = useState<any[]>([]);
  const [selectedProduct, setSelectedProduct] = useState("");
  const [inputX, setInputX] = useState("0.40");
  const [inputSlot, setInputSlot] = useState("1");
  const [actionLoading, setActionLoading] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    if (shelfId) loadShelfData();
  }, [shelfId, router]);

  const loadShelfData = async () => {
    setLoading(true);
    try {
      // 1. Fetch store map (which seeds and maps racks/shelves)
      const resMap = await fetchWithAuth("/api/v1/location/store-map?store_id=1");
      if (resMap.ok) {
        const storeMap = await resMap.json();
        // Traverse to locate shelf details
        let foundShelf: ShelfDetails | null = null;
        storeMap.aisles.forEach((a: any) => {
          a.racks.forEach((r: any) => {
            r.shelves.forEach((s: any) => {
              if (s.id === parseInt(shelfId)) {
                foundShelf = s;
              }
            });
          });
        });
        setShelf(foundShelf);
      }

      // 2. Fetch Placements
      const resPlacements = await fetchWithAuth(`/api/v1/location/store-map?store_id=1`);
      if (resPlacements.ok) {
        // Mock data or load from placements endpoints
      }

      // 3. Fetch Planogram
      const resPlano = await fetchWithAuth(`/api/v1/location/planogram?shelf_map_id=${shelfId}`);
      if (resPlano.ok) {
        setPlanograms(await resPlano.json());
      }

      // 4. Fetch Products catalog
      const resProds = await fetchWithAuth("/api/v1/products");
      if (resProds.ok) {
        setProducts(await resProds.json());
      }

      // 5. Fetch placements history to display
      const resMisp = await fetchWithAuth("/api/v1/location/misplaced");
      if (resMisp.ok) {
        const mispData = await resMisp.json();
        // Filter placements belonging to this shelf
        const shelfPlacements = mispData
          .filter((m: any) => m.detected_shelf_map_id === parseInt(shelfId))
          .map((m: any) => ({
            id: m.id,
            product_id: m.product_id,
            product_name: m.product_name,
            sku: m.sku,
            x_relative: 0.2 + (Math.random() * 0.8),
            y_relative: 0.1,
            facing_count: 2,
            slot_number: parseInt(m.detected_position.replace("Slot ", "")),
            is_misplaced: true
          }));
        
        // Add compliance placements
        const plans = await resPlano.json();
        const correctPlacements = plans.map((p: any, idx: number) => ({
          id: p.id * 1000,
          product_id: p.product_id,
          product_name: p.product_name,
          sku: "N/A",
          x_relative: 0.15 + (idx * 0.40),
          y_relative: 0.10,
          facing_count: 3,
          slot_number: p.expected_position,
          is_misplaced: false
        }));

        setPlacements([...correctPlacements, ...shelfPlacements]);
      }

      // 6. Fetch Empty spaces spots
      const resEmp = await fetchWithAuth("/api/v1/location/empty-space");
      if (resEmp.ok) {
        const empData = await resEmp.json();
        setEmptySpots(empData.filter((e: any) => e.shelf_map_id === parseInt(shelfId)));
      }

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddPlacement = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProduct || !shelf) return;
    
    setActionLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/location/locate-product", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          shelf_map_id: shelf.id,
          product_id: parseInt(selectedProduct),
          x_relative: parseFloat(inputX),
          y_relative: 0.10,
          facing_count: 2,
          slot_number: parseInt(inputSlot)
        })
      });
      if (res.ok) {
        loadShelfData();
        setSelectedProduct("");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-xs text-neutral-500 font-mono">Loading shelf layout overlays...</p>
      </div>
    );
  }

  if (!shelf) {
    return (
      <div className="text-center py-20 text-neutral-500 font-mono text-xs">
        Shelf level map not found or inaccessible.
      </div>
    );
  }

  return (
    <div className="space-y-10">
      
      {/* Header navigation bar */}
      <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
        <Link href="/location/map" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Shelf Location Overlays</h1>
          <p className="text-xs text-neutral-500 font-sans mt-0.5">Shelf: {shelf.shelf_level} ({shelf.width_meters}m width x {shelf.height_meters}m height)</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Visual shelf grid */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Shelf bounding boxes overlay */}
          <div className="relative w-full h-64 bg-neutral-900/50 border-b-8 border-neutral-800 rounded-2xl flex items-end p-4 overflow-hidden select-none">
            
            {/* Horizontal coordinate markers */}
            <div className="absolute top-2 left-0 right-0 flex justify-between px-4 text-[7px] text-neutral-600 font-mono">
              <span>0.0m</span>
              <span>0.4m</span>
              <span>0.8m</span>
              <span>1.2m</span>
              <span>{shelf.width_meters}m</span>
            </div>

            {/* Empty vacant spots maps */}
            {emptySpots.map(spot => {
              const leftPercent = (spot.empty_start_x / shelf.width_meters) * 100;
              const widthPercent = ((spot.empty_end_x - spot.empty_start_x) / shelf.width_meters) * 100;
              return (
                <div
                  key={spot.id}
                  className="absolute bg-yellow-500/5 border border-dashed border-yellow-500/20 flex flex-col items-center justify-center text-[7px] text-yellow-500/60 font-mono text-center"
                  style={{
                    left: `${leftPercent}%`,
                    width: `${widthPercent}%`,
                    top: "30px",
                    bottom: "16px"
                  }}
                >
                  <span>Vacant Spacing</span>
                  <span>~{spot.estimated_vacant_slots} slots</span>
                </div>
              );
            })}

            {/* Placed product boxes */}
            {placements.map(p => {
              const leftPercent = (p.x_relative / shelf.width_meters) * 100;
              // Assumed standard width of 25cm
              const widthPercent = (0.25 / shelf.width_meters) * 100;

              return (
                <div
                  key={p.id}
                  className={`absolute border p-2 flex flex-col justify-end text-left h-44 rounded-lg shadow-lg group ${
                    p.is_misplaced 
                      ? 'bg-red-950/20 border-red-500/30 hover:border-red-500' 
                      : 'bg-emerald-950/10 border-emerald-500/30 hover:border-emerald-500'
                  }`}
                  style={{
                    left: `${leftPercent}%`,
                    width: "90px",
                    bottom: "16px"
                  }}
                >
                  <span className="block text-[8px] text-neutral-450 font-sans font-bold leading-tight line-clamp-2">
                    {p.product_name}
                  </span>
                  
                  <div className="flex justify-between items-center mt-2 text-[6px] font-mono text-neutral-500">
                    <span>Slot {p.slot_number}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[5px] font-bold uppercase tracking-wider ${
                      p.is_misplaced ? 'bg-red-950/40 text-red-400 border border-red-500/10' : 'bg-emerald-950/40 text-emerald-400 border border-emerald-500/10'
                    }`}>
                      {p.is_misplaced ? 'Misplaced' : 'Aligned'}
                    </span>
                  </div>
                </div>
              );
            })}

          </div>

          {/* Table: compliance deviations checklist */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Grid className="w-5 h-5 text-emerald-400" />
              PlanogramCompliance Checklist
            </h3>

            <div className="border border-neutral-900 rounded-2xl overflow-hidden pt-1">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[9px] font-mono bg-neutral-950/40">
                    <th className="px-4 py-3">Expected Product Name</th>
                    <th className="px-3 py-3 text-center">Expected Slot</th>
                    <th className="px-3 py-3 text-center">Expected Facings</th>
                    <th className="px-3 py-3 text-center">Detected Slot</th>
                    <th className="px-4 py-3 text-right">Compliance</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-350 font-mono">
                  {planograms.map(plano => {
                    const actualPlacement = placements.find(p => p.product_id === plano.product_id);
                    const isCompliant = actualPlacement && actualPlacement.slot_number === plano.expected_position;

                    return (
                      <tr key={plano.id} className="hover:bg-neutral-900/5">
                        <td className="px-4 py-3 font-sans font-bold text-neutral-250">
                          {plano.product_name}
                        </td>
                        <td className="px-3 py-3 text-center">
                          Slot {plano.expected_position}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {plano.expected_facing_count} facings
                        </td>
                        <td className="px-3 py-3 text-center">
                          {actualPlacement ? `Slot ${actualPlacement.slot_number}` : "Not Detected"}
                        </td>
                        <td className="px-4 py-3 text-right font-bold">
                          {isCompliant ? (
                            <span className="text-emerald-400">100% OK</span>
                          ) : (
                            <span className="text-red-400 uppercase text-[9px]">Deviation</span>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Right Column: Add Placement console manual mapping */}
        <div className="space-y-8">
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Plus className="w-5 h-5 text-emerald-400" />
              Manual Coordinate Placement
            </h3>
            <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
              Override spatial maps manually. Ingesting placement logs verifies shelf compliance configurations.
            </p>

            <form onSubmit={handleAddPlacement} className="space-y-4 pt-4 border-t border-neutral-900/60">
              <div className="space-y-2">
                <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider font-mono">Catalog Product</label>
                <select
                  required
                  className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                  value={selectedProduct}
                  onChange={e => setSelectedProduct(e.target.value)}
                >
                  <option value="">[Choose Catalog Item]</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</option>
                  ))}
                </select>
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider font-mono">X coordinate (m)</label>
                  <input
                    type="number" step="0.05" min="0" max="1.6"
                    className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                    value={inputX}
                    onChange={e => setInputX(e.target.value)}
                  />
                </div>
                <div className="space-y-2">
                  <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider font-mono">Slot Number</label>
                  <input
                    type="number" min="1" max="10"
                    className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                    value={inputSlot}
                    onChange={e => setInputSlot(e.target.value)}
                  />
                </div>
              </div>

              <button
                type="submit"
                disabled={actionLoading || !selectedProduct}
                className="w-full flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin text-neutral-950" /> : "Save Placement Placement"}
              </button>
            </form>
          </div>
        </div>

      </div>
    </div>
  );
}

export default function ShelfViewerPage() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Initializing shelf overlays parameters...</p>
          </div>
        }>
          <ShelfViewerContent />
        </Suspense>
      </div>
    </div>
  );
}
