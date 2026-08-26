"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  QrCode, 
  RotateCw, 
  Loader2, 
  CheckCircle, 
  XCircle, 
  Camera, 
  Sparkles
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

export default function BarcodeScannerPage() {
  const router = useRouter();
  const [barcodeInput, setBarcodeInput] = useState("6666666666666");
  const [scanning, setScanning] = useState(false);
  const [scanResult, setScanResult] = useState<any>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
  }, [router]);

  const handleScanBarcode = async (codeToScan?: string) => {
    const code = codeToScan || barcodeInput;
    if (!code.trim()) return;

    setScanning(true);
    try {
      const res = await fetchWithAuth(`/api/v1/availability/barcode/${encodeURIComponent(code)}?store_id=1`);
      if (res.ok) {
        setScanResult(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setScanning(false);
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
            <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Barcode & QR Code Scanner</h1>
            <p className="text-xs text-neutral-500 font-sans mt-0.5">Scans item optical codes to execute instant availability checks.</p>
          </div>
        </div>

        {/* Viewfinder simulator */}
        <div className="bg-neutral-900/10 border border-neutral-900 p-8 rounded-3xl space-y-6 text-center">
          <div className="w-full max-w-sm mx-auto h-48 border-2 border-dashed border-emerald-500/40 rounded-2xl flex flex-col items-center justify-center space-y-3 bg-neutral-950/60 relative overflow-hidden">
            <div className="absolute inset-x-0 top-1/2 h-0.5 bg-emerald-500/60 animate-pulse" />
            <Camera className="w-8 h-8 text-emerald-400" />
            <p className="text-[10px] font-mono text-neutral-400">Position barcode or QR inside viewfinder frame</p>
          </div>

          <div className="max-w-md mx-auto flex gap-2">
            <input
              type="text"
              placeholder="Enter or scan barcode digits..."
              className="flex-1 px-4 py-2.5 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 font-mono text-xs focus:outline-none"
              value={barcodeInput}
              onChange={e => setBarcodeInput(e.target.value)}
            />
            <button
              onClick={() => handleScanBarcode()}
              disabled={scanning}
              className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-colors"
            >
              {scanning ? <Loader2 className="w-4 h-4 animate-spin" /> : "Verify Scan"}
            </button>
          </div>

          {/* Quick presets */}
          <div className="flex justify-center items-center gap-2 text-[10px] font-mono text-neutral-500 pt-2">
            <span>Presets:</span>
            <button onClick={() => { setBarcodeInput("6666666666666"); handleScanBarcode("6666666666666"); }} className="px-2 py-1 rounded bg-neutral-900 border border-neutral-850 hover:text-emerald-400">Milk 1L (6666...)</button>
            <button onClick={() => { setBarcodeInput("7777777777777"); handleScanBarcode("7777777777777"); }} className="px-2 py-1 rounded bg-neutral-900 border border-neutral-850 hover:text-emerald-400">Butter (7777...)</button>
            <button onClick={() => { setBarcodeInput("4444444444444"); handleScanBarcode("4444444444444"); }} className="px-2 py-1 rounded bg-neutral-900 border border-neutral-850 hover:text-emerald-400">Juice (4444...)</button>
          </div>
        </div>

        {/* Outcome Card */}
        {scanResult && (
          <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-4 font-mono">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {scanResult.status === "YES" ? (
                  <span className="text-emerald-400 font-bold text-lg">✅ YES - Product Available</span>
                ) : (
                  <span className="text-red-400 font-bold text-lg">❌ NO - {scanResult.reason}</span>
                )}
              </div>
              <span className="text-xs text-neutral-500">{scanResult.search_time_ms} ms</span>
            </div>

            {scanResult.status === "YES" && (
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs text-neutral-300 pt-4 border-t border-neutral-900">
                <div><span className="text-neutral-500 block text-[9px]">Name:</span> <b>{scanResult.product_name}</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Stock:</span> <b className="text-emerald-400">{scanResult.available_quantity} pcs</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Aisle:</span> <b>{scanResult.aisle}</b></div>
                <div><span className="text-neutral-500 block text-[9px]">Shelf:</span> <b>{scanResult.shelf}</b></div>
              </div>
            )}
          </div>
        )}

      </div>
    </div>
  );
}
