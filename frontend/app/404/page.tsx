"use client";

import React from "react";
import Link from "next/link";
import { HelpCircle, ArrowLeft } from "lucide-react";

export default function NotFoundPage() {
  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col items-center justify-center p-6 text-neutral-100 relative">
      <div className="absolute top-1/3 left-1/2 -translate-x-1/2 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="w-full max-w-md p-8 rounded-3xl border border-neutral-900 bg-neutral-900/40 backdrop-blur-md text-center space-y-6 relative z-10">
        <div className="w-16 h-16 rounded-2xl bg-emerald-500/10 border border-emerald-500/20 mx-auto flex items-center justify-center">
          <HelpCircle className="w-8 h-8 text-emerald-400" />
        </div>

        <div className="space-y-2">
          <h1 className="text-4xl font-black tracking-tight text-neutral-50">404</h1>
          <h2 className="text-lg font-bold text-neutral-200">Page Not Found</h2>
          <p className="text-xs text-neutral-500 leading-relaxed">
            The target route location you are attempting to access is missing or has been relocated to another workspace address.
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
