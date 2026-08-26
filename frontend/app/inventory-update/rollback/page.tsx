"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Trash2, 
  RotateCw, 
  Loader2, 
  ShieldAlert, 
  Check, 
  Clock
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Snapshot {
  tag: string;
  records_count: number;
  created_at: string;
}

export default function RollbackCenterPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [snapshots, setSnapshots] = useState<Snapshot[]>([]);
  const [selectedTag, setSelectedTag] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadSnapshots();
  }, [router]);

  const loadSnapshots = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/snapshots?store_id=1");
      if (res.ok) {
        setSnapshots(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleTriggerRollback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedTag) return;

    setActionLoading(true);
    setActionSuccess(false);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/rollback", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          rollback_batch_tag: selectedTag,
          store_id: 1
        })
      });
      if (res.ok) {
        setActionSuccess(true);
        setSelectedTag("");
        loadSnapshots();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Rollback Center</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Revert bulk stock adjustments by restoring previous database snapshots tags.
            </p>
          </div>

          <button 
            onClick={loadSnapshots}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Snapshots
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Retrieving database snapshots tags...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Col: Rollback triggers forms */}
            <div className="lg:col-span-2 space-y-6">
              
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
                  <Trash2 className="w-5 h-5 text-emerald-400" />
                  Initiate Reversion Snapshot
                </h3>
                
                {actionSuccess && (
                  <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-xs font-mono">
                    Snapshot rollback completed successfully. Previous stock quantities restored.
                  </div>
                )}

                <form onSubmit={handleTriggerRollback} className="space-y-4 pt-4 border-t border-neutral-900/60 font-mono text-xs">
                  <div className="space-y-2">
                    <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider">Select Snapshot Tag</label>
                    <select
                      required
                      className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-305 text-xs focus:outline-none"
                      value={selectedTag}
                      onChange={e => setSelectedTag(e.target.value)}
                    >
                      <option value="">[Choose snapshot points]</option>
                      {snapshots.map(s => (
                        <option key={s.tag} value={s.tag}>
                          Tag: {s.tag} ({s.records_count} records) - {new Date(s.created_at).toLocaleString()}
                        </option>
                      ))}
                    </select>
                  </div>

                  <button
                    type="submit"
                    disabled={actionLoading || !selectedTag}
                    className="w-full flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-red-500 text-neutral-950 text-xs font-bold hover:bg-red-405 hover:bg-red-400 transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    {actionLoading ? <Loader2 className="w-4 h-4 animate-spin text-neutral-950" /> : "Confirm & Restore Snapshot"}
                  </button>
                </form>
              </div>

            </div>

            {/* Right Col: Warnings guidelines */}
            <div className="space-y-6">
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                  <ShieldAlert className="w-5 h-5 text-red-450 text-red-450" />
                  Caution Rollback Actions
                </h4>
                <p className="text-[10px] text-neutral-550 leading-relaxed font-sans">
                  Restoring snapshots overwrites current quantity values inside the stock item records. This override is audited in adjustments logs.
                </p>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
