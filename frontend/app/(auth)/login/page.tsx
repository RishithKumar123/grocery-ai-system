"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { KeyRound, Mail, AlertCircle, Loader2, ArrowRight } from "lucide-react";
import { setTokens, setUserProfile, getAccessToken, getApiUrl } from "../../../lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    // If already logged in, go to dashboard
    if (getAccessToken()) {
      router.push("/dashboard");
    }
  }, [router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);

    try {
      const apiBase = getApiUrl();
      const res = await fetch(`${apiBase}/api/v1/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error?.message || "Invalid email or password");
      }

      const data = await res.json();
      setTokens(data.access_token, data.refresh_token);

      // Fetch user profile info
      const profileRes = await fetch(`${apiBase}/api/v1/auth/me`, {
        headers: { Authorization: `Bearer ${data.access_token}` },
      });

      if (profileRes.ok) {
        const profile = await profileRes.json();
        setUserProfile(profile);
      }

      router.push("/dashboard");
    } catch (err: any) {
      setError(err?.message || "Something went wrong. Please check your credentials.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-neutral-950 px-4 py-12 sm:px-6 lg:px-8">
      {/* Dynamic gradients */}
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-85 h-85 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="glass w-full max-w-md space-y-8 p-8 rounded-3xl z-10 relative">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-50">Welcome back</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Sign in to access your inventory portal
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div className="relative">
              <label htmlFor="email-address" className="sr-only">Email address</label>
              <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            
            <div className="relative">
              <label htmlFor="password" className="sr-only">Password</label>
              <KeyRound className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          <div className="flex items-center justify-between text-xs">
            <Link 
              href="/forgot-password" 
              className="font-medium text-emerald-400 hover:text-emerald-300 transition-colors"
            >
              Forgot password?
            </Link>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="relative flex w-full justify-center items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50"
            >
              {loading ? (
                <>
                  <Loader2 className="w-4 h-4 animate-spin" /> Signing in...
                </>
              ) : (
                <>
                  Sign In <ArrowRight className="w-4 h-4" />
                </>
              )}
            </button>
          </div>
        </form>

        <div className="text-center text-sm text-neutral-400">
          <span>Don&apos;t have an account? </span>
          <Link href="/register" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
            Register
          </Link>
        </div>
      </div>
    </div>
  );
}
