"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { CheckCircle2, AlertCircle, Loader2 } from "lucide-react";
import { getApiUrl } from "../../../lib/auth";

function VerifyEmailForm() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const token = searchParams.get("token") || "";

  const [loading, setLoading] = useState(true);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!token) {
      setLoading(false);
      setError("No verification token was provided.");
      return;
    }

    const verifyToken = async () => {
      try {
        const apiBase = getApiUrl();
        const res = await fetch(`${apiBase}/api/v1/auth/verify-email`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ token }),
        });

        if (!res.ok) {
          const data = await res.json().catch(() => ({}));
          throw new Error(data?.detail || "Invalid or expired verification token.");
        }

        setSuccess(true);
      } catch (err: any) {
        setError(err?.message || "Failed to verify email.");
      } finally {
        setLoading(false);
      }
    };

    verifyToken();
  }, [token]);

  if (loading) {
    return (
      <div className="text-center py-8 space-y-4">
        <Loader2 className="w-12 h-12 text-emerald-400 animate-spin mx-auto" />
        <p className="text-neutral-400 text-sm">Verifying your email address, please wait...</p>
      </div>
    );
  }

  return (
    <div className="text-center space-y-6 py-4">
      {success ? (
        <>
          <div className="flex justify-center">
            <CheckCircle2 className="w-16 h-16 text-emerald-400" />
          </div>
          <h3 className="text-lg font-bold text-neutral-100">Verification Successful!</h3>
          <p className="text-sm text-neutral-400">
            Thank you. Your email address has been verified. You can now access all services.
          </p>
          <div className="pt-4">
            <Link
              href="/login"
              className="inline-flex justify-center rounded-xl bg-emerald-500 px-6 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all"
            >
              Sign In to Dashboard
            </Link>
          </div>
        </>
      ) : (
        <>
          <div className="flex justify-center">
            <AlertCircle className="w-16 h-16 text-red-400" />
          </div>
          <h3 className="text-lg font-bold text-neutral-100">Verification Failed</h3>
          <p className="text-sm text-neutral-400">{error}</p>
          <div className="pt-4">
            <Link href="/login" className="text-sm font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
              Back to Login
            </Link>
          </div>
        </>
      )}
    </div>
  );
}

export default function VerifyEmailPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center bg-neutral-950 px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      
      <div className="glass w-full max-w-md space-y-8 p-8 rounded-3xl z-10 relative">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-50">Email Verification</h2>
          <p className="mt-2 text-sm text-neutral-400 mb-6">
            Activating your grocery account
          </p>
        </div>

        <Suspense fallback={<div className="text-center text-sm text-neutral-400">Validating token payload...</div>}>
          <VerifyEmailForm />
        </Suspense>
      </div>
    </div>
  );
}
