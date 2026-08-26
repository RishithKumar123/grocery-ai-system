"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Folder, 
  ChevronRight, 
  ChevronDown, 
  Plus, 
  Trash2, 
  RefreshCw, 
  Edit3, 
  Save, 
  ArrowLeft,
  Search,
  Grid,
  Info,
  Loader2,
  FolderOpen,
  Eye,
  AlertTriangle
} from "lucide-react";
import { fetchWithAuth } from "../../../lib/auth";

export default function CategoryManagementPage() {
  // Category list state
  const [categories, setCategories] = useState<any[]>([]);
  const [roots, setRoots] = useState<any[]>([]);
  
  // Selection and editor states
  const [selectedCategory, setSelectedCategory] = useState<any>(null);
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  
  // Form values
  const [name, setName] = useState("");
  const [desc, setDesc] = useState("");
  const [parentId, setParentId] = useState<number | "">("");
  const [imgUrl, setImgUrl] = useState("");
  const [iconName, setIconName] = useState("");
  const [isActive, setIsActive] = useState(true);
  const [orderIdx, setOrderIdx] = useState(0);

  // Tree expansion state
  const [expandedNodes, setExpandedNodes] = useState<Record<number, boolean>>({});
  
  // Search / filters
  const [searchQuery, setSearchQuery] = useState("");
  const [showDeleted, setShowDeleted] = useState(false);

  // Loaders
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  useEffect(() => {
    loadCategories();
  }, [showDeleted]);

  const loadCategories = async () => {
    setLoading(true);
    try {
      const url = `/api/v1/categories?include_deleted=${showDeleted}`;
      const res = await fetchWithAuth(url);
      if (res.ok) {
        const data = await res.json();
        setCategories(data);
        
        // Group by roots
        const rootsList = data.filter((c: any) => c.parent_id === null);
        setRoots(rootsList);
      }
    } catch (err) {
      console.error("Failed to load categories", err);
    } finally {
      setLoading(false);
    }
  };

  const getSubcategories = (parent_id: number) => {
    return categories.filter(c => c.parent_id === parent_id);
  };

  const toggleNode = (nodeId: number) => {
    setExpandedNodes(prev => ({
      ...prev,
      [nodeId]: !prev[nodeId]
    }));
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    const payload = {
      name,
      description: desc || null,
      parent_id: parentId === "" ? null : parentId,
      image_url: imgUrl || null,
      icon_name: iconName || null,
      is_active: isActive,
      order_index: orderIdx
    };

    try {
      let res;
      if (isCreating) {
        res = await fetchWithAuth("/api/v1/categories", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetchWithAuth(`/api/v1/categories/${selectedCategory.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update category.");
      }

      setSuccessMsg(`Category ${isCreating ? "registered" : "updated"} successfully.`);
      setIsCreating(false);
      setIsEditing(false);
      setSelectedCategory(null);
      loadCategories();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save category specifications.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to soft delete this category?")) return;
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetchWithAuth(`/api/v1/categories/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setSuccessMsg("Category soft-deleted successfully.");
        setSelectedCategory(null);
        setIsEditing(false);
        loadCategories();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not delete category.");
    }
  };

  const handleRestore = async (id: number) => {
    setSuccessMsg(null);
    setErrorMsg(null);
    try {
      const res = await fetchWithAuth(`/api/v1/categories/${id}/restore`, {
        method: "PATCH"
      });
      if (res.ok) {
        setSuccessMsg("Category restored successfully.");
        loadCategories();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not restore category.");
    }
  };

  const selectCategoryForView = (cat: any) => {
    setSelectedCategory(cat);
    setIsEditing(false);
    setIsCreating(false);
    setName(cat.name);
    setDesc(cat.description || "");
    setParentId(cat.parent_id || "");
    setImgUrl(cat.image_url || "");
    setIconName(cat.icon_name || "");
    setIsActive(cat.is_active);
    setOrderIdx(cat.order_index);
  };

  const triggerCreateNew = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedCategory(null);
    setName("");
    setDesc("");
    setParentId("");
    setImgUrl("");
    setIconName("");
    setIsActive(true);
    setOrderIdx(0);
  };

  // Render tree node recursive
  const renderCategoryNode = (cat: any, depth = 0) => {
    const children = getSubcategories(cat.id);
    const hasChildren = children.length > 0;
    const isExpanded = expandedNodes[cat.id];

    return (
      <div key={cat.id} className="space-y-1">
        <div 
          onClick={() => selectCategoryForView(cat)}
          style={{ paddingLeft: `${depth * 16}px` }}
          className={`flex items-center justify-between p-3 rounded-xl border border-neutral-900 transition-colors cursor-pointer ${
            selectedCategory?.id === cat.id 
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : cat.deleted_at
                ? "bg-neutral-900/20 border-red-950/20 text-neutral-500"
                : "bg-neutral-950 hover:bg-neutral-900"
          }`}
        >
          <div className="flex items-center gap-2">
            {hasChildren && (
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  toggleNode(cat.id);
                }}
                className="p-0.5 rounded text-neutral-500 hover:text-neutral-300"
              >
                {isExpanded ? <ChevronDown className="w-3.5 h-3.5" /> : <ChevronRight className="w-3.5 h-3.5" />}
              </button>
            )}
            {!hasChildren && <div className="w-4.5" />}
            <Folder className={`w-4 h-4 ${cat.deleted_at ? 'text-red-500/40' : 'text-emerald-500/60'}`} />
            <span className="text-xs font-semibold">{cat.name}</span>
          </div>

          <div className="flex items-center gap-1.5">
            {cat.deleted_at && (
              <button 
                onClick={(e) => {
                  e.stopPropagation();
                  handleRestore(cat.id);
                }}
                className="px-2 py-0.5 rounded bg-emerald-500/10 border border-emerald-500/20 text-emerald-400 text-[9px] font-bold"
              >
                Restore
              </button>
            )}
            <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono ${cat.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-neutral-900 text-neutral-500'}`}>
              {cat.is_active ? "Active" : "Inactive"}
            </span>
          </div>
        </div>

        {hasChildren && isExpanded && (
          <div className="space-y-1 mt-1">
            {children.map(child => renderCategoryNode(child, depth + 1))}
          </div>
        )}
      </div>
    );
  };

  if (loading && categories.length === 0) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-neutral-950">
        <span className="text-neutral-400 text-sm animate-pulse font-mono">Indexing hierarchy catalog...</span>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Header Block */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <FolderOpen className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight">Category Tree Manager</h2>
              <p className="text-xs text-neutral-500">Configure multi-nested parent/child groupings</p>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
        </div>

        {/* Global Notifications Banners */}
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
          
          {/* Column Left: Hierarchical Tree Navigation */}
          <div className="lg:col-span-5 space-y-4">
            
            <div className="flex justify-between items-center gap-4">
              <button 
                onClick={triggerCreateNew}
                className="px-4 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 transition-colors flex items-center gap-1.5 cursor-pointer"
              >
                <Plus className="w-4 h-4" /> Create Category
              </button>

              <label className="flex items-center gap-1.5 text-xs text-neutral-400 cursor-pointer">
                <input 
                  type="checkbox" 
                  checked={showDeleted}
                  onChange={(e) => setShowDeleted(e.target.checked)}
                  className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                /> Show Deleted
              </label>
            </div>

            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4 min-h-[400px]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400">Category Catalog Hierarchy</h3>
              
              {roots.length === 0 ? (
                <div className="text-center py-12 text-xs text-neutral-500">No categories found. Create a parent node first.</div>
              ) : (
                <div className="space-y-2">
                  {roots.map(root => renderCategoryNode(root))}
                </div>
              )}
            </div>

          </div>

          {/* Column Right: Active Editor / Details Viewer */}
          <div className="lg:col-span-7">
            
            {!selectedCategory && !isCreating && (
              <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 text-center py-24 space-y-3">
                <Folder className="w-12 h-12 text-neutral-600 mx-auto" />
                <p className="text-xs text-neutral-500">Select a category node on the left to edit or manage properties.</p>
              </div>
            )}

            {(selectedCategory || isCreating) && (
              <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
                
                {/* Editor Header */}
                <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                  <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400">
                    {isCreating ? "New Category Registration" : `Editing: ${selectedCategory.name}`}
                  </h3>
                  
                  {!isCreating && (
                    <button 
                      onClick={() => handleDelete(selectedCategory.id)}
                      className="p-2 text-neutral-500 hover:text-red-400 hover:bg-neutral-900 rounded-xl"
                      title="Soft Delete Category"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  )}
                </div>

                <form onSubmit={handleSave} className="space-y-4 text-xs">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Category Name</label>
                      <input 
                        type="text" 
                        required
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={name}
                        onChange={(e) => setName(e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Parent Assignment</label>
                      <select 
                        className="w-full px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={parentId}
                        onChange={(e) => setParentId(e.target.value === "" ? "" : Number(e.target.value))}
                      >
                        <option value="">[None - Root Category]</option>
                        {categories
                          .filter(c => !isCreating ? c.id !== selectedCategory.id : true)
                          .map(c => (
                            <option key={c.id} value={c.id}>{c.name}</option>
                          ))
                        }
                      </select>
                    </div>
                  </div>

                  <div>
                    <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Description</label>
                    <textarea 
                      className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200 h-20"
                      value={desc}
                      onChange={(e) => setDesc(e.target.value)}
                    />
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Order Weight</label>
                      <input 
                        type="number" 
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={orderIdx}
                        onChange={(e) => setOrderIdx(Number(e.target.value))}
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Icon Reference</label>
                      <input 
                        type="text" 
                        placeholder="e.g. coffee, milk"
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={iconName}
                        onChange={(e) => setIconName(e.target.value)}
                      />
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Cover Image URL</label>
                      <input 
                        type="text" 
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200"
                        value={imgUrl}
                        onChange={(e) => setImgUrl(e.target.value)}
                      />
                    </div>
                  </div>

                  <div className="flex items-center gap-2 py-2">
                    <input 
                      type="checkbox" 
                      id="catActive"
                      checked={isActive}
                      onChange={(e) => setIsActive(e.target.checked)}
                      className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                    />
                    <label htmlFor="catActive" className="text-neutral-300 font-bold select-none cursor-pointer">Active in store catalog</label>
                  </div>

                  <button
                    type="submit"
                    disabled={saving}
                    className="px-5 py-2.5 rounded-xl bg-emerald-500 text-neutral-950 text-xs font-bold hover:bg-emerald-400 flex items-center gap-1.5 disabled:opacity-50 cursor-pointer"
                  >
                    {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save Specifications
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
