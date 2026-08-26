"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Layers, 
  Activity, 
  ShieldAlert, 
  Loader2, 
  Check, 
  Clock, 
  ListOrdered,
  CheckCircle,
  HelpCircle
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Track {
  id: number;
  track_id: number;
  product_id?: number;
  product_name: string;
  confidence: number;
  bounding_box: Record<string, any>;
  start_frame: number;
  end_frame: number;
  status: string;
}

interface Validation {
  id: number;
  validation_rule_key: string;
  value: string;
  status: string;
  validation_notes?: string;
}

interface Job {
  id: number;
  store_id: number;
  video_id?: number;
  status: string;
  started_at: string;
  completed_at?: string;
  total_counted: number;
  average_confidence: number;
  tracks: Track[];
  validations: Validation[];
  statistics?: {
    total_products_counted: number;
    average_counting_accuracy: number;
    duplicate_detection_rate: number;
    tracking_accuracy: number;
    processing_speed: number;
    products_per_minute: number;
  };
}

function TrackingViewerContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get("id") || "";

  const [loading, setLoading] = useState(true);
  const [job, setJob] = useState<Job | null>(null);
  const [actionLoading, setActionLoading] = useState(false);
  const [actionSuccess, setActionSuccess] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    if (jobId) loadJobDetails();
  }, [jobId, router]);

  const loadJobDetails = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/counting/jobs/${jobId}`);
      if (res.ok) {
        setJob(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyCounts = async () => {
    if (!job) return;
    setActionLoading(true);
    setActionSuccess(false);
    try {
      const res = await fetchWithAuth(`/api/v1/counting/jobs/${job.id}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ notes: "Auditor approved trajectories counts." })
      });
      if (res.ok) {
        setActionSuccess(true);
        // Refresh job state
        loadJobDetails();
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
        <p className="text-xs text-neutral-500 font-mono">Fusing track coordinates trajectories...</p>
      </div>
    );
  }

  if (!job) {
    return (
      <div className="text-center py-20 text-neutral-500 font-mono text-xs">
        Counting job record not found.
      </div>
    );
  }

  return (
    <div className="space-y-10">
      
      {/* Header navigation bar */}
      <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
        <Link href="/counting" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Track Trajectory Details</h1>
          <p className="text-xs text-neutral-500 font-sans mt-0.5">Job ID: #{job.id}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Col 1 & 2: Trajectory List and stats */}
        <div className="lg:col-span-2 space-y-8">
          
          {/* Card: Job stats summary */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <Activity className="w-5 h-5 text-emerald-400" />
              Tracking Statistics Summary
            </h3>

            <div className="grid grid-cols-2 md:grid-cols-4 gap-6 pt-4 border-t border-neutral-900/60 font-mono text-xs">
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Tracking Accuracy</span>
                <span className="block text-sm font-bold text-emerald-400">
                  {job.statistics?.tracking_accuracy || 100.0}%
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Processing Speed</span>
                <span className="block text-sm font-bold text-neutral-200">
                  {job.statistics?.processing_speed || 30.0} fps
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Duplicates Rate</span>
                <span className="block text-sm font-bold text-yellow-400">
                  {job.statistics?.duplicate_detection_rate || 0.0}%
                </span>
              </div>
              <div className="space-y-1">
                <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Acc. confidence</span>
                <span className="block text-sm font-bold text-neutral-200">
                  {Math.round(job.average_confidence * 100)}%
                </span>
              </div>
            </div>
          </div>

          {/* Card: list of tracks trajectories */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <ListOrdered className="w-5 h-5 text-emerald-400" />
              Active trajectories timeline tracks
            </h3>

            <div className="border border-neutral-900 rounded-2xl overflow-hidden pt-1">
              <table className="w-full text-left text-xs border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[9px] font-mono bg-neutral-950/40">
                    <th className="px-4 py-3">Track ID</th>
                    <th className="px-4 py-3">Catalog Mapped Item</th>
                    <th className="px-3 py-3 text-center">Confidence</th>
                    <th className="px-3 py-3 text-center">Start Frame</th>
                    <th className="px-3 py-3 text-center">End Frame</th>
                    <th className="px-4 py-3 text-right">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900/40 text-neutral-350 font-mono">
                  {job.tracks.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="text-center py-8 text-neutral-500">No objects tracked for this stream job.</td>
                    </tr>
                  ) : (
                    job.tracks.map(t => (
                      <tr key={t.id} className="hover:bg-neutral-900/5">
                        <td className="px-4 py-3 font-bold text-neutral-400">
                          #{t.track_id}
                        </td>
                        <td className="px-4 py-3 font-sans font-bold text-neutral-250">
                          {t.product_name || "Unknown Product"}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {Math.round(t.confidence * 100)}%
                        </td>
                        <td className="px-3 py-3 text-center">
                          {t.start_frame}
                        </td>
                        <td className="px-3 py-3 text-center">
                          {t.end_frame}
                        </td>
                        <td className="px-4 py-3 text-right">
                          <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${
                            t.status === 'Active' ? 'bg-emerald-950/20 text-emerald-400 border-emerald-500/20' :
                            t.status === 'Lost' ? 'bg-yellow-950/20 text-yellow-400 border-yellow-500/20' :
                            'bg-neutral-900 text-neutral-450 border-neutral-850'
                          }`}>
                            {t.status}
                          </span>
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* Col 3: Actions and Validation Checks */}
        <div className="space-y-8">
          
          {/* Card: Approve validation rules checks */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              Approve Verification Counts
            </h3>
            <p className="text-[10px] text-neutral-500 leading-relaxed font-sans">
              Verify this track record. Submitting syncs counting totals into history lists.
            </p>

            {actionSuccess && (
              <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-[10px] font-mono">
                Counts verified and approved. Logged in History database.
              </div>
            )}

            <button
              onClick={handleVerifyCounts}
              disabled={actionLoading || job.status === "Completed"}
              className="w-full flex items-center justify-center gap-1.5 px-4 py-3 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors disabled:opacity-50 cursor-pointer"
            >
              {actionLoading ? <Loader2 className="w-4 h-4 animate-spin text-neutral-950" /> : <Check className="w-4 h-4" />} Approve Counts Verification
            </button>
          </div>

          {/* Card: list of validation checks reports */}
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
              <ShieldAlert className="w-5 h-5 text-emerald-400" />
              Counting Pipeline Validations
            </h3>

            <div className="space-y-4 pt-4 border-t border-neutral-900/60 text-xs">
              {job.validations.map(val => (
                <div key={val.id} className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1.5 font-mono">
                  <div className="flex justify-between items-center text-[9px]">
                    <span className="text-neutral-500 font-bold uppercase">{val.validation_rule_key}</span>
                    <span className={`px-1.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider ${
                      val.status === 'Passed' ? 'bg-emerald-950/30 text-emerald-400 border border-emerald-500/10' : 'bg-red-950/30 text-red-400 border border-red-500/10'
                    }`}>
                      {val.status}
                    </span>
                  </div>
                  <span className="block text-neutral-300">Target Value: {val.value}</span>
                  {val.validation_notes && (
                    <p className="text-[10px] text-neutral-500 italic">"{val.validation_notes}"</p>
                  )}
                </div>
              ))}
            </div>
          </div>

        </div>

      </div>
    </div>
  );
}

export default function TrackingViewerPage() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Initializing viewer parameters...</p>
          </div>
        }>
          <TrackingViewerContent />
        </Suspense>
      </div>
    </div>
  );
}
