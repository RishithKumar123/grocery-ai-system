"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getAccessToken, getUserProfile } from "../lib/auth";
import { Loader2 } from "lucide-react";

export default function RootLandingPage() {
  const router = useRouter();

  useEffect(() => {
    const token = getAccessToken();
    const user = getUserProfile();

    if (token && user) {
      router.push("/dashboard");
    } else {
      router.push("/login");
    }
  }, [router]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-neutral-950">
      <div className="text-center space-y-3">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin mx-auto" />
        <p className="text-xs text-neutral-500 font-mono">Authenticating session parameters...</p>
      </div>
    </div>
  );
}
