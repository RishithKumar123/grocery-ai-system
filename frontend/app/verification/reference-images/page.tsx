"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  UploadCloud, 
  RotateCw, 
  Loader2, 
  CheckCircle2, 
  Trash2, 
  ImageIcon, 
  Sparkles,
  Plus
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";

interface ReferenceImage {
  id: number;
  image_url: string;
  is_primary: boolean;
  embedding_generated: boolean;
  quality_score: number;
  created_at: string;
}

interface ProductItem {
  id: number;
  name: string;
  sku: string;
  barcode?: string;
  reference_image_count: number;
}

export default function ReferenceImagesManagerPage() {
  const router = useRouter();
  const [loading, setLoading] = useState(true);
  const [products, setProducts] = useState<ProductItem[]>([]);
  const [selectedProductId, setSelectedProductId] = useState<number | null>(null);
  
  // Reference images gallery
  const [refImages, setRefImages] = useState<ReferenceImage[]>([]);
  const [uploading, setUploading] = useState(false);
  const [selectedFiles, setSelectedFiles] = useState<FileList | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState(false);

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
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/products");
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
        if (data.length > 0 && !selectedProductId) {
          setSelectedProductId(data[0].id);
          loadReferenceImages(data[0].id);
        }
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadReferenceImages = async (prodId: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/product-verification/reference-images/${prodId}`);
      if (res.ok) {
        const data = await res.json();
        setRefImages(data.reference_images || []);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleProductSelect = (id: number) => {
    setSelectedProductId(id);
    loadReferenceImages(id);
  };

  const handleBatchUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId || !selectedFiles || selectedFiles.length === 0) return;

    setUploading(true);
    setUploadSuccess(false);

    try {
      const formData = new FormData();
      for (let i = 0; i < selectedFiles.length; i++) {
        formData.append("files", selectedFiles[i]);
      }

      const res = await fetchWithAuth(`/api/v1/product-verification/batch-register-reference-images?product_id=${selectedProductId}`, {
        method: "POST",
        body: formData
      });

      if (res.ok) {
        setUploadSuccess(true);
        setSelectedFiles(null);
        loadReferenceImages(selectedProductId);
        loadProducts();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleDeleteImage = async (imageId: number) => {
    if (!selectedProductId) return;
    try {
      const res = await fetchWithAuth(`/api/v1/product-verification/reference-images/${imageId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        loadReferenceImages(selectedProductId);
        loadProducts();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectedProd = products.find(p => p.id === selectedProductId);

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 py-10 px-4 md:px-12 bg-[radial-gradient(ellipse_60%_50%_at_50%_-10%,rgba(16,185,129,0.08),rgba(255,255,255,0))]">
      <div className="max-w-7xl mx-auto space-y-10">
        
        {/* Header navigation bar */}
        <div className="flex flex-col md:flex-row md:justify-between md:items-center gap-4 border-b border-neutral-900 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <Link href="/verification" className="p-2 rounded-xl bg-neutral-900 border border-neutral-800 text-neutral-400 hover:text-neutral-100 transition-colors">
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <h1 className="text-2xl font-bold tracking-tight text-neutral-50 font-mono">Zero-Retraining Reference Images Manager</h1>
            </div>
            <p className="text-xs text-neutral-500 font-sans">
              Upload 3–10 reference photos per product to generate SigLIP visual embeddings for instant searchability without model retraining.
            </p>
          </div>

          <button 
            onClick={loadProducts}
            className="flex items-center gap-1.5 px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-semibold text-neutral-350 hover:bg-neutral-850 transition-colors cursor-pointer"
          >
            <RotateCw className="w-3.5 h-3.5" /> Refresh Catalog
          </button>
        </div>

        {loading ? (
          <div className="flex flex-col items-center justify-center py-32 space-y-4">
            <Loader2 className="w-10 h-10 text-emerald-400 animate-spin" />
            <p className="text-xs text-neutral-500 font-mono">Loading product reference images...</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            
            {/* Left Col: Product Picker */}
            <div className="space-y-4">
              <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-400">Select Product Catalog Item</h3>
              
              <div className="space-y-2 max-h-[600px] overflow-y-auto pr-1">
                {products.map(p => {
                  const isSelected = p.id === selectedProductId;

                  return (
                    <button
                      key={p.id}
                      onClick={() => handleProductSelect(p.id)}
                      className={`w-full p-4 rounded-2xl border text-left font-mono transition-all cursor-pointer space-y-1 ${
                        isSelected ? 'bg-emerald-950/20 border-emerald-500/40 text-neutral-100' : 'bg-neutral-900/20 border-neutral-900 text-neutral-400 hover:border-neutral-800'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-sans font-bold text-xs text-neutral-200">{p.name}</span>
                        <span className="px-2 py-0.5 rounded bg-neutral-900 text-[8px] text-emerald-400 font-bold">{p.reference_image_count} photos</span>
                      </div>
                      <p className="text-[10px] text-neutral-500">SKU: {p.sku} • Bar: {p.barcode || "N/A"}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Right 2 Cols: Reference Image Uploader & Gallery */}
            <div className="lg:col-span-2 space-y-6">
              
              {/* Batch Uploader Box */}
              <div className="bg-neutral-900/10 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center">
                  <h3 className="text-xs font-mono font-bold uppercase tracking-wider text-neutral-200 flex items-center gap-2">
                    <UploadCloud className="w-4 h-4 text-emerald-400" />
                    Upload Reference Photos (3–10 Recommended)
                  </h3>
                  {selectedProd && <span className="text-xs font-mono font-bold text-emerald-400">{selectedProd.name}</span>}
                </div>

                {uploadSuccess && (
                  <div className="p-3 rounded-xl border border-emerald-500/20 bg-emerald-950/30 text-emerald-400 text-xs font-mono">
                    Reference photos uploaded and visual embeddings generated successfully!
                  </div>
                )}

                <form onSubmit={handleBatchUpload} className="space-y-4">
                  <div className="border-2 border-dashed border-neutral-800 hover:border-emerald-500/40 rounded-2xl p-6 bg-neutral-950/60 text-center space-y-3">
                    <ImageIcon className="w-8 h-8 text-emerald-400 mx-auto" />
                    <p className="text-xs font-mono font-bold text-neutral-300">
                      {selectedFiles && selectedFiles.length > 0 ? `${selectedFiles.length} photos selected` : "Choose 3–10 photos from multiple angles"}
                    </p>
                    <input
                      type="file"
                      multiple
                      accept="image/*"
                      id="batch-img-input"
                      className="hidden"
                      onChange={e => setSelectedFiles(e.target.files)}
                    />
                    <label htmlFor="batch-img-input" className="inline-block px-4 py-2 rounded-xl bg-neutral-900 border border-neutral-800 text-xs font-bold font-mono text-neutral-300 hover:text-emerald-400 cursor-pointer">
                      Browse Multiple Images
                    </label>
                  </div>

                  <button
                    type="submit"
                    disabled={uploading || !selectedFiles || selectedFiles.length === 0}
                    className="w-full flex items-center justify-center gap-2 py-3 rounded-xl bg-emerald-500 hover:bg-emerald-400 text-neutral-950 font-bold font-mono text-xs cursor-pointer transition-colors disabled:opacity-50"
                  >
                    {uploading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    Generate Embeddings & Save Reference Photos
                  </button>
                </form>
              </div>

              {/* Reference Images Gallery */}
              <div className="space-y-4 font-mono">
                <h4 className="text-xs font-bold uppercase tracking-wider text-neutral-400">Current Reference Images ({refImages.length})</h4>

                <div className="grid grid-cols-2 sm:grid-cols-3 gap-4">
                  {refImages.map(img => (
                    <div key={img.id} className="relative group bg-neutral-900/20 border border-neutral-900 p-3 rounded-2xl space-y-2">
                      <div className="h-32 w-full rounded-xl overflow-hidden bg-neutral-950 flex items-center justify-center">
                        <img src={img.image_url} alt="Reference" className="h-full w-full object-cover" />
                      </div>
                      
                      <div className="flex justify-between items-center text-[8px]">
                        <span className={img.embedding_generated ? 'text-emerald-400 font-bold' : 'text-yellow-400'}>
                          {img.embedding_generated ? '✓ Vector Embedded' : 'Pending'}
                        </span>
                        <button
                          onClick={() => handleDeleteImage(img.id)}
                          className="text-neutral-550 hover:text-red-400 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>

            </div>

          </div>
        )}

      </div>
    </div>
  );
}
