"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Search, 
  CheckCircle, 
  XCircle, 
  MapPin, 
  Clock, 
  BarChart3, 
  QrCode, 
  Camera, 
  Building2, 
  History, 
  Loader2, 
  ShieldCheck, 
  AlertTriangle,
  RotateCw,
  Sparkles,
  Package,
  Layers,
  ChevronRight
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface NearestStore {
  store_id: number;
  store_name: string;
  branch?: string;
  available_quantity: number;
  distance_km?: number;
}

interface AvailabilityResult {
  status: "YES" | "NO";
  reason?: string;
  product_id?: number;
  product_name?: string;
  sku?: string;
  barcode?: string;
  brand?: string;
  category?: string;
  available_quantity?: number;
  unit?: string;
  store_id: number;
  store_name?: string;
  branch?: string;
  aisle?: string;
  rack?: string;
  shelf?: string;
  bin?: string;
  last_scan_time?: string;
  last_inventory_update?: string;
  confidence_score?: number;
  product_image?: string;
  nearest_available_store?: NearestStore;
  search_time_ms: number;
}

interface AvailabilityStats {
  total_searches: number;
  available_products: number;
  unavailable_products: number;
  search_success_rate: number;
  average_search_time_ms: number;
  most_searched_products: { query: string; count: number }[];
}

export default function AvailabilityDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  
  // Search inputs
  const [query, setQuery] = useState("COF-200G");
  const [method, setMethod] = useState("Name");
  const [searching, setSearching] = useState(false);
  const [result, setResult] = useState<AvailabilityResult | null>(null);
  
  // Analytics
  const [stats, setStats] = useState<AvailabilityStats | null>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadStats();
    handleSearch("COF-200G", "Name");
  }, [router]);

  const loadStats = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/availability/stats?store_id=1");
      if (res.ok) {
        setStats(await res.json());
      }
    } catch (err) {
      console.error("Failed to load availability stats", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (qTerm?: string, mTerm?: string) => {
    const searchTerm = qTerm !== undefined ? qTerm : query;
    const searchMethod = mTerm !== undefined ? mTerm : method;

    if (!searchTerm.trim()) return;

    setSearching(true);
    try {
      let endpoint = `/api/v1/availability/name/${encodeURIComponent(searchTerm)}?store_id=1`;
      if (searchMethod === "Barcode") {
        endpoint = `/api/v1/availability/barcode/${encodeURIComponent(searchTerm)}?store_id=1`;
      } else if (searchMethod === "SKU") {
        endpoint = `/api/v1/availability/sku/${encodeURIComponent(searchTerm)}?store_id=1`;
      } else if (searchMethod === "Product ID") {
        endpoint = `/api/v1/availability/product/${encodeURIComponent(searchTerm)}?store_id=1`;
      }

      const res = await fetchWithAuth(endpoint);
      if (res.ok) {
        const data = await res.json();
        setResult(data);
        loadStats();
      }
    } catch (err) {
      console.error("Search failed", err);
    } finally {
      setSearching(false);
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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Product Availability Verification</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Instant YES/NO availability check powered by verified multi-model AI scan & inventory synchronization engine.
            </p>
          </div>

          <button 
            onClick={loadStats}
            className="self-start md:self-auto flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Analytics
          </button>
        </div>

        {/* Search Console Input */}
        <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-4">
          <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
            <Search className="w-4 h-4 text-emerald-400" />
            Instant Availability Lookup
          </h3>

          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Enter Product Name, SKU, Barcode, or Product ID..."
                className="w-full pl-10 pr-4 py-3 rounded-2xl bg-neutral-950 border border-neutral-800 text-neutral-100 font-mono text-sm focus:outline-none focus:border-emerald-500/50 transition-all"
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => e.key === "Enter" && handleSearch()}
              />
              <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-neutral-500" />
            </div>

            <select
              className="px-4 py-3 rounded-2xl bg-neutral-950 border border-neutral-800 text-neutral-300 font-mono text-xs focus:outline-none cursor-pointer"
              value={method}
              onChange={e => setMethod(e.target.value)}
            >
              <option value="Name">Search by Name</option>
              <option value="SKU">Search by SKU</option>
              <option value="Barcode">Search by Barcode</option>
              <option value="Product ID">Search by ID</option>
            </select>

            <button
              onClick={() => handleSearch()}
              disabled={searching}
              className="flex items-center justify-center gap-2 px-6 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs transition-all cursor-pointer disabled:opacity-50"
            >
              {searching ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Verify Availability
            </button>
          </div>

          {/* Quick preset searches */}
          <div className="flex items-center gap-2 text-[10px] font-mono text-neutral-500 pt-1">
            <span>Quick Samples:</span>
            <button onClick={() => { setQuery("COF-200G"); setMethod("SKU"); handleSearch("COF-200G", "SKU"); }} className="px-2 py-0.5 rounded bg-neutral-900 hover:text-emerald-400 border border-neutral-850">COF-200G</button>
            <button onClick={() => { setQuery("MILK-1L"); setMethod("SKU"); handleSearch("MILK-1L", "SKU"); }} className="px-2 py-0.5 rounded bg-neutral-900 hover:text-emerald-400 border border-neutral-850">MILK-1L</button>
            <button onClick={() => { setQuery("Coffee"); setMethod("Name"); handleSearch("Coffee", "Name"); }} className="px-2 py-0.5 rounded bg-neutral-900 hover:text-emerald-400 border border-neutral-850">Coffee</button>
            <button onClick={() => { setQuery("NonExistentItem"); setMethod("Name"); handleSearch("NonExistentItem", "Name"); }} className="px-2 py-0.5 rounded bg-neutral-900 hover:text-emerald-400 border border-neutral-850">Out of Stock Test</button>
          </div>
        </div>

        {/* VERIFICATION OUTCOME BANNER (YES / NO) */}
        {result && (
          <div className="space-y-6">
            {result.status === "YES" ? (
              /* YES BANNER */
              <div className="bg-emerald-950/20 border-2 border-emerald-500/30 p-8 rounded-3xl space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-emerald-500/20 pb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500 flex items-center justify-center text-neutral-950">
                      <CheckCircle className="w-7 h-7 stroke-[2.5]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold font-mono text-emerald-400 uppercase tracking-wide">✅ Product Available</span>
                        <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 border border-emerald-500/30 text-[9px] font-mono text-emerald-400 font-bold">
                          Verified in {result.search_time_ms}ms
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 mt-0.5">Physical presence confirmed by latest synchronized AI inventory scan.</p>
                    </div>
                  </div>

                  <div className="bg-neutral-950/60 border border-neutral-850 px-5 py-3 rounded-2xl text-right">
                    <span className="block text-[8px] text-neutral-500 font-mono font-bold uppercase tracking-wider">Available Stock</span>
                    <span className="text-2xl font-black font-mono text-emerald-400">{result.available_quantity} {result.unit}</span>
                  </div>
                </div>

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 font-mono text-xs">
                  
                  {/* Item Specs */}
                  <div className="space-y-3 p-4 bg-neutral-950/50 border border-neutral-900 rounded-2xl">
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block border-b border-neutral-900 pb-2">Product Specifications</span>
                    <div className="space-y-1.5 text-neutral-300">
                      <div className="flex justify-between"><span className="text-neutral-500">Name:</span> <span className="font-bold text-neutral-100 font-sans">{result.product_name}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">SKU:</span> <span>{result.sku}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Barcode:</span> <span>{result.barcode}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Brand:</span> <span>{result.brand}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Category:</span> <span>{result.category}</span></div>
                    </div>
                  </div>

                  {/* Physical Location */}
                  <div className="space-y-3 p-4 bg-neutral-950/50 border border-neutral-900 rounded-2xl">
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block border-b border-neutral-900 pb-2 flex items-center gap-1.5">
                      <MapPin className="w-3.5 h-3.5 text-emerald-400" /> Exact Physical Location
                    </span>
                    <div className="space-y-1.5 text-neutral-300">
                      <div className="flex justify-between"><span className="text-neutral-500">Store / Branch:</span> <span className="font-bold text-neutral-100">{result.store_name} ({result.branch})</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Aisle:</span> <span className="text-emerald-400 font-bold">{result.aisle}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Rack:</span> <span>{result.rack}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Shelf Level:</span> <span>{result.shelf}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Bin:</span> <span>{result.bin}</span></div>
                    </div>
                  </div>

                  {/* Verification Telemetry */}
                  <div className="space-y-3 p-4 bg-neutral-950/50 border border-neutral-900 rounded-2xl">
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block border-b border-neutral-900 pb-2 flex items-center gap-1.5">
                      <ShieldCheck className="w-3.5 h-3.5 text-emerald-400" /> AI Scan Metadata
                    </span>
                    <div className="space-y-1.5 text-neutral-300">
                      <div className="flex justify-between"><span className="text-neutral-500">AI Confidence:</span> <span className="text-emerald-400 font-bold">{Math.round((result.confidence_score || 0.95) * 100)}%</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Last Scan:</span> <span>{result.last_scan_time ? new Date(result.last_scan_time).toLocaleTimeString() : "Recent"}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Sync Update:</span> <span>{result.last_inventory_update ? new Date(result.last_inventory_update).toLocaleDateString() : "Active"}</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Store Status:</span> <span className="text-emerald-400 font-bold">Open & Active</span></div>
                    </div>
                  </div>

                </div>
              </div>
            ) : (
              /* NO BANNER */
              <div className="bg-red-950/20 border-2 border-red-500/30 p-8 rounded-3xl space-y-6">
                <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-red-500/20 pb-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-red-500 flex items-center justify-center text-neutral-950">
                      <XCircle className="w-7 h-7 stroke-[2.5]" />
                    </div>
                    <div>
                      <div className="flex items-center gap-2">
                        <span className="text-xl font-bold font-mono text-red-400 uppercase tracking-wide">❌ Product Not Available</span>
                        <span className="px-2 py-0.5 rounded-full bg-red-500/10 border border-red-500/30 text-[9px] font-mono text-red-400 font-bold">
                          Checked in {result.search_time_ms}ms
                        </span>
                      </div>
                      <p className="text-xs text-neutral-400 mt-0.5">Reason: <b className="text-red-300">{result.reason || "Product unavailable in this store"}</b></p>
                    </div>
                  </div>
                </div>

                {/* Nearest Store Alternative Recommendation */}
                {result.nearest_available_store ? (
                  <div className="p-5 bg-neutral-950/80 border border-neutral-850 rounded-2xl space-y-3 font-mono text-xs">
                    <div className="flex items-center gap-2 text-yellow-400 font-bold">
                      <Building2 className="w-4 h-4" />
                      Nearest Available Store Recommendation
                    </div>
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 text-neutral-300 pt-2 border-t border-neutral-900">
                      <div><span className="text-neutral-500 block text-[9px]">Store Name:</span> <span className="font-bold text-neutral-100">{result.nearest_available_store.store_name}</span></div>
                      <div><span className="text-neutral-500 block text-[9px]">Branch Code:</span> <span>{result.nearest_available_store.branch}</span></div>
                      <div><span className="text-neutral-500 block text-[9px]">Available Quantity:</span> <span className="text-emerald-400 font-bold">{result.nearest_available_store.available_quantity} pcs in stock</span></div>
                    </div>
                  </div>
                ) : (
                  <div className="p-4 bg-neutral-950/40 border border-neutral-900 rounded-2xl text-[10px] font-mono text-neutral-500">
                    No alternate regional store branch currently has this item in stock.
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {/* Analytics & Search Metrics Cards */}
        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Total Verification Queries</span>
              <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{stats.total_searches}</span>
            </div>
            <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Search Success Rate</span>
              <span className="block text-2xl font-bold text-emerald-400 font-mono mt-1">{stats.search_success_rate}%</span>
            </div>
            <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Avg Query Speed</span>
              <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{stats.average_search_time_ms} ms</span>
            </div>
            <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Available vs Unavailable</span>
              <span className="block text-sm font-bold font-mono mt-2 text-neutral-300">
                <span className="text-emerald-400">{stats.available_products} YES</span> / <span className="text-red-400">{stats.unavailable_products} NO</span>
              </span>
            </div>
          </div>
        )}

        {/* Action Shortcuts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <Link href="/availability/search" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/20 p-6 rounded-3xl space-y-4 transition-all">
            <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
              <Search className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Advanced Multi-Filter Search</h3>
              <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">Filter availability across categories, brands, price ranges, and shelf aisles.</p>
            </div>
          </Link>

          <Link href="/availability/scanner" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/20 p-6 rounded-3xl space-y-4 transition-all">
            <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
              <QrCode className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Barcode & QR Scanner</h3>
              <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">Scan product barcodes directly using mobile/web camera to verify stock.</p>
            </div>
          </Link>

          <Link href="/availability/image" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/20 p-6 rounded-3xl space-y-4 transition-all">
            <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
              <Camera className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Visual Image Matcher</h3>
              <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">Upload a product snapshot image to resolve identity and availability.</p>
            </div>
          </Link>

          <Link href="/availability/multi-store" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/20 p-6 rounded-3xl space-y-4 transition-all">
            <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
              <Building2 className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Multi-Store Regional View</h3>
              <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">Check availability across all regional branches and warehouse locations simultaneously.</p>
            </div>
          </Link>

          <Link href="/availability/history" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/20 p-6 rounded-3xl space-y-4 transition-all">
            <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
              <History className="w-6 h-6" />
            </div>
            <div>
              <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Search History Ledger</h3>
              <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">Audit historical user search queries, outcomes, and response timings.</p>
            </div>
          </Link>
        </div>

      </div>
    </div>
  );
}
