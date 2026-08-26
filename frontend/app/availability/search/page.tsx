"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Search, 
  Filter, 
  RotateCw, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  MapPin
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Product {
  id: number;
  name: string;
  sku: string;
  barcode: string;
  category: string;
  brand: string;
  price: number;
}

export default function AvailabilitySearchPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<Product[]>([]);
  
  // Filters
  const [query, setQuery] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("All");
  const [availabilityFilter, setAvailabilityFilter] = useState("All");
  const [verifyingId, setVerifyingId] = useState<number | null>(null);
  const [checkResults, setCheckResults] = useState<{ [id: number]: any }>({});

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadProducts();
  }, [router]);

  const loadProducts = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/products");
      if (res.ok) {
        setProducts(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyItem = async (prod: Product) => {
    setVerifyingId(prod.id);
    try {
      const res = await fetchWithAuth(`/api/v1/availability/product/${prod.id}?store_id=1`);
      if (res.ok) {
        const data = await res.json();
        setCheckResults(prev => ({ ...prev, [prod.id]: data }));
      }
    } catch (err) {
      console.error(err);
    } finally {
      setVerifyingId(null);
    }
  };

  const categories = ["All", ...Array.from(new Set(products.map(p => p.category).filter(Boolean)))];

  const filteredProducts = products.filter(p => {
    if (query && !p.name.toLowerCase().includes(query.toLowerCase()) && !p.sku.toLowerCase().includes(query.toLowerCase())) return false;
    if (selectedCategory !== "All" && p.category !== selectedCategory) return false;
    if (availabilityFilter !== "All") {
      const res = checkResults[p.id];
      if (availabilityFilter === "Available" && res && res.status !== "YES") return false;
      if (availabilityFilter === "Unavailable" && res && res.status !== "NO") return false;
    }
    return true;
  });

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/availability" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Advanced Multi-Filter Search</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Search and filter product catalog items with real-time AI availability verification checks.
            </p>
          </div>

          <button 
            onClick={loadProducts}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Catalog
          </button>
        </div>

        {/* Filters Panel */}
        <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 font-mono text-xs">
            
            <div className="space-y-1.5">
              <label className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">Search Query</label>
              <input
                type="text"
                placeholder="Product name or SKU..."
                className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-850 text-neutral-100 focus:outline-none"
                value={query}
                onChange={e => setQuery(e.target.value)}
              />
            </div>

            <div className="space-y-1.5">
              <label className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">Category Filter</label>
              <select
                className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-850 text-neutral-300 focus:outline-none cursor-pointer"
                value={selectedCategory}
                onChange={e => setSelectedCategory(e.target.value)}
              >
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>

            <div className="space-y-1.5">
              <label className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">Availability Filter</label>
              <select
                className="w-full px-3 py-2 rounded-xl bg-neutral-950 border border-neutral-850 text-neutral-300 focus:outline-none cursor-pointer"
                value={availabilityFilter}
                onChange={e => setAvailabilityFilter(e.target.value)}
              >
                <option value="All">All Items</option>
                <option value="Available">Only Available (YES)</option>
                <option value="Unavailable">Only Unavailable (NO)</option>
              </select>
            </div>

            <div className="flex items-end">
              <button
                onClick={() => { setQuery(""); setSelectedCategory("All"); setAvailabilityFilter("All"); }}
                className="w-full py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 font-bold text-xs cursor-pointer transition-colors"
              >
                Reset Filters
              </button>
            </div>

          </div>
        </div>

        {/* Results Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading product catalog list...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 font-mono text-xs">
            {filteredProducts.map(prod => {
              const res = checkResults[prod.id];

              return (
                <div key={prod.id} className="bg-neutral-900/10 border border-neutral-900 p-5 rounded-3xl space-y-4 flex flex-col justify-between">
                  <div className="space-y-2">
                    <div className="flex justify-between items-start">
                      <span className="text-[9px] text-neutral-550 font-bold uppercase tracking-wider">ID #{prod.id}</span>
                      {res && (
                        <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${
                          res.status === 'YES' ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' : 'bg-red-950/20 text-red-400 border-red-500/20'
                        }`}>
                          {res.status === 'YES' ? '✅ Available' : '❌ Unavailable'}
                        </span>
                      )}
                    </div>
                    <h3 className="font-sans font-bold text-neutral-100 text-sm">{prod.name}</h3>
                    <p className="text-[10px] text-neutral-500">SKU: {prod.sku} • Category: {prod.category}</p>
                  </div>

                  {res && res.status === "YES" && (
                    <div className="p-3 bg-neutral-950/50 border border-neutral-900 rounded-xl space-y-1 text-[10px]">
                      <div className="flex justify-between"><span className="text-neutral-500">Stock:</span> <span className="text-emerald-400 font-bold">{res.available_quantity} pcs</span></div>
                      <div className="flex justify-between"><span className="text-neutral-500">Location:</span> <span>{res.aisle}, {res.shelf}</span></div>
                    </div>
                  )}

                  <button
                    onClick={() => handleVerifyItem(prod)}
                    disabled={verifyingId === prod.id}
                    className="w-full py-2.5 rounded-xl bg-neutral-900 hover:bg-neutral-850 border border-neutral-800 text-neutral-200 hover:text-emerald-400 font-bold text-xs cursor-pointer transition-colors flex items-center justify-center gap-1.5"
                  >
                    {verifyingId === prod.id ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : "Verify Availability"}
                  </button>
                </div>
              );
            })}
          </div>
        )}

      </div>
    </div>
  );
}
