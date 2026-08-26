"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { 
  Building2, 
  MapPin, 
  Users, 
  Truck, 
  Boxes, 
  ArrowLeft, 
  Plus, 
  Edit3, 
  Trash2, 
  ArrowRight, 
  Loader2, 
  X, 
  Save,
  BarChart3,
  AlertCircle,
  Phone,
  Clock,
  Settings,
  ToggleLeft
} from "lucide-react";
import { getAccessToken, fetchWithAuth, clearTokens } from "../../lib/auth";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { useToast } from "../../components/ui/toast";

interface Store {
  id: number;
  name: string;
  location: string | null;
  address: string | null;
  contact: string | null;
  timezone: string;
  is_active: boolean;
  settings: string | null;
  total_stock: number;
  employee_count: number;
  vendor_count: number;
  created_at: string;
  updated_at: string;
}

export default function StoresPage() {
  const router = useRouter();
  const { toast } = useToast();
  
  const [stores, setStores] = useState<Store[]>([]);
  const [loading, setLoading] = useState(true);

  // Modals state
  const [isAddOpen, setIsAddOpen] = useState(false);
  const [isEditOpen, setIsEditOpen] = useState(false);
  const [selectedStore, setSelectedStore] = useState<Store | null>(null);

  // Form Fields State
  const [name, setName] = useState("");
  const [location, setLocation] = useState("");
  const [address, setAddress] = useState("");
  const [contact, setContact] = useState("");
  const [timezone, setTimezone] = useState("UTC");
  const [isActive, setIsActive] = useState(true);
  const [settings, setSettings] = useState("{}");

  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [formLoading, setFormLoading] = useState(false);

  useEffect(() => {
    const token = getAccessToken();
    if (!token) {
      clearTokens();
      router.push("/login");
      return;
    }
    loadStores();
  }, [router]);

  const loadStores = async () => {
    setLoading(true);
    try {
      const res = await fetchWithAuth("/api/v1/stores");
      if (res.ok) {
        const data = await res.json();
        setStores(data);
      }
    } catch (err) {
      console.error("Failed to load stores", err);
    } finally {
      setLoading(false);
    }
  };

  const handleAddSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg(null);
    setFormLoading(true);

    try {
      const res = await fetchWithAuth("/api/v1/stores", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          name, 
          location: location || null,
          address: address || null,
          contact: contact || null,
          timezone,
          is_active: isActive,
          settings: settings || "{}"
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || "Failed to create store branch.");
      }

      setIsAddOpen(false);
      resetForm();
      toast({ title: "Branch Registered", description: "Successfully added new outlet branch.", type: "success" });
      loadStores();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  const openEditModal = (s: Store) => {
    setSelectedStore(s);
    setName(s.name);
    setLocation(s.location || "");
    setAddress(s.address || "");
    setContact(s.contact || "");
    setTimezone(s.timezone || "UTC");
    setIsActive(s.is_active);
    setSettings(s.settings || "{}");
    setIsEditOpen(true);
  };

  const handleEditSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedStore) return;
    setErrorMsg(null);
    setFormLoading(true);

    try {
      const res = await fetchWithAuth(`/api/v1/stores/${selectedStore.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          name, 
          location: location || null,
          address: address || null,
          contact: contact || null,
          timezone,
          is_active: isActive,
          settings: settings || "{}"
        })
      });

      if (!res.ok) {
        const errData = await res.json().catch(() => ({}));
        throw new Error(errData?.error?.message || "Failed to update store branch.");
      }

      setIsEditOpen(false);
      resetForm();
      toast({ title: "Branch Settings Saved", description: "Updated parameters successfully.", type: "success" });
      loadStores();
    } catch (err: any) {
      setErrorMsg(err.message);
    } finally {
      setFormLoading(false);
    }
  };

  const handleDeleteStore = async (id: number) => {
    if (!confirm("Are you sure you want to delete this branch? All corresponding inventories, cameras, and order records will be permanently removed.")) return;
    try {
      const res = await fetchWithAuth(`/api/v1/stores/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        toast({ title: "Branch Deleted", description: "Purged branch logs from active network.", type: "success" });
        loadStores();
      }
    } catch (err) {
      console.error("Failed to delete store", err);
    }
  };

  const resetForm = () => {
    setName("");
    setLocation("");
    setAddress("");
    setContact("");
    setTimezone("UTC");
    setIsActive(true);
    setSettings("{}");
    setErrorMsg(null);
    setSelectedStore(null);
  };

  const totalBranches = stores.length;
  const maxStock = Math.max(...stores.map(s => s.total_stock), 1);

  return (
    <div className="min-h-screen bg-neutral-950 flex flex-col px-4 py-12 text-xs">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Header Navbar */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Building2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight text-neutral-100">Store & Branch Network</h2>
              <p className="text-xs text-neutral-500 font-sans">Monitor metrics and assign employees to retail outlets</p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
              <ArrowLeft className="w-3.5 h-3.5" /> Back
            </Link>
            <Button variant="primary" size="sm" onClick={() => { resetForm(); setIsAddOpen(true); }}>
              <Plus className="w-3.5 h-3.5 mr-1" /> Add Store Branch
            </Button>
          </div>
        </div>

        {/* Analytics Summary */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Building2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Active branches</p>
              <h3 className="text-lg font-black text-neutral-200">{totalBranches} Locations</h3>
            </div>
          </div>
          
          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Users className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Total Staff Linkages</p>
              <h3 className="text-lg font-black text-neutral-200">
                {stores.reduce((acc, s) => acc + s.employee_count, 0)} Employees
              </h3>
            </div>
          </div>

          <div className="bg-neutral-900/40 border border-neutral-900 p-5 rounded-2xl flex items-center gap-4">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 border border-emerald-500/20 flex items-center justify-center">
              <Truck className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <p className="text-[10px] uppercase font-bold text-neutral-500 font-mono">Contracted Vendors</p>
              <h3 className="text-lg font-black text-neutral-200">
                {stores.reduce((acc, s) => acc + s.vendor_count, 0)} Providers
              </h3>
            </div>
          </div>
        </div>

        {/* Store Branches Grid */}
        {loading ? (
          <div className="flex justify-center items-center py-20">
            <Loader2 className="w-8 h-8 text-emerald-400 animate-spin" />
          </div>
        ) : stores.length === 0 ? (
          <div className="text-center py-20 border border-neutral-900 rounded-3xl bg-neutral-900/10 space-y-3">
            <Building2 className="w-12 h-12 text-neutral-700 mx-auto" />
            <h3 className="font-bold text-neutral-300">No branches registered</h3>
            <p className="text-neutral-500 max-w-sm mx-auto">Create a retail branch to configure camera scanners and assign employees.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {stores.map(s => (
              <div key={s.id} className={`p-6 rounded-3xl border flex flex-col justify-between space-y-6 hover:border-neutral-800 transition-all group ${s.is_active ? 'bg-neutral-900/20 border-neutral-900' : 'bg-neutral-900/10 border-neutral-950 opacity-60'}`}>
                <div className="space-y-4">
                  <div className="flex justify-between items-start">
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <h3 className="text-sm font-bold text-neutral-100 group-hover:text-emerald-400 transition-colors">{s.name}</h3>
                        <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono ${s.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-neutral-900 text-neutral-500'}`}>
                          {s.is_active ? "Active" : "Inactive"}
                        </span>
                      </div>
                      
                      <div className="flex items-center gap-1.5 text-neutral-400">
                        <MapPin className="w-3.5 h-3.5 text-emerald-400/80 shrink-0" />
                        <span>{s.address || s.location || "Address unconfigured"}</span>
                      </div>

                      {s.contact && (
                        <div className="flex items-center gap-1.5 text-neutral-500">
                          <Phone className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
                          <span>{s.contact}</span>
                        </div>
                      )}

                      <div className="flex items-center gap-1.5 text-neutral-500">
                        <Clock className="w-3.5 h-3.5 text-neutral-600 shrink-0" />
                        <span>Timezone: {s.timezone}</span>
                      </div>
                    </div>
                    
                    <div className="flex gap-2">
                      <button
                        onClick={() => openEditModal(s)}
                        className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/30 text-neutral-400 hover:text-emerald-400 transition-colors cursor-pointer"
                        title="Edit Branch Settings"
                      >
                        <Edit3 className="w-3.5 h-3.5" />
                      </button>
                      <button
                        onClick={() => handleDeleteStore(s.id)}
                        className="p-2 rounded-xl border border-neutral-900 bg-neutral-900/30 text-neutral-400 hover:text-red-400 transition-colors cursor-pointer"
                        title="Delete Branch"
                      >
                        <Trash2 className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>

                  {/* Quick stats row */}
                  <div className="grid grid-cols-3 gap-3 pt-2">
                    <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-center">
                      <span className="text-[10px] text-neutral-500 font-semibold block uppercase font-mono">Stock</span>
                      <span className="text-sm font-bold text-neutral-200 mt-1 block">{s.total_stock}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-center">
                      <span className="text-[10px] text-neutral-500 font-semibold block uppercase font-mono">Staff</span>
                      <span className="text-sm font-bold text-neutral-200 mt-1 block">{s.employee_count}</span>
                    </div>
                    <div className="p-3 rounded-xl bg-neutral-950 border border-neutral-900 text-center">
                      <span className="text-[10px] text-neutral-500 font-semibold block uppercase font-mono">Vendors</span>
                      <span className="text-sm font-bold text-neutral-200 mt-1 block">{s.vendor_count}</span>
                    </div>
                  </div>
                </div>

                <div className="border-t border-neutral-900/60 pt-4 flex justify-between items-center">
                  <span className="text-[10px] text-neutral-500 font-mono uppercase">ID: BR-{s.id}</span>
                  <Link
                    href={`/stores/${s.id}`}
                    className="flex items-center gap-1.5 font-semibold text-emerald-400 hover:text-emerald-300 transition-colors group/link"
                  >
                    View Branch Dashboard 
                    <ArrowRight className="w-3.5 h-3.5 group-hover/link:translate-x-0.5 transition-transform" />
                  </Link>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Store Network Analytics */}
        {stores.length > 0 && (
          <div className="bg-neutral-900/20 p-6 rounded-3xl border border-neutral-900 space-y-6">
            <h3 className="font-bold text-neutral-250 flex items-center gap-2">
              <BarChart3 className="w-5 h-5 text-emerald-400" />
              Store Network Analytics
            </h3>
            <div className="space-y-4">
              {stores.map(s => {
                const stockPercentage = Math.round((s.total_stock / maxStock) * 100);
                return (
                  <div key={s.id} className="space-y-2">
                    <div className="flex justify-between text-xs">
                      <span className="font-semibold text-neutral-300">{s.name}</span>
                      <span className="text-neutral-400 font-mono">{s.total_stock} stock units ({stockPercentage}%)</span>
                    </div>
                    <div className="h-2 w-full rounded-full bg-neutral-950 overflow-hidden border border-neutral-900">
                      <div 
                        className="h-full bg-emerald-500 rounded-full transition-all duration-500" 
                        style={{ width: `${stockPercentage}%` }}
                      />
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}
      </div>

      {/* Add Branch Modal */}
      {isAddOpen && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-md rounded-3xl p-6 relative space-y-6 shadow-2xl">
            <button onClick={() => setIsAddOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-neutral-50">Add Store Branch</h3>
              <p className="text-[10px] text-neutral-500">Introduce a new branch location</p>
            </div>

            {errorMsg && (
              <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}

            <form onSubmit={handleAddSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Branch Name *</label>
                <Input type="text" required value={name} onChange={e => setName(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Location Region</label>
                <Input type="text" placeholder="e.g. North Metropolis" value={location} onChange={e => setLocation(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Street Address</label>
                <Input type="text" placeholder="e.g. 100 Main St" value={address} onChange={e => setAddress(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Contact Number / Email</label>
                <Input type="text" placeholder="e.g. +1-555-0199" value={contact} onChange={e => setContact(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Timezone *</label>
                <Input type="text" required value={timezone} onChange={e => setTimezone(e.target.value)} />
              </div>
              
              <div className="flex items-center gap-2 py-2">
                <input 
                  type="checkbox" 
                  id="storeActive"
                  checked={isActive}
                  onChange={e => setIsActive(e.target.checked)}
                  className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                />
                <label htmlFor="storeActive" className="text-neutral-300 font-bold select-none cursor-pointer">Active branch status</label>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Custom Low-Stock Settings (JSON)</label>
                <textarea rows={2} className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-250 focus:outline-none" value={settings} onChange={e => setSettings(e.target.value)} />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => setIsAddOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={formLoading}>
                  {formLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Save Branch
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Edit Branch Modal */}
      {isEditOpen && selectedStore && (
        <div className="fixed inset-0 bg-neutral-950/80 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-neutral-950 border border-neutral-900 w-full max-w-md rounded-3xl p-6 relative space-y-6 shadow-2xl">
            <button onClick={() => setIsEditOpen(false)} className="absolute right-6 top-6 p-1.5 rounded-xl border border-neutral-900 text-neutral-500 hover:text-neutral-200 transition-colors">
              <X className="w-4 h-4" />
            </button>
            <div>
              <h3 className="text-base font-bold text-neutral-50">Edit Branch Details</h3>
              <p className="text-[10px] text-neutral-500">Update configuration settings</p>
            </div>

            {errorMsg && (
              <div className="flex items-center gap-2 p-4 rounded-xl border border-red-500/20 bg-red-950/20 text-red-400">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <p>{errorMsg}</p>
              </div>
            )}

            <form onSubmit={handleEditSubmit} className="space-y-4">
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Branch Name *</label>
                <Input type="text" required value={name} onChange={e => setName(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Location Region</label>
                <Input type="text" value={location} onChange={e => setLocation(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Street Address</label>
                <Input type="text" value={address} onChange={e => setAddress(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Contact Number / Email</label>
                <Input type="text" value={contact} onChange={e => setContact(e.target.value)} />
              </div>
              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Timezone *</label>
                <Input type="text" required value={timezone} onChange={e => setTimezone(e.target.value)} />
              </div>
              
              <div className="flex items-center gap-2 py-2">
                <input 
                  type="checkbox" 
                  id="storeActiveEdit"
                  checked={isActive}
                  onChange={e => setIsActive(e.target.checked)}
                  className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                />
                <label htmlFor="storeActiveEdit" className="text-neutral-300 font-bold select-none cursor-pointer">Active branch status</label>
              </div>

              <div>
                <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Custom Low-Stock Settings (JSON)</label>
                <textarea rows={2} className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-250 focus:outline-none" value={settings} onChange={e => setSettings(e.target.value)} />
              </div>

              <div className="flex justify-end gap-3 pt-4 border-t border-neutral-900">
                <Button variant="ghost" onClick={() => setIsEditOpen(false)}>Cancel</Button>
                <Button type="submit" disabled={formLoading}>
                  {formLoading ? <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" /> : <Save className="w-3.5 h-3.5 mr-1" />} Save Updates
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
