"use client";

import React, { useState } from "react";
import Link from "next/link";
import { Mail, ArrowLeft, Loader2, CheckCircle2 } from "lucide-react";
import { getApiUrl } from "../../../lib/auth";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const apiBase = getApiUrl();
      const res = await fetch(`${apiBase}/api/v1/auth/forgot-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email }),
      });

      if (!res.ok) {
        throw new Error("Password reset request failed.");
      }

      setSuccess(true);
    } catch (err: any) {
      setError(err?.message || "Failed to request password reset.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-neutral-950 px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="glass w-full max-w-md space-y-8 p-8 rounded-3xl z-10 relative">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-50">Reset Password</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Enter your email address to receive a recovery link
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-sm">
            {error}
          </div>
        )}

        {success ? (
          <div className="text-center space-y-6 py-4">
            <div className="flex justify-center">
              <CheckCircle2 className="w-16 h-16 text-emerald-400 animate-bounce" />
            </div>
            <p className="text-sm text-neutral-300">
              A recovery link has been simulated in the backend stdout logs. Click it to set a new password.
            </p>
            <div className="pt-2">
              <Link href="/login" className="text-sm font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
                Back to Login
              </Link>
            </div>
          </div>
        ) : (
          <form className="space-y-6" onSubmit={handleSubmit}>
            <div className="relative">
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input
                type="email"
                required
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>

            <button
              type="submit"
              disabled={loading}
              className="flex w-full justify-center items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Processing...
                </>
              ) : (
                "Send Reset Link"
              )}
            </button>
          </form>
        )}

        <div className="text-center">
          <Link href="/login" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Log In
          </Link>
        </div>
      </div>
    </div>
  );
}
