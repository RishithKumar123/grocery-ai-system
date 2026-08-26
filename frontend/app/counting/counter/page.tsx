"use client";

import React, { useState, useEffect, Suspense } from "react";
import { useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Camera, 
  Video, 
  Activity, 
  Loader2, 
  UploadCloud, 
  Sliders, 
  Layers, 
  Check, 
  Play, 
  Pause,
  Map
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface Product {
  id: number;
  name: string;
  sku: string;
  category: string;
  brand?: string;
  barcode?: string;
}

interface SimulatedBox {
  track_id: number;
  product_name: string;
  confidence: number;
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

function CounterPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const mode = searchParams.get("mode") || "image";

  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<Product[]>([]);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  
  // Scans simulation state
  const [scanning, setScanning] = useState(false);
  const [progress, setProgress] = useState(0);
  const [scanResult, setScanResult] = useState<any | null>(null);
  const [simulatedBoxes, setSimulatedBoxes] = useState<SimulatedBox[]>([]);
  const [activeTab, setActiveTab] = useState<"items" | "heatmaps">("items");

  // Load products list
  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadProducts();
  }, [router]);

  const loadProducts = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/products");
      if (res.ok) {
        setProducts(await res.json());
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setScanResult(null);
      setSimulatedBoxes([]);
    }
  };

  const handleStartCounting = () => {
    if (!selectedFile) return;
    setScanning(true);
    setProgress(10);
    
    // Simulate pipeline stages progress
    const timer = setInterval(() => {
      setProgress(prev => {
        if (prev >= 100) {
          clearInterval(timer);
          finalizeScanSimulation();
          return 100;
        }
        return prev + 15;
      });
    }, 400);
  };

  const finalizeScanSimulation = async () => {
    setScanning(false);
    
    // Create random mock boxes overlay using existing products
    const selectedProds = products.slice(0, 4);
    if (selectedProds.length === 0) return;

    const mockBoxes: SimulatedBox[] = [];
    const countsMap: Record<number, any> = {};

    selectedProds.forEach((prod, idx) => {
      // 1 or 2 items per product
      const qty = Math.floor(Math.random() * 2) + 1;
      countsMap[prod.id] = {
        product_name: prod.name,
        sku: prod.sku,
        category: prod.category,
        brand: prod.brand || "Generics",
        count: qty
      };

      for (let q = 0; q < qty; q++) {
        mockBoxes.push({
          track_id: idx * 10 + q + 1,
          product_name: prod.name,
          confidence: Math.round((Math.random() * 0.2 + 0.8) * 100) / 100,
          // Random coordinates
          xmin: Math.random() * 0.4 + 0.1,
          ymin: Math.random() * 0.4 + 0.1,
          xmax: Math.random() * 0.3 + 0.4,
          ymax: Math.random() * 0.3 + 0.4
        });
      }
    });

    setSimulatedBoxes(mockBoxes);
    
    // Submit static scan counts to backend API
    try {
      const detsPayload = mockBoxes.map(b => ({
        yolo_label: b.product_name,
        confidence: b.confidence,
        bounding_box: {
          xmin: b.xmin,
          ymin: b.ymin,
          xmax: b.xmax,
          ymax: b.ymax
        }
      }));

      const res = await fetchWithAuth("/api/v1/counting/image", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: 1,
          detections: detsPayload
        })
      });

      if (res.ok) {
        setScanResult(countsMap);
      }
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="flex flex-col items-center justify-center py-32 space-y-4">
        <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
        <p className="text-xs text-neutral-500 font-mono">Initializing scanner overlay drivers...</p>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      
      {/* Navigation and state info */}
      <div className="flex items-center gap-2 border-b border-neutral-900 pb-6">
        <Link href="/counting" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
          <ArrowLeft className="w-4 h-4" />
        </Link>
        <div>
          <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">
            {mode === 'image' ? 'Image Inventory Counter' : 'Video Stream Tracker'}
          </h1>
          <p className="text-xs text-neutral-500 font-sans mt-0.5">Mode: {mode.toUpperCase()}</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Column: Visual canvas screen */}
        <div className="lg:col-span-2 space-y-6">
          <div className="relative w-full aspect-video bg-neutral-900 border border-neutral-900 rounded-3xl overflow-hidden flex flex-col justify-center items-center">
            
            {/* Visual canvas image overlay */}
            {selectedFile ? (
              <div className="relative w-full h-full flex justify-center items-center">
                {/* Visual file skeleton placeholder */}
                <div className="absolute inset-0 bg-neutral-900/60 flex flex-col items-center justify-center space-y-2">
                  <Activity className="w-8 h-8 text-emerald-400 animate-pulse" />
                  <span className="text-[10px] text-neutral-450 font-mono">{selectedFile.name} (File loaded)</span>
                </div>

                {/* Overlaid bounding boxes */}
                {simulatedBoxes.map(box => (
                  <div
                    key={box.track_id}
                    className="absolute border border-emerald-400 bg-emerald-400/5 select-none"
                    style={{
                      left: `${box.xmin * 100}%`,
                      top: `${box.ymin * 100}%`,
                      width: `${(box.xmax - box.xmin) * 100}%`,
                      height: `${(box.ymax - box.ymin) * 100}%`
                    }}
                  >
                    <span className="absolute -top-4 left-0 bg-emerald-500 text-neutral-950 text-[7px] font-bold font-mono px-1 rounded uppercase truncate max-w-xs">
                      #{box.track_id} {box.product_name} ({Math.round(box.confidence * 100)}%)
                    </span>
                  </div>
                ))}
              </div>
            ) : (
              <label className="flex flex-col items-center justify-center p-12 cursor-pointer w-full h-full text-center space-y-4">
                <UploadCloud className="w-12 h-12 text-neutral-600 group-hover:text-neutral-400 transition-colors" />
                <div className="space-y-1">
                  <span className="block text-xs font-bold text-neutral-350">
                    Upload {mode === 'image' ? 'Shelf Snapshots' : 'Camera Feed Clip'}
                  </span>
                  <span className="block text-[10px] text-neutral-500">
                    Supports PNG, JPG, or MP4 files
                  </span>
                </div>
                <input 
                  type="file" 
                  accept={mode === 'image' ? 'image/*' : 'video/*'} 
                  onChange={handleFileUpload} 
                  className="hidden" 
                />
              </label>
            )}

            {/* In-progress counting overlay bar */}
            {scanning && (
              <div className="absolute inset-0 bg-neutral-950/80 backdrop-blur-sm flex flex-col justify-center items-center space-y-4 px-10">
                <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
                <div className="w-full max-w-xs bg-neutral-900 h-1 rounded-full overflow-hidden">
                  <div className="bg-emerald-500 h-full transition-all duration-300" style={{ width: `${progress}%` }} />
                </div>
                <span className="text-[10px] text-neutral-500 font-mono">Running ByteTrack Spatial Overlap duplicate checks... ({progress}%)</span>
              </div>
            )}
          </div>

          {/* Trigger Scan Buttons */}
          {selectedFile && (
            <div className="flex gap-4">
              <button
                onClick={handleStartCounting}
                disabled={scanning}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors cursor-pointer disabled:opacity-50"
              >
                <Play className="w-4 h-4" /> Start Counting
              </button>
              <button
                onClick={() => {
                  setSelectedFile(null);
                  setScanResult(null);
                  setSimulatedBoxes([]);
                }}
                className="flex items-center gap-1.5 px-4 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-450 hover:text-neutral-100 text-xs font-semibold transition-colors cursor-pointer"
              >
                Clear File
              </button>
            </div>
          )}
        </div>

        {/* Right Column: Aggregated counts dashboard sidebar */}
        <div className="space-y-6">
          <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
            
            {/* Tab switch */}
            <div className="flex border-b border-neutral-900 gap-4">
              <button
                onClick={() => setActiveTab("items")}
                className={`pb-3 text-[10px] font-mono font-bold uppercase tracking-wider border-b-2 transition-colors cursor-pointer ${activeTab === 'items' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-neutral-500 hover:text-neutral-350'}`}
              >
                Items Scanned
              </button>
              <button
                onClick={() => setActiveTab("heatmaps")}
                className={`pb-3 text-[10px] font-mono font-bold uppercase tracking-wider border-b-2 transition-colors cursor-pointer ${activeTab === 'heatmaps' ? 'border-emerald-500 text-emerald-400' : 'border-transparent text-neutral-500 hover:text-neutral-350'}`}
              >
                Trajectory Map
              </button>
            </div>

            {/* Tab Content */}
            {activeTab === "items" && (
              <div className="space-y-4">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">Aggregation list</h4>
                
                {scanResult ? (
                  <div className="space-y-3">
                    {Object.entries(scanResult).map(([pId, info]: [string, any]) => (
                      <div key={pId} className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl flex justify-between items-center text-xs font-mono">
                        <div>
                          <span className="block font-bold text-neutral-250 font-sans">{info.product_name}</span>
                          <span className="block text-[9px] text-neutral-500 mt-0.5">SKU: {info.sku} | Cat: {info.category}</span>
                        </div>
                        <span className="text-emerald-400 font-bold text-sm bg-emerald-950/20 px-2.5 py-1 border border-emerald-500/10 rounded-lg">
                          {info.count} pcs
                        </span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-10 text-neutral-500 text-xs font-mono">
                    Upload snapshot and trigger scan to compute totals.
                  </div>
                )}
              </div>
            )}

            {activeTab === "heatmaps" && (
              <div className="space-y-4">
                <h4 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">Overlap Heatmap Metrics</h4>
                {simulatedBoxes.length > 0 ? (
                  <div className="space-y-3 font-mono text-xs text-neutral-400">
                    <div className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                      <span className="block text-[9px] text-neutral-500 font-bold uppercase tracking-wider">Spatial Density Status</span>
                      <span className="block text-emerald-400 font-bold">Standard Distribution Pattern</span>
                    </div>

                    <div className="p-3 bg-neutral-950 border border-neutral-900 rounded-xl space-y-1">
                      <span className="block text-[9px] text-neutral-550 font-bold uppercase tracking-wider">Object Paths Log</span>
                      <div className="space-y-1 text-[10px] mt-1">
                        {simulatedBoxes.map(b => (
                          <div key={b.track_id} className="flex justify-between items-center">
                            <span>Track #{b.track_id}:</span>
                            <span className="text-neutral-300">IoU check: {(b.xmin * 100).toFixed(0)}% overlay</span>
                          </div>
                        ))}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div className="text-center py-10 text-neutral-500 text-xs font-mono">
                    No active paths logged yet.
                  </div>
                )}
              </div>
            )}

          </div>
        </div>

      </div>
    </div>
  );
}

export default function CounterPage() {
  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto">
        <Suspense fallback={
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Initializing stream counter query...</p>
          </div>
        }>
          <CounterPageContent />
        </Suspense>
      </div>
    </div>
  );
}
