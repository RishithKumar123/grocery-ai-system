"use client";

import React, { useState, useEffect } from "react";
import { useRouter, useParams } from "next/navigation";
import Link from "next/link";
import { 
  Building2, 
  ArrowLeft, 
  Users, 
  Truck, 
  Boxes, 
  Video, 
  ShoppingBag, 
  ScanLine, 
  Plus, 
  Trash2, 
  Loader2, 
  X,
  UserPlus,
  AlertCircle,
  FileDown,
  Layers,
  MapPin,
  Save,
  CheckCircle,
  Eye,
  History,
  TrendingUp,
  Sliders
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../../lib/auth";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { useToast } from "../../../components/ui/toast";

interface StoreUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  is_verified: boolean;
}

interface InventoryItem {
  id: number;
  product_id: number;
  name: string;
  sku: string;
  quantity: number;
  available_stock: number;
  reserved_stock: number;
  damaged_stock: number;
  min_stock: number;
  max_stock: number;
  reorder_level: number;
  stock_valuation: number;
  expiry_date: string | null;
  location_bin: string;
  confidence: number | null;
  status: string;
  updated_at: string;
}

interface ScanHistoryItem {
  id: number;
  video_id: number | null;
  image_url: string;
  status: string;
  created_at: string;
  detections_count: number;
}

interface AuditLogItem {
  id: number;
  action: string;
  created_at: string;
  payload: {
    store_id: number;
    location_bin: string;
    product_id?: number;
    product_name?: string;
    sku?: string;
    old_quantity?: number;
    new_quantity?: number;
    details: string;
  };
}

interface Shelf {
  id: number;
  store_id: number;
  aisle: string;
  shelf_level: string;
  section: string;
  bin_rack: string;
  capacity: number;
  status: string;
  created_at: string;
  updated_at: string;
}

interface StockTransaction {
  id: number;
  store_id: number;
  product_id: number;
  user_id: number | null;
  transaction_type: string;
  quantity_change: number;
  previous_quantity: number;
  new_quantity: number;
  notes: string | null;
  created_at: string;
}

interface StoreDetails {
  id: number;
  name: string;
  location: string | null;
  created_at: string;
  employees: StoreUser[];
  vendors: StoreUser[];
  inventory: InventoryItem[];
  scans_history: ScanHistoryItem[];
  audit_logs: AuditLogItem[];
  analytics: {
    total_stock_skus: number;
    total_stock_units: number;
    total_videos: number;
    total_orders: number;
    total_scans: number;
  };
}

interface ProductInfo {
  id: number;
  name: string;
  sku: string;
}

export default function StoreDashboardPage() {
  const router = useRouter();
  const params = useParams();
  const { toast } = useToast();
  const storeId = params.id;

  const [details, setDetails] = useState<StoreDetails | null>(null);
  const [availableUsers, setAvailableUsers] = useState<StoreUser[]>([]);
  const [shelves, setShelves] = useState<Shelf[]>([]);
  const [transactions, setTransactions] = useState<StockTransaction[]>([]);
  const [products, setProducts] = useState<ProductInfo[]>([]);
  const [loading, setLoading] = useState(true);

  // Tab state: "overview" | "layout" | "ledger"
  const [activeTab, setActiveTab] = useState<"overview" | "layout" | "ledger">("overview");

  // Assignment states
  const [isAssignOpen, setIsAssignOpen] = useState(false);
  const [selectedUserId, setSelectedUserId] = useState("");
  const [assignRole, setAssignRole] = useState<"Shopkeeper" | "Vendor">("Shopkeeper");
  const [assignError, setAssignError] = useState<string | null>(null);
  const [assignLoading, setAssignLoading] = useState(false);
  
  // Layout Management states
  const [isAddShelfOpen, setIsAddShelfOpen] = useState(false);
  const [aisle, setAisle] = useState("");
  const [shelfLevel, setShelfLevel] = useState("");
  const [section, setSection] = useState("");
  const [binRack, setBinRack] = useState("");
  const [capacity, setCapacity] = useState("50");
  const [shelfStatus, setShelfStatus] = useState("active");
  const [shelfLoading, setShelfLoading] = useState(false);

  // Transaction Ledger states
  const [isPostTransactionOpen, setIsPostTransactionOpen] = useState(false);
  const [selectedProductId, setSelectedProductId] = useState("");
  const [transactionType, setTransactionType] = useState("Purchase");
  const [qtyChange, setQtyChange] = useState("");
  const [txNotes, setTxNotes] = useState("");
  const [txLoading, setTxLoading] = useState(false);

  const [exportLoading, setExportLoading] = useState(false);

  const handleExportExcel = async () => {
    setExportLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/reports/store/${storeId}`, {
        method: "POST"
      });
      if (res.ok) {
        const data = await res.json();
        if (data.file_url) {
          window.open(`${data.file_url}`, "_blank");
          loadData();
        }
      } else {
        alert("Failed to generate Excel report. Make sure backend is running.");
      }
    } catch (err) {
      console.error("Export error", err);
      alert("An unexpected error occurred during Excel export.");
    } finally {
      setExportLoading(false);
    }
  };

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }

    loadData();
    loadShelves();
    loadTransactions();
    loadProducts();
  }, [storeId, router]);

  const loadData = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth(`/api/v1/stores/${storeId}`);
      if (res.ok) {
        const data = await res.json();
        setDetails(data);
      } else {
        router.push("/stores");
      }

      // Load available users for assignment
      const usersRes = await fetchWithAuth("/api/v1/stores/users/available");
      if (usersRes.ok) {
        const usersData = await usersRes.json();
        setAvailableUsers(usersData);
      }
    } catch (err) {
      console.error("Failed to load store dashboard data", err);
    } finally {
      setLoading(false);
    }
  };

  const loadShelves = async () => {
    try {
      const res = await fetchWithAuth(`/api/v1/layout?store_id=${storeId}`);
      if (res.ok) {
        const data = await res.json();
        setShelves(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadTransactions = async () => {
    try {
      const res = await fetchWithAuth(`/api/v1/transactions?store_id=${storeId}`);
      if (res.ok) {
        const data = await res.json();
        setTransactions(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadProducts = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/products");
      if (res.ok) {
        const data = await res.json();
        setProducts(data.map((p: any) => ({ id: p.id, name: p.name, sku: p.sku })));
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleAssignSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedUserId) return;
    setAssignError(null);
    setAssignLoading(true);

    try {
      const res = await fetchWithAuth(`/api/v1/stores/${storeId}/assign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: parseInt(selectedUserId) })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || "Failed to link user to branch.");
      }

      setIsAssignOpen(false);
      setSelectedUserId("");
      toast({ title: "User Linked", description: "Linked user to this branch outlet.", type: "success" });
      loadData();
    } catch (err: any) {
      setAssignError(err.message);
    } finally {
      setAssignLoading(false);
    }
  };

  const handleUnassignUser = async (userId: number) => {
    if (!confirm("Are you sure you want to remove this user's assignment from this branch?")) return;
    try {
      const res = await fetchWithAuth(`/api/v1/stores/${storeId}/unassign`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ user_id: userId })
      });
      if (res.ok) {
        toast({ title: "User Unassigned", description: "Unlinked user from store.", type: "success" });
        loadData();
      }
    } catch (err) {
      console.error("Failed to unassign user", err);
    }
  };

  const handleAddShelfSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setShelfLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/layout", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: parseInt(storeId as string),
          aisle,
          shelf_level: shelfLevel,
          section,
          bin_rack: binRack,
          capacity: parseInt(capacity) || 50,
          status: shelfStatus
        })
      });

      if (res.ok) {
        setIsAddShelfOpen(false);
        setAisle("");
        setShelfLevel("");
        setSection("");
        setBinRack("");
        setCapacity("50");
        toast({ title: "Shelf Created", description: "Layout coordinates cataloged.", type: "success" });
        loadShelves();
      } else {
        alert("Failed to create layout shelf configuration.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setShelfLoading(false);
    }
  };

  const handleDeleteShelf = async (id: number) => {
    if (!confirm("Are you sure you want to delete this physical shelf? All inventory items mapped to this shelf will lose their placement locator.")) return;
    try {
      const res = await fetchWithAuth(`/api/v1/layout/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        toast({ title: "Shelf Removed", description: "Purged layout mapping.", type: "success" });
        loadShelves();
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handlePostTransactionSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedProductId || !qtyChange) return;
    setTxLoading(true);

    try {
      const res = await fetchWithAuth("/api/v1/transactions", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          store_id: parseInt(storeId as string),
          product_id: parseInt(selectedProductId),
          transaction_type: transactionType,
          quantity_change: parseInt(qtyChange),
          notes: txNotes || null
        })
      });

      if (res.ok) {
        setIsPostTransactionOpen(false);
        setSelectedProductId("");
        setQtyChange("");
        setTxNotes("");
        toast({ title: "Ledger Adjusted", description: "Reconciled stock levels successfully.", type: "success" });
        loadTransactions();
        loadData(); // Reload inventory counts
      } else {
        const errData = await res.json().catch(() => ({}));
        alert(errData.detail || "Failed to post transaction ledger adjustment.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setTxLoading(false);
    }
  };

  if (loading || !details) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
      </div>
    );
  }

  const assignedIds = new Set([
    ...details.employees.map(e => e.id),
    ...details.vendors.map(v => v.id)
  ]);

  const assignableFiltered = availableUsers.filter(u => 
    u.role === assignRole && !assignedIds.has(u.id)
  );

  // Group shelves by aisle for structural hierarchy layouts
  const groupedShelves: { [key: string]: Shelf[] } = {};
  shelves.forEach(s => {
    if (!groupedShelves[s.aisle]) {
      groupedShelves[s.aisle] = [];
    }
    groupedShelves[s.aisle].push(s);
  });

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col px-4 py-12 text-xs">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Top Navbar */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <Link href="/stores" className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/50 text-neutral-400 hover:text-emerald-400 transition-colors">
              <ArrowLeft className="w-4 h-4" />
            </Link>
            <div>
              <div className="flex items-center gap-2">
                <Building2 className="w-5 h-5 text-emerald-400" />
                <h2 className="text-xl font-extrabold text-neutral-100">{details.name}</h2>
              </div>
              <span className="text-[10px] text-neutral-500 font-mono mt-0.5 block">{details.location || "No location coordinates configured"}</span>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportExcel}
              disabled={exportLoading}
              className="flex items-center gap-1.5 rounded-xl border border-neutral-800 hover:border-emerald-500/30 hover:bg-emerald-950/10 px-4 py-2 text-sm font-semibold text-neutral-300 hover:text-emerald-400 transition-all cursor-pointer disabled:opacity-50"
            >
              {exportLoading ? <Loader2 className="w-4 h-4 animate-spin" /> : <FileDown className="w-4 h-4 text-emerald-450" />} Report
            </button>
            <Button variant="primary" onClick={() => { setAssignError(null); setIsAssignOpen(true); }}>
              <UserPlus className="w-3.5 h-3.5 mr-1" /> Link Staff / Vendor
            </Button>
          </div>
        </div>

        {/* Tab Selection */}
        <div className="flex gap-3 border-b border-neutral-900 pb-3">
          <button 
            onClick={() => setActiveTab("overview")}
            className={`px-4 py-2 rounded-xl font-bold font-mono tracking-wider ${activeTab === 'overview' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
          >
            1. Branch Overview
          </button>
          <button 
            onClick={() => setActiveTab("layout")}
            className={`px-4 py-2 rounded-xl font-bold font-mono tracking-wider ${activeTab === 'layout' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
          >
            2. Physical Layout ({shelves.length} Shelves)
          </button>
          <button 
            onClick={() => setActiveTab("ledger")}
            className={`px-4 py-2 rounded-xl font-bold font-mono tracking-wider ${activeTab === 'ledger' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'text-neutral-500 hover:text-neutral-300'}`}
          >
            3. Stock Movements ({transactions.length} Logged)
          </button>
        </div>

        {activeTab === "overview" && (
          <>
            {/* Branch Metrics row */}
            <div className="grid grid-cols-2 md:grid-cols-5 gap-6">
              <div className="bg-neutral-900/40 border border-neutral-900 p-4 rounded-2xl text-center">
                <Boxes className="w-5 h-5 text-emerald-400 mx-auto" />
                <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-2 block font-mono">Catalog SKUs</span>
                <span className="text-lg font-bold text-neutral-200 mt-1 block">{details.analytics.total_stock_skus}</span>
              </div>
              <div className="bg-neutral-900/40 border border-neutral-900 p-4 rounded-2xl text-center">
                <Boxes className="w-5 h-5 text-emerald-400 mx-auto" />
                <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-2 block font-mono">Stock Quantity</span>
                <span className="text-lg font-bold text-neutral-200 mt-1 block">{details.analytics.total_stock_units}</span>
              </div>
              <div className="bg-neutral-900/40 border border-neutral-900 p-4 rounded-2xl text-center">
                <Video className="w-5 h-5 text-emerald-400 mx-auto" />
                <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-2 block font-mono">Cameras</span>
                <span className="text-lg font-bold text-neutral-200 mt-1 block">{details.analytics.total_videos}</span>
              </div>
              <div className="bg-neutral-900/40 border border-neutral-900 p-4 rounded-2xl text-center">
                <ShoppingBag className="w-5 h-5 text-emerald-400 mx-auto" />
                <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-2 block font-mono">Supplier Orders</span>
                <span className="text-lg font-bold text-neutral-200 mt-1 block">{details.analytics.total_orders}</span>
              </div>
              <div className="bg-neutral-900/40 border border-neutral-900 p-4 rounded-2xl text-center col-span-2 md:col-span-1">
                <ScanLine className="w-5 h-5 text-emerald-400 mx-auto" />
                <span className="text-[10px] text-neutral-500 uppercase font-semibold mt-2 block font-mono">AI Scans</span>
                <span className="text-lg font-bold text-neutral-200 mt-1 block">{details.analytics.total_scans}</span>
              </div>
            </div>

            {/* Dynamic Splits - Staff vs Vendors */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              
              {/* Employees List (Shopkeepers) */}
              <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm">
                    <Users className="w-5 h-5 text-emerald-400" />
                    Assigned Employees
                  </h3>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-450 font-mono">
                    {details.employees.length} Staff
                  </span>
                </div>

                {details.employees.length === 0 ? (
                  <div className="text-center py-10 text-neutral-500 text-xs">
                    No shopkeepers linked to this branch. Click Link Staff above to assign.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {details.employees.map(emp => (
                      <div key={emp.id} className="flex justify-between items-center p-3 rounded-2xl bg-neutral-950 border border-neutral-900/60 hover:border-neutral-900 transition-colors">
                        <div>
                          <div className="font-bold text-neutral-200 text-xs">{emp.full_name}</div>
                          <div className="text-[10px] text-neutral-500 font-mono mt-0.5">{emp.email}</div>
                        </div>
                        <button
                          onClick={() => handleUnassignUser(emp.id)}
                          className="p-2 rounded-xl bg-neutral-900/40 text-neutral-400 hover:text-red-400 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Vendors List */}
              <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6">
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm">
                    <Truck className="w-5 h-5 text-emerald-400" />
                    Assigned Vendors
                  </h3>
                  <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-450 font-mono">
                    {details.vendors.length} Vendors
                  </span>
                </div>

                {details.vendors.length === 0 ? (
                  <div className="text-center py-10 text-neutral-500 text-xs">
                    No vendors associated with this branch. Click Link Vendor above to assign.
                  </div>
                ) : (
                  <div className="space-y-3">
                    {details.vendors.map(ven => (
                      <div key={ven.id} className="flex justify-between items-center p-3 rounded-2xl bg-neutral-950 border border-neutral-900/60 hover:border-neutral-900 transition-colors">
                        <div>
                          <div className="font-bold text-neutral-200 text-xs">{ven.full_name}</div>
                          <div className="text-[10px] text-neutral-500 font-mono mt-0.5">{ven.email}</div>
                        </div>
                        <button
                          onClick={() => handleUnassignUser(ven.id)}
                          className="p-2 rounded-xl bg-neutral-900/40 text-neutral-400 hover:text-red-400 transition-colors cursor-pointer"
                        >
                          <Trash2 className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    ))}
                  </div>
                )}
              </div>

            </div>

            {/* Section 2: Inventory Counts by Product & Shelf */}
            <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm">
                  <Boxes className="w-5 h-5 text-emerald-400" />
                  Shelf Inventory & Stock Counts
                </h3>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-450 font-mono">
                  {(details.inventory || []).length} Active SKUs
                </span>
              </div>

              {!(details.inventory && details.inventory.length > 0) ? (
                <div className="text-center py-12 text-neutral-500 text-xs">
                  No products counted in stock yet. Upload security footage to run a shelf scan.
                </div>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-neutral-900 text-neutral-400 font-bold uppercase tracking-wider text-[10px] font-mono">
                        <th className="pb-3">Product Name</th>
                        <th className="pb-3 text-center">Stock Levels (Cur / Avail / Res / Dmg)</th>
                        <th className="pb-3 text-center">Thresholds (Min / Reorder)</th>
                        <th className="pb-3 text-right">Valuation</th>
                        <th className="pb-3">Location Bin</th>
                        <th className="pb-3">Confidence</th>
                        <th className="pb-3 text-right">Last Scanned</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                      {details.inventory.map(item => {
                        const isUnderMin = item.quantity <= item.min_stock;
                        const isUnderReorder = item.quantity <= item.reorder_level;
                        
                        let warningText = "";
                        let warningClass = "";
                        if (isUnderMin) {
                          warningText = "Under Min";
                          warningClass = "bg-red-950 text-red-400 border-red-500/20";
                        } else if (isUnderReorder) {
                          warningText = "Reorder Warning";
                          warningClass = "bg-amber-950 text-amber-400 border-amber-500/20";
                        }

                        return (
                          <tr key={item.id} className="hover:bg-neutral-900/10 transition-colors">
                            <td className="py-3.5">
                              <div>
                                <span className="font-bold text-neutral-200 block">{item.name}</span>
                                <span className="text-[10px] text-neutral-500 font-mono mt-0.5">SKU: {item.sku}</span>
                              </div>
                            </td>
                            <td className="py-3.5 text-center font-mono">
                              <div className="flex justify-center gap-2">
                                <span className="text-neutral-100 font-bold" title="Current Stock">{item.quantity}</span>
                                <span className="text-neutral-550">/</span>
                                <span className="text-emerald-400 font-bold" title="Available Stock">{item.available_stock}</span>
                                <span className="text-neutral-550">/</span>
                                <span className="text-blue-400" title="Reserved Stock">{item.reserved_stock}</span>
                                <span className="text-neutral-550">/</span>
                                <span className="text-red-450" title="Damaged Stock">{item.damaged_stock}</span>
                              </div>
                            </td>
                            <td className="py-3.5 text-center font-mono">
                              <div className="flex flex-col items-center gap-1">
                                <span className="text-neutral-400 text-[10px]">Min: {item.min_stock} | Reorder: {item.reorder_level}</span>
                                {warningText && (
                                  <span className={`px-2 py-0.5 rounded text-[8px] font-bold border uppercase tracking-wider ${warningClass}`}>
                                    {warningText}
                                  </span>
                                )}
                              </div>
                            </td>
                            <td className="py-3.5 text-right font-mono font-bold text-emerald-400">
                              ₹{item.stock_valuation.toFixed(2)}
                            </td>
                            <td className="py-3.5">
                              <span className="px-2 py-0.5 rounded-full bg-neutral-950 border border-neutral-900 text-neutral-350 font-mono">
                                {item.location_bin}
                              </span>
                            </td>
                            <td className="py-3.5">
                              {item.confidence ? (
                                <span className={`px-1.5 py-0.5 rounded text-[10px] font-bold font-mono ${
                                  item.confidence > 0.8
                                    ? "bg-emerald-950/20 text-emerald-400 border border-emerald-500/10"
                                    : "bg-yellow-950/20 text-yellow-400 border border-yellow-500/10"
                                }`}>
                                  {Math.round(item.confidence * 100)}%
                                </span>
                              ) : (
                                <span className="text-neutral-600">Manual</span>
                              )}
                            </td>
                            <td className="py-3.5 text-right text-neutral-500 font-mono">
                              {new Date(item.updated_at).toLocaleString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* Section 3: AI Scan Execution History */}
            <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm">
                  <ScanLine className="w-5 h-5 text-emerald-400" />
                  AI Shelf Scan History
                </h3>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-450 font-mono">
                  {(details.scans_history || []).length} Scans Run
                </span>
              </div>

              {!(details.scans_history && details.scans_history.length > 0) ? (
                <div className="text-center py-12 text-neutral-500 text-xs">
                  No scans executed. Upload camera footage to begin.
                </div>
              ) : (
                <div className="space-y-3">
                  {details.scans_history.map(scan => (
                    <div key={scan.id} className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900/60 flex justify-between items-center text-xs">
                      <div className="space-y-1">
                        <span className="font-bold text-neutral-250">Scan Execution: #SCN-{scan.id}</span>
                        <div className="text-[10px] text-neutral-500 font-mono">
                          Source Video Feed: {scan.video_id ? `Feed #${scan.video_id}` : "Manual Upload"} | {new Date(scan.created_at).toLocaleString()}
                        </div>
                      </div>
                      <div className="flex items-center gap-4">
                        <span className="px-2 py-0.5 rounded bg-emerald-950/20 text-emerald-400 border border-emerald-500/10 font-bold font-mono">
                          {scan.detections_count} Items Detected
                        </span>
                        <span className="px-2 py-0.5 rounded bg-neutral-900 border border-neutral-855 text-neutral-400 font-medium">
                          Status: {scan.status}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* Section 4: Inventory Audit Logs */}
            <div className="bg-neutral-900/20 border border-neutral-900 p-6 rounded-3xl space-y-6">
              <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                <h3 className="font-bold text-neutral-100 flex items-center gap-2 text-sm">
                  <Boxes className="w-5 h-5 text-emerald-400" />
                  Inventory Reconciliation Audit Trail
                </h3>
                <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-neutral-900 border border-neutral-800 text-neutral-450 font-mono">
                  {(details.audit_logs || []).length} System Logs
                </span>
              </div>

              {!(details.audit_logs && details.audit_logs.length > 0) ? (
                <div className="text-center py-12 text-neutral-500 text-xs">
                  No reconciliation audit logs recorded yet. Run a shelf camera scan to trigger logs.
                </div>
              ) : (
                <div className="space-y-3">
                  {details.audit_logs.map(log => {
                    let badgeColor = "bg-neutral-900 text-neutral-400 border-neutral-800";
                    if (log.action === "INVENTORY_RECONCILE_NEW") {
                      badgeColor = "bg-emerald-950/20 text-emerald-400 border-emerald-500/15";
                    } else if (log.action === "INVENTORY_RECONCILE_MISSING") {
                      badgeColor = "bg-red-950/20 text-red-400 border-red-500/15";
                    } else if (log.action === "INVENTORY_RECONCILE_UPDATE") {
                      badgeColor = "bg-blue-950/20 text-blue-400 border-blue-500/15";
                    }

                    return (
                      <div key={log.id} className="p-4 rounded-2xl bg-neutral-950 border border-neutral-900/60 flex flex-col md:flex-row md:justify-between md:items-center text-xs gap-3">
                        <div className="space-y-1">
                          <div className="flex items-center gap-2 flex-wrap">
                            <span className={`px-2 py-0.5 rounded border text-[10px] font-bold uppercase tracking-wider ${badgeColor}`}>
                              {log.action.replace("INVENTORY_RECONCILE_", "")}
                            </span>
                            <span className="font-bold text-neutral-200">{log.payload.product_name}</span>
                            <span className="text-[10px] text-neutral-500 font-mono">({log.payload.sku})</span>
                          </div>
                          <p className="text-neutral-400 text-[11px]">{log.payload.details}</p>
                        </div>
                        <div className="flex items-center gap-4 shrink-0 font-mono text-[10px] md:text-right flex-wrap md:flex-col md:items-end">
                          <div className="flex items-center gap-2">
                            {log.payload.old_quantity !== undefined && (
                              <span className="text-neutral-550 font-mono">Qty: {log.payload.old_quantity} →</span>
                            )}
                            <span className="text-neutral-200 font-bold">Qty: {log.payload.new_quantity}</span>
                            <span className="text-neutral-500">({log.payload.location_bin})</span>
                          </div>
                          <span className="text-neutral-600">
                            {new Date(log.created_at).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          </>
        )}

        {activeTab === "layout" && (
          /* TAB 2: PHYSICAL LAYOUT CONFIGURATIONS */
          <div className="space-y-6">
            
            <div className="flex justify-between items-center bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <div>
                <h3 className="font-bold text-neutral-200 flex items-center gap-2 text-sm">
                  <Layers className="w-5 h-5 text-emerald-400" />
                  Physical Store Aisles & Shelves
                </h3>
                <p className="text-[10px] text-neutral-500 font-sans mt-0.5">Map shelf coordinates to help the AI localize item bounding boxes</p>
              </div>
              <Button variant="primary" onClick={() => setIsAddShelfOpen(true)}>
                <Plus className="w-3.5 h-3.5 mr-1" /> Add Shelf Coordinates
              </Button>
            </div>

            {shelves.length === 0 ? (
              <div className="text-center py-20 border border-neutral-900 rounded-3xl bg-neutral-900/10 space-y-3">
                <Layers className="w-12 h-12 text-neutral-700 mx-auto" />
                <h4 className="text-sm font-bold text-neutral-400">Empty Layout Registry</h4>
                <p className="text-neutral-500 max-w-sm mx-auto">Create physical layout shelves to localize scanning cameras.</p>
              </div>
            ) : (
              <div className="space-y-8">
                {Object.keys(groupedShelves).map(aisleName => (
                  <div key={aisleName} className="space-y-4">
                    <div className="flex items-center gap-2 border-b border-neutral-900 pb-2">
                      <span className="w-2.5 h-2.5 rounded-full bg-emerald-500" />
                      <h4 className="text-xs font-black uppercase tracking-wider text-neutral-300 font-mono">{aisleName}</h4>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                      {groupedShelves[aisleName].map(shelf => {
                        // Calculate items on this shelf Level Section
                        const itemsOnShelf = details.inventory.filter(
                          item => item.location_bin === `${shelf.aisle} - ${shelf.shelf_level} - ${shelf.section}`
                        );
                        const filledUnits = itemsOnShelf.reduce((acc, curr) => acc + curr.quantity, 0);
                        const capacityPercentage = Math.min(Math.round((filledUnits / shelf.capacity) * 100), 100);

                        return (
                          <div key={shelf.id} className="bg-neutral-900/30 border border-neutral-900 p-5 rounded-2xl space-y-4 hover:border-neutral-850 transition-all flex flex-col justify-between">
                            <div className="space-y-2">
                              <div className="flex justify-between items-start">
                                <div className="space-y-1">
                                  <span className="text-[10px] uppercase font-bold text-neutral-500 font-mono tracking-wide">
                                    {shelf.shelf_level} • {shelf.section}
                                  </span>
                                  <h5 className="font-bold text-xs text-neutral-200 mt-0.5">{shelf.bin_rack}</h5>
                                </div>
                                <div className="flex items-center gap-1.5">
                                  <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono uppercase ${shelf.status === 'active' ? 'bg-emerald-950 text-emerald-400' : 'bg-neutral-900 text-neutral-500'}`}>
                                    {shelf.status}
                                  </span>
                                  <button onClick={() => handleDeleteShelf(shelf.id)} className="p-1 rounded bg-neutral-900 text-neutral-500 hover:text-red-400">
                                    <Trash2 className="w-3.5 h-3.5" />
                                  </button>
                                </div>
                              </div>

                              <div className="space-y-1">
                                <div className="flex justify-between text-[9px] text-neutral-500 font-mono">
                                  <span>Capacity Allocation</span>
                                  <span className="font-bold text-neutral-350">{filledUnits} / {shelf.capacity} units ({capacityPercentage}%)</span>
                                </div>
                                <div className="h-1.5 w-full bg-neutral-950 rounded-full overflow-hidden border border-neutral-900">
                                  <div 
                                    className={`h-full rounded-full transition-all duration-300 ${capacityPercentage > 90 ? 'bg-red-400' : capacityPercentage > 70 ? 'bg-amber-400' : 'bg-emerald-500'}`}
                                    style={{ width: `${capacityPercentage}%` }}
                                  />
                                </div>
                              </div>
                            </div>

                            <div className="pt-3 border-t border-neutral-900/60 flex justify-between items-center text-[10px]">
                              <span className="text-neutral-500 font-mono uppercase text-[8px]">ID: SH-{shelf.id}</span>
                              <span className="text-neutral-450 font-bold font-mono">{itemsOnShelf.length} Unique SKUs</span>
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        {activeTab === "ledger" && (
          /* TAB 3: STOCK MOVEMENTS LEDGER AUDIT TRAIL */
          <div className="space-y-6">
            
            <div className="flex justify-between items-center bg-neutral-900/20 border border-neutral-900 p-5 rounded-2xl">
              <div>
                <h3 className="font-bold text-neutral-200 flex items-center gap-2 text-sm">
                  <History className="w-5 h-5 text-emerald-400" />
                  Stock Movement Transactions Ledger
                </h3>
                <p className="text-[10px] text-neutral-500 font-sans mt-0.5">Complete audit trail ledger tracking purchases, sales, and damage adjustments</p>
              </div>
              <Button variant="primary" onClick={() => setIsPostTransactionOpen(true)}>
                <Plus className="w-3.5 h-3.5 mr-1" /> Post Stock Adjustment
              </Button>
            </div>

            {transactions.length === 0 ? (
              <div className="text-center py-20 border border-neutral-900 rounded-3xl bg-neutral-900/10 space-y-3">
                <History className="w-12 h-12 text-neutral-700 mx-auto" />
                <h4 className="text-sm font-bold text-neutral-400">Empty Ledger Logs</h4>
                <p className="text-neutral-500 max-w-sm mx-auto">Reconcile inventory or post adjustments to trigger movement entries.</p>
              </div>
            ) : (
              <div className="bg-neutral-900/20 border border-neutral-900 rounded-3xl overflow-hidden">
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-xs border-collapse">
                    <thead>
                      <tr className="border-b border-neutral-900 bg-neutral-900/30 text-neutral-400 font-bold uppercase tracking-wider text-[10px] font-mono px-6 py-4">
                        <th className="px-6 py-4">Transaction Details</th>
                        <th className="px-6 py-4">Type</th>
                        <th className="px-6 py-4 text-center">Movement Qty</th>
                        <th className="px-6 py-4 text-center">Previous Qty → New Qty</th>
                        <th className="px-6 py-4">Audit Notes</th>
                        <th className="px-6 py-4 text-right">Timestamp</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-neutral-900/40 text-neutral-300">
                      {transactions.map(tx => {
                        let typeColor = "bg-neutral-900 text-neutral-400 border-neutral-850";
                        if (tx.transaction_type === "Purchase") typeColor = "bg-emerald-950 text-emerald-400 border-emerald-500/20";
                        if (tx.transaction_type === "Sale") typeColor = "bg-blue-950 text-blue-400 border-blue-500/20";
                        if (tx.transaction_type === "Damage") typeColor = "bg-red-950 text-red-400 border-red-500/20";
                        if (tx.transaction_type === "Expiry") typeColor = "bg-yellow-950 text-yellow-400 border-yellow-500/20";
                        
                        const matchedProduct = products.find(p => p.id === tx.product_id);

                        return (
                          <tr key={tx.id} className="hover:bg-neutral-900/10 transition-colors">
                            <td className="px-6 py-4 font-bold text-neutral-200">
                              {matchedProduct ? matchedProduct.name : `Product ID: ${tx.product_id}`}
                              <span className="block font-mono text-[9px] text-neutral-500 mt-0.5">
                                {matchedProduct ? matchedProduct.sku : `ID: ${tx.product_id}`}
                              </span>
                            </td>
                            <td className="px-6 py-4">
                              <span className={`px-2 py-0.5 rounded text-[8px] font-bold uppercase border tracking-wider ${typeColor}`}>
                                {tx.transaction_type}
                              </span>
                            </td>
                            <td className={`px-6 py-4 text-center font-bold font-mono ${tx.quantity_change > 0 ? 'text-emerald-400' : 'text-red-400'}`}>
                              {tx.quantity_change > 0 ? `+${tx.quantity_change}` : tx.quantity_change}
                            </td>
                            <td className="px-6 py-4 text-center font-mono text-neutral-400">
                              {tx.previous_quantity} units → {tx.new_quantity} units
                            </td>
                            <td className="px-6 py-4 text-neutral-400 max-w-xs truncate" title={tx.notes || ""}>
                              {tx.notes || "-"}
                            </td>
                            <td className="px-6 py-4 text-right font-mono text-neutral-600">
                              {new Date(tx.created_at).toLocaleString()}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            )}
          </div>
        )}

      </div>

      {/* Assignment Modal */}
      {isAssignOpen && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-md rounded-3xl p-6 relative space-y-6 shadow-2xl">
            <button onClick={() => setIsAssignOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-neutral-55">Link Staff / Vendor</h3>
              <p className="text-[10px] text-neutral-500">Assign a user identity to this branch</p>
            </div>

            {assignError && (
              <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400 text-xs">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{assignError}</p>
              </div>
            )}

            <form onSubmit={handleAssignSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Assignment Role Category</label>
                <div className="grid grid-cols-2 gap-2">
                  <button
                    type="button"
                    onClick={() => { setAssignRole("Shopkeeper"); setSelectedUserId(""); }}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors cursor-pointer ${
                      assignRole === "Shopkeeper"
                        ? "bg-emerald-500 text-neutral-950 border-emerald-500"
                        : "bg-neutral-950 border-neutral-850 text-neutral-400 hover:text-neutral-200"
                    }`}
                  >
                    Shopkeeper (Staff)
                  </button>
                  <button
                    type="button"
                    onClick={() => { setAssignRole("Vendor"); setSelectedUserId(""); }}
                    className={`py-2 px-3 rounded-xl text-xs font-bold border transition-colors cursor-pointer ${
                      assignRole === "Vendor"
                        ? "bg-emerald-500 text-neutral-950 border-emerald-500"
                        : "bg-neutral-950 border-neutral-850 text-neutral-400 hover:text-neutral-200"
                    }`}
                  >
                    Vendor (Supplier)
                  </button>
                </div>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Select User</label>
                {assignableFiltered.length === 0 ? (
                  <div className="text-xs text-neutral-500 p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-center font-sans">
                    No available verified {assignRole.toLowerCase()}s found to assign.
                  </div>
                ) : (
                  <select 
                    required
                    className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-400 focus:outline-none focus:ring-2 focus:ring-emerald-500/50 text-sm" 
                    value={selectedUserId} 
                    onChange={e => setSelectedUserId(e.target.value)}
                  >
                    <option value="">Choose User...</option>
                    {assignableFiltered.map(u => (
                      <option key={u.id} value={u.id}>{u.full_name} ({u.email})</option>
                    ))}
                  </select>
                )}
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => setIsAssignOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={assignLoading || !selectedUserId}>
                  {assignLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Plus className="w-3.5 h-3.5 mr-1" />} Create Link
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Add Shelf Coordinates Modal */}
      {isAddShelfOpen && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-md rounded-3xl p-6 relative space-y-6 shadow-2xl">
            <button onClick={() => setIsAddShelfOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-neutral-50">Create Physical Shelf</h3>
              <p className="text-[10px] text-neutral-500">Configure spatial location bins for inventory scanners</p>
            </div>

            <form onSubmit={handleAddShelfSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Aisle Name *</label>
                <Input type="text" required placeholder="e.g. Aisle A" value={aisle} onChange={e => setAisle(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Shelf Level *</label>
                <Input type="text" required placeholder="e.g. Level 2" value={shelfLevel} onChange={e => setShelfLevel(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Section tag *</label>
                <Input type="text" required placeholder="e.g. Section B" value={section} onChange={e => setSection(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Bin / Rack tag *</label>
                <Input type="text" required placeholder="e.g. Cooler 1" value={binRack} onChange={e => setBinRack(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Max capacity (Items count)</label>
                <Input type="number" required value={capacity} onChange={e => setCapacity(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Operational status</label>
                <select className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300" value={shelfStatus} onChange={e => setShelfStatus(e.target.value)}>
                  <option value="active">Active</option>
                  <option value="inactive">Inactive</option>
                </select>
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => setIsAddShelfOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={shelfLoading}>
                  {shelfLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Save Shelf
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Post Stock Adjustment Modal */}
      {isPostTransactionOpen && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-md rounded-3xl p-6 relative space-y-6 shadow-2xl">
            <button onClick={() => setIsPostTransactionOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-neutral-50">Post Stock Ledger Adjustment</h3>
              <p className="text-[10px] text-neutral-500">Record stock movements and reconcile shelf counts</p>
            </div>

            <form onSubmit={handlePostTransactionSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Select Product *</label>
                <select 
                  required
                  className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 focus:outline-none text-sm" 
                  value={selectedProductId} 
                  onChange={e => setSelectedProductId(e.target.value)}
                >
                  <option value="">Choose product...</option>
                  {products.map(p => (
                    <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Transaction Type *</label>
                <select 
                  className="w-full px-3 py-2 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-sm"
                  value={transactionType}
                  onChange={e => setTransactionType(e.target.value)}
                >
                  <option value="Purchase">Purchase (+)</option>
                  <option value="Sale">Sale (-)</option>
                  <option value="Return">Return (+)</option>
                  <option value="Adjustment">Adjustment (+ / -)</option>
                  <option value="Damage">Damage (-)</option>
                  <option value="Transfer">Transfer (+ / -)</option>
                  <option value="Expiry">Expiry (-)</option>
                </select>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Quantity Change *</label>
                <Input type="number" required placeholder="e.g. +10, -5" value={qtyChange} onChange={e => setQtyChange(e.target.value)} />
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Audit Notes</label>
                <textarea rows={2} className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-250 focus:outline-none" placeholder="Reason for adjustment" value={txNotes} onChange={e => setTxNotes(e.target.value)} />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => setIsPostTransactionOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={txLoading}>
                  {txLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Post Transaction
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

    </div>
  );
}
