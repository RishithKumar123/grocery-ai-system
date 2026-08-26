"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { User, Mail, KeyRound, ShieldAlert, AlertCircle, Loader2, ArrowRight, CheckCircle2 } from "lucide-react";
import { getAccessToken, getApiUrl } from "../../../lib/auth";

export default function RegisterPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("Shopkeeper");
  
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
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
      const res = await fetch(`${apiBase}/api/v1/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password, full_name: fullName, role }),
      });

      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        throw new Error(data?.error?.message || "Registration failed. Email might already be taken.");
      }

      setSuccess(true);
    } catch (err: any) {
      setError(err?.message || "Something went wrong.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="relative flex min-h-screen items-center justify-center bg-neutral-950 px-4 py-12 sm:px-6 lg:px-8">
      {/* Background radial effects */}
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/10 rounded-full blur-[100px] pointer-events-none" />
      <div className="absolute bottom-1/4 right-1/4 w-85 h-85 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="glass w-full max-w-md space-y-8 p-8 rounded-3xl z-10 relative">
        <div className="text-center">
          <h2 className="text-3xl font-bold tracking-tight text-neutral-50">Create an account</h2>
          <p className="mt-2 text-sm text-neutral-400">
            Sign up to manage your store inventories
          </p>
        </div>

        {error && (
          <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-sm">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <p>{error}</p>
          </div>
        )}

        {success ? (
          <div className="text-center space-y-6 py-6">
            <div className="flex justify-center">
              <CheckCircle2 className="w-16 h-16 text-emerald-400 animate-bounce" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-neutral-100">Registration Successful!</h3>
              <p className="text-sm text-neutral-400">
                A verification link has been logged in the backend. Click "Verify Email" to simulate activation.
              </p>
            </div>
            <div className="pt-4">
              <Link
                href="/login"
                className="inline-flex w-full justify-center rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all"
              >
                Proceed to Log In
              </Link>
            </div>
          </div>
        ) : (
          <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
            <div className="space-y-4 rounded-md shadow-sm">
              <div className="relative">
                <label htmlFor="full-name" className="sr-only">Full Name</label>
                <User className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input
                  id="full-name"
                  name="fullName"
                  type="text"
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
                  placeholder="Full Name"
                  value={fullName}
                  onChange={(e) => setFullName(e.target.value)}
                />
              </div>

              <div className="relative">
                <label htmlFor="email-address" className="sr-only">Email address</label>
                <Mail className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <input
                  id="email-address"
                  name="email"
                  type="email"
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
                  required
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-200 placeholder-neutral-500 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm"
                  placeholder="Password (min 6 chars)"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                />
              </div>

              <div className="relative">
                <ShieldAlert className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-neutral-500" />
                <select
                  id="role"
                  name="role"
                  className="w-full pl-10 pr-4 py-3 rounded-xl border border-neutral-800 bg-neutral-900/50 text-neutral-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 focus:border-emerald-500 transition-all text-sm appearance-none"
                  value={role}
                  onChange={(e) => setRole(e.target.value)}
                >
                  <option value="Shopkeeper">Shopkeeper (Monitors Stocks)</option>
                  <option value="Vendor">Vendor (Supplies Stock Items)</option>
                  <option value="Admin">Admin (Full System Controls)</option>
                </select>
              </div>
            </div>

            <div>
              <button
                type="submit"
                disabled={loading}
                className="relative flex w-full justify-center items-center gap-2 rounded-xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-neutral-950 hover:bg-emerald-400 transition-all focus:outline-none focus:ring-2 focus:ring-emerald-500 focus:ring-offset-2 disabled:opacity-50"
              >
                {loading ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Registering...
                  </>
                ) : (
                  <>
                    Create Account <ArrowRight className="w-4 h-4" />
                  </>
                )}
              </button>
            </div>
          </form>
        )}

        {!success && (
          <div className="text-center text-sm text-neutral-400">
            <span>Already have an account? </span>
            <Link href="/login" className="font-semibold text-emerald-400 hover:text-emerald-300 transition-colors">
              Log In
            </Link>
          </div>
        )}
      </div>
    </div>
  );
}
