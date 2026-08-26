"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  CheckCircle, 
  XCircle, 
  Loader2, 
  Activity, 
  Layers, 
  ShieldAlert, 
  Check, 
  X, 
  Edit,
  FolderOpen
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Candidate {
  id: number;
  product_id?: number;
  product_name: string;
  yolo_score: number;
  ocr_score: number;
  barcode_score: number;
  embedding_score: number;
  combined_score: number;
}

interface Feedback {
  id: number;
  corrected_product_id?: number;
  notes?: string;
  created_at: string;
}

interface Decision {
  id: number;
  video_id?: number;
  store_id?: number;
  selected_product_id?: number;
  raw_yolo_label?: string;
  raw_ocr_text?: string;
  raw_barcode?: string;
  final_confidence: number;
  status: string;
  explanation?: {
    reason: string;
    timeline: string[];
    weights_used?: Record<string, number>;
  };
  created_at: string;
  candidates: Candidate[];
  feedback: Feedback[];
}

interface Product {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  category?: string;
}

function DecisionViewerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const decisionId = searchParams.get("id") || "";

  const [loading, setLoading] = useState(true);
  const [decision, setDecision] = useState<Decision | null>(null);
  const [products, setProducts] = useState<Product[]>([]);
  
  // Correction inputs
  const [correctedProduct, setCorrectedProduct] = useState("");
  const [correctionNotes, setCorrectionNotes] = useState("");
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    if (decisionId) loadDetails();
  }, [decisionId, router]);

  const loadDetails = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${decisionId}`);
      if (res.ok) {
        setDecision(await res.json());
      }
      
      const resProd = await fetchWithAuth("/api/v1/products");
      if (resProd.ok) {
        setProducts(await resProd.json());
      }
    } catch (err) {
      console.error("Failed to load decision candidates audit trail", err);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async () => {
    if (!decision) return;
    setActionLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${decision.id}/approve`, { method: "POST" });
      if (res.ok) {
        setDecision(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleReject = async () => {
    if (!decision) return;
    setActionLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${decision.id}/reject`, { method: "POST" });
      if (res.ok) {
        setDecision(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleSubmitFeedback = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!decision || !correctedProduct) return;
    
    setActionLoading(true);
    setActionSuccess(false);
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${decision.id}/feedback`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          corrected_product_id: parseInt(correctedProduct),
          notes: correctionNotes
        })
      });
      if (res.ok) {
        setDecision(await res.json());
        setActionSuccess(true);
        setCorrectionNotes("");
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
        <p className="text-xs text-neutral-500 font-mono">Loading candidates matching scores...</p>
      </div>
    );
  }

  if (!decision) {
    return (
      <div className="text-center py-20 text-neutral-500 font-mono text-xs">
        Decision record not found or inaccessible.
      </div>
    );
  }

  // Find currently resolved product metadata
  const currentProd = products.find(p => p.id === decision.selected_product_id);

  return (
    <div className="space-y-10">
      
      {/* Header navigation bar */}
      <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
        <Link href="/decision" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Decision Audit Details</h1>
          <p className="text-xs text-neutral-500 font-sans mt-0.5">Decision ID: #{decision.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Col 1 & 2: Audit Trail details */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Card: Fused result Summary */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Layers className="w-5 h-5 text-emerald-400" />
              Final Selection Summary
            </h3>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-6 pt-4 border-t border-neutral-900/60">
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Assigned Catalog Item</span>
                {currentProd ? (
                  <div>
                    <span className="block text-sm font-bold text-emerald-400">{currentProd.name}</span>
                    <span className="block text-[10px] text-neutral-500 font-mono mt-0.5">SKU: {currentProd.sku} | Category: {currentProd.category}</span>
                  </div>
                ) : (
                  <span className="block text-xs text-red-400 font-mono uppercase tracking-wider">Unknown / Mismatched Product</span>
                )}
              </div>

              <div className="space-y-1">
                <span className="text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Fuzzed Score Confidence</span>
                <div className="flex items-center gap-2">
                  <span className="text-2xl font-bold font-mono text-neutral-100">{Math.round(decision.final_confidence * 100)}%</span>
                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${
                    decision.status === 'Approved' ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' :
                    decision.status === 'Pending Review' ? 'bg-yellow-950/20 text-yellow-400 border-yellow-500/20' :
                    decision.status === 'Corrected' ? 'bg-blue-950/20 text-blue-400 border-blue-500/20' :
                    'bg-red-950/20 text-red-400 border-red-500/20'
                  }`}>
                    {decision.status}
                  </span>
                </div>
              </div>
            </div>

            {/* Input Signatures info */}
            <div className="grid grid-cols-3 gap-4 pt-4 border-t border-neutral-900/60 text-xs">
              <div className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider font-mono">YOLO Label</span>
                <span className="block text-neutral-250 font-mono truncate">{decision.raw_yolo_label || "None"}</span>
              </div>
              <div className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider font-mono">OCR Text</span>
                <span className="block text-neutral-250 font-mono truncate">{decision.raw_ocr_text || "None"}</span>
              </div>
              <div className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider font-mono">Barcode</span>
                <span className="block text-neutral-250 font-mono truncate">{decision.raw_barcode || "None"}</span>
              </div>
            </div>
          </div>

          {/* Card: Candidates scores details */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Activity className="w-5 h-5 text-emerald-400" />
              Sensor Fusion Scoreboards Comparison
            </h3>

            <div className="border border-neutral-900 rounded-2xl overflow-hidden pt-1">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[9px] font-mono bg-neutral-950/40">
                    <th className="px-4 py-3">Candidate Product Name</th>
                    <th className="px-3 py-3 text-center">YOLO</th>
                    <th className="px-3 py-3 text-center">OCR</th>
                    <th className="px-3 py-3 text-center">Barcode</th>
                    <th className="px-3 py-3 text-center">Embedding</th>
                    <th className="px-4 py-3 text-right">Combined</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-350 font-mono">
                  {decision.candidates.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-neutral-500">No candidates scored for this signature payload.</td>
                    </tr>
                  ) : (
                    decision.candidates.map(cand => (
                      <tr key={cand.id} className="hover:bg-neutral-900/5">
                        <td className="px-4 py-3 font-sans font-bold text-neutral-250">
                          {cand.product_name}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {Math.round(cand.yolo_score * 100)}%
                        </td>
                        <td className="px-3 py-3 text-center">
                          {Math.round(cand.ocr_score * 100)}%
                        </td>
                        <td className="px-3 py-3 text-center">
                          {Math.round(cand.barcode_score * 100)}%
                        </td>
                        <td className="px-3 py-3 text-center">
                          {Math.round(cand.embedding_score * 100)}%
                        </td>
                        <td className="px-4 py-3 text-right font-bold text-emerald-400">
                          {Math.round(cand.combined_score * 100)}%
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Card: Explanation details timeline */}
          {decision.explanation?.timeline && (
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
                <ShieldAlert className="w-5 h-5 text-emerald-400" />
                Explainable Decision Workflow Trace
              </h3>

              <div className="space-y-4 pt-4 border-t border-neutral-900/60 font-mono text-xs">
                {decision.explanation.timeline.map((log, idx) => (
                  <div key={idx} className="flex gap-3 items-start">
                    <span className="text-emerald-500 font-bold">[{idx + 1}]</span>
                    <span className="text-neutral-400 leading-relaxed">{log}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Col 3: Manual Overrides Panel */}
        <div className="space-y-8">
          
          {/* Action queue controls */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Check className="w-5 h-5 text-emerald-400" />
              Resolution Approvals Queue
            </h3>
            <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
              Change selection state or reject predictions in audit records directly.
            </p>

            <div className="grid grid-cols-2 gap-3 pt-4 border-t border-neutral-900/60">
              <button
                onClick={handleApprove}
                disabled={actionLoading || decision.status === 'Approved'}
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 font-bold text-xs hover:bg-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
              >
                <Check className="w-3.5 h-3.5" /> Approve Match
              </button>
              <button
                onClick={handleReject}
                disabled={actionLoading || decision.status === 'Rejected'}
                className="flex items-center justify-center gap-1.5 px-3 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 font-bold text-xs transition-colors disabled:opacity-50 cursor-pointer"
              >
                <X className="w-3.5 h-3.5" /> Reject Match
              </button>
            </div>
          </div>

          {/* Feedback loops overrides form */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Edit className="w-5 h-5 text-emerald-400" />
              Manual Correction Override
            </h3>
            <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
              Override matching tags manually. Submitting corrections appends feedback loops boosting this item matching criteria in subsequent runs.
            </p>

            <form onSubmit={handleSubmitFeedback} className="space-y-4 pt-4 border-t border-neutral-900/60">
              <div className="space-y-2">
                <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider font-mono">Catalog Product Mappings</label>
                <select
                  required
                  className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                  value={correctedProduct}
                  onChange={e => setCorrectedProduct(e.target.value)}
                >
                  <option value="">[Choose Catalog Item]</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} (SKU: {p.sku})</option>
                  ))}
                </select>
              </div>

              <div className="space-y-2">
                <label className="block text-[9px] font-bold text-neutral-550 uppercase tracking-wider font-mono">Auditor Override Notes</label>
                <textarea
                  rows={3}
                  className="w-full px-3.5 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                  placeholder="State reason for manual correction..."
                  value={correctionNotes}
                  onChange={e => setCorrectionNotes(e.target.value)}
                />
              </div>

              {actionSuccess && (
                <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-[10px] font-mono">
                  Override saved. Target product re-assigned successfully.
                </div>
              )}

              <button
                type="submit"
                disabled={actionLoading || !correctedProduct}
                className="w-full flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold text-neutral-300 hover:border-emerald-500/20 hover:text-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
              >
                {actionLoading ? <Loader2 className="w-4 h-4 animate-spin text-emerald-400" /> : "Submit Override Correction"}
              </button>
            </form>
          </div>

          {/* Feedback Loop Logs list */}
          {decision.feedback && decision.feedback.length > 0 && (
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
                <FolderOpen className="w-5 h-5 text-emerald-400" />
                Correction History Logs
              </h3>

              <div className="space-y-4 pt-4 border-t border-neutral-900/60 text-xs">
                {decision.feedback.map(feed => {
                  const targetProd = products.find(p => p.id === feed.corrected_product_id);
                  return (
                    <div key={feed.id} className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-2 font-mono">
                      <div className="flex justify-between items-center text-[9px] text-neutral-550">
                        <span>Auditor ID: System</span>
                        <span>{new Date(feed.created_at).toLocaleDateString()}</span>
                      </div>
                      <span className="block text-emerald-400 font-sans font-bold">
                        Re-assigned: {targetProd ? targetProd.name : `Product ID: ${feed.corrected_product_id}`}
                      </span>
                      {feed.notes && <p className="text-[10px] text-neutral-500 italic mt-1">"{feed.notes}"</p>}
                    </div>
                  );
                })}
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}

export default function DecisionViewerPage() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Initializing query parameters...</p>
          </div>
        }>
          <DecisionViewerContent />
        </Suspense>
      </div>
    </div>
  );
}
