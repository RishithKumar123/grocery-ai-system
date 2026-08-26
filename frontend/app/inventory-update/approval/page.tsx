"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  RotateCw, 
  Loader2, 
  Check, 
  X, 
  ThumbsUp,
  ThumbsDown,
  AlertOctagon
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface UpdateDetails {
  id: number;
  product_name: string;
  sku: string;
  previous_quantity: number;
  new_quantity: number;
  variance: number;
  confidence: number;
}

interface ApprovalRequest {
  id: number;
  inventory_update_id: number;
  requested_by: string;
  status: string;
  update_details: UpdateDetails;
}

export default function ApprovalQueuePage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [requests, setRequests] = useState<ApprovalRequest[]>([]);
  const [actionLoading, setActionLoading] = useState<number | null>(null);
  const [notes, setNotes] = useState("");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadRequests();
  }, [router]);

  const loadRequests = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/inventory-update/approval-queue");
      if (res.ok) {
        setRequests(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id: number, updateId: number) => {
    setActionLoading(id);
    try {
      const res = await fetchWithAuth(`/api/v1/inventory-update/approve/${updateId}?notes=${encodeURIComponent(notes)}`, {
        method: "POST"
      });
      if (res.ok) {
        setNotes("");
        loadRequests();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const handleReject = async (id: number, updateId: number) => {
    setActionLoading(id);
    try {
      const res = await fetchWithAuth(`/api/v1/inventory-update/reject/${updateId}?notes=${encodeURIComponent(notes)}`, {
        method: "POST"
      });
      if (res.ok) {
        setNotes("");
        loadRequests();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(null);
    }
  };

  const pendingRequests = requests.filter(r => r.status === "Pending");

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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Approval Queue</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Authorizes scanner updates that trigger high variance deviations limit parameters.
            </p>
          </div>

          <button 
            onClick={loadRequests}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Queue
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading approval requests...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Col: Requests checklist list */}
            <div className="lg:col-span-2 space-y-6">
              {pendingRequests.length === 0 ? (
                <div className="text-center py-20 bg-neutral-900/10 border border-neutral-900 rounded-3xl text-neutral-550 font-mono text-xs">
                  No pending variance authorization requests.
                </div>
              ) : (
                pendingRequests.map(req => (
                  <div key={req.id} className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                    <div className="flex justify-between items-center">
                      <div className="space-y-1">
                        <span className="block text-[8px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Request ID: #{req.id}</span>
                        <h3 className="text-sm font-bold text-neutral-200 font-sans">{req.update_details.product_name}</h3>
                        <p className="text-[10px] text-neutral-500 font-mono">SKU: {req.update_details.sku}</p>
                      </div>

                      <div className="text-right font-mono text-xs">
                        <span className="block text-[8px] text-neutral-550 font-bold uppercase">Variance</span>
                        <span className={`block text-sm font-bold ${req.update_details.variance >= 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                          {req.update_details.variance >= 0 ? `+${req.update_details.variance}` : req.update_details.variance} items
                        </span>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-4 pt-4 border-t border-neutral-900/60 font-mono text-xs text-neutral-450">
                      <div>
                        <span className="block text-[8px] text-neutral-550 font-bold uppercase">Database Stock</span>
                        <span>{req.update_details.previous_quantity} items</span>
                      </div>
                      <div>
                        <span className="block text-[8px] text-neutral-550 font-bold uppercase">Scanner Count</span>
                        <span className="text-neutral-100 font-bold">{req.update_details.new_quantity} items</span>
                      </div>
                      <div>
                        <span className="block text-[8px] text-neutral-550 font-bold uppercase">Confidence</span>
                        <span>{Math.round(req.update_details.confidence * 100)}%</span>
                      </div>
                    </div>

                    <div className="flex gap-4 pt-4 border-t border-neutral-900/60 items-center">
                      <input
                        type="text"
                        placeholder="Optional reviewer notes..."
                        className="flex-1 px-3 py-2 rounded-xl border border-neutral-850 bg-neutral-950 text-neutral-300 text-xs font-mono focus:outline-none"
                        value={notes}
                        onChange={e => setNotes(e.target.value)}
                      />

                      <button
                        onClick={() => handleApprove(req.id, req.inventory_update_id)}
                        disabled={actionLoading !== null}
                        className="flex items-center gap-1 px-3 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs cursor-pointer transition-colors"
                      >
                        <ThumbsUp className="w-3.5 h-3.5" /> Approve
                      </button>

                      <button
                        onClick={() => handleReject(req.id, req.inventory_update_id)}
                        disabled={actionLoading !== null}
                        className="flex items-center gap-1 px-3 py-2 rounded-xl bg-red-500 hover:bg-red-400 text-neutral-950 font-bold text-xs cursor-pointer transition-colors"
                      >
                        <ThumbsDown className="w-3.5 h-3.5" /> Reject
                      </button>
                    </div>

                  </div>
                ))
              )}
            </div>

            {/* Right Col: Stats preview */}
            <div className="space-y-6">
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6 font-sans">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                  <AlertOctagon className="w-5 h-5 text-yellow-400" />
                  Variance Warnings guidelines
                </h4>
                <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
                  Variance routing rules are enforced dynamically by Aetheria Sync. Rejections will preserve previous database quantities.
                </p>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
