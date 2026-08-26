"use client";

import React from "react";

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <html>
      <body className="bg-neutral-950 text-neutral-100 flex items-center justify-center min-h-screen font-mono p-4">
        <div className="max-w-md w-full p-8 bg-neutral-900 border border-neutral-800 rounded-3xl text-center space-y-4">
          <h2 className="text-lg font-bold text-red-400">Application Global Error</h2>
          <p className="text-xs text-neutral-400 font-sans">
            {error?.message || "An unexpected error occurred."}
          </p>
          <button
            onClick={() => reset()}
            className="px-5 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 font-bold text-xs cursor-pointer"
          >
            Reset Application
          </button>
        </div>
      </body>
    </html>
  );
}
