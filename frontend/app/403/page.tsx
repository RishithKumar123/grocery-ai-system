"use client";

import React from "react";
import Link from "next/link";
import { ShieldAlert, ArrowLeft } from "lucide-react";

export default function ForbiddenPage() {
  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 text-neutral-100 relative">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-80 h-80 bg-red-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="w-full max-w-md p-8 rounded-3xl border border-neutral-900 bg-neutral-900/40 backdrop-blur-md text-center space-y-6 relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-red-500/10 border border-red-500/20 mx-auto flex items-center justify-center">
          <ShieldAlert className="w-8 h-8 text-red-500" />
        </div>

        <div className="space-y-2">
          <h1 className="text-4xl font-black tracking-tight text-neutral-50">403</h1>
          <h2 className="text-lg font-bold text-neutral-200">Access Forbidden</h2>
          <p className="text-xs text-neutral-500 leading-relaxed">
            Your user profile does not possess the required RBAC clearance level to route to this view resource.
          </p>
        </div>

        <div className="pt-4 border-t border-neutral-900">
          <Link 
            href="/dashboard" 
            className="inline-flex items-center gap-1.5 px-5 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold hover:text-emerald-400 hover:border-emerald-500/20 transition-all"
          >
            <ArrowLeft className="w-3.5 h-3.5" /> Return to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
