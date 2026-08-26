"use client";

import React, { useState, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { KeyRound, CheckCircle2, Loader2 } from "lucide-react";
import { getApiUrl } from "../../../lib/auth";

function ResetPasswordForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError(null);

    try {
      const apiBase = getApiUrl();
      const res = await fetch(`${apiBase}/api/v1/auth/reset-password`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ token, new_password: password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.detail || "Invalid or expired reset token.");
      }

      setSuccess(true);
    } catch (err: any) {
      setError(err?.message || "Failed to reset password.");
    } finally {
      setLoading(false);
    }
  };

  if (!token) {
    return (
      <div className="text-center py-6">
        <p className="text-red-400 font-semibold mb-4">No password reset token was provided.</p>
        <Link href="/login" className="text-sm text-emerald-400 hover:text-emerald-300">
          Back to Login
        </Link>
      </div>
    );
  }

  return (
    <div>
      {error && (
        <div className="p-4 mb-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-sm">
          {error}
        </div>
      )}

      {success ? (
        <div className="text-center space-y-6 py-4">
          <div className="flex justify-center">
            <CheckCircle2 className="w-16 h-16 text-emerald-400" />
          </div>
          <p className="text-sm text-neutral-300">
            Your password has been reset successfully. You can now log in.
          </p>
          <div className="pt-2">
            <Link href="/login" className="inline-flex justify-center rounded-xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all">
              Go to Login
            </Link>
          </div>
        </div>
      ) : (
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="relative">
            <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
            <input
              type="password"
              required
              className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
              placeholder="Enter new password (min 6 chars)"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="flex w-full justify-center items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all disabled:opacity-50"
          >
            {loading ? (
              <>
                <Loader2 className="w-4 h-4 animate-spin" /> Saving...
              </>
            ) : (
              "Save New Password"
            )}
          </button>
        </form>
      )}
    </div>
  );
}

export default function ResetPasswordPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-neutral-950 px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="glass w-full max-w-md space-y-8 p-8 rounded-3xl z-10 relative">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-50">Set New Password</h2>
          <p className="mt-2 text-sm text-neutral-400 mb-6">
            Provide a secure password for your account
          </p>
        </div>

        <Suspense fallback={<div className="text-center text-sm text-neutral-400">Loading form parameters...</div>}>
          <ResetPasswordForm />
        </Suspense>
      </div>
    </div>
  );
}
