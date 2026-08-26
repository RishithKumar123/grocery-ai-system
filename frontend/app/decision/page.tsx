"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ShieldAlert, 
  ArrowLeft, 
  Settings2, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Sliders, 
  Activity, 
  FileText, 
  ThumbsUp, 
  ThumbsDown,
  Loader2,
  RefreshCw,
  Plus
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

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
}

interface Rule {
  id: number;
  rule_key: string;
  rule_name: string;
  rule_type: string;
  value: string;
  description?: string;
  is_active: boolean;
}

interface Weights {
  id: number;
  yolo_weight: number;
  ocr_weight: number;
  barcode_weight: number;
  embedding_weight: number;
  historical_weight: number;
  is_active: boolean;
}

interface Analytics {
  total_decisions: number;
  conflict_rate: number;
  unknown_rate: number;
  average_confidence: number;
  accuracy: number;
}

export default function DecisionDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<"queue" | "weights" | "rules">("queue");

  // State payloads
  const [decisions, setDecisions] = useState<Decision[]>([]);
  const [rules, setRules] = useState<Rule[]>([]);
  const [weights, setWeights] = useState<Weights | null>(null);
  const [analytics, setAnalytics] = useState<Analytics | null>(null);

  // Sliders input
  const [yoloW, setYoloW] = useState(0.25);
  const [ocrW, setOcrW] = useState(0.25);
  const [barcodeW, setBarcodeW] = useState(0.30);
  const [embeddingW, setEmbeddingW] = useState(0.20);
  const [saveLoading, setSaveLoading] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  const [weightsError, setWeightsError] = useState<string | null>(null);

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
      // 1. History
      const resHist = await fetchWithAuth("/api/v1/decisions/history");
      if (resHist.ok) {
        setDecisions(await resHist.json());
      }

      // 2. Rules
      const resRules = await fetchWithAuth("/api/v1/decisions/rules");
      if (resRules.ok) {
        setRules(await resRules.json());
      }

      // 3. Weights
      const resWeights = await fetchWithAuth("/api/v1/decisions/weights");
      if (resWeights.ok) {
        const wData = await resWeights.json();
        setWeights(wData);
        setYoloW(wData.yolo_weight);
        setOcrW(wData.ocr_weight);
        setBarcodeW(wData.barcode_weight);
        setEmbeddingW(wData.embedding_weight);
      }

      // 4. Analytics
      const resAnal = await fetchWithAuth("/api/v1/decisions/analytics/summary");
      if (resAnal.ok) {
        setAnalytics(await resAnal.json());
      }
    } catch (err) {
      console.error("Failed to load decisions telemetry data", err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRule = async (key: string, val: string, active: boolean) => {
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/rules/${key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: val, is_active: active })
      });
      if (res.ok) {
        // Refresh local rules state
        setRules(prev => prev.map(r => r.rule_key === key ? { ...r, value: val, is_active: active } : r));
      }
    } catch (err) {
      console.error("Failed to update business rule value", err);
    }
  };

  const handleSaveWeights = async () => {
    setWeightsError(null);
    setSaveSuccess(false);
    const sum = yoloW + ocrW + barcodeW + embeddingW;
    if (Math.abs(sum - 1.0) > 0.05) {
      setWeightsError(`Weight coefficients must normalize to 1.0. Current sum: ${sum.toFixed(2)}`);
      return;
    }

    setSaveLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/decisions/weights", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          yolo_weight: yoloW,
          ocr_weight: ocrW,
          barcode_weight: barcodeW,
          embedding_weight: embeddingW
        })
      });
      if (res.ok) {
        setSaveSuccess(true);
        const updated = await res.json();
        setWeights(updated);
        // Refresh telemetry
        const resAnal = await fetchWithAuth("/api/v1/decisions/analytics/summary");
        if (resAnal.ok) setAnalytics(await resAnal.json());
      } else {
        const errorData = await res.json();
        setWeightsError(errorData?.detail || "Weights configuration rejected by server.");
      }
    } catch (err) {
      console.error("Weights configuration save exception", err);
      setWeightsError("Failed to communicate weights parameter settings.");
    } finally {
      setSaveLoading(false);
    }
  };

  const handleQuickApprove = async (id: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${id}/approve`, { method: "POST" });
      if (res.ok) {
        setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "Approved" } : d));
        // Refresh stats
        const resAnal = await fetchWithAuth("/api/v1/decisions/analytics/summary");
        if (resAnal.ok) setAnalytics(await resAnal.json());
      }
    } catch (err) {
      console.error("Failed to approve decision ID: " + id, err);
    }
  };

  const handleQuickReject = async (id: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/decisions/${id}/reject`, { method: "POST" });
      if (res.ok) {
        setDecisions(prev => prev.map(d => d.id === id ? { ...d, status: "Rejected" } : d));
        // Refresh stats
        const resAnal = await fetchWithAuth("/api/v1/decisions/analytics/summary");
        if (resAnal.ok) setAnalytics(await resAnal.json());
      }
    } catch (err) {
      console.error("Failed to reject decision ID: " + id, err);
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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Multi-Model Decision Desk</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Combines predictions from YOLOv11, OCR models, and Barcodes to yield a single verified classification truth.
            </p>
          </div>
          <button 
            onClick={loadData}
            className="self-start md:self-auto flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RefreshCw className="w-3.5 h-3.5" /> Refresh Telemetry
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Fusing decision engine parameters...</p>
          </div>
        ) : (
          <>
            {/* 1. Analytics Cards */}
            {analytics && (
              <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
                <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                  <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Total Decisions</span>
                  <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{analytics.total_decisions}</span>
                </div>
                <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                  <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Decision Accuracy</span>
                  <span className="block text-2xl font-bold text-emerald-400 font-mono mt-1">{analytics.accuracy}%</span>
                </div>
                <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                  <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Avg Confidence</span>
                  <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{analytics.average_confidence}%</span>
                </div>
                <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                  <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Conflict Resolution Rate</span>
                  <span className="block text-2xl font-bold text-yellow-400 font-mono mt-1">{analytics.conflict_rate}%</span>
                </div>
                <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                  <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Unknown Product Rate</span>
                  <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{analytics.unknown_rate}%</span>
                </div>
              </div>
            )}

            {/* Tab navigation links */}
            <div className="flex border-b border-neutral-900 gap-6">
              <button 
                onClick={() => setActiveTab("queue")}
                className={`pb-4 text-xs font-mono font-bold uppercase tracking-wider border-b-2 transition-colors cursor-pointer ${activeTab === 'queue' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-neutral-500 hover:text-neutral-350'}`}
              >
                Auditing History Queue
              </button>
              <button 
                onClick={() => setActiveTab("weights")}
                className={`pb-4 text-xs font-mono font-bold uppercase tracking-wider border-b-2 transition-colors cursor-pointer ${activeTab === 'weights' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-neutral-500 hover:text-neutral-350'}`}
              >
                Model Weights Config
              </button>
              <button 
                onClick={() => setActiveTab("rules")}
                className={`pb-4 text-xs font-mono font-bold uppercase tracking-wider border-b-2 transition-colors cursor-pointer ${activeTab === 'rules' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-neutral-500 hover:text-neutral-350'}`}
              >
                Decision Override Rules
              </button>
            </div>

            {/* TAB CONTENT */}

            {/* tab 1: Decisions History list */}
            {activeTab === "queue" && (
              <div className="space-y-6">
                <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
                  <div className="overflow-x-auto">
                    <table className="w-full text-left text-xs border-collapse">
                      <thead>
                        <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                          <th className="px-6 py-4">Decision ID</th>
                          <th className="px-6 py-4">Resolved Product ID</th>
                          <th className="px-6 py-4">Prediction Signatures (YOLO / OCR / Barcode)</th>
                          <th className="px-6 py-4 text-center">Confidence</th>
                          <th className="px-6 py-4 text-center">Status</th>
                          <th className="px-6 py-4 text-right">Actions</th>
                        </tr>
                      </thead>
                      <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                        {decisions.length === 0 ? (
                          <tr>
                            <td colSpan={6} className="text-center py-20 text-neutral-500 font-mono text-xs">
                              No historical decision predictions registered. Run scanning sweeps to test.
                            </td>
                          </tr>
                        ) : (
                          decisions.map(d => {
                            let statusColor = "bg-neutral-900 text-neutral-450 border-neutral-800";
                            if (d.status === "Approved") statusColor = "bg-emerald-950/20 text-emerald-400 border-emerald-500/20";
                            if (d.status === "Pending Review") statusColor = "bg-yellow-950/20 text-yellow-400 border-yellow-500/20";
                            if (d.status === "Corrected") statusColor = "bg-blue-950/20 text-blue-400 border-blue-500/20";
                            if (d.status === "Rejected") statusColor = "bg-red-950/20 text-red-400 border-red-500/20";

                            return (
                              <tr key={d.id} className="hover:bg-neutral-900/10 transition-colors">
                                <td className="px-6 py-4 font-mono font-bold text-neutral-400">
                                  #{d.id}
                                </td>
                                <td className="px-6 py-4 font-bold text-neutral-200">
                                  {d.selected_product_id ? (
                                    <span className="text-emerald-400">Product ID: {d.selected_product_id}</span>
                                  ) : (
                                    <span className="text-red-450 uppercase tracking-wider text-[10px] font-mono">Unknown / Unassigned</span>
                                  )}
                                  <span className="block text-[9px] text-neutral-550 font-sans mt-0.5 max-w-xs truncate" title={d.explanation?.reason}>
                                    {d.explanation?.reason || "Fusing sensor details..."}
                                  </span>
                                </td>
                                <td className="px-6 py-4 font-mono text-[10px] text-neutral-400">
                                  <div className="flex flex-col gap-0.5">
                                    <span>YOLO: <b className="text-neutral-200">{d.raw_yolo_label || "None"}</b></span>
                                    <span>OCR: <b className="text-neutral-200">{d.raw_ocr_text || "None"}</b></span>
                                    <span>Barcode: <b className="text-neutral-200">{d.raw_barcode || "None"}</b></span>
                                  </div>
                                </td>
                                <td className="px-6 py-4 text-center font-mono font-bold text-neutral-100">
                                  {Math.round(d.final_confidence * 100)}%
                                </td>
                                <td className="px-6 py-4 text-center">
                                  <span className={`px-2.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border ${statusColor}`}>
                                    {d.status}
                                  </span>
                                </td>
                                <td className="px-6 py-4 text-right">
                                  <div className="flex justify-end gap-2">
                                    <Link 
                                      href={`/decision/viewer?id=${d.id}`}
                                      className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-800 hover:border-emerald-500/20 text-[10px] font-bold font-mono text-neutral-350 hover:text-emerald-400 transition-colors"
                                    >
                                      Inspect Candidates
                                    </Link>
                                    {d.status === "Pending Review" && (
                                      <>
                                        <button 
                                          onClick={() => handleQuickApprove(d.id)}
                                          className="p-1 rounded bg-emerald-950/20 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500 hover:text-neutral-950 transition-all cursor-pointer"
                                          title="Quick Approve"
                                        >
                                          <ThumbsUp className="w-3.5 h-3.5" />
                                        </button>
                                        <button 
                                          onClick={() => handleQuickReject(d.id)}
                                          className="p-1 rounded bg-red-950/20 text-red-400 border border-red-500/20 hover:bg-red-500 hover:text-neutral-950 transition-all cursor-pointer"
                                          title="Quick Reject"
                                        >
                                          <ThumbsDown className="w-3.5 h-3.5" />
                                        </button>
                                      </>
                                    )}
                                  </div>
                                </td>
                              </tr>
                            );
                          })
                        )}
                      </tbody>
                    </table>
                  </div>
                </div>
              </div>
            )}

            {/* tab 2: Model Weights Configuration sliders */}
            {activeTab === "weights" && (
              <div className="max-w-2xl bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="space-y-1">
                  <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
                    <Sliders className="w-5 h-5 text-emerald-400" />
                    Interactive Model Weights Dashboard
                  </h3>
                  <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
                    Configure prediction coefficient parameters dynamically. Change weights values using the sliders. Sum of all weights must equal **1.0**.
                  </p>
                </div>

                <div className="space-y-6 pt-4 border-t border-neutral-900">
                  {/* Slider 1: YOLO */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-neutral-350 font-bold">1. YOLOv11 Category Weight</span>
                      <span className="text-emerald-400 font-bold">{Math.round(yoloW * 100)}% ({yoloW.toFixed(2)})</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05" value={yoloW} 
                      onChange={e => setYoloW(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>

                  {/* Slider 2: OCR */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-neutral-350 font-bold">2. OCR Text Similarity Weight</span>
                      <span className="text-emerald-400 font-bold">{Math.round(ocrW * 100)}% ({ocrW.toFixed(2)})</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05" value={ocrW} 
                      onChange={e => setOcrW(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>

                  {/* Slider 3: Barcode */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-neutral-350 font-bold">3. Barcode & QR Match Weight</span>
                      <span className="text-emerald-400 font-bold">{Math.round(barcodeW * 100)}% ({barcodeW.toFixed(2)})</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05" value={barcodeW} 
                      onChange={e => setBarcodeW(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>

                  {/* Slider 4: Embeddings */}
                  <div className="space-y-2">
                    <div className="flex justify-between items-center text-xs font-mono">
                      <span className="text-neutral-350 font-bold">4. ResNet18 Embedding Cosine Match</span>
                      <span className="text-emerald-400 font-bold">{Math.round(embeddingW * 100)}% ({embeddingW.toFixed(2)})</span>
                    </div>
                    <input 
                      type="range" min="0" max="1" step="0.05" value={embeddingW} 
                      onChange={e => setEmbeddingW(parseFloat(e.target.value))}
                      className="w-full h-1.5 bg-neutral-900 rounded-lg appearance-none cursor-pointer accent-emerald-500"
                    />
                  </div>

                  {/* Sum Verification panel */}
                  <div className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900 flex justify-between items-center text-xs">
                    <span className="text-neutral-500 font-mono">Validation Sum:</span>
                    <span className={`font-mono font-bold ${(yoloW+ocrW+barcodeW+embeddingW).toFixed(2) === '1.00' ? 'text-emerald-400' : 'text-red-400 animate-pulse'}`}>
                      {(yoloW+ocrW+barcodeW+embeddingW).toFixed(2)} / 1.00
                    </span>
                  </div>

                  {weightsError && (
                    <div className="p-3.5 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-xs font-mono">
                      {weightsError}
                    </div>
                  )}

                  {saveSuccess && (
                    <div className="p-3.5 rounded-xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-xs font-mono">
                      Weights configuration updated successfully!
                    </div>
                  )}

                  <button
                    onClick={handleSaveWeights}
                    disabled={saveLoading}
                    className="w-full flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
                  >
                    {saveLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : "Save Weights Configuration"}
                  </button>
                </div>
              </div>
            )}

            {/* tab 3: Configurable override rules */}
            {activeTab === "rules" && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {rules.map(rule => (
                  <div key={rule.id} className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-4">
                    <div className="flex justify-between items-start">
                      <div className="space-y-1">
                        <span className="text-[10px] text-neutral-550 font-bold font-mono uppercase tracking-wider">{rule.rule_key}</span>
                        <h4 className="text-sm font-bold text-neutral-200">{rule.rule_name}</h4>
                      </div>
                      <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider ${rule.is_active ? 'bg-emerald-950/30 text-emerald-400 border border-emerald-500/10' : 'bg-neutral-900 text-neutral-550 border border-neutral-850'}`}>
                        {rule.is_active ? 'Active' : 'Disabled'}
                      </span>
                    </div>
                    
                    <p className="text-xs text-neutral-500 leading-relaxed font-sans">{rule.description || "No rule override description provided."}</p>

                    <div className="flex gap-4 items-center pt-2 border-t border-neutral-900/60">
                      {rule.rule_type === "boolean" ? (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateRule(rule.rule_key, "true", rule.is_active)}
                            className={`px-3 py-1 rounded-xl text-[10px] font-bold font-mono tracking-wider border transition-all cursor-pointer ${rule.value === 'true' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-neutral-950 text-neutral-500 border-neutral-900 hover:text-neutral-350'}`}
                          >
                            TRUE
                          </button>
                          <button
                            onClick={() => handleUpdateRule(rule.rule_key, "false", rule.is_active)}
                            className={`px-3 py-1 rounded-xl text-[10px] font-bold font-mono tracking-wider border transition-all cursor-pointer ${rule.value === 'false' ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/20' : 'bg-neutral-950 text-neutral-500 border-neutral-900 hover:text-neutral-350'}`}
                          >
                            FALSE
                          </button>
                        </div>
                      ) : (
                        <div className="flex gap-2 items-center flex-1">
                          <span className="text-[10px] text-neutral-500 font-mono">Value Threshold:</span>
                          <input
                            type="number" step="0.05" min="0" max="1"
                            className="w-20 px-2 py-1 rounded bg-neutral-950 border border-neutral-800 text-xs text-neutral-300 font-mono focus:outline-none"
                            value={rule.value}
                            onChange={e => handleUpdateRule(rule.rule_key, e.target.value, rule.is_active)}
                          />
                        </div>
                      )}

                      <button
                        onClick={() => handleUpdateRule(rule.rule_key, rule.value, !rule.is_active)}
                        className="ml-auto text-[10px] font-bold font-mono text-neutral-450 hover:text-emerald-400 transition-colors cursor-pointer"
                      >
                        {rule.is_active ? "Disable Rule" : "Enable Rule"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </>
        )}
      </div>
    </div>
  );
}
