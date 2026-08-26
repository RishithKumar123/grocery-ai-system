"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Scan, 
  ArrowLeft, 
  Target, 
  Info, 
  Sliders, 
  CheckCircle,
  Building2,
  Tv,
  ListFilter,
  UploadCloud,
  Camera,
  VideoOff,
  X,
  Clock,
  Award,
  Activity,
  Loader2
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";
import { getApiBaseUrl } from "../../lib/config";

interface Detection {
  id: number;
  scan_id: number;
  product_id: number | null;
  product_name: string;
  confidence: number;
  bounding_box: {
    xmin: number;
    ymin: number;
    xmax: number;
    ymax: number;
    track_id?: number | string | null;
    ocr_mrp?: number | null;
    ocr_weight?: string | null;
    ocr_batch?: string | null;
    ocr_mfg?: string | null;
    ocr_expiry?: string | null;
    barcode?: string | null;
    barcode_type?: string | null;
    brand?: string | null;
    variant?: string | null;
    sku?: string | null;
    matching_criteria?: string | null;
  };
  raw_ocr_text: string | null;
}

interface ScanReport {
  id: number;
  video_id: number | null;
  store_id: number;
  image_url: string;
  status: string;
  created_at: string;
  detections: Detection[];
}

export default function AIScansPage() {
  const router = useRouter();
  const [scans, setScans] = useState<ScanReport[]>([]);
  const [selectedScan, setSelectedScan] = useState<ScanReport | null>(null);
  const [loading, setLoading] = useState(true);

  // Modal & Timer States
  const [isScanModalOpen, setIsScanModalOpen] = useState(false);
  const [scanFile, setScanFile] = useState<File | null>(null);
  const [isLiveCamera, setIsLiveCamera] = useState(false);
  
  const [scanStatus, setScanStatus] = useState<"idle" | "uploading" | "processing" | "completed" | "failed">("idle");
  const [stage, setStage] = useState("");
  const [percent, setPercent] = useState(0);
  
  const [startTimeLocal, setStartTimeLocal] = useState<string | null>(null);
  const [endTimeLocal, setEndTimeLocal] = useState<string | null>(null);
  const [elapsedTime, setElapsedTime] = useState(0);
  const [scanDuration, setScanDuration] = useState(0);
  const [perfStats, setPerfStats] = useState<any>(null);

  const liveIntervalRef = useRef<any>(null);
  const startPerfTimeRef = useRef<number>(0);
  const videoRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const [webcamCountdown, setWebcamCountdown] = useState(10);
  const webcamIntervalRef = useRef<any>(null);
  const [isRecording, setIsRecording] = useState(false);

  // Webcam stream activation
  const startWebcam = async () => {
    setIsLiveCamera(true);
    setScanFile(null);
    setWebcamCountdown(10);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = mediaStream;
        videoRef.current.play();
      }
      
      const recorder = new MediaRecorder(mediaStream);
      mediaRecorderRef.current = recorder;
      
      const chunks: Blob[] = [];
      recorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          chunks.push(e.data);
        }
      };
      
      recorder.onstop = () => {
        const videoBlob = new Blob(chunks, { type: "video/mp4" });
        const videoFile = new File([videoBlob], "webcam-capture.mp4", { type: "video/mp4" });
        setScanFile(videoFile);
        setIsLiveCamera(false);
        triggerVideoScanProcess(videoFile);
        
        // Stop stream tracks
        mediaStream.getTracks().forEach(track => track.stop());
      };
    } catch (err) {
      console.error("Webcam initiation failed", err);
      alert("Could not access webcam stream. Please check browser permissions.");
    }
  };

  const stopWebcam = () => {
    setIsLiveCamera(false);
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(t => t.stop());
      videoRef.current.srcObject = null;
    }
    if (webcamIntervalRef.current) clearInterval(webcamIntervalRef.current);
    setIsRecording(false);
  };

  const startWebcamRecording = () => {
    if (!mediaRecorderRef.current) return;
    setIsRecording(true);
    mediaRecorderRef.current.start();
    
    // Start live elapsed timer immediately when user clicks start
    startPerfTimeRef.current = performance.now();
    setStartTimeLocal(new Date().toLocaleTimeString());
    setScanStatus("processing");
    setStage("Recording Video...");
    setPercent(5);

    liveIntervalRef.current = setInterval(() => {
      setElapsedTime((performance.now() - startPerfTimeRef.current) / 1000);
    }, 100);

    setWebcamCountdown(10);
    webcamIntervalRef.current = setInterval(() => {
      setWebcamCountdown((prev) => {
        if (prev <= 1) {
          stopWebcamRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const stopWebcamRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (webcamIntervalRef.current) {
        clearInterval(webcamIntervalRef.current);
      }
    }
  };

  const handleUseWebcamRecording = async () => {
    if (!scanFile) return;
    setIsLiveCamera(false);
    triggerVideoScanProcess(scanFile);
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setScanFile(file);
    }
  };

  const triggerScanSubmit = async () => {
    if (!scanFile) return;
    
    startPerfTimeRef.current = performance.now();
    setStartTimeLocal(new Date().toLocaleTimeString());
    
    liveIntervalRef.current = setInterval(() => {
      setElapsedTime((performance.now() - startPerfTimeRef.current) / 1000);
    }, 100);

    if (scanFile.type.startsWith("image/")) {
      triggerImageScanProcess(scanFile);
    } else {
      triggerVideoScanProcess(scanFile);
    }
  };

  const triggerImageScanProcess = async (file: File) => {
    setScanStatus("processing");
    setStage("Uploading Image...");
    setPercent(15);
    
    const formData = new FormData();
    formData.append("file", file);
    formData.append("store_id", "1");

    try {
      const res = await fetch("/api/v1/inventory/scan?store_id=1", {
        method: "POST",
        headers: {
          ...(getAccessToken() ? { "Authorization": `Bearer ${getAccessToken()}` } : {})
        },
        body: formData
      });

      if (!res.ok) {
        let msg = "Image scanning failed.";
        try {
          const errData = await res.json();
          if (errData?.detail) msg = errData.detail;
        } catch (_) {}
        setScanStatus("failed");
        setStage(msg);
        if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
        return;
      }
      
      const scansList = await fetchWithAuth("/api/v1/scans");
      if (scansList && scansList.ok) {
        const data = await scansList.json();
        if (data && data.length > 0) {
          const latestScan = data[0];
          finalizeTimerAndStats(latestScan);
        }
      }
    } catch (err: any) {
      setScanStatus("failed");
      setStage(`Error: ${err.message || "Scanning failed."}`);
      if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
    }
  };

  const triggerVideoScanProcess = async (file: File) => {
    setScanStatus("uploading");
    setStage("Uploading Video...");
    setPercent(10);

    const CHUNK_SIZE = 5 * 1024 * 1024;
    const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
    const uploadId = `upload_${Date.now()}`;
    const cleanFileName = file.name.replace(/[^a-zA-Z0-9.-]/g, "_");

    try {
      for (let chunkIndex = 0; chunkIndex < totalChunks; chunkIndex++) {
        const start = chunkIndex * CHUNK_SIZE;
        const end = Math.min(start + CHUNK_SIZE, file.size);
        const chunk = file.slice(start, end);

        const formData = new FormData();
        formData.append("chunk", chunk);
        formData.append("chunkIndex", chunkIndex.toString());
        formData.append("totalChunks", totalChunks.toString());
        formData.append("uploadId", uploadId);
        formData.append("filename", cleanFileName);

        const chunkRes = await fetch(`/api/v1/videos/upload/chunk?upload_id=${uploadId}&chunk_index=${chunkIndex}&total_chunks=${totalChunks}`, {
          method: "POST",
          headers: {
            ...(getAccessToken() ? { "Authorization": `Bearer ${getAccessToken()}` } : {})
          },
          body: formData
        });

        if (!chunkRes.ok) throw new Error(`Chunk ${chunkIndex} transfer failed.`);
        setPercent(Math.round(((chunkIndex + 1) / totalChunks) * 15) + 10);
      }

      setStage("Extracting Frames...");
      setPercent(25);

      const completeRes = await fetch("/api/v1/videos/upload/complete", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(getAccessToken() ? { "Authorization": `Bearer ${getAccessToken()}` } : {})
        },
        body: JSON.stringify({
          uploadId,
          filename: cleanFileName,
          store_id: 1,
          camera_name: "Aisle Cam 1"
        })
      });

      if (!completeRes.ok) throw new Error("Video completion trigger failed.");
      const videoData = await completeRes.json();
      
      setScanStatus("processing");
      pollProcessingStatus(videoData.id);

    } catch (err: any) {
      console.error(err);
      setScanStatus("failed");
      setStage(`Error: ${err.message}`);
      if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
    }
  };

  const pollProcessingStatus = async (videoId: number) => {
    const interval = setInterval(async () => {
      try {
        const res = await fetchWithAuth("/api/v1/scans");
        if (res.ok) {
          const scansList = await res.json();
          const targetScan = scansList.find((s: any) => s.video_id === videoId);
          if (targetScan) {
            setStage(targetScan.progress_stage || "Detecting Products...");
            setPercent(targetScan.progress_percentage || 50);

            if (targetScan.status === "Completed") {
              clearInterval(interval);
              finalizeTimerAndStats(targetScan);
            } else if (targetScan.status === "Failed") {
              clearInterval(interval);
              setScanStatus("failed");
              setStage(targetScan.progress_stage || "Processing Failed.");
              if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
            }
          }
        }
      } catch (err) {
        console.error("Polling error", err);
      }
    }, 1000);
  };

  const finalizeTimerAndStats = (scanRecord: any) => {
    if (liveIntervalRef.current) {
      clearInterval(liveIntervalRef.current);
    }
    
    setScanDuration(scanRecord?.scan_duration || 0);
    setElapsedTime(scanRecord?.scan_duration || 0);
    setEndTimeLocal(scanRecord?.scan_end_time ? new Date(scanRecord.scan_end_time).toLocaleTimeString() : new Date().toLocaleTimeString());
    setScanStatus("completed");
    setPercent(100);
    setStage("Completed...");

    const detectionsList = scanRecord?.detections || [];
    const totalDets = detectionsList.length;
    const identified = detectionsList.filter((d: any) => d.product_id !== null).length;
    
    const unknown = detectionsList.filter((d: any) => {
      const name = (d.product_name || "").toLowerCase();
      return name.includes("person") || name.includes("laptop") || name.includes("book") || name.includes("bottle") || name.includes("unknown");
    }).length;

    const avgConf = detectionsList.reduce((acc: number, curr: any) => acc + (curr.confidence || 0), 0) / (totalDets || 1);

    setPerfStats({
      total_detected: totalDets,
      total_identified: identified,
      unknown_products: unknown,
      ai_confidence: Math.round(avgConf * 100),
      frames_processed: scanRecord?.frames_processed || 1,
      fps: scanRecord?.fps || 1.0,
      duration: scanRecord?.scan_duration || 0
    });

    loadScans();
  };

  const resetModalStates = () => {
    setScanFile(null);
    setIsLiveCamera(false);
    setScanStatus("idle");
    setStage("");
    setPercent(0);
    setElapsedTime(0);
    setScanDuration(0);
    setStartTimeLocal(null);
    setEndTimeLocal(null);
    setPerfStats(null);
    if (liveIntervalRef.current) clearInterval(liveIntervalRef.current);
  };

  // Filters
  const [minConfidence, setMinConfidence] = useState(0.1);
  const [categoryFilter, setCategoryFilter] = useState("All");

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      setLoading(false);
      router.push("/login");
      return;
    }

    loadScans();
  }, [router]);

  const loadScans = async () => {
    const token = getAccessToken();
    if (!token) {
      setLoading(false);
      return;
    }

    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/scans");
      if (res && res.ok) {
        const data = await res.json();
        setScans(data || []);
        if (data && data.length > 0) {
          setSelectedScan(data[0]);
        }
      }
    } catch (err) {
      // Suppress unauthenticated fetch errors
    } finally {
      setLoading(false);
    }
  };

  // Filtered Detections for selected scan
  const filteredDetections = selectedScan
    ? selectedScan.detections.filter(det => {
        const confPass = det.confidence >= minConfidence;
        // Simple label mapping for categories
        if (categoryFilter === "All") return confPass;
        
        const label = det.product_name.toLowerCase();
        if (categoryFilter === "Fruits") {
          return confPass && ["banana", "apple", "orange", "strawberry", "lemon"].some(x => label.includes(x));
        }
        if (categoryFilter === "Vegetables") {
          return confPass && ["broccoli", "carrot", "cucumber", "tomato", "salad"].some(x => label.includes(x));
        }
        if (categoryFilter === "Drinks") {
          return confPass && ["bottle", "cup", "wine", "glass", "drink", "can"].some(x => label.includes(x));
        }
        if (categoryFilter === "Packaged Foods") {
          return confPass && ["sandwich", "pizza", "donut", "cake", "hot dog", "box", "cornflakes"].some(x => label.includes(x));
        }
        if (categoryFilter === "Dairy") {
          return confPass && ["milk", "cheese", "butter", "yogurt"].some(x => label.includes(x));
        }
        return confPass;
      })
    : [];

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col">
      {/* Top Navbar */}
      <nav className="border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-20 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/50 text-neutral-400 hover:text-emerald-400 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Target className="w-6 h-6 text-emerald-400" />
            <span className="font-bold text-lg text-neutral-100">YOLOv11 AI Shelf Detection Console</span>
          </div>
        </div>
        <button
          onClick={() => { setIsScanModalOpen(true); resetModalStates(); }}
          className="flex items-center gap-1.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 px-4 py-2.5 text-xs font-bold text-neutral-950 transition-all cursor-pointer shadow-lg shadow-emerald-500/10"
        >
          <Scan className="w-4 h-4" /> Start New Scan
        </button>
      </nav>

      {/* Main Grid */}
      <main className="flex-1 w-full max-w-7xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left: Scans List (Col span 4) */}
        <div className="lg:col-span-4 space-y-4 max-h-[80vh] overflow-y-auto pr-1">
          <div className="border-b border-neutral-900 pb-3 flex justify-between items-center">
            <h3 className="font-bold text-neutral-200 text-sm">Scan Reports</h3>
            <span className="px-2 py-0.5 rounded-full bg-emerald-950/40 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold">
              {scans.length} Total
            </span>
          </div>

          {loading ? (
            <div className="py-20 text-center text-neutral-500 text-xs">Loading scan feeds...</div>
          ) : scans.length === 0 ? (
            <div className="py-20 text-center text-neutral-600 text-xs">No shelf scans processed yet. Upload security footage to trigger.</div>
          ) : (
            <div className="space-y-3">
              {scans.map(s => (
                <button
                  key={s.id}
                  onClick={() => setSelectedScan(s)}
                  className={`w-full text-left p-4 rounded-2xl border transition-all cursor-pointer ${
                    selectedScan?.id === s.id
                      ? "bg-emerald-950/10 border-emerald-500/40 text-emerald-300"
                      : "bg-neutral-900/40 border-neutral-850 hover:border-neutral-800 text-neutral-300"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-bold text-xs">Scan ID: #SCN-{s.id}</span>
                    <span className="px-1.5 py-0.5 rounded bg-emerald-950/20 text-emerald-400 text-[8px] font-mono font-bold tracking-wider">
                      {s.detections.length} DETECTED
                    </span>
                  </div>
                  <div className="text-[10px] text-neutral-500 space-y-1">
                    <div className="flex items-center gap-1">
                      <Building2 className="w-3 h-3" /> Branch Store: #{s.store_id}
                    </div>
                    {s.video_id && (
                      <div className="flex items-center gap-1">
                        <Tv className="w-3 h-3" /> Source Video: Feed #{s.video_id}
                      </div>
                    )}
                    <div className="text-[9px] text-neutral-600 pt-1 font-mono">
                      {new Date(s.created_at).toLocaleString()}
                    </div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Right: Active Frame Viewer & Detections Details (Col span 8) */}
        {selectedScan ? (
          <div className="lg:col-span-8 space-y-6">
            
            {/* Interactive Image Frame Viewer with overlays */}
            <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-4">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-3">
                <div>
                  <h3 className="font-bold text-neutral-100 text-sm">Shelf Frame Overlay</h3>
                  <p className="text-[10px] text-neutral-500">Overlay representing detected bounding boxes from model inference</p>
                </div>
                <div className="flex items-center gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400" />
                  <span className="text-xs text-neutral-400">YOLOv11 Integrated</span>
                </div>
              </div>

              {/* Bounding Box Container */}
              <div className="relative aspect-video w-full rounded-2xl bg-neutral-900 overflow-hidden border border-neutral-850 flex items-center justify-center">
                {/* Fallback visual background representation */}
                <div className="absolute inset-0 bg-gradient-to-br from-neutral-900 to-neutral-950 flex flex-col items-center justify-center text-center p-6 space-y-3">
                  <Target className="w-12 h-12 text-emerald-400 stroke-[1]" />
                  <div>
                    <h4 className="font-bold text-xs text-neutral-300">YOLOv11 Detections Container</h4>
                    <p className="text-[10px] text-neutral-500 max-w-sm mt-1">
                      Rendered Bounding Box dimensions scaled dynamically relative to the target 640x640 frame resolution.
                    </p>
                  </div>
                </div>

                {/* Overlaid bounding box boxes */}
                <div className="absolute inset-0 w-full h-full pointer-events-none">
                  {filteredDetections.map((det, idx) => {
                    // Convert bounding box coordinates (assuming 640x640 input resolution) into percentages
                    const left = `${(det.bounding_box.xmin / 640) * 100}%`;
                    const top = `${(det.bounding_box.ymin / 640) * 100}%`;
                    const width = `${((det.bounding_box.xmax - det.bounding_box.xmin) / 640) * 100}%`;
                    const height = `${((det.bounding_box.ymax - det.bounding_box.ymin) / 640) * 100}%`;

                    const confPercent = det.confidence > 1 ? Math.round(det.confidence) : Math.round(det.confidence * 100);
                    const barcodeTag = (det.bounding_box.barcode && det.bounding_box.barcode_type) ? `[${det.bounding_box.barcode_type}]` : "";
                    const trackTag = det.bounding_box.track_id ? `#${det.bounding_box.track_id}` : "";

                    return (
                      <div
                        key={det.id}
                        className="absolute border-2 border-emerald-400/80 bg-emerald-500/5 flex items-start pl-1 pt-0.5 rounded-sm transition-all"
                        style={{ left, top, width, height }}
                      >
                        <span className="absolute -top-5 left-0 px-1 py-0.5 bg-emerald-500 text-neutral-950 font-bold text-[8px] rounded-sm whitespace-nowrap shadow-md">
                          {det.product_name} {barcodeTag} {trackTag} ({confPercent}%)
                        </span>
                      </div>
                    );
                  })}
                </div>
              </div>
            </div>

            {/* Filters and Detections Details grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              
              {/* Sliders Panel */}
              <div className="glass p-5 rounded-3xl border border-neutral-900 space-y-5">
                <h4 className="font-bold text-neutral-200 text-xs flex items-center gap-1.5">
                  <Sliders className="w-4 h-4 text-emerald-400" /> Filters
                </h4>

                <div className="space-y-4">
                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-2">
                      Min Confidence: {Math.round(minConfidence * 100)}%
                    </label>
                    <input
                      type="range"
                      min="0.3"
                      max="0.95"
                      step="0.05"
                      className="w-full accent-emerald-500 bg-neutral-800 rounded-lg appearance-none h-1"
                      value={minConfidence}
                      onChange={e => setMinConfidence(parseFloat(e.target.value))}
                    />
                  </div>

                  <div>
                    <label className="block text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-1.5">
                      Category Filter
                    </label>
                    <select
                      className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs focus:outline-none"
                      value={categoryFilter}
                      onChange={e => setCategoryFilter(e.target.value)}
                    >
                      <option value="All">All Categories</option>
                      <option value="Dairy">Dairy</option>
                      <option value="Fruits">Fruits</option>
                      <option value="Vegetables">Vegetables</option>
                      <option value="Drinks">Drinks</option>
                      <option value="Packaged Foods">Packaged Foods</option>
                    </select>
                  </div>
                </div>
              </div>

              {/* Detections List (Col span 2) */}
              <div className="glass p-5 rounded-3xl border border-neutral-900 space-y-4 md:col-span-2 max-h-[35vh] overflow-y-auto">
                <div className="border-b border-neutral-900 pb-3 flex justify-between items-center">
                  <h4 className="font-bold text-neutral-200 text-xs flex items-center gap-1.5">
                    <ListFilter className="w-4 h-4 text-emerald-400" /> Details List
                  </h4>
                  <span className="text-[10px] text-neutral-500 font-medium">
                    Showing {filteredDetections.length} of {selectedScan.detections.length}
                  </span>
                </div>

                {filteredDetections.length === 0 ? (
                  <div className="py-8 text-center text-neutral-600 text-xs">No matching detections filter match.</div>
                ) : (
                  <div className="space-y-2">
                    {filteredDetections.map(det => (
                      <div key={det.id} className="p-3.5 rounded-xl bg-neutral-950 border border-neutral-900/60 flex justify-between items-center text-xs">
                        <div className="flex-1 min-w-0 pr-4">
                          <span className="font-bold text-neutral-200 block truncate">
                            {det.product_name} {det.bounding_box.track_id ? `(Track #${det.bounding_box.track_id})` : ""}
                          </span>
                          <div className="flex flex-wrap gap-1.5 mt-2">
                            <span className="text-[8px] font-mono bg-neutral-900 text-neutral-400 px-1.5 py-0.5 rounded border border-neutral-850">
                              Box: [{det.bounding_box.xmin}, {det.bounding_box.ymin}, {det.bounding_box.xmax}, {det.bounding_box.ymax}]
                            </span>
                            {det.bounding_box.ocr_mrp && (
                              <span className="text-[8px] font-mono bg-emerald-950/20 text-emerald-400 px-1.5 py-0.5 rounded border border-emerald-900/20">
                                MRP: Rs. {det.bounding_box.ocr_mrp}
                              </span>
                            )}
                            {det.bounding_box.ocr_weight && (
                              <span className="text-[8px] font-mono bg-sky-950/20 text-sky-400 px-1.5 py-0.5 rounded border border-sky-900/20">
                                Wt: {det.bounding_box.ocr_weight}
                              </span>
                            )}
                            {det.bounding_box.ocr_batch && (
                              <span className="text-[8px] font-mono bg-purple-950/20 text-purple-400 px-1.5 py-0.5 rounded border border-purple-900/20">
                                Batch: {det.bounding_box.ocr_batch}
                              </span>
                            )}
                            {det.bounding_box.ocr_mfg && (
                              <span className="text-[8px] font-mono bg-neutral-900 text-neutral-400 px-1.5 py-0.5 rounded border border-neutral-800">
                                Mfg: {det.bounding_box.ocr_mfg}
                              </span>
                            )}
                            {det.bounding_box.ocr_expiry && (
                              <span className="text-[8px] font-mono bg-yellow-950/20 text-yellow-400 px-1.5 py-0.5 rounded border border-yellow-900/20">
                                Exp: {det.bounding_box.ocr_expiry}
                              </span>
                            )}
                            {det.bounding_box.barcode && (
                              <span className="text-[8px] font-mono bg-pink-950/20 text-pink-400 px-1.5 py-0.5 rounded border border-pink-900/20">
                                Barcode ({det.bounding_box.barcode_type}): {det.bounding_box.barcode}
                              </span>
                            )}
                            {det.bounding_box.brand && (
                              <span className="text-[8px] font-mono bg-violet-950/20 text-violet-400 px-1.5 py-0.5 rounded border border-violet-900/20">
                                Brand: {det.bounding_box.brand}
                              </span>
                            )}
                            {det.bounding_box.variant && (
                              <span className="text-[8px] font-mono bg-indigo-950/20 text-indigo-400 px-1.5 py-0.5 rounded border border-indigo-900/20">
                                Var: {det.bounding_box.variant}
                              </span>
                            )}
                            {det.bounding_box.sku && (
                              <span className="text-[8px] font-mono bg-amber-950/20 text-amber-400 px-1.5 py-0.5 rounded border border-amber-900/20">
                                SKU: {det.bounding_box.sku}
                              </span>
                            )}
                            {det.bounding_box.matching_criteria && (
                              <span className="text-[8px] font-mono bg-cyan-950/20 text-cyan-400 px-1.5 py-0.5 rounded border border-cyan-900/20">
                                Match: {det.bounding_box.matching_criteria}
                              </span>
                            )}
                          </div>
                        </div>
                        <div className="text-right">
                          <span className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                            det.confidence > 0.8 || det.confidence > 80
                              ? "bg-emerald-950/20 text-emerald-400 border border-emerald-500/10"
                              : "bg-yellow-950/20 text-yellow-400 border border-yellow-500/10"
                          }`}>
                            {det.confidence > 1 ? Math.round(det.confidence) : Math.round(det.confidence * 100)}% Conf
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

          </div>
        ) : (
          <div className="lg:col-span-8 flex flex-col items-center justify-center py-40 border border-dashed border-neutral-900 rounded-3xl text-center space-y-3">
            <Target className="w-10 h-10 text-neutral-800" />
            <p className="text-neutral-500 text-sm">Select a shelf scan report to view frame overlay boxes and confidence meters</p>
          </div>
        )}

      </main>

      {/* Start Scan High-Fidelity Modal */}
      {isScanModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-md p-4 overflow-y-auto">
          <div className="glass w-full max-w-2xl rounded-3xl border border-neutral-900 bg-neutral-950/90 text-left shadow-2xl overflow-hidden flex flex-col my-8">
            {/* Header */}
            <div className="px-6 py-5 border-b border-neutral-900 flex justify-between items-center">
              <div className="flex items-center gap-2">
                <Scan className="w-5 h-5 text-emerald-400" />
                <h3 className="font-bold text-sm text-neutral-200">Start Shelf Scanning</h3>
              </div>
              <button
                onClick={() => { stopWebcam(); setIsScanModalOpen(false); }}
                className="p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 hover:border-neutral-800 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Content */}
            <div className="p-6 space-y-6 flex-1 overflow-y-auto max-h-[70vh]">
              {scanStatus === "idle" && (
                <>
                  {!isLiveCamera ? (
                    /* Select Source Drop Desk */
                    <div className="space-y-6">
                      <div className="p-10 border border-dashed border-neutral-900 hover:border-neutral-800 bg-neutral-900/10 rounded-2xl text-center space-y-4">
                        <UploadCloud className="w-12 h-12 text-emerald-400 stroke-[1.5] mx-auto" />
                        <div>
                          <h4 className="font-bold text-xs text-neutral-200">Upload Shelf Image or Video</h4>
                          <p className="text-[10px] text-neutral-500 mt-1">Supports PNG, JPG, MP4, MOV formats up to 100MB</p>
                        </div>

                        <div className="flex justify-center items-center gap-3 pt-2">
                          <label className="px-4 py-2 rounded-xl border border-neutral-800 bg-neutral-950 hover:bg-neutral-900 text-neutral-400 hover:text-neutral-200 text-xs font-semibold cursor-pointer transition-all">
                            Browse File
                            <input type="file" accept="image/*,video/*" className="hidden" onChange={handleFileChange} />
                          </label>
                          <span className="text-[10px] text-neutral-600 font-bold">OR</span>
                          <button
                            onClick={startWebcam}
                            className="px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-1.5 cursor-pointer transition-all"
                          >
                            <Camera className="w-4 h-4" /> Record Webcam
                          </button>
                        </div>
                      </div>

                      {scanFile && (
                        <div className="p-4 rounded-xl bg-neutral-900/50 border border-neutral-900 flex justify-between items-center text-xs">
                          <div>
                            <span className="font-semibold text-neutral-300 block truncate max-w-sm">{scanFile.name}</span>
                            <span className="text-[10px] text-neutral-500">{(scanFile.size / (1024 * 1024)).toFixed(2)} MB</span>
                          </div>
                          <button
                            onClick={triggerScanSubmit}
                            className="px-4 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold cursor-pointer"
                          >
                            Start Scan
                          </button>
                        </div>
                      )}
                    </div>
                  ) : (
                    /* Live Webcam Record Desk */
                    <div className="space-y-4">
                      <div className="relative aspect-video w-full rounded-2xl bg-neutral-900 overflow-hidden border border-neutral-850">
                        <video ref={videoRef} muted playsInline className="w-full h-full object-cover" />
                        {isRecording && (
                          <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-red-600/90 text-white text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5 animate-pulse">
                            <span className="w-2 h-2 bg-white rounded-full" /> REC {webcamCountdown}s
                          </div>
                        )}
                      </div>

                      <div className="flex justify-center gap-3 pt-2">
                        {!isRecording ? (
                          !scanFile ? (
                            <button
                              onClick={startWebcamRecording}
                              className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer shadow-lg shadow-red-600/10"
                            >
                              <Camera className="w-4 h-4" /> Start Recording
                            </button>
                          ) : (
                            <>
                              <button
                                onClick={startWebcam}
                                className="px-4 py-2.5 rounded-xl border border-neutral-800 text-neutral-400 hover:text-neutral-200 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                              >
                                Retake Video
                              </button>
                              <button
                                onClick={handleUseWebcamRecording}
                                className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
                              >
                                <CheckCircle className="w-4 h-4" /> Use Recording
                              </button>
                            </>
                          )
                        ) : (
                          <button
                            onClick={stopWebcamRecording}
                            className="px-5 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-300 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
                          >
                            <VideoOff className="w-4 h-4" /> Stop Recording
                          </button>
                        )}
                      </div>
                    </div>
                  )}
                </>
              )}

              {(scanStatus === "uploading" || scanStatus === "processing") && (
                /* Scanning Stage Progress */
                <div className="space-y-6 text-center py-6">
                  <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
                    {/* Ring bar */}
                    <div className="absolute inset-0 rounded-full border-4 border-neutral-900" />
                    <div 
                      className="absolute inset-0 rounded-full border-4 border-emerald-500 border-t-transparent border-r-transparent animate-spin" 
                      style={{ animationDuration: "1.5s" }}
                    />
                    <span className="font-mono text-sm font-bold text-neutral-100">{percent}%</span>
                  </div>

                  <div className="space-y-2">
                    <h4 className="font-bold text-neutral-200 text-sm animate-pulse">{stage}</h4>
                    <div className="max-w-xs mx-auto text-[11px] text-neutral-500 space-y-1 font-mono">
                      <div>Start Time: <span className="text-neutral-300">{startTimeLocal || "N/A"}</span></div>
                      <div>Elapsed Scan Time: <span className="text-emerald-400 font-bold">{elapsedTime.toFixed(2)} Seconds</span></div>
                    </div>
                  </div>

                  {/* Horizontal visual indicator bar */}
                  <div className="w-full bg-neutral-900 h-1.5 rounded-full overflow-hidden">
                    <div 
                      className="bg-emerald-500 h-full transition-all duration-300 shadow-[0_0_8px_rgba(16,185,129,0.5)]" 
                      style={{ width: `${percent}%` }}
                    />
                  </div>
                </div>
              )}

              {scanStatus === "completed" && perfStats && (
                /* Complete High Fidelity Performance Report Dashboard */
                <div className="space-y-6">
                  <div className="p-4 rounded-2xl bg-emerald-950/10 border border-emerald-500/20 text-center space-y-2">
                    <CheckCircle className="w-10 h-10 text-emerald-400 mx-auto stroke-[1.5]" />
                    <h4 className="font-bold text-neutral-200">AI Shelf Inventory Scan Complete!</h4>
                    <p className="text-[10px] text-neutral-500 max-w-sm mx-auto">
                      All pipeline stages completed, inventories updated in PostgreSQL/SQLite, and Excel report dispatched.
                    </p>
                  </div>

                  {/* Performance stats grids */}
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Products Detected</div>
                      <div className="text-lg font-bold text-neutral-200 mt-1">{perfStats.total_detected}</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Products Identified</div>
                      <div className="text-lg font-bold text-emerald-400 mt-1">{perfStats.total_identified}</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Unknown Fallbacks</div>
                      <div className="text-lg font-bold text-yellow-400 mt-1">{perfStats.unknown_products}</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Avg AI Confidence</div>
                      <div className="text-lg font-bold text-neutral-200 mt-1">{perfStats.ai_confidence}%</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Frames Processed</div>
                      <div className="text-lg font-bold text-neutral-200 mt-1">{perfStats.frames_processed}</div>
                    </div>
                    <div className="p-3.5 rounded-xl bg-neutral-900 border border-neutral-850">
                      <div className="text-[10px] text-neutral-500 font-semibold uppercase">Processing Speed</div>
                      <div className="text-lg font-bold text-neutral-200 mt-1">{perfStats.fps.toFixed(1)} FPS</div>
                    </div>
                  </div>

                  {/* Precise Time calculations audit panel */}
                  <div className="p-4 rounded-xl bg-neutral-900 border border-neutral-800/60 font-mono text-xs text-neutral-400 space-y-2">
                    <div className="flex justify-between">
                      <span>Start Time:</span>
                      <span className="text-neutral-300 font-semibold">{startTimeLocal}</span>
                    </div>
                    <div className="flex justify-between">
                      <span>End Time:</span>
                      <span className="text-neutral-300 font-semibold">{endTimeLocal}</span>
                    </div>
                    <div className="flex justify-between border-t border-neutral-800 pt-2 text-sm">
                      <span className="font-bold text-neutral-200">Total Scan Time:</span>
                      <span className="text-emerald-400 font-bold">{scanDuration.toFixed(2)} Seconds</span>
                    </div>
                  </div>

                  <div className="flex justify-end gap-3 pt-2">
                    <button
                      onClick={resetModalStates}
                      className="px-4 py-2 rounded-xl border border-neutral-800 text-neutral-400 hover:text-neutral-200 text-xs font-semibold cursor-pointer"
                    >
                      Scan Another
                    </button>
                    <button
                      onClick={() => { stopWebcam(); setIsScanModalOpen(false); }}
                      className="px-5 py-2 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs cursor-pointer"
                    >
                      View Reports
                    </button>
                  </div>
                </div>
              )}

              {scanStatus === "failed" && (
                <div className="space-y-4 text-center py-6">
                  <div className="w-12 h-12 rounded-full bg-red-950/20 border border-red-500/30 flex items-center justify-center mx-auto text-red-500">
                    <X className="w-6 h-6" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="font-bold text-neutral-200">Pipeline Execution Interrupted</h4>
                    <p className="text-[11px] text-neutral-500 font-mono">{stage}</p>
                  </div>
                  <button
                    onClick={resetModalStates}
                    className="px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-300 hover:text-neutral-200 text-xs font-semibold cursor-pointer"
                  >
                    Retry Scan
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
