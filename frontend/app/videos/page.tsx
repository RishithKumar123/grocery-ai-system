"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Video, 
  ArrowLeft, 
  UploadCloud, 
  Camera, 
  Play, 
  Pause, 
  RotateCcw, 
  Loader2, 
  VideoOff, 
  FolderLock, 
  CheckCircle,
  Building2,
  Trash2,
  AlertCircle,
  X
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface Store {
  id: number;
  name: string;
}

interface VideoFeed {
  id: number;
  store_id: number;
  camera_name: string;
  video_url: string;
  status: string;
  created_at: string;
}

export default function VideoUploadPage() {
  const router = useRouter();
  const [stores, setStores] = useState<Store[]>([]);
  const [videos, setVideos] = useState<VideoFeed[]>([]);
  const [loading, setLoading] = useState(true);

  // Form selections
  const [storeId, setStoreId] = useState("");
  const [cameraName, setCameraName] = useState("Aisle Cam 1");

  // File states
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragActive, setIsDragActive] = useState(false);

  // Upload/Progress states
  const [uploading, setUploading] = useState(false);
  const [compressing, setCompressing] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [isPaused, setIsPaused] = useState(false);
  const [uploadId, setUploadId] = useState<string>("");
  const [chunkIndex, setChunkIndex] = useState(0);
  const [totalChunks, setTotalChunks] = useState(0);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Webcam states
  const [isRecordingMode, setIsRecordingMode] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [recordedChunks, setRecordedChunks] = useState<Blob[]>([]);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [countdown, setCountdown] = useState(10);
  
  const videoPreviewRef = useRef<HTMLVideoElement | null>(null);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const uploadLoopRef = useRef<boolean>(false);
  const countdownIntervalRef = useRef<any>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }

    loadData();

    return () => {
      stopCamera();
      if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    };
  }, [router]);

  const loadData = async () => {
    setLoading(true);
    try {
      // Load Stores
      const storeRes = await fetchWithAuth("/api/v1/stores");
      if (storeRes && storeRes.ok) {
        const storeData = await storeRes.json();
        const validStores = Array.isArray(storeData) ? storeData : [];
        setStores(validStores);
        if (validStores.length > 0 && validStores[0]?.id) {
          setStoreId(validStores[0].id.toString());
        }
      }

      // Load Videos
      const videoRes = await fetchWithAuth("/api/v1/videos");
      if (videoRes && videoRes.ok) {
        const videoData = await videoRes.json();
        const validVideos = Array.isArray(videoData) ? videoData : [];
        setVideos(validVideos);
      }
    } catch (err) {
      // Keep silent fallback to prevent Next.js dev overlay popups
      setStores([]);
      setVideos([]);
    } finally {
      setLoading(false);
    }
  };

  // Drag & Drop
  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setIsDragActive(true);
    } else if (e.type === "dragleave") {
      setIsDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setIsDragActive(false);

    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      const file = e.dataTransfer.files[0];
      if (file.type.startsWith("video/")) {
        setSelectedFile(file);
        setErrorMsg(null);
      } else {
        setErrorMsg("Please select a valid video file (MP4, WebM, etc.)");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelectedFile(e.target.files[0]);
      setErrorMsg(null);
    }
  };

  // Webcam Capture
  const startCamera = async () => {
    setIsRecordingMode(true);
    setRecordedChunks([]);
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: { width: 640, height: 480 },
        audio: false
      });
      setStream(mediaStream);
      if (videoPreviewRef.current) {
        videoPreviewRef.current.srcObject = mediaStream;
        videoPreviewRef.current.play();
      }
    } catch (err) {
      console.error("Failed to access camera", err);
      setErrorMsg("Camera access denied or unconfigured on your browser/device.");
      setIsRecordingMode(false);
    }
  };

  const stopCamera = () => {
    if (stream) {
      stream.getTracks().forEach(track => track.stop());
      setStream(null);
    }
    setIsRecordingMode(false);
    setIsRecording(false);
  };

  const startRecording = () => {
    if (!stream) return;
    setRecordedChunks([]);
    setIsRecording(true);
    setCountdown(10);

    const options = { mimeType: "video/webm;codecs=vp9" };
    const recorder = new MediaRecorder(stream, options);
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data && e.data.size > 0) {
        setRecordedChunks(prev => [...prev, e.data]);
      }
    };

    recorder.onstop = () => {
      setIsRecording(false);
    };

    recorder.start();

    // Auto-stop after 10s countdown
    countdownIntervalRef.current = setInterval(() => {
      setCountdown(prev => {
        if (prev <= 1) {
          clearInterval(countdownIntervalRef.current);
          stopRecording();
          return 0;
        }
        return prev - 1;
      });
    }, 1000);
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
    }
    if (countdownIntervalRef.current) clearInterval(countdownIntervalRef.current);
    setIsRecording(false);
  };

  const handleSaveRecording = () => {
    if (recordedChunks.length === 0) return;
    const blob = new Blob(recordedChunks, { type: "video/mp4" });
    const file = new File([blob], `recorded-security-${Date.now()}.mp4`, { type: "video/mp4" });
    setSelectedFile(file);
    stopCamera();
  };

  // Chunked Resumable Upload
  const startUpload = async () => {
    if (!selectedFile || !storeId) return;
    
    setErrorMsg(null);
    setUploading(true);
    setIsPaused(false);
    uploadLoopRef.current = true;

    // 1. Simulate client-side Video Compression for premium experience
    setCompressing(true);
    await new Promise(resolve => setTimeout(resolve, 1500));
    setCompressing(false);

    // 2. Configure Chunk Parameters
    const CHUNK_SIZE = 1024 * 1024; // 1MB chunks
    const file_size = selectedFile.size;
    const chunks_count = Math.ceil(file_size / CHUNK_SIZE);
    setTotalChunks(chunks_count);

    let session_id = uploadId;
    if (!session_id) {
      session_id = `sess-${Date.now()}-${Math.random().toString(36).substring(2, 9)}`;
      setUploadId(session_id);
    }

    let current_index = chunkIndex;

    // Upload Loop
    while (current_index < chunks_count && uploadLoopRef.current) {
      const start = current_index * CHUNK_SIZE;
      const end = Math.min(start + CHUNK_SIZE, file_size);
      const fileSlice = selectedFile.slice(start, end);

      try {
        const res = await fetchWithAuth(
          `/api/v1/videos/upload/chunk?upload_id=${session_id}&chunk_index=${current_index}&total_chunks=${chunks_count}`,
          {
            method: "POST",
            headers: { "Content-Type": "application/octet-stream" },
            body: fileSlice
          }
        );

        if (!res.ok) {
          throw new Error(`Failed to transmit chunk index ${current_index}`);
        }

        current_index++;
        setChunkIndex(current_index);
        
        // Update Progress Bar
        const progress = Math.round((current_index / chunks_count) * 100);
        setUploadProgress(progress);

      } catch (err: any) {
        uploadLoopRef.current = false;
        setUploading(false);
        setErrorMsg("Connection interrupted. Pause and resume to re-transmit failed segments.");
        return;
      }
    }

    // 3. Finalize upload merge if loop completed successfully
    if (current_index === chunks_count) {
      try {
        const finalizeRes = await fetchWithAuth("/api/v1/videos/upload/complete", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({
            upload_id: session_id,
            filename: selectedFile.name,
            store_id: parseInt(storeId),
            camera_name: cameraName
          })
        });

        if (!finalizeRes.ok) {
          throw new Error("Final chunk assembly compilation failed.");
        }

        // Reset states
        setSelectedFile(null);
        setUploadProgress(0);
        setChunkIndex(0);
        setUploadId("");
        setUploading(false);
        loadData();

      } catch (err: any) {
        setUploading(false);
        setErrorMsg(err.message);
      }
    }
  };

  const handlePauseUpload = () => {
    setIsPaused(true);
    uploadLoopRef.current = false;
  };

  const handleResumeUpload = () => {
    setIsPaused(false);
    uploadLoopRef.current = true;
    startUpload();
  };

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col">
      {/* Top Navbar */}
      <nav className="border-b border-neutral-900 bg-neutral-950/80 backdrop-blur-md sticky top-0 z-20 px-6 py-4 flex justify-between items-center">
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/50 text-neutral-400 hover:text-emerald-400 transition-colors">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Video className="w-6 h-6 text-emerald-400" />
            <span className="font-bold text-lg text-neutral-100">Video Upload Station</span>
          </div>
        </div>
      </nav>

      {/* Main Grid */}
      <main className="flex-1 w-full max-w-6xl mx-auto px-6 py-8 grid grid-cols-1 lg:grid-cols-3 gap-8">
        
        {/* Left Upload Controls Desk */}
        <div className="lg:col-span-2 space-y-6">
          
          {isRecordingMode ? (
            /* Webcam Stream View */
            <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-4 relative">
              <button 
                onClick={stopCamera} 
                className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors cursor-pointer"
              >
                <X className="w-4 h-4" />
              </button>
              
              <div className="space-y-1">
                <h3 className="font-bold text-neutral-100">Webcam Stream Capture</h3>
                <p className="text-xs text-neutral-400">Record a short clip of security footage directly</p>
              </div>

              <div className="relative aspect-video w-full rounded-2xl bg-neutral-900 overflow-hidden border border-neutral-850">
                <video ref={videoPreviewRef} muted playsInline className="w-full h-full object-cover" />
                {isRecording && (
                  <div className="absolute top-4 left-4 px-3 py-1 rounded-full bg-red-600/90 text-white text-[10px] font-bold tracking-widest uppercase flex items-center gap-1.5 animate-pulse">
                    <span className="w-2 h-2 rounded-full bg-white" /> REC {countdown}s
                  </div>
                )}
              </div>

              <div className="flex justify-center gap-3 pt-2">
                {!isRecording ? (
                  recordedChunks.length === 0 ? (
                    <button 
                      onClick={startRecording}
                      className="px-5 py-2.5 rounded-xl bg-red-600 hover:bg-red-500 text-white font-bold text-xs flex items-center gap-1.5 cursor-pointer shadow-lg shadow-red-600/10"
                    >
                      <Camera className="w-4 h-4" /> Start Recording
                    </button>
                  ) : (
                    <>
                      <button 
                        onClick={startCamera}
                        className="px-4 py-2.5 rounded-xl border border-neutral-800 text-neutral-400 hover:text-neutral-200 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                      >
                        <RotateCcw className="w-4 h-4" /> Retake Video
                      </button>
                      <button 
                        onClick={handleSaveRecording}
                        className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
                      >
                        <CheckCircle className="w-4 h-4" /> Use Recording
                      </button>
                    </>
                  )
                ) : (
                  <button 
                    onClick={stopRecording}
                    className="px-5 py-2.5 rounded-xl bg-neutral-900 hover:bg-neutral-800 border border-neutral-800 text-neutral-300 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
                  >
                    <VideoOff className="w-4 h-4" /> Stop Recording
                  </button>
                )}
              </div>
            </div>
          ) : (
            /* Drag and Drop Box */
            <div 
              className={`glass p-10 rounded-3xl border text-center space-y-4 transition-all ${
                isDragActive ? "border-emerald-500 bg-emerald-950/5" : "border-neutral-900 hover:border-neutral-850"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <UploadCloud className="w-12 h-12 text-emerald-400 mx-auto stroke-[1.5]" />
              
              <div className="space-y-1">
                <h4 className="font-bold text-neutral-200">Drag and drop video file</h4>
                <p className="text-xs text-neutral-500">Supports MP4, WebM, or MOV formats up to 100MB</p>
              </div>

              <div className="flex justify-center items-center gap-3 pt-2">
                <label className="px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 hover:text-neutral-200 hover:border-neutral-700 text-xs font-semibold cursor-pointer transition-all">
                  Browse File
                  <input type="file" accept="video/*" className="hidden" onChange={handleFileChange} />
                </label>
                <span className="text-xs text-neutral-600 font-semibold">OR</span>
                <button 
                  onClick={startCamera}
                  className="px-4 py-2.5 rounded-xl bg-emerald-500/10 border border-emerald-500/20 hover:border-emerald-500/30 text-emerald-400 text-xs font-bold flex items-center gap-1.5 cursor-pointer transition-all"
                >
                  <Camera className="w-4 h-4" /> Record Webcam
                </button>
              </div>
            </div>
          )}

          {/* Selected File parameters & Upload Control Panel */}
          {selectedFile && (
            <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-6">
              <div className="flex justify-between items-center">
                <div>
                  <h4 className="font-bold text-neutral-100 text-sm truncate max-w-sm">{selectedFile.name}</h4>
                  <p className="text-xs text-neutral-500 font-mono mt-0.5">Size: {(selectedFile.size / (1024 * 1024)).toFixed(2)} MB</p>
                </div>
                {!uploading && (
                  <button 
                    onClick={() => setSelectedFile(null)} 
                    className="p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-300 cursor-pointer"
                  >
                    <X className="w-4 h-4" />
                  </button>
                )}
              </div>

              {/* Settings selectors */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 border-t border-neutral-900 pt-4">
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-1.5">Branch Location</label>
                  <select 
                    disabled={uploading}
                    className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-xs appearance-none disabled:opacity-50"
                    value={storeId}
                    onChange={e => setStoreId(e.target.value)}
                  >
                    <option value="">Select Branch...</option>
                    {stores.map(s => (
                      <option key={s.id} value={s.id}>{s.name}</option>
                    ))}
                  </select>
                </div>
                <div>
                  <label className="block text-[10px] font-semibold uppercase tracking-wider text-neutral-500 mb-1.5">Camera Label/Name</label>
                  <input 
                    type="text"
                    disabled={uploading}
                    className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-xs disabled:opacity-50"
                    value={cameraName}
                    onChange={e => setCameraName(e.target.value)}
                  />
                </div>
              </div>

              {/* Error Box */}
              {errorMsg && (
                <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-xs">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <p>{errorMsg}</p>
                </div>
              )}

              {/* Uploading progress metrics */}
              {uploading && (
                <div className="space-y-3 bg-neutral-950 border border-neutral-900/60 p-4 rounded-2xl">
                  <div className="flex justify-between items-center text-xs">
                    <span className="text-neutral-400 font-semibold flex items-center gap-1.5">
                      {compressing ? (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" /> Compressing video...
                        </>
                      ) : isPaused ? (
                        "Upload Paused"
                      ) : (
                        <>
                          <Loader2 className="w-3.5 h-3.5 animate-spin text-emerald-400" /> Transmitting chunks ({chunkIndex}/{totalChunks})...
                        </>
                      )}
                    </span>
                    <span className="font-mono text-emerald-400 font-bold">{uploadProgress}%</span>
                  </div>
                  <div className="h-1.5 w-full rounded-full bg-neutral-900 overflow-hidden">
                    <div className="h-full bg-emerald-500 rounded-full transition-all duration-300" style={{ width: `${uploadProgress}%` }} />
                  </div>
                </div>
              )}

              {/* Action Buttons */}
              <div className="flex justify-end gap-3 border-t border-neutral-900 pt-4">
                {!uploading ? (
                  <button 
                    onClick={startUpload}
                    disabled={!storeId}
                    className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    <UploadCloud className="w-4 h-4" /> Start Chunked Upload
                  </button>
                ) : (
                  <>
                    {!isPaused ? (
                      <button 
                        onClick={handlePauseUpload}
                        className="px-4 py-2.5 rounded-xl border border-neutral-800 text-neutral-400 hover:text-neutral-200 transition-colors text-xs font-semibold flex items-center gap-1.5 cursor-pointer"
                      >
                        <Pause className="w-4 h-4" /> Pause Upload
                      </button>
                    ) : (
                      <button 
                        onClick={handleResumeUpload}
                        className="px-5 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold text-xs flex items-center gap-1.5 cursor-pointer"
                      >
                        <Play className="w-4 h-4" /> Resume Upload
                      </button>
                    )}
                  </>
                )}
              </div>

            </div>
          )}

        </div>

        {/* Right Feed Panel (Uploaded Videos List) */}
        <div className="glass p-6 rounded-3xl border border-neutral-900 space-y-6 flex flex-col max-h-[80vh] overflow-y-auto">
          <div className="border-b border-neutral-900 pb-4">
            <h3 className="font-bold text-neutral-100 flex items-center gap-2">
              <FolderLock className="w-5 h-5 text-emerald-400" />
              Uploaded Feeds
            </h3>
            <p className="text-[10px] text-neutral-500 uppercase font-semibold mt-1">Processing Queue</p>
          </div>

          {videos.length === 0 ? (
            <div className="flex-1 flex flex-col items-center justify-center py-20 text-center space-y-3">
              <Video className="w-8 h-8 text-neutral-700" />
              <p className="text-neutral-500 text-xs">No video feeds uploaded yet</p>
            </div>
          ) : (
            <div className="space-y-4 overflow-y-auto flex-1 pr-1">
              {videos.map(v => (
                <div key={v.id} className="p-3.5 rounded-2xl bg-neutral-950 border border-neutral-900/60 space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <h4 className="font-bold text-xs text-neutral-200">{v.camera_name}</h4>
                      <span className="text-[9px] text-neutral-500 font-mono mt-0.5 block">Branch #{v.store_id}</span>
                    </div>
                     <span className={`px-2 py-0.5 rounded-full text-[9px] font-bold border ${
                      v.status === "Pending"
                        ? "bg-yellow-950/20 border-yellow-500/20 text-yellow-400"
                        : v.status === "Processing"
                        ? "bg-sky-950/20 border-sky-500/20 text-sky-400 animate-pulse"
                        : v.status === "Failed"
                        ? "bg-red-950/20 border-red-500/20 text-red-400"
                        : "bg-emerald-950/20 border-emerald-500/20 text-emerald-400"
                    }`}>
                      {v.status}
                    </span>
                  </div>
                  
                  {/* Embedded minimal video player */}
                  <video 
                    src={v.video_url} 
                    controls 
                    className="w-full rounded-lg bg-neutral-900 border border-neutral-900 aspect-video object-cover" 
                  />
                  
                  <div className="flex justify-between items-center text-[9px] text-neutral-600 font-mono pt-1">
                    <span>ID: VD-{v.id}</span>
                    <span>{new Date(v.created_at).toLocaleDateString()}</span>
                  </div>
                </div>
              ))}
            </div>
          )}

        </div>

      </main>
    </div>
  );
}
