"use client";

import React, { useState, useEffect, useRef } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Package, 
  Search, 
  Plus, 
  Trash2, 
  Edit3, 
  QrCode, 
  ArrowLeft,
  Loader2, 
  Save, 
  X,
  FileText,
  DollarSign,
  Boxes,
  Activity,
  AlertCircle,
  Download,
  Upload,
  Layers,
  Settings,
  Eye,
  CheckSquare,
  Square
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useToast } from "../../components/ui/toast";

interface Product {
  id: number;
  name: string;
  barcode: string;
  sku: string;
  category: string;
  brand: string | null;
  variant: string | null;
  weight: string | null;
  price: number;
  image_url: string | null;
  description: string | null;
  supplier_id: number | null;
  supplier_name: string | null;
  total_stock: number;
  created_at: string;
  updated_at: string;

  // Extended Specifications
  qr_code: string | null;
  unit: string | null;
  dimensions: string | null;
  cost_price: number;
  tax: number;
  shelf_life: number | null;
  expiry_tracking: boolean;
  status: string;
  images: string | null;

  // AI Metadata
  yolo_class_mapping: number | null;
  clip_embeddings: string | null;
  ocr_reference_text: string | null;
  confidence_threshold: number;
  aliases: string | null;
}

interface Supplier {
  id: number;
  name: string;
}

export default function ProductsPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  const [products, setProducts] = useState<Product[]>([]);
  const [suppliers, setSuppliers] = useState<Supplier[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Advanced search and filters state
  const [search, setSearch] = useState("");
  const [categoryFilter, setCategoryFilter] = useState("");
  const [brandFilter, setBrandFilter] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [supplierFilter, setSupplierFilter] = useState("");

  // Bulk actions selection
  const [selectedProductIds, setSelectedProductIds] = useState<number[]>([]);

  // Modals state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [isCodeOpen, setIsCodeOpen] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);

  // Form Tab selection ("general" | "specs" | "ai")
  const [formTab, setFormTab] = useState<"general" | "specs" | "ai">("general");

  // Form Fields State
  const [name, setName] = useState("");
  const [barcode, setBarcode] = useState("");
  const [sku, setSku] = useState("");
  const [category, setCategory] = useState("Groceries");
  const [brand, setBrand] = useState("");
  const [variant, setVariant] = useState("");
  const [weight, setWeight] = useState("");
  const [price, setPrice] = useState("0.00");
  const [supplierId, setSupplierId] = useState("");
  const [initialStock, setInitialStock] = useState("0");
  const [storeId, setStoreId] = useState("1");
  const [description, setDescription] = useState("");

  // Extended Specifications
  const [qrCode, setQrCode] = useState("");
  const [unit, setUnit] = useState("pcs");
  const [dimensions, setDimensions] = useState("");
  const [costPrice, setCostPrice] = useState("0.00");
  const [tax, setTax] = useState("0.00");
  const [shelfLife, setShelfLife] = useState("");
  const [expiryTracking, setExpiryTracking] = useState(false);
  const [statusField, setStatusField] = useState("active");

  // AI Metadata parameters
  const [yoloClass, setYoloClass] = useState("");
  const [clipEmbeddings, setClipEmbeddings] = useState("");
  const [ocrText, setOcrText] = useState("");
  const [confidence, setConfidence] = useState(0.5);
  const [aliases, setAliases] = useState("");

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);
  const [importing, setImporting] = useState(false);
  
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadData();
  }, [router, categoryFilter, brandFilter, statusFilter, supplierFilter]);

  const loadData = async () => {
    setLoading(true);
    try {
      let url = "/api/v1/products?";
      if (search) url += `search=${encodeURIComponent(search)}&`;
      if (categoryFilter) url += `category=${encodeURIComponent(categoryFilter)}&`;
      if (brandFilter) url += `brand=${encodeURIComponent(brandFilter)}&`;
      if (statusFilter) url += `status_filter=${encodeURIComponent(statusFilter)}&`;
      if (supplierFilter) url += `supplier_id=${encodeURIComponent(supplierFilter)}&`;

      const res = await fetchWithAuth(url);
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      }

      // Load Suppliers
      const supRes = await fetchWithAuth("/api/v1/suppliers");
      if (supRes.ok) {
        const supData = await supRes.json();
        setSuppliers(supData);
      }
    } catch (err) {
      console.error("Failed to load products", err);
    } finally {
      setLoading(false);
    }
  };

  const handleSearchKeyPress = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (e.key === "Enter") {
      loadData();
    }
  };

  // Add Product Submit
  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFormLoading(true);

    try {
      const payload = {
        name,
        barcode,
        sku,
        category,
        brand: brand || null,
        variant: variant || null,
        weight: weight || null,
        price: parseFloat(price) || 0.0,
        supplier_id: supplierId ? parseInt(supplierId) : null,
        initial_stock: parseInt(initialStock) || 0,
        store_id: storeId ? parseInt(storeId) : null,
        description: description || null,

        // Extended Specifications
        qr_code: qrCode || null,
        unit: unit || null,
        dimensions: dimensions || null,
        cost_price: parseFloat(costPrice) || 0.0,
        tax: parseFloat(tax) || 0.0,
        shelf_life: shelfLife ? parseInt(shelfLife) : null,
        expiry_tracking: expiryTracking,
        status: statusField,

        // AI Metadata
        yolo_class_mapping: yoloClass ? parseInt(yoloClass) : null,
        clip_embeddings: clipEmbeddings || null,
        ocr_reference_text: ocrText || null,
        confidence_threshold: confidence,
        aliases: aliases || null
      };

      const res = await fetchWithAuth("/api/v1/products", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || "Failed to create product. Check that SKU and Barcode are unique.");
      }

      setIsAddOpen(false);
      resetForm();
      toast({ title: "Product Added", description: "Successfully introduced catalog item.", type: "success" });
      loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  // Edit Product Open
  const openEditModal = (p: Product) => {
    setSelectedProduct(p);
    setName(p.name);
    setBarcode(p.barcode);
    setSku(p.sku);
    setCategory(p.category);
    setBrand(p.brand || "");
    setVariant(p.variant || "");
    setWeight(p.weight || "");
    setPrice(p.price.toString());
    setSupplierId(p.supplier_id?.toString() || "");
    setDescription(p.description || "");

    // Extended Specs
    setQrCode(p.qr_code || "");
    setUnit(p.unit || "pcs");
    setDimensions(p.dimensions || "");
    setCostPrice(p.cost_price.toString());
    setTax(p.tax.toString());
    setShelfLife(p.shelf_life?.toString() || "");
    setExpiryTracking(p.expiry_tracking);
    setStatusField(p.status);

    // AI parameters
    setYoloClass(p.yolo_class_mapping?.toString() || "");
    setClipEmbeddings(p.clip_embeddings || "");
    setOcrText(p.ocr_reference_text || "");
    setConfidence(p.confidence_threshold);
    setAliases(p.aliases || "");

    setFormTab("general");
    setIsEditOpen(true);
  };

  // Edit Product Submit
  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProduct) return;
    setErrorMsg(null);
    setFormLoading(true);

    try {
      const payload = {
        name,
        barcode,
        sku,
        category,
        brand: brand || null,
        variant: variant || null,
        weight: weight || null,
        price: parseFloat(price) || 0.0,
        supplier_id: supplierId ? parseInt(supplierId) : null,
        description: description || null,

        // Extended Specifications
        qr_code: qrCode || null,
        unit: unit || null,
        dimensions: dimensions || null,
        cost_price: parseFloat(costPrice) || 0.0,
        tax: parseFloat(tax) || 0.0,
        shelf_life: shelfLife ? parseInt(shelfLife) : null,
        expiry_tracking: expiryTracking,
        status: statusField,

        // AI Metadata
        yolo_class_mapping: yoloClass ? parseInt(yoloClass) : null,
        clip_embeddings: clipEmbeddings || null,
        ocr_reference_text: ocrText || null,
        confidence_threshold: confidence,
        aliases: aliases || null
      };

      const res = await fetchWithAuth(`/api/v1/products/${selectedProduct.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload)
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || "Failed to update product details.");
      }

      setIsEditOpen(false);
      resetForm();
      toast({ title: "Product Updated", description: "Updated parameters successfully.", type: "success" });
      loadData();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  // Delete Product
  const handleDeleteProduct = async (id: number) => {
    if (!confirm("Are you sure you want to delete this product? All corresponding stock logs will be removed.")) return;
    try {
      const res = await fetchWithAuth(`/api/v1/products/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        toast({ title: "Product deleted", description: "Removed catalog entry.", type: "success" });
        loadData();
      }
    } catch (err) {
      console.error("Failed to delete product", err);
    }
  };

  // Bulk Delete Selection
  const handleToggleSelectProduct = (id: number) => {
    if (selectedProductIds.includes(id)) {
      setSelectedProductIds(selectedProductIds.filter(pid => pid !== id));
    } else {
      setSelectedProductIds([...selectedProductIds, id]);
    }
  };

  const handleToggleSelectAll = () => {
    if (selectedProductIds.length === products.length) {
      setSelectedProductIds([]);
    } else {
      setSelectedProductIds(products.map(p => p.id));
    }
  };

  const handleBulkDelete = async () => {
    if (!confirm(`Are you sure you want to delete the ${selectedProductIds.length} selected products?`)) return;
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/products/bulk-delete", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(selectedProductIds)
      });
      if (res.ok) {
        toast({ title: "Bulk Delete Completed", description: "Successfully purged product entries.", type: "success" });
        setSelectedProductIds([]);
        loadData();
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Import / Export CSV Triggers
  const handleExportCSV = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/products/export/csv");
      if (res.ok) {
        const blob = await res.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = "products_catalog.csv";
        document.body.appendChild(a);
        a.click();
        a.remove();
        toast({ title: "CSV Exported", description: "Full catalog downloaded successfully.", type: "success" });
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleImportCSVClick = () => {
    fileInputRef.current?.click();
  };

  const handleCSVFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setImporting(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const token = getAccessToken();
      const res = await fetch("/api/v1/products/import/csv", {
        method: "POST",
        headers: token ? { "Authorization": `Bearer ${token}` } : {},
        body: formData
      });

      if (res.ok) {
        const data = await res.json();
        toast({ 
          title: "Import Success", 
          description: `Processed CSV. Inserted: ${data.inserted}, Updated: ${data.updated}`, 
          type: "success" 
        });
        loadData();
      } else {
        toast({ title: "Import Error", description: "Failed to parse CSV file structure.", type: "error" });
      }
    } catch (err) {
      console.error(err);
    } finally {
      setImporting(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
    }
  };

  const openCodeModal = (p: Product) => {
    setSelectedProduct(p);
    setIsCodeOpen(true);
  };

  const resetForm = () => {
    setName("");
    setBarcode("");
    setSku("");
    setCategory("Groceries");
    setBrand("");
    setVariant("");
    setWeight("");
    setPrice("0.00");
    setSupplierId("");
    setInitialStock("0");
    setDescription("");

    // Extended parameters
    setQrCode("");
    setUnit("pcs");
    setDimensions("");
    setCostPrice("0.00");
    setTax("0.00");
    setShelfLife("");
    setExpiryTracking(false);
    setStatusField("active");

    // AI parameters
    setYoloClass("");
    setClipEmbeddings("");
    setOcrText("");
    setConfidence(0.5);
    setAliases("");

    setErrorMsg(null);
    setSelectedProduct(null);
  };

  const totalSKUs = products.length;
  const totalStock = products.reduce((acc, p) => acc + p.total_stock, 0);
  const outOfStock = products.filter(p => p.total_stock === 0).length;

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col px-4 py-12 text-xs">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      {/* Hidden file input for CSV import */}
      <input 
        type="file" 
        ref={fileInputRef} 
        onChange={handleCSVFileChange} 
        accept=".csv" 
        className="hidden" 
      />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Header console */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Package className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight text-neutral-100">Product Catalog Management</h2>
              <p className="text-xs text-neutral-500">Configure AI annotations, OCR text mappings, and bulk imports</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={handleExportCSV}>
              <Download className="w-3.5 h-3.5 mr-1" /> Export CSV
            </Button>
            <Button variant="ghost" size="sm" onClick={handleImportCSVClick} disabled={importing}>
              {importing ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Upload className="w-3.5 h-3.5 mr-1" />} Import CSV
            </Button>
            <Button variant="primary" size="sm" onClick={() => { resetForm(); setFormTab("general"); setIsAddOpen(true); }}>
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Product
            </Button>
          </div>
        </div>

        {/* Metrics summary widgets */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-6">
          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Package className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Catalog items</p>
              <h3 className="text-lg font-black text-neutral-200">{totalSKUs} SKUs registered</h3>
            </div>
          </div>

          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Boxes className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Cumulative Stock</p>
              <h3 className="text-lg font-black text-neutral-200">{totalStock} Units on shelves</h3>
            </div>
          </div>

          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-red-500/10 border border-red-500/20 flex items-center justify-center">
              <Activity className="w-5 h-5 text-red-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Out of stock</p>
              <h3 className="text-lg font-black text-neutral-200 text-red-400">{outOfStock} items empty</h3>
            </div>
          </div>
        </div>

        {/* Filter controls console */}
        <div className="bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
            <div className="relative">
              <Search className="absolute left-3 top-3 w-4 h-4 text-neutral-600" />
              <input 
                type="text"
                placeholder="Fuzzy search name, SKU, tags..."
                className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                value={search}
                onChange={e => setSearch(e.target.value)}
                onKeyDown={handleSearchKeyPress}
              />
            </div>

            <select 
              className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 appearance-none"
              value={categoryFilter}
              onChange={e => setCategoryFilter(e.target.value)}
            >
              <option value="">All Categories</option>
              <option value="Groceries">Groceries</option>
              <option value="Dairy & Eggs">Dairy & Eggs</option>
              <option value="Produce">Produce</option>
              <option value="Beverages">Beverages</option>
              <option value="Bakery">Bakery</option>
              <option value="Snacks">Snacks</option>
            </select>

            <input 
              type="text"
              placeholder="Filter by brand..."
              className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
              value={brandFilter}
              onChange={e => setBrandFilter(e.target.value)}
            />

            <select
              className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 appearance-none"
              value={statusFilter}
              onChange={e => setStatusFilter(e.target.value)}
            >
              <option value="">All Statuses</option>
              <option value="active">Active Only</option>
              <option value="inactive">Inactive Only</option>
            </select>

            <select
              className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 appearance-none"
              value={supplierFilter}
              onChange={e => setSupplierFilter(e.target.value)}
            >
              <option value="">All Suppliers</option>
              {suppliers.map(s => (
                <option key={s.id} value={s.id}>{s.name}</option>
              ))}
            </select>
          </div>

          <div className="flex justify-between items-center pt-2 border-t border-neutral-900">
            <span className="text-neutral-500 font-mono">Fuzzy keys: matched against names, SKU codes, OCR references, and barcode numbers</span>
            <Button variant="primary" onClick={loadData}>Apply Search Filters</Button>
          </div>
        </div>

        {/* Bulk Action panel triggers */}
        {selectedProductIds.length > 0 && (
          <div className="p-4 rounded-xl border border-red-500/20 bg-red-950/20 flex justify-between items-center">
            <span className="text-red-400 font-bold font-mono">{selectedProductIds.length} items selected for bulk execution</span>
            <Button variant="ghost" className="text-red-400 hover:bg-red-950" onClick={handleBulkDelete}>
              <Trash2 className="w-3.5 h-3.5 mr-1" /> Purge Selected Catalog
            </Button>
          </div>
        )}

        {/* Products lists Table */}
        {loading ? (
          <div className="flex justify-center items-center py-24">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
          </div>
        ) : products.length === 0 ? (
          <div className="text-center py-24 border border-neutral-900 rounded-3xl bg-neutral-900/10 space-y-3">
            <Package className="w-12 h-12 text-neutral-700 mx-auto" />
            <h4 className="text-sm font-bold text-neutral-400">Empty Catalog Registry</h4>
            <p className="text-neutral-500 max-w-sm mx-auto">Create a product catalog item or upload a CSV file to populate the shelf registry.</p>
          </div>
        ) : (
          <div className="bg-neutral-900/20 rounded-3xl border border-neutral-900 overflow-hidden">
            <div className="overflow-x-auto">
              <table className="w-full text-left border-collapse">
                <thead>
                  <tr className="border-b border-neutral-900 bg-neutral-900/30 text-neutral-400 font-bold uppercase font-mono">
                    <th className="px-6 py-4 w-12 text-center">
                      <button onClick={handleToggleSelectAll} className="p-1 text-neutral-600 hover:text-neutral-400">
                        {selectedProductIds.length === products.length ? <CheckSquare className="w-4 h-4 text-emerald-400" /> : <Square className="w-4 h-4" />}
                      </button>
                    </th>
                    <th className="px-6 py-4">Item Catalog Details</th>
                    <th className="px-6 py-4">Status & Info</th>
                    <th className="px-6 py-4">SKU / Barcode</th>
                    <th className="px-6 py-4 text-right">Price</th>
                    <th className="px-6 py-4 text-right">Stock</th>
                    <th className="px-6 py-4 text-center">Visual Actions</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-neutral-900 text-neutral-200">
                  {products.map(p => (
                    <tr key={p.id} className="hover:bg-neutral-900/10 transition-colors">
                      <td className="px-6 py-4 text-center">
                        <button onClick={() => handleToggleSelectProduct(p.id)} className="p-1 text-neutral-600 hover:text-neutral-400">
                          {selectedProductIds.includes(p.id) ? <CheckSquare className="w-4 h-4 text-emerald-400" /> : <Square className="w-4 h-4" />}
                        </button>
                      </td>
                      <td className="px-6 py-4">
                        <div>
                          <span className="font-bold text-xs text-neutral-100 block">{p.name}</span>
                          <span className="text-[10px] text-neutral-500 font-mono mt-0.5">
                            {p.brand && `${p.brand} • `}{p.weight || "Standard variant"} {p.unit && `(${p.unit})`}
                          </span>
                        </div>
                      </td>
                      <td className="px-6 py-4">
                        <div className="space-y-1">
                          <span className={`px-2 py-0.5 rounded text-[8px] font-bold font-mono ${p.status === 'active' ? 'bg-emerald-950 text-emerald-400' : 'bg-neutral-900 text-neutral-500'}`}>
                            {p.status}
                          </span>
                          {p.expiry_tracking && (
                            <span className="block text-[8px] text-amber-500 font-bold font-mono uppercase tracking-wider">Expiry Tracked</span>
                          )}
                        </div>
                      </td>
                      <td className="px-6 py-4 font-mono text-[10px] text-neutral-400">
                        <div>SKU: {p.sku}</div>
                        <div className="text-[9px] text-neutral-500 mt-0.5">Barcode: {p.barcode}</div>
                      </td>
                      <td className="px-6 py-4 text-right font-bold text-emerald-400">
                        ₹{p.price.toFixed(2)}
                      </td>
                      <td className="px-6 py-4 text-right">
                        <span className={`font-mono font-bold text-xs ${p.total_stock === 0 ? "text-red-400" : "text-neutral-100"}`}>
                          {p.total_stock}
                        </span>
                      </td>
                      <td className="px-6 py-4">
                        <div className="flex justify-center gap-3">
                          <button onClick={() => openCodeModal(p)} className="p-2 text-neutral-500 hover:text-emerald-400 hover:bg-neutral-900 rounded-xl" title="View Codes">
                            <QrCode className="w-4 h-4" />
                          </button>
                          <button onClick={() => openEditModal(p)} className="p-2 text-neutral-500 hover:text-emerald-400 hover:bg-neutral-900 rounded-xl" title="Edit Parameters">
                            <Edit3 className="w-4 h-4" />
                          </button>
                          <button onClick={() => handleDeleteProduct(p.id)} className="p-2 text-neutral-500 hover:text-red-400 hover:bg-neutral-900 rounded-xl" title="Delete">
                            <Trash2 className="w-4 h-4" />
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}

      </div>

      {/* Add / Edit Product Multi-Tab Dialog */}
      {(isAddOpen || isEditOpen) && (
        <div className="fixed inset-0 bg-neutral-950/85 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-2xl rounded-3xl p-6 relative space-y-6 max-h-[90vh] overflow-y-auto shadow-2xl">
            
            <button onClick={() => { setIsAddOpen(false); setIsEditOpen(false); }} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200">
              <X className="w-4 h-4" />
            </button>

            <div>
              <h3 className="text-base font-bold text-neutral-50">
                {isAddOpen ? "Add Catalog Product" : `Edit Details: ${name}`}
              </h3>
              <p className="text-[10px] text-neutral-500">Configure catalog specs, tax structures, and YOLO models</p>
            </div>

            {/* Form Tab select buttons */}
            <div className="flex gap-2 border-b border-neutral-900 pb-2">
              <button 
                type="button" 
                onClick={() => setFormTab("general")}
                className={`px-3 py-1.5 rounded-lg font-mono text-[10px] font-bold tracking-wider ${formTab === 'general' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                1. General Info
              </button>
              <button 
                type="button" 
                onClick={() => setFormTab("specs")}
                className={`px-3 py-1.5 rounded-lg font-mono text-[10px] font-bold tracking-wider ${formTab === 'specs' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                2. Inventory Specs
              </button>
              <button 
                type="button" 
                onClick={() => setFormTab("ai")}
                className={`px-3 py-1.5 rounded-lg font-mono text-[10px] font-bold tracking-wider ${formTab === 'ai' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
              >
                3. AI Annotations
              </button>
            </div>

            {errorMsg && (
              <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}

            <form onSubmit={isAddOpen ? handleAddSubmit : handleEditSubmit} className="space-y-4">
              
              {/* TAB 1: GENERAL INFO */}
              {formTab === "general" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Product Name *</label>
                    <Input type="text" required value={name} onChange={e => setName(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Brand Name</label>
                    <Input type="text" value={brand} onChange={e => setBrand(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">SKU Code (Unique) *</label>
                    <Input type="text" required className="font-mono" value={sku} onChange={e => setSku(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Barcode Number (EAN/UPC) *</label>
                    <Input type="text" required className="font-mono" value={barcode} onChange={e => setBarcode(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Category Group *</label>
                    <select className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300" value={category} onChange={e => setCategory(e.target.value)}>
                      <option value="Groceries">Groceries</option>
                      <option value="Dairy & Eggs">Dairy & Eggs</option>
                      <option value="Produce">Produce</option>
                      <option value="Beverages">Beverages</option>
                      <option value="Bakery">Bakery</option>
                      <option value="Snacks">Snacks</option>
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Selling Price (₹) *</label>
                    <Input type="number" step="0.01" required value={price} onChange={e => setPrice(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Supplier</label>
                    <select className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300" value={supplierId} onChange={e => setSupplierId(e.target.value)}>
                      <option value="">[Choose Supplier]</option>
                      {suppliers.map(s => (
                        <option key={s.id} value={s.id}>{s.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Weight / Volume</label>
                    <Input type="text" placeholder="e.g. 500g, 1.5L" value={weight} onChange={e => setWeight(e.target.value)} />
                  </div>
                  {isAddOpen && (
                    <>
                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Initial Stock Count</label>
                        <Input type="number" value={initialStock} onChange={e => setInitialStock(e.target.value)} />
                      </div>
                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Initial Store Target</label>
                        <select className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300" value={storeId} onChange={e => setStoreId(e.target.value)}>
                          <option value="1">Aetheria Main Store #1</option>
                        </select>
                      </div>
                    </>
                  )}
                  <div className="md:col-span-2">
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Catalog Item Description</label>
                    <textarea rows={2} className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-250 focus:outline-none" value={description} onChange={e => setDescription(e.target.value)} />
                  </div>
                </div>
              )}

              {/* TAB 2: INVENTORY SPECS */}
              {formTab === "specs" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">QR Code Identifier</label>
                    <Input type="text" placeholder="Scan codes mappings" value={qrCode} onChange={e => setQrCode(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Stocking Unit</label>
                    <Input type="text" placeholder="e.g. pcs, box, case" value={unit} onChange={e => setUnit(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Dimensions (LxWxH)</label>
                    <Input type="text" placeholder="e.g. 10x5x12 cm" value={dimensions} onChange={e => setDimensions(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Purchase Cost Price (₹)</label>
                    <Input type="number" step="0.01" value={costPrice} onChange={e => setCostPrice(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Tax Rate (%)</label>
                    <Input type="number" step="0.01" value={tax} onChange={e => setTax(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Shelf Life (Days)</label>
                    <Input type="number" value={shelfLife} onChange={e => setShelfLife(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Catalog Status</label>
                    <select className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-350" value={statusField} onChange={e => setStatusField(e.target.value)}>
                      <option value="active">Active</option>
                      <option value="inactive">Inactive</option>
                    </select>
                  </div>
                  <div className="flex items-center gap-2 py-4">
                    <input 
                      type="checkbox" 
                      id="expiryCheck"
                      checked={expiryTracking}
                      onChange={e => setExpiryTracking(e.target.checked)}
                      className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                    />
                    <label htmlFor="expiryCheck" className="text-neutral-300 font-bold select-none cursor-pointer">Enable Expiry Date Tracking</label>
                  </div>
                </div>
              )}

              {/* TAB 3: AI ANNOTATIONS */}
              {formTab === "ai" && (
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">YOLO Class Index</label>
                    <Input type="number" placeholder="e.g. 0, 1, 2" value={yoloClass} onChange={e => setYoloClass(e.target.value)} />
                  </div>
                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Confidence Threshold (0.0 - 1.0)</label>
                    <div className="flex items-center gap-3">
                      <input 
                        type="range" 
                        min="0" 
                        max="1" 
                        step="0.05"
                        value={confidence}
                        onChange={e => setConfidence(parseFloat(e.target.value))}
                        className="flex-1 accent-emerald-500 bg-neutral-900 rounded-lg appearance-none h-2"
                      />
                      <span className="font-mono text-neutral-300 font-bold text-xs">{confidence}</span>
                    </div>
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">OCR Reference Text Match</label>
                    <Input type="text" placeholder="Reference text inside brand label" value={ocrText} onChange={e => setOcrText(e.target.value)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Product Aliases (Comma separated)</label>
                    <Input type="text" placeholder="e.g. Coke, Coca Cola, Diet Coke" value={aliases} onChange={e => setAliases(e.target.value)} />
                  </div>
                  <div className="md:col-span-2">
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">CLIP Embedding Array Vector</label>
                    <textarea rows={2} placeholder="Vector embeddings from neural pipeline" className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-250 focus:outline-none" value={clipEmbeddings} onChange={e => setClipEmbeddings(e.target.value)} />
                  </div>
                </div>
              )}

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => { setIsAddOpen(false); setIsEditOpen(false); }}>Cancel</Button>
                <Button type="submit" disabled={formLoading}>
                  {formLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Save Catalog Item
                </Button>
              </div>

            </form>
          </div>
        </div>
      )}

      {/* Code visualizer drawer */}
      {isCodeOpen && selectedProduct && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-sm rounded-3xl p-6 relative space-y-6 text-center shadow-2xl">
            <button onClick={() => setIsCodeOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200">
              <X className="w-4 h-4" />
            </button>
            <div className="space-y-1">
              <h3 className="text-sm font-bold text-neutral-50">{selectedProduct.name}</h3>
              <p className="text-[10px] text-neutral-500">Visual Code Indicators</p>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-neutral-200 space-y-3 flex flex-col items-center justify-center">
              <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider">Product Barcode</span>
              <div className="flex items-center justify-center h-12 w-48 gap-[1.5px] bg-neutral-950 p-2 rounded">
                {[...Array(38)].map((_, i) => (
                  <div key={i} className="h-full bg-white shrink-0" style={{ width: i % 3 === 0 ? "4px" : i % 5 === 0 ? "1px" : "2px" }} />
                ))}
              </div>
              <span className="font-mono text-neutral-955 text-xs tracking-widest">{selectedProduct.barcode}</span>
            </div>

            <div className="p-5 rounded-2xl bg-white border border-neutral-200 space-y-3 flex flex-col items-center justify-center">
              <span className="text-[8px] text-neutral-500 font-bold uppercase tracking-wider">Product QR Code</span>
              <img 
                src={`https://api.qrserver.com/v1/create-qr-code/?size=150x150&data=${encodeURIComponent(selectedProduct.sku)}`} 
                alt="Product QR code" 
                className="w-28 h-28 border border-neutral-100 p-1 bg-white rounded"
              />
              <span className="font-mono text-neutral-955 text-[10px] tracking-wider uppercase font-semibold">{selectedProduct.sku}</span>
            </div>

            <Button variant="ghost" className="w-full" onClick={() => setIsCodeOpen(false)}>Close Visualizer</Button>
          </div>
        </div>
      )}

    </div>
  );
}
