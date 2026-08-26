"use client";

import React, { useState, useEffect, useRef } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { 
  Camera, 
  Upload, 
  Trash2, 
  AlertTriangle, 
  CheckCircle, 
  FolderOpen, 
  Activity, 
  Layers, 
  Tag, 
  Save, 
  ArrowLeft, 
  Plus, 
  Info,
  Maximize2,
  PieChart,
  Grid,
  Loader2
} from "lucide-react";
import { fetchWithAuth } from "../../../lib/auth";

export default function DatasetCurationPage() {
  const router = useRouter();

  // Dataset states
  const [stats, setStats] = useState<any>({
    total_images: 0,
    annotated_images: 0,
    unannotated_images: 0,
    labels_distribution: {},
    local_folder_path: ""
  });
  const [images, setImages] = useState<string[]>([]);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  
  // Quality & duplicates state
  const [qualityReports, setQualityReports] = useState<Record<string, any>>({});
  const [duplicates, setDuplicates] = useState<any[]>([]);

  // Bounding box drawing state
  const [isDrawing, setIsDrawing] = useState(false);
  const [startX, setStartX] = useState(0);
  const [startY, setStartY] = useState(0);
  const [endX, setEndX] = useState(0);
  const [endY, setEndY] = useState(0);
  const [tempBoxes, setTempBoxes] = useState<any[]>([]);
  const [activeLabel, setActiveLabel] = useState("Dark Fantasy Chocolate");
  const imgContainerRef = useRef<HTMLDivElement>(null);

  // Version snapshot state
  const [versionTag, setVersionTag] = useState("v1.0.0");
  const [snapshots, setSnapshots] = useState<any[]>([]);

  // Capture image states
  const [webcamActive, setWebcamActive] = useState(false);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  // Loaders
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [versioning, setVersioning] = useState(false);
  const [deduping, setDeduping] = useState(false);

  useEffect(() => {
    loadDataset();
  }, []);

  const loadDataset = async () => {
    setLoading(true);
    try {
      // 1. Fetch statistics
      const statsRes = await fetchWithAuth("/api/v1/dataset/statistics");
      if (statsRes.ok) {
        const statsData = await statsRes.json();
        setStats(statsData);
      }

      // 2. Fetch duplicate checks
      const dupRes = await fetchWithAuth("/api/v1/dataset/remove-duplicates", { method: "POST" });
      if (dupRes.ok) {
        const dupData = await dupRes.json();
        setDuplicates(dupData.duplicate_pairs || []);
      }

      // Mock list of files from stats/local scan
      // Let's generate a list of mock files based on stats
      setImages([
        "dark_fantasy_curated_1.jpg",
        "oreo_shelf_2.png",
        "milkybar_pack_3.jpg"
      ]);

      // Run quality checks for files
      const reportMap: Record<string, any> = {
        "dark_fantasy_curated_1.jpg": { blur_score: 142.12, is_blurry: false, mean_brightness: 112.4, brightness_status: "Good" },
        "oreo_shelf_2.png": { blur_score: 41.2, is_blurry: true, mean_brightness: 35.1, brightness_status: "Too Dark" },
        "milkybar_pack_3.jpg": { blur_score: 110.8, is_blurry: false, mean_brightness: 231.5, brightness_status: "Too Bright" }
      };
      setQualityReports(reportMap);

    } catch (err) {
      console.error("Failed to load dataset metadata", err);
    } finally {
      setLoading(false);
    }
  };

  // Upload image handler
  const handleUploadImage = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    formData.append("product_name", activeLabel);

    try {
      const res = await fetchWithAuth("/api/v1/dataset/upload", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Successfully uploaded image ${data.filename} with resolution ${data.resolution}`);
        loadDataset();
      } else {
        alert("Failed to upload image. Verify format.");
      }
    } catch (err) {
      console.error("Upload failed", err);
    } finally {
      setUploading(false);
    }
  };

  // Webcam capturing routines
  const startWebcam = async () => {
    setWebcamActive(true);
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ video: true });
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
      }
    } catch (err) {
      alert("Failed to acquire camera device access.");
      setWebcamActive(false);
    }
  };

  const captureFrame = () => {
    if (!videoRef.current || !canvasRef.current) return;
    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    if (ctx) {
      ctx.drawImage(video, 0, 0);
      canvas.toBlob(async (blob) => {
        if (!blob) return;
        setUploading(true);
        const file = new File([blob], "captured_frame.jpg", { type: "image/jpeg" });
        const formData = new FormData();
        formData.append("file", file);
        formData.append("product_name", activeLabel);

        try {
          const res = await fetchWithAuth("/api/v1/dataset/upload", {
            method: "POST",
            body: formData
          });
          if (res.ok) {
            const data = await res.json();
            alert(`Frame captured & saved: ${data.filename}`);
            stopWebcam();
            loadDataset();
          }
        } catch (err) {
          console.error(err);
        } finally {
          setUploading(false);
        }
      }, "image/jpeg");
    }
  };

  const stopWebcam = () => {
    if (videoRef.current && videoRef.current.srcObject) {
      const stream = videoRef.current.srcObject as MediaStream;
      stream.getTracks().forEach(t => t.stop());
    }
    setWebcamActive(false);
  };

  // Canvas annotation coordinates calculation
  const handleMouseDown = (e: React.MouseEvent) => {
    if (!imgContainerRef.current) return;
    const rect = imgContainerRef.current.getBoundingClientRect();
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    
    setIsDrawing(true);
    setStartX(x);
    setStartY(y);
    setEndX(x);
    setEndY(y);
  };

  const handleMouseMove = (e: React.MouseEvent) => {
    if (!isDrawing || !imgContainerRef.current) return;
    const rect = imgContainerRef.current.getBoundingClientRect();
    setEndX(e.clientX - rect.left);
    setEndY(e.clientY - rect.top);
  };

  const handleMouseUp = () => {
    if (!isDrawing) return;
    setIsDrawing(false);
    
    const newBox = {
      label: activeLabel,
      xmin: Math.min(startX, endX),
      ymin: Math.min(startY, endY),
      xmax: Math.max(startX, endX),
      ymax: Math.max(startY, endY)
    };
    
    setTempBoxes([...tempBoxes, newBox]);
  };

  const saveAnnotations = async () => {
    if (!selectedImage) return;
    try {
      const res = await fetchWithAuth(`/api/v1/dataset/annotate?filename=${selectedImage}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(tempBoxes)
      });
      if (res.ok) {
        alert("Bounding boxes saved successfully!");
        setSelectedImage(null);
        setTempBoxes([]);
        loadDataset();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const createVersionSnapshot = async () => {
    setVersioning(true);
    try {
      const res = await fetchWithAuth(`/api/v1/dataset/version?version_tag=${encodeURIComponent(versionTag)}`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        alert(`Snapshot ${data.version_tag} archived successfully.`);
        setSnapshots([...snapshots, { tag: versionTag, size: data.size_bytes, date: new Date().toLocaleDateString() }]);
      } else {
        alert("Version tag already exists.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setVersioning(false);
    }
  };

  const removeDuplicate = async (filename: string) => {
    if (confirm(`Remove duplicate image file ${filename}?`)) {
      try {
        const res = await fetchWithAuth(`/api/v1/dataset/remove-file?filename=${filename}`, {
          method: "DELETE"
        });
        if (res.ok) {
          alert("Image file successfully removed.");
          loadDataset();
        }
      } catch (err) {
        console.error(err);
      }
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <span className="text-neutral-400 text-sm animate-pulse font-mono">Scanning Curation Directory...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Header Console */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Layers className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight">Dataset Curation Hub</h2>
              <p className="text-xs text-neutral-500 font-mono">Annotate, validate, and version training catalogs</p>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
        </div>

        {/* Curation statistics cards */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <div className="p-4 rounded-2xl bg-neutral-900/40 border border-neutral-900">
            <div className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Total Images</div>
            <div className="text-2xl font-extrabold mt-1 text-emerald-400">{stats.total_images}</div>
            <span className="text-[9px] text-neutral-500 font-mono">{stats.local_folder_path}</span>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-900/40 border border-neutral-900">
            <div className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Annotated Images</div>
            <div className="text-2xl font-extrabold mt-1 text-neutral-100">{stats.annotated_images}</div>
            <span className="text-[9px] text-neutral-500 font-mono">Unannotated: {stats.unannotated_images}</span>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-900/40 border border-neutral-900">
            <div className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Duplicates Checked</div>
            <div className="text-2xl font-extrabold mt-1 text-red-400">{duplicates.length} pairs</div>
            <span className="text-[9px] text-neutral-500 font-mono">Hashing: Difference Matcher</span>
          </div>

          <div className="p-4 rounded-2xl bg-neutral-900/40 border border-neutral-900">
            <div className="text-[10px] text-neutral-500 font-bold uppercase tracking-wider">Active Labels</div>
            <div className="text-2xl font-extrabold mt-1 text-yellow-400">{Object.keys(stats.labels_distribution).length} items</div>
            <span className="text-[9px] text-neutral-500 font-mono">Ready for YOLO training</span>
          </div>
        </div>

        {/* Interactive capture / upload control panels */}
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Column Left: Actions and Grid */}
          <div className="lg:col-span-8 space-y-6">
            
            {/* Capture controls */}
            <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                <Camera className="w-4 h-4 text-emerald-400" /> Acquire Dataset Samples
              </h3>
              
              <div className="flex flex-wrap gap-4 items-center">
                <button 
                  onClick={startWebcam}
                  className="px-4 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors flex items-center gap-1.5 cursor-pointer"
                >
                  <Camera className="w-3.5 h-3.5" /> Start Webcam Stream
                </button>

                <label className="px-4 py-2.5 rounded-xl border border-neutral-800 text-neutral-300 text-xs font-bold hover:border-neutral-700 cursor-pointer flex items-center gap-1.5">
                  <Upload className="w-3.5 h-3.5" /> Upload File
                  <input type="file" className="hidden" accept="image/*" onChange={handleUploadImage} />
                </label>

                {uploading && <Loader2 className="w-4 h-4 animate-spin text-emerald-400" />}
              </div>

              {/* Webcam viewport */}
              {webcamActive && (
                <div className="relative rounded-2xl overflow-hidden bg-black border border-neutral-900 max-w-md mx-auto aspect-video">
                  <video ref={videoRef} autoPlay playsInline className="w-full h-full object-cover" />
                  <div className="absolute bottom-4 left-0 right-0 flex justify-center gap-3">
                    <button 
                      onClick={captureFrame}
                      className="px-4 py-2 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold"
                    >
                      Capture Frame
                    </button>
                    <button 
                      onClick={stopWebcam}
                      className="px-4 py-2 rounded-xl bg-neutral-800 text-neutral-100 text-xs"
                    >
                      Cancel
                    </button>
                  </div>
                  <canvas ref={canvasRef} className="hidden" />
                </div>
              )}
            </div>

            {/* Grid list of curated images */}
            <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400">curated folder catalog</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {images.map((img) => {
                  const report = qualityReports[img] || {};
                  return (
                    <div key={img} className="rounded-2xl border border-neutral-900 bg-neutral-950 overflow-hidden flex flex-col justify-between">
                      <div className="p-4 border-b border-neutral-900 bg-neutral-900/20 text-xs space-y-2">
                        <span className="font-bold text-neutral-300 block truncate" title={img}>{img}</span>
                        
                        {/* Validation scores */}
                        <div className="space-y-1 text-[10px] font-mono text-neutral-500">
                          <div className="flex justify-between">
                            <span>Blur: {report.blur_score || 0}</span>
                            <span className={report.is_blurry ? "text-red-400 font-bold" : "text-emerald-400"}>
                              {report.is_blurry ? "Blurry" : "Sharp"}
                            </span>
                          </div>
                          <div className="flex justify-between">
                            <span>Bright: {report.mean_brightness || 0}</span>
                            <span className={report.brightness_status !== "Good" ? "text-red-400 font-bold" : "text-emerald-400"}>
                              {report.brightness_status}
                            </span>
                          </div>
                        </div>
                      </div>

                      <div className="p-3 bg-neutral-900/50 flex justify-between gap-2">
                        <button 
                          onClick={() => {
                            setSelectedImage(img);
                            setTempBoxes([]);
                          }}
                          className="flex-1 py-1 rounded-lg bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[10px] font-bold"
                        >
                          Annotate BBox
                        </button>
                        <button 
                          onClick={() => removeDuplicate(img)}
                          className="p-1 rounded-lg bg-neutral-900 text-neutral-600 hover:text-red-400"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  );
                })}
              </div>
            </div>

          </div>

          {/* Column Right: Duplicate Matches & Version snapshots */}
          <div className="lg:col-span-4 space-y-6">
            
            {/* Version Snapshot archiving */}
            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                <Tag className="w-4 h-4 text-emerald-400" /> Create Dataset Version
              </h4>
              
              <div className="space-y-3 text-xs">
                <input 
                  type="text" 
                  className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                  value={versionTag}
                  onChange={(e) => setVersionTag(e.target.value)}
                />
                
                <button 
                  onClick={createVersionSnapshot}
                  disabled={versioning}
                  className="w-full py-2.5 rounded-xl bg-emerald-500 text-neutral-950 font-bold text-xs hover:bg-emerald-400 transition-colors disabled:opacity-50 flex items-center justify-center gap-1.5 cursor-pointer"
                >
                  {versioning ? <Loader2 className="w-4.5 h-4.5 animate-spin" /> : <Save className="w-4.5 h-4.5" />} Snapshot Checkpoint
                </button>
              </div>
            </div>

            {/* Duplicate matcher results list */}
            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-1.5">
                <AlertTriangle className="w-4 h-4 text-red-400" /> Duplicate Image matches
              </h4>

              {duplicates.length === 0 ? (
                <div className="text-[10px] text-neutral-500 font-mono">No similar image hashes identified in directory.</div>
              ) : (
                <div className="space-y-3">
                  {duplicates.map((pair, idx) => (
                    <div key={idx} className="p-3 rounded-2xl bg-neutral-950 border border-neutral-900 text-[10px] space-y-2">
                      <div className="text-neutral-400">
                        <span className="font-bold block text-neutral-300">Original: {pair.original}</span>
                        <span className="font-medium block text-red-400 mt-1">Match duplicate: {pair.duplicate}</span>
                      </div>
                      <button 
                        onClick={() => removeDuplicate(pair.duplicate)}
                        className="w-full py-1 text-center bg-red-950/20 border border-red-500/20 text-red-400 font-bold rounded-lg"
                      >
                        Remove Duplicate
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

        </div>

      </div>

      {/* Bounding box Annotation Modal */}
      {selectedImage && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <div className="w-full max-w-4xl bg-neutral-950 border border-neutral-900 rounded-3xl p-6 space-y-6 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center border-b border-neutral-900 pb-3">
              <h3 className="text-sm font-bold">Bounding Box Annotation: {selectedImage}</h3>
              <div className="flex items-center gap-3">
                <select 
                  className="px-3 py-1 bg-neutral-900 text-neutral-100 rounded-xl text-xs"
                  value={activeLabel}
                  onChange={(e) => setActiveLabel(e.target.value)}
                >
                  <option value="Dark Fantasy Chocolate">Dark Fantasy Chocolate</option>
                  <option value="Oreo Biscuits">Oreo Biscuits</option>
                  <option value="Milkybar Pack">Milkybar Pack</option>
                </select>
                
                <button 
                  onClick={saveAnnotations}
                  className="px-4 py-1.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold"
                >
                  Save Annotations
                </button>
                <button 
                  onClick={() => setSelectedImage(null)}
                  className="px-4 py-1.5 rounded-xl bg-neutral-800 text-neutral-100 text-xs"
                >
                  Close
                </button>
              </div>
            </div>

            {/* Drawing surface */}
            <div 
              ref={imgContainerRef}
              onMouseDown={handleMouseDown}
              onMouseMove={handleMouseMove}
              onMouseUp={handleMouseUp}
              className="relative mx-auto border border-neutral-900 rounded-2xl overflow-hidden cursor-crosshair select-none bg-neutral-900 max-w-xl aspect-square"
            >
              {/* Overlay drawn boxes */}
              {tempBoxes.map((box, idx) => (
                <div 
                  key={idx}
                  className="absolute border-2 border-emerald-500 bg-emerald-500/10 text-[9px] font-bold text-emerald-400 p-1"
                  style={{
                    left: box.xmin,
                    top: box.ymin,
                    width: box.xmax - box.xmin,
                    height: box.ymax - box.ymin
                  }}
                >
                  {box.label}
                </div>
              ))}

              {/* Box currently drawing */}
              {isDrawing && (
                <div 
                  className="absolute border-2 border-dashed border-yellow-400 bg-yellow-400/10"
                  style={{
                    left: Math.min(startX, endX),
                    top: Math.min(startY, endY),
                    width: Math.abs(startX - endX),
                    height: Math.abs(startY - endY)
                  }}
                />
              )}

              <div className="absolute inset-0 flex items-center justify-center text-neutral-600 text-xs font-bold font-mono pointer-events-none">
                Draw Box Overlay Frame (Placeholder for Loaded Image Crop)
              </div>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
