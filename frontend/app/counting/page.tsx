"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Activity, 
  Clock, 
  CheckCircle, 
  XCircle, 
  Sliders, 
  ShieldAlert, 
  Camera, 
  Video, 
  FileText, 
  TrendingUp,
  RotateCw,
  Plus,
  Loader2,
  ListOrdered
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface Job {
  id: number;
  store_id: number;
  video_id?: number;
  status: string;
  started_at: string;
  completed_at?: string;
  total_counted: number;
  average_confidence: number;
  statistics?: {
    total_products_counted: number;
    average_counting_accuracy: number;
    duplicate_detection_rate: number;
    tracking_accuracy: number;
    processing_speed: number;
    products_per_minute: number;
  };
}

export default function CountingDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [jobs, setJobs] = useState<Job[]>([]);
  const [actionLoading, setActionLoading] = useState(false);

  // Summary Metrics
  const [totalCounted, setTotalCounted] = useState(0);
  const [avgAccuracy, setAvgAccuracy] = useState(98.5);
  const [duplicateRate, setDuplicateRate] = useState(5.2);
  const [trackingAccuracy, setTrackingAccuracy] = useState(96.8);
  const [speedFps, setSpeedFps] = useState(30.0);

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
      const res = await fetchWithAuth("/api/v1/counting/jobs");
      if (res.ok) {
        const jobsData = await res.json();
        const validJobs: Job[] = Array.isArray(jobsData) ? jobsData : (jobsData.jobs || jobsData.data || []);
        setJobs(validJobs);
        
        // Calculate dynamic summary aggregates
        if (validJobs.length > 0) {
          let sumCounted = 0;
          let sumAcc = 0;
          let sumDup = 0;
          let sumTrack = 0;
          let sumFps = 0;
          let jobsWithStats = 0;

          validJobs.forEach((j: Job) => {
            sumCounted += j.total_counted || 0;
            if (j.statistics) {
              sumAcc += j.statistics.average_counting_accuracy || 0;
              sumDup += j.statistics.duplicate_detection_rate || 0;
              sumTrack += j.statistics.tracking_accuracy || 0;
              sumFps += j.statistics.processing_speed || 0;
              jobsWithStats++;
            }
          });

          setTotalCounted(sumCounted);
          if (jobsWithStats > 0) {
            setAvgAccuracy(round(sumAcc / jobsWithStats, 1));
            setDuplicateRate(round(sumDup / jobsWithStats, 1));
            setTrackingAccuracy(round(sumTrack / jobsWithStats, 1));
            setSpeedFps(round(sumFps / jobsWithStats, 1));
          }
        }
      }
    } catch (err) {
      console.error("Failed to load inventory counting metrics:", err);
    } finally {
      setLoading(false);
    }
  };

  const handleStartSimulatedJob = async () => {
    setActionLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/counting/jobs", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: 1,
          config: { min_confidence: 0.50, tracking_timeout: 30 }
        })
      });
      if (res.ok) {
        loadData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setActionLoading(false);
    }
  };

  const handleVerifyCounts = async (id: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/counting/jobs/${id}/verify`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({})
      });
      if (res.ok) {
        setJobs(prev => prev.map(j => j.id === id ? { ...j, status: "Completed" } : j));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const round = (num: number, decimals: number) => {
    const t = Math.pow(10, decimals);
    return Math.round(num * t) / t;
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
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Inventory Counting Desk</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Tracks coordinates and assigns unique object trajectories across frames to count stock without double-counting.
            </p>
          </div>
          
          <div className="flex gap-2">
            <button 
              onClick={loadData}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
            >
              <RotateCw className="w-3.5 h-3.5" /> Refresh
            </button>
            <button 
              onClick={handleStartSimulatedJob}
              disabled={actionLoading}
              className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors cursor-pointer disabled:opacity-50"
            >
              {actionLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Plus className="w-3.5 h-3.5" />} Sim Stream Job
            </button>
          </div>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Fusing track coordinates analytics...</p>
          </div>
        ) : (
          <>
            {/* 1. Analytics Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-5 gap-6">
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Total Counted</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{totalCounted}</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Average Accuracy</span>
                <span className="block text-2xl font-bold text-emerald-400 font-mono mt-1">{avgAccuracy}%</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Duplicate Rate</span>
                <span className="block text-2xl font-bold text-yellow-400 font-mono mt-1">{duplicateRate}%</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Tracking Accuracy</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{trackingAccuracy}%</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Speed (FPS)</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{speedFps} fps</span>
              </div>
            </div>

            {/* Quick Action Shortcuts */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <Link href="/counting/counter?mode=image" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Camera className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Image Counter</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Upload static shelf snapshots to run high-precision spatial box intersection deduplication algorithms.
                  </p>
                </div>
              </Link>

              <Link href="/counting/counter?mode=video" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Video className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Video Tracker</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Track shelf items across frames. Reconstructs lost tracks after occlusions and computes duplicates.
                  </p>
                </div>
              </Link>

              <Link href="/counting/history" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <ListOrdered className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">History Ledger</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Inspect count validation rules, past audits, and verified product counts grouped by category and shelf.
                  </p>
                </div>
              </Link>
            </div>

            {/* List of Active/Completed Jobs */}
            <div className="space-y-4">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">Auditing Counting Jobs</h3>
              
              <div className="bg-neutral-900/25 border border-neutral-900 rounded-3xl overflow-hidden">
                <table className="w-full text-left text-xs border-collapse">
                  <thead>
                    <tr className="border-b border-neutral-900 text-neutral-450 font-bold uppercase tracking-wider text-[10px] font-mono bg-neutral-950/40">
                      <th className="px-6 py-4">Job ID</th>
                      <th className="px-6 py-4">Target Store</th>
                      <th className="px-6 py-4 text-center">Video Target</th>
                      <th className="px-6 py-4 text-center">Total Counted</th>
                      <th className="px-6 py-4 text-center">Average Confidence</th>
                      <th className="px-6 py-4 text-center">Status</th>
                      <th className="px-6 py-4 text-right">Actions</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                    {jobs.length === 0 ? (
                      <tr>
                        <td colSpan={7} className="text-center py-20 text-neutral-500 font-mono text-xs">
                          No active or completed counting jobs. Ingest a stream or upload an image to start.
                        </td>
                      </tr>
                    ) : (
                      jobs.map(job => (
                        <tr key={job.id} className="hover:bg-neutral-900/10 transition-colors">
                          <td className="px-6 py-4 font-mono font-bold text-neutral-400">
                            #{job.id}
                          </td>
                          <td className="px-6 py-4 font-bold text-neutral-200">
                            Store Branch ID: {job.store_id}
                          </td>
                          <td className="px-6 py-4 text-center font-mono text-neutral-450">
                            {job.video_id ? `Video ID: ${job.video_id}` : "Camera Stream Scan"}
                          </td>
                          <td className="px-6 py-4 text-center font-mono font-bold text-neutral-100">
                            {job.total_counted} pcs
                          </td>
                          <td className="px-6 py-4 text-center font-mono text-neutral-100">
                            {Math.round(job.average_confidence * 100)}%
                          </td>
                          <td className="px-6 py-4 text-center">
                            <span className={`px-2.5 py-0.5 rounded text-[8px] font-bold uppercase tracking-wider border ${
                              job.status === "Completed" ? "bg-emerald-950/20 text-emerald-400 border-emerald-500/20" :
                              job.status === "Running" ? "bg-yellow-950/20 text-yellow-400 border-yellow-500/20" :
                              "bg-neutral-900 text-neutral-400 border-neutral-850"
                            }`}>
                              {job.status}
                            </span>
                          </td>
                          <td className="px-6 py-4 text-right">
                            <div className="flex justify-end gap-2">
                              <Link 
                                href={`/counting/viewer?id=${job.id}`}
                                className="px-2.5 py-1 rounded bg-neutral-900 border border-neutral-800 hover:border-emerald-500/20 text-[10px] font-bold font-mono text-neutral-350 hover:text-emerald-400 transition-colors"
                              >
                                Inspect Tracks
                              </Link>
                              {job.status === "Running" && (
                                <button
                                  onClick={() => handleVerifyCounts(job.id)}
                                  className="px-2.5 py-1 rounded bg-emerald-950/20 text-emerald-400 border border-emerald-500/20 hover:bg-emerald-500 hover:text-neutral-950 text-[10px] font-bold font-mono transition-colors cursor-pointer"
                                >
                                  Approve Counts
                                </button>
                              )}
                            </div>
                          </td>
                        </tr>
                      ))
                    )}
                  </tbody>
                </table>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
}
