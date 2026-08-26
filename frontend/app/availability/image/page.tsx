"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Camera, 
  UploadCloud, 
  RotateCw, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Sparkles
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

export default function ImageSearchPage() {
  const router = useRouter();
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [result, setResult] = useState<any>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
  }, [router]);

  const handleUploadImage = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setUploading(true);
    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetchWithAuth("/api/v1/availability/image?store_id=1", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        setResult(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-4xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
          <Link href="/availability" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Visual Image Matcher</h1>
            <p className="text-xs text-neutral-500 font-sans mt-0.5">Upload product snapshots to identify catalog matches and check availability.</p>
          </div>
        </div>

        {/* Uploader Box */}
        <div className="bg-neutral-900/10 border border-neutral-900 p-8 rounded-3xl space-y-6">
          <form onSubmit={handleUploadImage} className="space-y-6 text-center">
            
            <div className="border-2 border-dashed border-neutral-800 hover:border-emerald-500/50 rounded-2xl p-8 bg-neutral-950/60 transition-colors cursor-pointer space-y-3">
              <UploadCloud className="w-10 h-10 text-emerald-400 mx-auto" />
              <div className="space-y-1">
                <p className="text-xs font-mono font-bold text-neutral-200">
                  {selectedFile ? selectedFile.name : "Click to select or drag product image snapshot"}
                </p>
                <p className="text-[10px] text-neutral-500 font-mono">Supports PNG, JPG, WEBP up to 10MB</p>
              </div>
              <input
                type="file"
                accept="image/*"
                className="hidden"
                id="img-upload-input"
                onChange={e => e.target.files && setSelectedFile(e.target.files[0])}
              />
              <label htmlFor="img-upload-input" className="inline-block px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold font-mono text-neutral-300 hover:text-emerald-400 cursor-pointer">
                Browse Files
              </label>
            </div>

            <button
              type="submit"
              disabled={uploading || !selectedFile}
              className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-colors disabled:opacity-50"
            >
              {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
              Match Snapshot & Verify Availability
            </button>
          </form>
        </div>

        {/* Outcome Card */}
        {result && (
          <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-4 font-mono">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {result.status === "YES" ? (
                  <span className="text-emerald-400 font-bold text-lg">✅ YES - Product Available</span>
                ) : (
                  <span className="text-red-400 font-bold text-lg">❌ NO - {result.reason}</span>
                )}
              </div>
              <span className="text-xs text-neutral-500">{result.search_time_ms} ms</span>
            </div>

            {result.status === "YES" && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-neutral-300 pt-4 border-t border-neutral-900">
                <div><span className="text-neutral-500 block text-[9px]">Matched Product:</span> <b>{result.product_name}</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Stock:</span> <b className="text-emerald-400">{result.available_quantity} pcs</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Aisle:</span> <b>{result.aisle}</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Shelf:</span> <b>{result.shelf}</b></div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
