"use client";

import React, { useState } from "react";
import Link from "next/link";
import { 
  Type, 
  Palette, 
  Maximize2, 
  Grid, 
  Layers, 
  Sliders, 
  ArrowLeft,
  Sun,
  Moon,
  Sparkles,
  Info,
  TrendingUp,
  AlertTriangle,
  FolderOpen,
  Terminal,
  HelpCircle
} from "lucide-react";

// Import our newly created reusable UI components
import { Button } from "@/components/ui/button";
import { Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter } from "@/components/ui/card";
import { Dialog } from "@/components/ui/dialog";
import { Drawer } from "@/components/ui/drawer";
import { Input } from "@/components/ui/input";
import { TableContainer, Table, TableHeader, TableBody, TableRow, TableCell, TableHead } from "@/components/ui/table";
import { ToastProvider, useToast } from "@/components/ui/toast";
import { LoadingState, EmptyState, ErrorState } from "@/components/ui/states";
import { BarChart, LineChart, PieChart } from "@/components/ui/chart";

function DesignSystemContent() {
  const [theme, setTheme] = useState<"dark" | "light" | "emerald">("dark");
  const [activeTab, setActiveTab] = useState("tokens");
  
  // Dialog state
  const [dialogOpen, setDialogOpen] = useState(false);
  
  // Drawer state
  const [drawerOpen, setDrawerOpen] = useState(false);
  
  // Toast trigger hook
  const { toast } = useToast();

  const getThemeClass = () => {
    if (theme === "light") return "bg-neutral-50 text-neutral-900 border-neutral-200";
    if (theme === "emerald") return "bg-emerald-950/20 text-emerald-100 border-emerald-900/40";
    return "bg-neutral-950 text-neutral-100 border-neutral-900";
  };

  const chartData = [
    { label: "Beverages", value: 120, color: "#10b981" },
    { label: "Snacks", value: 85, color: "#3b82f6" },
    { label: "Produce", value: 210, color: "#f59e0b" },
    { label: "Dairy", value: 65, color: "#ef4444" },
    { label: "Frozen", value: 45, color: "#8b5cf6" }
  ];

  return (
    <div className={`min-h-screen transition-all duration-300 flex flex-col ${getThemeClass()}`}>
      
      {/* Design System Header */}
      <nav className={`border-b sticky top-0 z-20 px-6 py-4 flex justify-between items-center backdrop-blur-md ${
        theme === "light" ? "bg-white/80 border-neutral-200" : "bg-neutral-950/80 border-neutral-900"
      }`}>
        <div className="flex items-center gap-3">
          <Link href="/dashboard" className="p-2 rounded-xl border border-neutral-800 bg-neutral-900/50 hover:text-emerald-400 text-neutral-400">
            <ArrowLeft className="w-4 h-4" />
          </Link>
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-emerald-500" />
            <span className="font-extrabold text-sm tracking-tight">Aetheria SaaS Component Library</span>
          </div>
        </div>

        {/* Theme Controls */}
        <div className="flex items-center gap-2 p-1 rounded-xl bg-neutral-900/50 border border-neutral-850">
          <button 
            onClick={() => setTheme("dark")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              theme === "dark" ? "bg-neutral-850 text-neutral-100 shadow" : "text-neutral-500 hover:text-neutral-350"
            }`}
          >
            <Moon className="w-3.5 h-3.5" /> Dark
          </button>
          <button 
            onClick={() => setTheme("light")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              theme === "light" ? "bg-neutral-200 text-neutral-900 shadow" : "text-neutral-500 hover:text-neutral-350"
            }`}
          >
            <Sun className="w-3.5 h-3.5" /> Light
          </button>
          <button 
            onClick={() => setTheme("emerald")}
            className={`px-3 py-1.5 rounded-lg text-xs font-bold transition-all flex items-center gap-1.5 cursor-pointer ${
              theme === "emerald" ? "bg-emerald-500 text-neutral-950 shadow" : "text-emerald-400 hover:text-emerald-350"
            }`}
          >
            <Sparkles className="w-3.5 h-3.5" /> Emerald
          </button>
        </div>
      </nav>

      {/* Main Layout */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-6 py-10 grid grid-cols-1 lg:grid-cols-12 gap-8">
        
        {/* Left Navigator Menu */}
        <aside className="lg:col-span-3 space-y-2">
          <div className="text-[10px] font-bold uppercase tracking-wider text-neutral-500 px-3 mb-2">Modules Navigation</div>
          {[
            { id: "tokens", label: "Foundational Tokens", icon: Grid },
            { id: "typography", label: "Typography System", icon: Type },
            { id: "colors", label: "Color Systems", icon: Palette },
            { id: "actions", label: "Buttons & Modal Dialogs", icon: Sliders },
            { id: "data-views", label: "Charts & Visualizers", icon: Layers }
          ].map(tab => {
            const Icon = tab.icon;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`w-full text-left px-4 py-3 rounded-2xl border transition-all text-xs font-bold flex items-center gap-2.5 cursor-pointer ${
                  activeTab === tab.id
                    ? "bg-emerald-500/10 border-emerald-500/30 text-emerald-400 shadow-sm"
                    : "bg-neutral-900/40 border-neutral-900 hover:border-neutral-800 text-neutral-450"
                }`}
              >
                <Icon className="w-4 h-4" />
                {tab.label}
              </button>
            )
          })}
        </aside>

        {/* Right Details Panel */}
        <main className="lg:col-span-9 space-y-10">

          {/* TAB 1: TOKENS */}
          {activeTab === "tokens" && (
            <section className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold uppercase tracking-wider text-neutral-200">Spacing & Corner Radials</h2>
                <p className="text-neutral-500 text-xs mt-1">Configured using relative variables inside tailwind properties sheet.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Spacing guide</CardTitle>
                    <CardDescription>Visual margins scale layout constants</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 font-mono text-xs">
                    {[
                      { token: "var(--space-2xs)", val: "4px (0.25rem)" },
                      { token: "var(--space-xs)", val: "8px (0.5rem)" },
                      { token: "var(--space-sm)", val: "12px (0.75rem)" },
                      { token: "var(--space-md)", val: "16px (1.0rem)" },
                      { token: "var(--space-lg)", val: "24px (1.5rem)" }
                    ].map(item => (
                      <div key={item.token} className="flex justify-between items-center p-2 rounded-lg bg-neutral-950 border border-neutral-900">
                        <span className="text-emerald-400 font-bold">{item.token}</span>
                        <span className="text-neutral-500">{item.val}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Border Radials</CardTitle>
                    <CardDescription>Standardized rounding borders</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-3 font-mono text-xs">
                    {[
                      { token: "var(--radius-sm)", val: "6px (0.375rem)" },
                      { token: "var(--radius-md)", val: "12px (0.75rem)" },
                      { token: "var(--radius-lg)", val: "16px (1.0rem)" },
                      { token: "var(--radius-xl)", val: "24px (1.5rem)" }
                    ].map(item => (
                      <div key={item.token} className="flex justify-between items-center p-2 rounded-lg bg-neutral-950 border border-neutral-900">
                        <span className="text-emerald-400 font-bold">{item.token}</span>
                        <span className="text-neutral-500">{item.val}</span>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </section>
          )}

          {/* TAB 2: TYPOGRAPHY */}
          {activeTab === "typography" && (
            <section className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold uppercase tracking-wider text-neutral-200">Typography Scale</h2>
                <p className="text-neutral-500 text-xs mt-1">Inter and Segoe UI pairings optimized for maximum screen readability.</p>
              </div>

              <Card>
                <CardContent className="space-y-6 pt-6">
                  <div>
                    <span className="text-[9px] font-mono text-neutral-500 block mb-1">H1 Header - var(--text-3xl)</span>
                    <h1 className="text-3xl font-extrabold tracking-tight">Enterprise Grocery Scanner</h1>
                  </div>
                  <div>
                    <span className="text-[9px] font-mono text-neutral-500 block mb-1">H2 Header - var(--text-xl)</span>
                    <h2 className="text-xl font-bold tracking-tight">Active Shelf Inventory</h2>
                  </div>
                  <div>
                    <span className="text-[9px] font-mono text-neutral-500 block mb-1">Paragraph text - var(--text-sm)</span>
                    <p className="text-sm text-neutral-400 leading-relaxed">
                      This platform enables real-time product tracking via YOLO models and EasyOCR detections to minimize manual logging efforts.
                    </p>
                  </div>
                </CardContent>
              </Card>
            </section>
          )}

          {/* TAB 3: COLORS */}
          {activeTab === "colors" && (
            <section className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold uppercase tracking-wider text-neutral-200">Color Palette Tokens</h2>
                <p className="text-neutral-500 text-xs mt-1">Semantic layout colors for actions, indicators, and backgrounds.</p>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Emerald Brand Accents</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {[
                      { name: "Primary highlight", hex: "#10b981", token: "emerald-500" },
                      { name: "Hover state", hex: "#34d399", token: "emerald-400" },
                      { name: "Subtle background", hex: "#064e3b", token: "emerald-900" }
                    ].map(c => (
                      <div key={c.hex} className="flex items-center gap-3 p-2 rounded-xl bg-neutral-950 border border-neutral-900">
                        <div className="w-8 h-8 rounded-lg" style={{ backgroundColor: c.hex }} />
                        <div className="text-xs">
                          <span className="font-bold block text-neutral-300">{c.name}</span>
                          <span className="font-mono text-neutral-500">{c.hex} • {c.token}</span>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Diagnostic Flags</CardTitle>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {[
                      { name: "Danger / Lockout", hex: "#ef4444", token: "red-500" },
                      { name: "Warning / Low stock", hex: "#f59e0b", token: "yellow-500" },
                      { name: "Informational", hex: "#3b82f6", token: "blue-500" }
                    ].map(c => (
                      <div key={c.hex} className="flex items-center gap-3 p-2 rounded-xl bg-neutral-950 border border-neutral-900">
                        <div className="w-8 h-8 rounded-lg" style={{ backgroundColor: c.hex }} />
                        <div className="text-xs">
                          <span className="font-bold block text-neutral-300">{c.name}</span>
                          <span className="font-mono text-neutral-500">{c.hex} • {c.token}</span>
                        </div>
                      </div>
                    ))}
                  </CardContent>
                </Card>
              </div>
            </section>
          )}

          {/* TAB 4: ACTIONS */}
          {activeTab === "actions" && (
            <section className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold uppercase tracking-wider text-neutral-200">Action Panels & Overlays</h2>
                <p className="text-neutral-500 text-xs mt-1">Reusable dialogs, slide-out drawer menus, and toast alert controls.</p>
              </div>

              <Card>
                <CardHeader>
                  <CardTitle>Interactive Actions Curation</CardTitle>
                </CardHeader>
                <CardContent className="space-y-6">
                  {/* Button types */}
                  <div className="space-y-2">
                    <span className="text-[9px] font-mono text-neutral-500 block uppercase">Button variant states</span>
                    <div className="flex flex-wrap gap-3">
                      <Button variant="primary">Primary action</Button>
                      <Button variant="secondary">Secondary outline</Button>
                      <Button variant="destructive">Destructive action</Button>
                      <Button variant="ghost">Ghost toggle</Button>
                      <Button variant="primary" loading={true}>Processing spinner</Button>
                    </div>
                  </div>

                  {/* Toast notifier triggers */}
                  <div className="space-y-2 pt-4 border-t border-neutral-900/50">
                    <span className="text-[9px] font-mono text-neutral-500 block uppercase">Toast alerts popup</span>
                    <div className="flex flex-wrap gap-3">
                      <Button 
                        variant="secondary" 
                        onClick={() => toast({ title: "Task finished", description: "All database files backup completed successfully.", type: "success" })}
                      >
                        Trigger Success Alert
                      </Button>
                      <Button 
                        variant="secondary" 
                        onClick={() => toast({ title: "Low Stock Warning", description: "Inventory items on Shelf 4 are under threshold limits.", type: "warning" })}
                      >
                        Trigger Warning Alert
                      </Button>
                      <Button 
                        variant="secondary" 
                        onClick={() => toast({ title: "Write Permission Error", description: "Your current token session does not allow writing changes.", type: "error" })}
                      >
                        Trigger Danger Alert
                      </Button>
                    </div>
                  </div>

                  {/* Modal / Drawers triggers */}
                  <div className="space-y-2 pt-4 border-t border-neutral-900/50">
                    <span className="text-[9px] font-mono text-neutral-500 block uppercase">Overlay triggers</span>
                    <div className="flex flex-wrap gap-3">
                      <Button variant="outline" onClick={() => setDialogOpen(true)}>Open dialog Modal</Button>
                      <Button variant="outline" onClick={() => setDrawerOpen(true)}>Open Slide-out Drawer</Button>
                    </div>
                  </div>

                  {/* Accessible Dialog */}
                  <Dialog 
                    open={dialogOpen} 
                    onOpenChange={setDialogOpen}
                    title="Audit Log Trace"
                    description="This is a reusable overlay container with close listeners."
                  >
                    <div className="space-y-4 font-mono">
                      <p className="text-[10px] text-neutral-400">
                        User action: Edit category registry details.
                      </p>
                      <p className="text-[10px] text-neutral-400">
                        Status Code: 200 OK • Response processed in 45ms.
                      </p>
                      <Button variant="primary" size="sm" onClick={() => setDialogOpen(false)}>Close Tracer</Button>
                    </div>
                  </Dialog>

                  {/* Slide-out Drawer */}
                  <Drawer 
                    open={drawerOpen} 
                    onOpenChange={setDrawerOpen}
                    title="Filter Settings Console"
                  >
                    <div className="space-y-4">
                      <p className="text-neutral-400">
                        Adjust visual filter guidelines and database queries mapping.
                      </p>
                      <Input label="Country origin code" placeholder="e.g. UK, IN" />
                      <Button variant="primary" onClick={() => setDrawerOpen(false)}>Apply Configurations</Button>
                    </div>
                  </Drawer>

                </CardContent>
              </Card>
            </section>
          )}

          {/* TAB 5: DATA VIEWS */}
          {activeTab === "data-views" && (
            <section className="space-y-6">
              <div>
                <h2 className="text-lg font-extrabold uppercase tracking-wider text-neutral-200">SVG Charts & Data Displays</h2>
                <p className="text-neutral-500 text-xs mt-1">Accessible SVG charts, responsive tables, and empty/error indicators.</p>
              </div>

              {/* SVG Charts display */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <Card>
                  <CardHeader>
                    <CardTitle>Catalog items count (Bar Chart)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <BarChart data={chartData} height={140} />
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>Active scanning speed (Line Chart)</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <LineChart data={chartData} height={140} />
                  </CardContent>
                </Card>
              </div>

              {/* Data Table */}
              <Card>
                <CardHeader>
                  <CardTitle>Product variants list</CardTitle>
                </CardHeader>
                <CardContent>
                  <TableContainer>
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead>Item Details</TableHead>
                          <TableHead>Category</TableHead>
                          <TableHead>Unit Price</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        <TableRow>
                          <TableCell>Classic Milk Chocolate</TableCell>
                          <TableCell>Snacks</TableCell>
                          <TableCell className="font-mono text-emerald-400">$2.50</TableCell>
                        </TableRow>
                        <TableRow>
                          <TableCell>Diet Fizz Soda Can</TableCell>
                          <TableCell>Beverages</TableCell>
                          <TableCell className="font-mono text-emerald-400">$1.20</TableCell>
                        </TableRow>
                      </TableBody>
                    </Table>
                  </TableContainer>
                </CardContent>
              </Card>

              {/* Diagnostic Panels */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <EmptyState 
                  title="No scan records linked"
                  description="Scan a shelf barcode to start registering inventory details."
                  actionLabel="Initiate scan feed"
                  onAction={() => alert("Redirecting to video scanner...")}
                />
                
                <ErrorState 
                  title="Database connection refused"
                  description="PostgreSQL backend did not reply on port 5432. Check service status."
                  retryLabel="Re-verify socket"
                  onRetry={() => alert("Re-verifying backend pool...")}
                />
              </div>

            </section>
          )}

        </main>
      </div>

    </div>
  );
}

export default function DesignSystemPage() {
  return (
    <ToastProvider>
      <DesignSystemContent />
    </ToastProvider>
  );
}
