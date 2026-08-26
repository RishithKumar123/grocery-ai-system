"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Globe, 
  Plus, 
  Trash2, 
  Save, 
  ArrowLeft,
  Search,
  Grid,
  Info,
  Loader2,
  FolderOpen,
  Image,
  ExternalLink,
  Check,
  Upload
} from "lucide-react";
import { fetchWithAuth } from "../../../lib/auth";

export default function BrandManagementPage() {
  const [brands, setBrands] = useState<any[]>([]);
  const [selectedBrand, setSelectedBrand] = useState<any>(null);
  
  // Form states
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [origin, setOrigin] = useState("");
  const [web, setWeb] = useState("");
  const [logoUrl, setLogoUrl] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [countryFilter, setCountryFilter] = useState("");
  const [showDeleted, setShowDeleted] = useState(false);

  // Loaders
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [uploadingLogo, setUploadingLogo] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadBrands();
  }, [showDeleted, countryFilter]);

  const loadBrands = async () => {
    setLoading(true);
    try {
      let url = `/api/v1/brands?include_deleted=${showDeleted}`;
      if (countryFilter) {
        url += `&country=${encodeURIComponent(countryFilter)}`;
      }
      const res = await fetchWithAuth(url);
      if (res.ok) {
        const data = await res.json();
        setBrands(data);
      }
    } catch (err) {
      console.error("Failed to load brands", err);
    } finally {
      setLoading(false);
    }
  };

  const handleLogoUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files || e.target.files.length === 0) return;
    const file = e.target.files[0];
    
    setUploadingLogo(true);
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetchWithAuth("/api/v1/brands/upload-logo", {
        method: "POST",
        body: formData
      });
      if (res.ok) {
        const data = await res.json();
        setLogoUrl(data.logo_url);
        setSuccessMsg("Brand logo uploaded and linked successfully.");
      } else {
        alert("Failed to upload logo image.");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setUploadingLogo(false);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    const payload = {
      name,
      description: desc || null,
      logo_url: logoUrl || null,
      country_of_origin: origin || null,
      website: web || null,
      is_active: isActive
    };

    try {
      let res;
      if (isCreating) {
        res = await fetchWithAuth("/api/v1/brands", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetchWithAuth(`/api/v1/brands/${selectedBrand.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to save brand details.");
      }

      setSuccessMsg(`Brand ${isCreating ? "registered" : "updated"} successfully.`);
      setIsCreating(false);
      setIsEditing(false);
      setSelectedBrand(null);
      loadBrands();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to update brand.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to soft delete this brand?")) return;
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetchWithAuth(`/api/v1/brands/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setSuccessMsg("Brand soft-deleted successfully.");
        setSelectedBrand(null);
        setIsEditing(false);
        loadBrands();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not delete brand.");
    }
  };

  const handleRestore = async (id: number) => {
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const res = await fetchWithAuth(`/api/v1/brands/${id}/restore`, {
        method: "PATCH"
      });
      if (res.ok) {
        setSuccessMsg("Brand restored successfully.");
        loadBrands();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not restore brand.");
    }
  };

  const selectBrandForView = (brand: any) => {
    setSelectedBrand(brand);
    setIsEditing(false);
    setIsCreating(false);
    setName(brand.name);
    setDesc(brand.description || "");
    setOrigin(brand.country_of_origin || "");
    setWeb(brand.website || "");
    setLogoUrl(brand.logo_url || "");
    setIsActive(brand.is_active);
  };

  const triggerCreateNew = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedBrand(null);
    setName("");
    setDesc("");
    setOrigin("");
    setWeb("");
    setLogoUrl("");
    setIsActive(true);
  };

  // Filter local search list
  const filteredBrands = brands.filter(b => 
    b.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (b.description && b.description.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  if (loading && brands.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <span className="text-neutral-400 text-sm animate-pulse font-mono">Loading brand registry...</span>
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
              <Globe className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight">Brand Catalog Hub</h2>
              <p className="text-xs text-neutral-500">Manage manufacturing partners and origin registries</p>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
        </div>

        {/* Global Notifications */}
        {successMsg && (
          <div className="p-4 rounded-2xl border border-emerald-500/20 bg-emerald-950/20 text-emerald-400 text-xs font-semibold">
            {successMsg}
          </div>
        )}
        {errorMsg && (
          <div className="p-4 rounded-2xl border border-red-500/20 bg-red-950/20 text-red-400 text-xs font-semibold">
            {errorMsg}
          </div>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          
          {/* Column Left: Search List */}
          <div className="lg:col-span-5 space-y-4 text-xs">
            
            <div className="flex flex-col md:flex-row gap-3 items-stretch md:items-center justify-between">
              <button 
                onClick={triggerCreateNew}
                className="px-4 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 font-bold hover:bg-emerald-400 flex items-center gap-1.5 cursor-pointer text-xs"
              >
                <Plus className="w-4 h-4" /> Add New Brand
              </button>

              <label className="flex items-center gap-1.5 text-xs text-neutral-400 cursor-pointer select-none">
                <input 
                  type="checkbox" 
                  checked={showDeleted}
                  onChange={(e) => setShowDeleted(e.target.checked)}
                  className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                /> Show Deleted
              </label>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-neutral-600 absolute left-3 top-3" />
                <input 
                  type="text" 
                  placeholder="Search brand name..." 
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
              
              <select 
                className="px-3 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                value={countryFilter}
                onChange={(e) => setCountryFilter(e.target.value)}
              >
                <option value="">All Origins</option>
                <option value="UK">United Kingdom</option>
                <option value="US">United States</option>
                <option value="IN">India</option>
                <option value="CH">Switzerland</option>
              </select>
            </div>

            {/* List */}
            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-2 min-h-[350px]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-2">Registered Partners</h3>
              
              {filteredBrands.length === 0 ? (
                <div className="text-center py-12 text-neutral-500">No brand profiles match query filters.</div>
              ) : (
                <div className="space-y-2">
                  {filteredBrands.map(b => (
                    <div 
                      key={b.id} 
                      onClick={() => selectBrandForView(b)}
                      className={`p-3 rounded-xl border border-neutral-900 transition-colors flex justify-between items-center cursor-pointer ${
                        selectedBrand?.id === b.id 
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                          : b.deleted_at
                            ? "bg-neutral-900/20 border-red-950/20 text-neutral-500"
                            : "bg-neutral-950 hover:bg-neutral-900"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-neutral-900 border border-neutral-850 flex items-center justify-center text-xs overflow-hidden">
                          {b.logo_url ? <img src={b.logo_url} className="w-full h-full object-cover" /> : <Image className="w-4 h-4 text-neutral-600" />}
                        </div>
                        <div>
                          <span className="font-bold block text-xs">{b.name}</span>
                          <span className="text-[10px] text-neutral-500">{b.country_of_origin || "Global"} Origin</span>
                        </div>
                      </div>
                      
                      <div className="flex items-center gap-1.5">
                        {b.deleted_at && (
                          <button 
                            onClick={(e) => {
                              e.stopPropagation();
                              handleRestore(b.id);
                            }}
                            className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold"
                          >
                            Restore
                          </button>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Column Right: Details Editor */}
          <div className="lg:col-span-7">
            
            {!selectedBrand && !isCreating && (
              <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 text-center py-24 space-y-3">
                <Globe className="w-12 h-12 text-neutral-600 mx-auto" />
                <p className="text-xs text-neutral-500">Select a brand from the list to view specifications or update logo files.</p>
              </div>
            )}

            {(selectedBrand || isCreating) && (
              <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
                
                {/* Editor Header */}
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400">
                    {isCreating ? "New Brand Registration" : `Partner Profile: ${selectedBrand.name}`}
                  </h3>
                  
                  {!isCreating && (
                    <button 
                      onClick={() => handleDelete(selectedBrand.id)}
                      className="p-2 text-neutral-500 hover:text-red-400 hover:bg-neutral-900 rounded-xl"
                      title="Soft Delete Brand"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <form onSubmit={handleSave} className="space-y-4 text-xs">
                  
                  {/* Logo upload panel */}
                  <div className="flex items-center gap-4 p-4 rounded-2xl bg-neutral-950 border border-neutral-900">
                    <div className="w-16 h-16 rounded-xl bg-neutral-900 border border-neutral-850 flex items-center justify-center overflow-hidden">
                      {logoUrl ? <img src={logoUrl} className="w-full h-full object-cover" /> : <Image className="w-6 h-6 text-neutral-600" />}
                    </div>
                    
                    <div className="space-y-1">
                      <label className="px-3 py-1.5 rounded-lg border border-neutral-800 text-[10px] font-bold text-neutral-300 hover:border-neutral-700 cursor-pointer flex items-center gap-1">
                        <Upload className="w-3 h-3" /> Upload Logo Image
                        <input type="file" className="hidden" accept="image/*" onChange={handleLogoUpload} />
                      </label>
                      {uploadingLogo && <span className="text-[10px] text-emerald-400 animate-pulse block">Uploading logo blob...</span>}
                      <span className="text-[9px] text-neutral-500 block">Linked URL: {logoUrl || "None"}</span>
                    </div>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Brand Name</label>
                      <input 
                        type="text" 
                        required
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Country of Origin</label>
                      <input 
                        type="text" 
                        placeholder="e.g. UK, US, IN"
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={origin}
                        onChange={(e) => setOrigin(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-1 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Official Website</label>
                      <input 
                        type="url" 
                        placeholder="https://example.com"
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={web}
                        onChange={(e) => setWeb(e.target.value)}
                      />
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Partner Description</label>
                    <textarea 
                      className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200 h-24"
                      value={desc}
                      onChange={(e) => setDesc(e.target.value)}
                    />
                  </div>

                  <div className="flex items-center gap-2 py-2">
                    <input 
                      type="checkbox" 
                      id="brandActive"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                    />
                    <label htmlFor="brandActive" className="text-neutral-300 font-bold select-none cursor-pointer">Active supply status</label>
                  </div>

                  <button
                    type="submit"
                    disabled={saving}
                    className="px-5 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save Partner details
                  </button>

                </form>

              </div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}
