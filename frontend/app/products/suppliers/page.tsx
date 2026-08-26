"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { 
  Building2, 
  Plus, 
  Trash2, 
  Save, 
  ArrowLeft,
  Search,
  Grid,
  Info,
  Loader2,
  Phone,
  Mail,
  MapPin,
  FileText,
  DollarSign,
  User,
  Link2,
  Unlink
} from "lucide-react";
import { fetchWithAuth } from "../../../lib/auth";
import { Button } from "../../../components/ui/button";
import { Input } from "../../../components/ui/input";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "../../../components/ui/card";
import { Drawer } from "../../../components/ui/drawer";
import { useToast } from "../../../components/ui/toast";

export default function SupplierManagementPage() {
  const { toast } = useToast();
  const [suppliers, setSuppliers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [selectedSupplier, setSelectedSupplier] = useState<any>(null);
  
  // Linked products list for selected supplier
  const [linkedProducts, setLinkedProducts] = useState<any[]>([]);
  const [productToLink, setProductToLink] = useState<string>("");

  // Form states
  const [isEditing, setIsEditing] = useState(false);
  const [isCreating, setIsCreating] = useState(false);
  const [name, setName] = useState("");
  const [companyName, setCompanyName] = useState("");
  const [contactPerson, setContactPerson] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [address, setAddress] = useState("");
  const [gstVat, setGstVat] = useState("");
  const [region, setRegion] = useState("");
  const [paymentTerms, setPaymentTerms] = useState("");
  const [isActive, setIsActive] = useState(true);

  // Filters
  const [searchQuery, setSearchQuery] = useState("");
  const [regionFilter, setRegionFilter] = useState("");
  const [activeFilter, setActiveFilter] = useState<string>("");

  // Loaders
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [linking, setLinking] = useState(false);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Link drawer trigger
  const [linkDrawerOpen, setLinkDrawerOpen] = useState(false);

  useEffect(() => {
    loadSuppliers();
    loadAllProducts();
  }, [regionFilter, activeFilter]);

  const loadSuppliers = async () => {
    setLoading(true);
    try {
      let url = `/api/v1/suppliers?`;
      if (regionFilter) url += `region=${encodeURIComponent(regionFilter)}&`;
      if (activeFilter !== "") url += `is_active=${activeFilter === "true"}&`;
      
      const res = await fetchWithAuth(url);
      if (res.ok) {
        const data = await res.json();
        setSuppliers(data);
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadAllProducts = async () => {
    try {
      const res = await fetchWithAuth("/api/v1/products");
      if (res.ok) {
        const data = await res.json();
        setProducts(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const loadLinkedProducts = async (supId: number) => {
    try {
      const res = await fetchWithAuth(`/api/v1/suppliers/${supId}/products`);
      if (res.ok) {
        const data = await res.json();
        setLinkedProducts(data);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const handleSave = async (e: React.FormEvent) => {
    e.preventDefault();
    setSaving(true);
    setSuccessMsg(null);
    setErrorMsg(null);

    const payload = {
      name,
      company_name: companyName || null,
      contact_person: contactPerson || null,
      contact_email: email || null,
      phone: phone || null,
      address: address || null,
      gst_vat: gstVat || null,
      region: region || null,
      payment_terms: paymentTerms || null,
      is_active: isActive
    };

    try {
      let res;
      if (isCreating) {
        res = await fetchWithAuth("/api/v1/suppliers", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      } else {
        res = await fetchWithAuth(`/api/v1/suppliers/${selectedSupplier.id}`, {
          method: "PUT",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload)
        });
      }

      if (!res.ok) {
        const data = await res.json();
        throw new Error(data.detail || "Failed to update supplier.");
      }

      setSuccessMsg(`Supplier ${isCreating ? "registered" : "updated"} successfully.`);
      setIsCreating(false);
      setIsEditing(false);
      setSelectedSupplier(null);
      loadSuppliers();
    } catch (err: any) {
      setErrorMsg(err.message || "Failed to save supplier profile.");
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm("Are you sure you want to delete this supplier profile?")) return;
    setSuccessMsg(null);
    setErrorMsg(null);

    try {
      const res = await fetchWithAuth(`/api/v1/suppliers/${id}`, {
        method: "DELETE"
      });
      if (res.ok) {
        setSuccessMsg("Supplier deleted successfully.");
        setSelectedSupplier(null);
        setIsEditing(false);
        loadSuppliers();
      }
    } catch (err: any) {
      setErrorMsg(err.message || "Could not delete supplier.");
    }
  };

  const handleLinkProduct = async () => {
    if (!productToLink || !selectedSupplier) return;
    setLinking(true);
    try {
      const res = await fetchWithAuth(`/api/v1/suppliers/${selectedSupplier.id}/products/${productToLink}`, {
        method: "POST"
      });
      if (res.ok) {
        toast({ title: "Product mapped", description: "Product associated to supplier.", type: "success" });
        loadLinkedProducts(selectedSupplier.id);
        setProductToLink("");
      }
    } catch (err) {
      console.error(err);
    } finally {
      setLinking(false);
    }
  };

  const handleUnlinkProduct = async (prodId: number) => {
    if (!selectedSupplier) return;
    try {
      const res = await fetchWithAuth(`/api/v1/suppliers/${selectedSupplier.id}/products/${prodId}`, {
        method: "DELETE"
      });
      if (res.ok) {
        loadLinkedProducts(selectedSupplier.id);
      }
    } catch (err) {
      console.error(err);
    }
  };

  const selectSupplierForView = (sup: any) => {
    setSelectedSupplier(sup);
    setIsEditing(false);
    setIsCreating(false);
    setName(sup.name);
    setCompanyName(sup.company_name || "");
    setContactPerson(sup.contact_person || "");
    setEmail(sup.contact_email || "");
    setPhone(sup.phone || "");
    setAddress(sup.address || "");
    setGstVat(sup.gst_vat || "");
    setRegion(sup.region || "");
    setPaymentTerms(sup.payment_terms || "");
    setIsActive(sup.is_active);

    loadLinkedProducts(sup.id);
  };

  const triggerCreateNew = () => {
    setIsCreating(true);
    setIsEditing(false);
    setSelectedSupplier(null);
    setName("");
    setCompanyName("");
    setContactPerson("");
    setEmail("");
    setPhone("");
    setAddress("");
    setGstVat("");
    setRegion("");
    setPaymentTerms("");
    setIsActive(true);
    setLinkedProducts([]);
  };

  const filteredSuppliers = suppliers.filter(s => 
    s.name.toLowerCase().includes(searchQuery.toLowerCase()) || 
    (s.company_name && s.company_name.toLowerCase().includes(searchQuery.toLowerCase())) ||
    (s.contact_person && s.contact_person.toLowerCase().includes(searchQuery.toLowerCase()))
  );

  return (
    <div className="min-h-screen bg-neutral-950 text-neutral-100 flex flex-col px-4 py-12">
      <div className="absolute top-1/4 left-1/4 w-80 h-80 bg-emerald-500/5 rounded-full blur-[120px] pointer-events-none" />

      <div className="w-full max-w-6xl mx-auto space-y-8 relative z-10">
        
        {/* Header console */}
        <div className="flex items-center justify-between border-b border-neutral-900 pb-5">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-2xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20">
              <Building2 className="w-5 h-5 text-emerald-400" />
            </div>
            <div>
              <h2 className="text-2xl font-extrabold tracking-tight">Suppliers & Vendors</h2>
              <p className="text-xs text-neutral-500">Configure global supply parameters and tax categories</p>
            </div>
          </div>
          <Link href="/dashboard" className="inline-flex items-center gap-1.5 text-xs text-neutral-400 hover:text-emerald-400 transition-colors font-bold">
            <ArrowLeft className="w-3.5 h-3.5" /> Back to Dashboard
          </Link>
        </div>

        {/* Notifiers */}
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
          
          {/* Column Left: Filters & Search list */}
          <div className="lg:col-span-5 space-y-4 text-xs">
            
            <div className="flex justify-between items-center">
              <Button variant="primary" onClick={triggerCreateNew}>
                <Plus className="w-4 h-4" /> Add Supplier
              </Button>
            </div>

            <div className="flex gap-2">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-neutral-600 absolute left-3 top-3" />
                <input 
                  type="text" 
                  placeholder="Search name, contact, company..." 
                  className="w-full pl-9 pr-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                />
              </div>
            </div>

            <div className="grid grid-cols-2 gap-2">
              <select 
                className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                value={regionFilter}
                onChange={(e) => setRegionFilter(e.target.value)}
              >
                <option value="">All Regions</option>
                <option value="US">United States (US)</option>
                <option value="EU">European Union (EU)</option>
                <option value="IN">India (IN)</option>
              </select>

              <select 
                className="px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300"
                value={activeFilter}
                onChange={(e) => setActiveFilter(e.target.value)}
              >
                <option value="">All Statuses</option>
                <option value="true">Active Only</option>
                <option value="false">Inactive Only</option>
              </select>
            </div>

            {/* List */}
            <div className="p-5 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-2 min-h-[350px]">
              <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-400 mb-2 font-mono">Registered Suppliers</h3>
              
              {filteredSuppliers.length === 0 ? (
                <div className="text-center py-12 text-neutral-500 font-mono">No supplier records match filters.</div>
              ) : (
                <div className="space-y-2">
                  {filteredSuppliers.map(s => (
                    <div 
                      key={s.id} 
                      onClick={() => selectSupplierForView(s)}
                      className={`p-3 rounded-xl border border-neutral-900 transition-colors flex justify-between items-center cursor-pointer ${
                        selectedSupplier?.id === s.id 
                          ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                          : s.is_active === false
                            ? "opacity-50"
                            : "bg-neutral-950 hover:bg-neutral-900"
                      }`}
                    >
                      <div>
                        <span className="font-bold block text-xs">{s.name}</span>
                        <span className="text-[10px] text-neutral-500">{s.company_name || "No company details"}</span>
                      </div>
                      
                      <span className={`px-1.5 py-0.5 rounded text-[8px] font-mono ${s.is_active ? 'bg-emerald-950 text-emerald-400' : 'bg-neutral-900 text-neutral-500'}`}>
                        {s.is_active ? "Active" : "Inactive"}
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>

          </div>

          {/* Column Right: Supplier Details / Linkage drawer */}
          <div className="lg:col-span-7">
            
            {!selectedSupplier && !isCreating && (
              <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 text-center py-24 space-y-3">
                <Building2 className="w-12 h-12 text-neutral-600 mx-auto" />
                <p className="text-xs text-neutral-500">Select a supplier record on the left to edit or manage product associations.</p>
              </div>
            )}

            {(selectedSupplier || isCreating) && (
              <div className="space-y-6">
                
                {/* Profile Form */}
                <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-6">
                  <div className="flex justify-between items-center border-b border-neutral-900 pb-4">
                    <h3 className="text-sm font-bold uppercase tracking-wider text-emerald-400 font-mono">
                      {isCreating ? "New Supplier Profile" : `Profile: ${selectedSupplier.name}`}
                    </h3>
                    
                    {!isCreating && (
                      <button 
                        onClick={() => handleDelete(selectedSupplier.id)}
                        className="p-2 text-neutral-500 hover:text-red-400 hover:bg-neutral-900 rounded-xl"
                        title="Delete Supplier"
                      >
                        <Trash2 className="w-4 h-4" />
                      </button>
                    )}
                  </div>

                  <form onSubmit={handleSave} className="space-y-4 text-xs">
                    
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Contact Name</label>
                        <Input 
                          type="text" 
                          required
                          value={name}
                          onChange={(e) => setName(e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Registered Company Name</label>
                        <Input 
                          type="text"
                          value={companyName}
                          onChange={(e) => setCompanyName(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Contact Person</label>
                        <Input 
                          type="text"
                          value={contactPerson}
                          onChange={(e) => setContactPerson(e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Email Address</label>
                        <Input 
                          type="email"
                          value={email}
                          onChange={(e) => setEmail(e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Phone Number</label>
                        <Input 
                          type="text"
                          value={phone}
                          onChange={(e) => setPhone(e.target.value)}
                        />
                      </div>
                    </div>

                    <div>
                      <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Warehouse Address</label>
                      <textarea 
                        className="w-full px-4 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-200 h-16 focus:outline-none"
                        value={address}
                        onChange={(e) => setAddress(e.target.value)}
                      />
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">GST / VAT Identifier</label>
                        <Input 
                          type="text"
                          value={gstVat}
                          onChange={(e) => setGstVat(e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Tax Region</label>
                        <Input 
                          type="text"
                          placeholder="e.g. IN, EU, US"
                          value={region}
                          onChange={(e) => setRegion(e.target.value)}
                        />
                      </div>

                      <div>
                        <label className="block text-[10px] font-bold text-neutral-500 mb-1.5 uppercase">Payment Terms</label>
                        <Input 
                          type="text"
                          placeholder="e.g. Net 30, Net 60, COD"
                          value={paymentTerms}
                          onChange={(e) => setPaymentTerms(e.target.value)}
                        />
                      </div>
                    </div>

                    <div className="flex items-center gap-2 py-2">
                      <input 
                        type="checkbox" 
                        id="supActive"
                        checked={isActive}
                        onChange={(e) => setIsActive(e.target.checked)}
                        className="rounded border-neutral-800 bg-neutral-950 text-emerald-500"
                      />
                      <label htmlFor="supActive" className="text-neutral-300 font-bold select-none cursor-pointer">Active supply status</label>
                    </div>

                    <Button type="submit" disabled={saving}>
                      {saving ? <Loader2 className="w-3.5 h-3.5 animate-spin" /> : <Save className="w-3.5 h-3.5" />} Save Supplier Profile
                    </Button>

                  </form>
                </div>

                {/* Many-to-many Linked products catalog */}
                {!isCreating && (
                  <div className="p-6 rounded-3xl bg-neutral-900/40 border border-neutral-900 space-y-4">
                    <div className="flex justify-between items-center border-b border-neutral-900 pb-3">
                      <h3 className="text-xs font-bold uppercase tracking-wider text-neutral-350 font-mono">Linked Products Catalog</h3>
                      <span className="text-[10px] text-neutral-500 font-bold">{linkedProducts.length} items mapped</span>
                    </div>

                    {/* Link product picker */}
                    <div className="flex gap-2">
                      <select
                        className="flex-1 px-3 py-2.5 rounded-xl border border-neutral-800 bg-neutral-950 text-neutral-300 text-xs"
                        value={productToLink}
                        onChange={(e) => setProductToLink(e.target.value)}
                      >
                        <option value="">[Select Product to Link]</option>
                        {products
                          .filter(p => !linkedProducts.some(lp => lp.id === p.id))
                          .map(p => (
                            <option key={p.id} value={p.id}>{p.name} ({p.sku})</option>
                          ))
                        }
                      </select>
                      <Button variant="primary" size="sm" onClick={handleLinkProduct} disabled={linking}>
                        <Link2 className="w-3.5 h-3.5" /> Map Link
                      </Button>
                    </div>

                    {/* Associated products list */}
                    {linkedProducts.length === 0 ? (
                      <div className="text-center py-6 text-[10px] text-neutral-500 font-mono">No products associated with this supplier yet.</div>
                    ) : (
                      <div className="space-y-2">
                        {linkedProducts.map(p => (
                          <div key={p.id} className="p-3 rounded-xl bg-neutral-950 border border-neutral-900 flex justify-between items-center text-xs">
                            <div>
                              <span className="font-bold block text-neutral-300">{p.name}</span>
                              <span className="text-[10px] text-neutral-555">SKU: {p.sku} • Price: ${p.price}</span>
                            </div>
                            <Button 
                              variant="ghost" 
                              size="sm" 
                              className="text-neutral-500 hover:text-red-400 !p-1"
                              onClick={() => handleUnlinkProduct(p.id)}
                            >
                              <Unlink className="w-3.5 h-3.5" />
                            </Button>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                )}

              </div>
            )}

          </div>

        </div>

      </div>
    </div>
  );
}
