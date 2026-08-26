"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Search, 
  CheckCircle2, 
  XCircle, 
  Camera, 
  UploadCloud, 
  RotateCw, 
  Loader2, 
  ShieldCheck, 
  PackageCheck, 
  Layers, 
  Image as ImageIcon,
  Sparkles,
  Barcode,
  Check,
  Plus
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";

interface ProductCatalogItem {
  id: number;
  name: string;
  brand?: string;
  sku: string;
  barcode?: string;
  image_url?: string;
  reference_image_count: number;
  has_embeddings: boolean;
}

interface BoundingBox {
  xmin: number;
  ymin: number;
  xmax: number;
  ymax: number;
}

interface VerificationResult {
  present: boolean;
  confidence: number;
  quantity: number;
  bounding_boxes: number[][];
  barcode_matched: boolean;
  ocr_matched: boolean;
  embedding_similarity: number;
  detection_time_ms: number;
  explanation: string;
  product_id: number;
  product_name: string;
}

export default function PresenceVerificationPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  
  // Catalog search
  const [searchQuery, setSearchQuery] = useState("Patanjali");
  const [catalogItems, setCatalogItems] = useState<ProductCatalogItem[]>([]);
  const [selectedProduct, setSelectedProduct] = useState<ProductCatalogItem | null>(null);

  // Verification Input & State
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string | null>(null);
  const [verifying, setVerifying] = useState(false);
  const [result, setResult] = useState<VerificationResult | null>(null);
  
  // Inventory update status
  const [updatingStock, setUpdatingStock] = useState(false);
  const [stockSuccess, setStockSuccess] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      setLoading(false);
      router.push("/login");
      return;
    }
    loadCatalog("Patanjali");
  }, [router]);

  const loadCatalog = async (qTerm: string) => {
    setLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/verification/products/search?query=${encodeURIComponent(qTerm)}&limit=10`);
      if (res.ok) {
        const data = await res.json();
        setCatalogItems(data.results || []);
        if (data.results && data.results.length > 0 && !selectedProduct) {
          setSelectedProduct(data.results[0]);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleFileChange = (file: File) => {
    setSelectedFile(file);
    const reader = new FileReader();
    reader.onloadend = () => {
      setImagePreview(reader.result as string);
    };
    reader.readAsDataURL(file);
  };

  const handleVerifyPresence = async () => {
    if (!selectedProduct || !selectedFile) return;

    setVerifying(true);
    setResult(null);
    setStockSuccess(false);

    try {
      const formData = new FormData();
      formData.append("file", selectedFile);

      const res = await fetchWithAuth(`/api/v1/verification/verify-product?product_id=${selectedProduct.id}&confidence_threshold=0.5`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setResult(await res.json());
      }
    } catch (err) {
      console.error("Verification error", err);
    } finally {
      setVerifying(false);
    }
  };

  const handleUpdateStock = async () => {
    if (!selectedProduct || !result || !result.present) return;
    
    setUpdatingStock(true);
    setStockSuccess(false);
    try {
      // Apply quantity update and record audit entry
      const res = await fetchWithAuth(`/api/v1/verification/inventory/update`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: 1,
          product_id: selectedProduct.id,
          quantity: result.quantity
        })
      });

      if (res.ok) {
        setStockSuccess(true);
      }
    } catch (err) {
      console.error("Stock update error", err);
    } finally {
      setUpdatingStock(false);
    }
  };

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/dashboard" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Product Presence Verification Scanner</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Zero-Retraining AI system verifying if a specific target product is physically present in the camera scan.
            </p>
          </div>

          <Link
            href="/verification/reference-images"
            className="flex items-center gap-2 px-4 py-2 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-xs font-bold font-mono hover:bg-emerald-500/20 transition-all cursor-pointer"
          >
            <ImageIcon className="w-4 h-4" /> Reference Images & Embeddings
          </Link>
        </div>

        {/* STEP 1: TARGET PRODUCT SEARCH & SELECTION */}
        <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
          <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
            <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
              <PackageCheck className="w-4 h-4 text-emerald-400" />
              Step 1: Select Target Product
            </h3>
            <span className="text-[10px] font-mono text-neutral-500">Search 100,000+ catalog items</span>
          </div>

          <div className="flex flex-col md:flex-row gap-3">
            <div className="relative flex-1">
              <input
                type="text"
                placeholder="Search catalog by name (e.g., Patanjali Honey, Tata Salt, Maggi)..."
                className="w-full pl-10 pr-4 py-2.5 rounded-xl bg-neutral-950 border border-neutral-800 text-neutral-100 font-mono text-xs focus:outline-none"
                value={searchQuery}
                onChange={e => {
                  setSearchQuery(e.target.value);
                  loadCatalog(e.target.value);
                }}
              />
              <Search className="absolute left-3.5 top-3 w-4 h-4 text-neutral-500" />
            </div>
          </div>

          {/* Catalog Selection Cards */}
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-4 gap-4">
            {catalogItems.map(item => {
              const isSelected = selectedProduct?.id === item.id;

              return (
                <button
                  key={item.id}
                  onClick={() => setSelectedProduct(item)}
                  className={`p-4 rounded-2xl border text-left font-mono transition-all cursor-pointer space-y-2 ${
                    isSelected ? 'bg-emerald-950/20 border-emerald-500/40 text-neutral-100' : 'bg-neutral-950/40 border-neutral-900 text-neutral-400 hover:border-neutral-800'
                  }`}
                >
                  <div className="flex justify-between items-start">
                    <span className="text-[9px] font-bold uppercase text-neutral-550">ID #{item.id}</span>
                    {isSelected && <CheckCircle2 className="w-4 h-4 text-emerald-400" />}
                  </div>
                  <h4 className="font-sans font-bold text-xs line-clamp-1">{item.name}</h4>
                  <div className="text-[9px] space-y-0.5 text-neutral-500">
                    <p>SKU: {item.sku}</p>
                    <p>Bar: {item.barcode || "N/A"}</p>
                  </div>
                  <div className="pt-1 flex items-center justify-between text-[8px]">
                    <span className={item.has_embeddings ? 'text-emerald-400 font-bold' : 'text-yellow-400'}>
                      {item.has_embeddings ? '✓ Embeddings Ready' : '⚠ No Embeddings'}
                    </span>
                    <span>{item.reference_image_count} photos</span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* STEP 2 & 3: SCANNER FEED & REAL-TIME VERIFICATION OUTCOME */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          
          {/* Left 2 Cols: Camera Feed / Image Uploader */}
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <div className="flex justify-between items-center">
                <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400 flex items-center gap-2">
                  <Camera className="w-4 h-4 text-emerald-400" />
                  Step 2: Live Camera / Image Scan Input
                </h3>
                {selectedProduct && (
                  <span className="px-3 py-1 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-mono text-emerald-400 font-bold">
                    Target: {selectedProduct.name}
                  </span>
                )}
              </div>

              {/* Upload Drop Zone */}
              <div className="border-2 border-dashed border-neutral-800 hover:border-emerald-500/40 rounded-2xl p-8 bg-neutral-950/60 transition-colors text-center space-y-4">
                {imagePreview ? (
                  <div className="relative max-h-72 w-full flex items-center justify-center overflow-hidden rounded-xl bg-neutral-950">
                    <img src={imagePreview} alt="Scan preview" className="max-h-72 object-contain rounded-xl" />
                  </div>
                ) : (
                  <div className="space-y-2 py-4">
                    <UploadCloud className="w-10 h-10 text-emerald-400 mx-auto" />
                    <p className="text-xs font-mono font-bold text-neutral-300">Upload or capture products scan image</p>
                    <p className="text-[10px] font-mono text-neutral-500">Camera frame image containing incoming inventory products</p>
                  </div>
                )}

                <input
                  type="file"
                  accept="image/*"
                  id="presence-file-input"
                  className="hidden"
                  onChange={e => e.target.files && handleFileChange(e.target.files[0])}
                />
                <div className="flex justify-center gap-3">
                  <label htmlFor="presence-file-input" className="px-4 py-2.5 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold font-mono text-neutral-300 hover:text-emerald-400 cursor-pointer">
                    {imagePreview ? "Change Image" : "Browse Image File"}
                  </label>

                  <button
                    onClick={handleVerifyPresence}
                    disabled={verifying || !selectedProduct || !selectedFile}
                    className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-all disabled:opacity-50 flex items-center gap-2"
                  >
                    {verifying ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    Search ONLY for Target Product
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Right Col: Instant Verification Outcome Display (YES / NO) */}
          <div className="space-y-6">
            {result ? (
              result.present ? (
                /* YES OUTCOME CARD */
                <div className="bg-emerald-950/20 border-2 border-emerald-500/30 p-6 rounded-3xl space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-emerald-500 flex items-center justify-center text-neutral-950">
                      <CheckCircle2 className="w-7 h-7 stroke-[2.5]" />
                    </div>
                    <div>
                      <span className="text-lg font-bold font-mono text-emerald-400 uppercase tracking-wide">✓ YES - PRODUCT PRESENT</span>
                      <p className="text-[10px] text-neutral-400 font-sans mt-0.5">Target product identified with verified confidence.</p>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 font-mono text-xs pt-4 border-t border-emerald-500/20">
                    <div className="p-3 bg-neutral-950/60 border border-neutral-900 rounded-xl space-y-1">
                      <span className="block text-[8px] text-neutral-500 font-bold uppercase">Confidence</span>
                      <span className="block text-lg font-bold text-emerald-400">{Math.round(result.confidence * 100)}%</span>
                    </div>

                    <div className="p-3 bg-neutral-950/60 border border-neutral-900 rounded-xl space-y-1">
                      <span className="block text-[8px] text-neutral-500 font-bold uppercase">Quantity Detected</span>
                      <span className="block text-lg font-bold text-neutral-100">{result.quantity} pcs</span>
                    </div>
                  </div>

                  {/* Signals Badges */}
                  <div className="space-y-2 font-mono text-[10px]">
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">Verification Signals</span>
                    <div className="space-y-1 text-neutral-300">
                      <div className="flex justify-between p-2 bg-neutral-950/40 rounded-lg">
                        <span className="text-neutral-500">Barcode Matched:</span>
                        <span className={result.barcode_matched ? 'text-emerald-400 font-bold' : 'text-neutral-500'}>{result.barcode_matched ? '✓ YES (Exact)' : '✗ No'}</span>
                      </div>
                      <div className="flex justify-between p-2 bg-neutral-950/40 rounded-lg">
                        <span className="text-neutral-500">OCR Text Match:</span>
                        <span className={result.ocr_matched ? 'text-emerald-400 font-bold' : 'text-neutral-500'}>{result.ocr_matched ? '✓ YES (Text)' : '✗ No'}</span>
                      </div>
                      <div className="flex justify-between p-2 bg-neutral-950/40 rounded-lg">
                        <span className="text-neutral-500">Visual Embedding Sim:</span>
                        <span className="text-emerald-400 font-bold">{Math.round(result.embedding_similarity * 100)}%</span>
                      </div>
                      <div className="flex justify-between p-2 bg-neutral-950/40 rounded-lg">
                        <span className="text-neutral-500">Detection Latency:</span>
                        <span>{result.detection_time_ms} ms</span>
                      </div>
                    </div>
                  </div>

                  {/* One Click Inventory Update */}
                  <div className="pt-4 border-t border-emerald-500/20 space-y-3">
                    {stockSuccess && (
                      <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-950/40 text-emerald-400 text-[10px] font-mono">
                        Inventory stock updated to {result.quantity} pcs!
                      </div>
                    )}

                    <button
                      onClick={handleUpdateStock}
                      disabled={updatingStock}
                      className="w-full py-3 rounded-2xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-all flex items-center justify-center gap-2"
                    >
                      {updatingStock ? <Loader2 className="w-4 h-4 animate-spin" /> : <PackageCheck className="w-4 h-4" />}
                      One-Click Update Stock Inventory
                    </button>
                  </div>
                </div>
              ) : (
                /* NO OUTCOME CARD */
                <div className="bg-red-950/20 border-2 border-red-500/30 p-6 rounded-3xl space-y-6">
                  <div className="flex items-center gap-3">
                    <div className="w-12 h-12 rounded-2xl bg-red-500 flex items-center justify-center text-neutral-950">
                      <XCircle className="w-7 h-7 stroke-[2.5]" />
                    </div>
                    <div>
                      <span className="text-lg font-bold font-mono text-red-400 uppercase tracking-wide">✗ NO - PRODUCT ABSENT</span>
                      <p className="text-[10px] text-neutral-400 font-sans mt-0.5">Target product was not detected in camera scan.</p>
                    </div>
                  </div>

                  <div className="p-4 bg-neutral-950/60 border border-neutral-900 rounded-2xl space-y-2 font-mono text-xs">
                    <span className="text-[9px] text-neutral-500 font-bold uppercase tracking-wider block">Explanation</span>
                    <p className="text-neutral-300 text-[11px] leading-relaxed">{result.explanation}</p>
                  </div>
                </div>
              )
            ) : (
              <div className="bg-neutral-900/10 border border-neutral-900 p-8 rounded-3xl text-center space-y-3 font-mono text-xs text-neutral-550">
                <ShieldCheck className="w-10 h-10 text-neutral-800 mx-auto" />
                <p>Select target product and upload scan image to run instant presence verification.</p>
              </div>
            )}
          </div>

        </div>

      </div>
    </div>
  );
}
