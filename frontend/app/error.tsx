"use client";

import React, { useEffect } from "react";
import Link from "next/link";
import { AlertTriangle, RotateCw, LayoutDashboard } from "lucide-react";

export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Unhandled Application Error:", error);
  }, [error]);

  return (
    <div className="min-h-screen bg-neutral-950 flex items-center justify-center p-6 text-neutral-100 font-mono">
      <div className="max-w-md w-full bg-neutral-900/40 border border-neutral-800 p-8 rounded-3xl text-center space-y-6">
        <div className="w-14 h-14 rounded-2xl bg-amber-500/10 border border-amber-500/20 flex items-center justify-center mx-auto text-amber-400">
          <AlertTriangle className="w-8 h-8 stroke-[2]" />
        </div>

        <div className="space-y-2">
          <h2 className="text-xl font-bold tracking-tight text-neutral-50">System Notice</h2>
          <p className="text-xs text-neutral-400 font-sans leading-relaxed">
            An unhandled runtime state occurred. You can retry the action or return to the main dashboard.
          </p>
        </div>

        {error?.message && (
          <div className="p-3 bg-neutral-950 rounded-xl border border-neutral-800/80 text-[10px] text-neutral-400 text-left overflow-x-auto max-h-24">
            <code>{error.message}</code>
          </div>
        )}

        <div className="flex flex-col sm:flex-row gap-3 pt-2">
          <button
            onClick={() => reset()}
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs cursor-pointer transition-colors"
          >
            <RotateCw className="w-4 h-4" /> Try Again
          </button>
          <Link
            href="/dashboard"
            className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-xl bg-neutral-800 hover:bg-neutral-700 text-neutral-200 font-bold text-xs transition-colors"
          >
            <LayoutDashboard className="w-4 h-4" /> Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
