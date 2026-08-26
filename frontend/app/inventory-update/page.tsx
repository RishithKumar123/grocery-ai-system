"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  RefreshCw, 
  RotateCw, 
  Loader2, 
  Activity, 
  Grid, 
  CheckCircle,
  Sliders,
  AlertTriangle,
  FolderSync,
  History,
  Trash2,
  Clock,
  ShieldCheck
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface UpdateRule {
  id: number;
  rule_key: string;
  rule_name: string;
  value: string;
  description: string;
  is_active: boolean;
}

export default function SyncDashboardPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  
  // Data State
  const [rules, setRules] = useState<UpdateRule[]>([]);
  const [pendingCount, setPendingCount] = useState(0);
  const [diffCount, setDiffCount] = useState(0);
  const [historyCount, setHistoryCount] = useState(0);
  const [accuracy, setAccuracy] = useState(100.0);

  // Edit Rules inputs
  const [actionLoading, setActionLoading] = useState(false);
  const [rulesSuccess, setRulesSuccess] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadDashboardData();
  }, [router]);

  const loadDashboardData = async () => {
    setLoading(true);
    try {
      // 1. Fetch Rules
      const resRules = await fetchWithAuth("/api/v1/inventory-update/rules");
      if (resRules.ok) {
        setRules(await resRules.json());
      }

      // 2. Fetch Approval queue count
      const resApp = await fetchWithAuth("/api/v1/inventory-update/approval-queue");
      if (resApp.ok) {
        const appData = await resApp.json();
        setPendingCount(appData.filter((r: any) => r.status === "Pending").length);
      }

      // 3. Fetch differences count
      const resDiff = await fetchWithAuth("/api/v1/inventory-update/preview?store_id=1");
      if (resDiff.ok) {
        const diffData = await resDiff.json();
        setDiffCount(diffData.filter((d: any) => d.difference !== 0).length);
      }

      // 4. Fetch history count
      const resHist = await fetchWithAuth("/api/v1/inventory-update/history?store_id=1");
      if (resHist.ok) {
        const histData = await resHist.json();
        setHistoryCount(histData.length);
      }

    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleUpdateRuleValue = async (key: string, val: string, active: boolean) => {
    setActionLoading(true);
    setRulesSuccess(false);
    try {
      const res = await fetchWithAuth(`/api/v1/inventory-update/rules/${key}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ value: val, is_active: active })
      });
      if (res.ok) {
        setRulesSuccess(true);
        // Refresh local rules state
        setRules(prev => prev.map(r => r.rule_key === key ? { ...r, value: val, is_active: active } : r));
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
              <Link href="/dashboard" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Inventory Sync Desk</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Synchronizes verified AI scanner counting data with the central stock registry database.
            </p>
          </div>
          <button 
            onClick={loadDashboardData}
            className="self-start md:self-auto flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Telemetry
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Fusing sync updates logs...</p>
          </div>
        ) : (
          <>
            {/* 1. Analytics Cards */}
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Pending Approvals</span>
                <span className="block text-2xl font-bold text-yellow-400 font-mono mt-1">{pendingCount} requests</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Active Differences</span>
                <span className="block text-2xl font-bold text-red-405 font-mono mt-1 text-red-400">{diffCount} items</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Sync Accuracy Rate</span>
                <span className="block text-2xl font-bold text-emerald-450 font-mono text-emerald-400">{accuracy}%</span>
              </div>
              <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
                <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider font-mono">Applied updates</span>
                <span className="block text-2xl font-bold text-neutral-100 font-mono mt-1">{historyCount} logs</span>
              </div>
            </div>

            {/* Quick links grid cards */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              <Link href="/inventory-update/approval" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <CheckCircle className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Approval Queue</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Review and authorize high-impact variance stock revisions before committing to store catalogs.
                  </p>
                </div>
              </Link>

              <Link href="/inventory-update/diff" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Activity className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Difference Viewer</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Compare current database quantities side-by-side with verified scanner counting logs.
                  </p>
                </div>
              </Link>

              <Link href="/inventory-update/rollback" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Trash2 className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Rollback Center</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Restore previous database state snapshots to reverse bulk incorrect update operations.
                  </p>
                </div>
              </Link>

              <Link href="/inventory-update/reconciliation" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <FolderSync className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Reconciliation Dashboard</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Consolidate stock levels telemetry indicators and variance accuracy graphs.
                  </p>
                </div>
              </Link>

              <Link href="/inventory-update/timeline" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <Clock className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Inventory Timeline</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Track item stock modifications and scanner counts chronologically by SKU.
                  </p>
                </div>
              </Link>

              <Link href="/inventory-update/history" className="group bg-neutral-900/10 border border-neutral-900 hover:border-emerald-500/10 p-6 rounded-3xl space-y-4 transition-all">
                <div className="p-3 bg-neutral-900 rounded-2xl w-fit text-emerald-400 group-hover:bg-emerald-500 group-hover:text-neutral-950 transition-colors">
                  <History className="w-6 h-6" />
                </div>
                <div>
                  <h3 className="text-sm font-bold font-mono uppercase tracking-wider text-neutral-200">Update History</h3>
                  <p className="text-[10px] text-neutral-500 mt-1 font-sans leading-relaxed">
                    Review history ledgers auditing updates applied, rejected, or rolled back.
                  </p>
                </div>
              </Link>

            </div>

            {/* Configurable Business Rules override */}
            <div className="max-w-2xl bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm font-mono uppercase tracking-wider">
                <Sliders className="w-5 h-5 text-emerald-400" />
                Sync Validation Rules
              </h3>
              
              {rulesSuccess && (
                <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-[10px] font-mono">
                  Sync validation rule parameter updated successfully.
                </div>
              )}

              <div className="space-y-4 pt-4 border-t border-neutral-900/60 font-mono text-xs text-neutral-400">
                {rules.map(rule => (
                  <div key={rule.id} className="p-4 bg-neutral-950 border border-neutral-900 rounded-xl space-y-3">
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-neutral-200">{rule.rule_name}</span>
                      <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${
                        rule.is_active ? 'bg-emerald-950/30 text-emerald-400 border-emerald-500/10' : 'bg-neutral-900 text-neutral-500 border-neutral-850'
                      }`}>
                        {rule.is_active ? 'Enabled' : 'Disabled'}
                      </span>
                    </div>
                    <p className="text-[10px] text-neutral-500 font-sans leading-relaxed">{rule.description}</p>
                    
                    <div className="flex gap-4 items-center pt-2 border-t border-neutral-900/40">
                      {rule.rule_key === "prevent_negative_inventory" ? (
                        <div className="flex gap-2">
                          <button
                            onClick={() => handleUpdateRuleValue(rule.rule_key, "true", rule.is_active)}
                            className={`px-3 py-1 rounded bg-neutral-900 border text-[9px] font-bold hover:border-emerald-500/20 cursor-pointer ${rule.value === 'true' ? 'text-emerald-400 border-emerald-500/25' : 'text-neutral-500 border-neutral-850'}`}
                          >
                            TRUE
                          </button>
                          <button
                            onClick={() => handleUpdateRuleValue(rule.rule_key, "false", rule.is_active)}
                            className={`px-3 py-1 rounded bg-neutral-900 border text-[9px] font-bold hover:border-emerald-500/20 cursor-pointer ${rule.value === 'false' ? 'text-emerald-400 border-emerald-500/25' : 'text-neutral-500 border-neutral-850'}`}
                          >
                            FALSE
                          </button>
                        </div>
                      ) : (
                        <div className="flex items-center gap-2 flex-1">
                          <span className="text-[10px] text-neutral-500">Value:</span>
                          <input
                            type="text"
                            className="px-2 py-1 rounded bg-neutral-900 border border-neutral-800 text-neutral-300 w-24 text-xs font-bold"
                            value={rule.value}
                            onChange={e => handleUpdateRuleValue(rule.rule_key, e.target.value, rule.is_active)}
                          />
                        </div>
                      )}

                      <button
                        onClick={() => handleUpdateRuleValue(rule.rule_key, rule.value, !rule.is_active)}
                        className="ml-auto text-[9px] font-bold uppercase text-neutral-450 hover:text-emerald-450 transition-colors cursor-pointer"
                      >
                        {rule.is_active ? "Disable Rule" : "Enable Rule"}
                      </button>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </>
        )}

      </div>
    </div>
  );
}
