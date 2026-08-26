"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Building2, 
  RotateCw, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Search
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface StoreBranch {
  id: number;
  name: string;
  location: string;
  status: "YES" | "NO";
  quantity: number;
}

export default function MultiStorePage() {
  const router = useRouter();
  const [skuQuery, setSkuQuery] = useState("COF-200G");
  const [loading, setLoading] = useState(false);
  const [stores, setStores] = useState<StoreBranch[]>([]);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    handleCompareStores("COF-200G");
  }, [router]);

  const handleCompareStores = async (qTerm?: string) => {
    const query = qTerm || skuQuery;
    if (!query.trim()) return;

    setLoading(true);
    try {
      // Query stores 1, 2, 3 in parallel
      const storeIds = [1, 2, 3];
      const results: StoreBranch[] = [];

      for (const sid of storeIds) {
        const res = await fetchWithAuth(`/api/v1/availability/sku/${encodeURIComponent(query)}?store_id=${sid}`);
        if (res.ok) {
          const data = await res.json();
          results.push({
            id: sid,
            name: sid === 1 ? "Main Supermarket (HQ)" : sid === 2 ? "Downtown Branch" : "Northside Warehouse",
            location: sid === 1 ? "Central Ave" : sid === 2 ? "Downtown" : "Industrial Zone",
            status: data.status,
            quantity: data.available_quantity || 0
          });
        }
      }

      setStores(results);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-5xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
          <Link href="/availability" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Multi-Store Regional View</h1>
            <p className="text-xs text-neutral-500 font-sans mt-0.5">Compare product stock availability across all regional store branches & warehouses.</p>
          </div>
        </div>

        {/* Input Console */}
        <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-4">
          <div className="flex gap-3">
            <input
              type="text"
              placeholder="Enter SKU or Product Name..."
              className="flex-1 px-4 py-3 rounded-2xl bg-neutral-950 border border-neutral-800 text-neutral-100 font-mono text-xs focus:outline-none"
              value={skuQuery}
              onChange={e => setSkuQuery(e.target.value)}
            />
            <button
              onClick={() => handleCompareStores()}
              disabled={loading}
              className="px-6 py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-colors"
            >
              {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Compare Stores"}
            </button>
          </div>
        </div>

        {/* Store Comparison Grid */}
        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Comparing regional inventory databases...</p>
          </div>
        ) : (
          <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
            <table className="w-full text-left text-xs border-collapse font-mono">
              <thead>
                <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] bg-neutral-950/40">
                  <th className="px-6 py-4">Store Branch</th>
                  <th className="px-6 py-4">Location</th>
                  <th className="px-6 py-4 text-center">Availability Status</th>
                  <th className="px-6 py-4 text-right">Available Stock</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                {stores.map(s => (
                  <tr key={s.id} className="hover:bg-neutral-900/10 transition-colors">
                    <td className="px-6 py-4 font-bold text-neutral-100">{s.name}</td>
                    <td className="px-6 py-4 text-neutral-400">{s.location}</td>
                    <td className="px-6 py-4 text-center">
                      <span className={`px-2.5 py-1 rounded text-[9px] font-bold uppercase border tracking-wider ${
                        s.status === 'YES' ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' : 'bg-red-950/20 text-red-400 border-red-500/20'
                      }`}>
                        {s.status === 'YES' ? '✅ YES Available' : '❌ NO Stock'}
                      </span>
                    </td>
                    <td className="px-6 py-4 text-right font-bold text-neutral-100">
                      {s.quantity} pcs
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

      </div>
    </div>
  );
}
