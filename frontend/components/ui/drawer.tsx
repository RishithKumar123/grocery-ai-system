import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Button } from "./button";

export interface DrawerProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  side?: "right" | "bottom";
  children: React.ReactNode;
  className?: string;
}

export function Drawer({ open, onOpenChange, title, side = "right", children, className = "" }: DrawerProps) {
  const drawerRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === "Escape" && open) {
        onOpenChange(false);
      }
    };
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [open, onOpenChange]);

  if (!open) return null;

  const sideClasses = {
    right: "right-0 top-0 bottom-0 h-full w-full max-w-md border-l border-neutral-900 animate-slide-in-right",
    bottom: "bottom-0 left-0 right-0 w-full max-h-[80vh] border-t border-neutral-900 animate-slide-in-bottom"
  };

  return (
    <div 
      className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm"
      onClick={() => onOpenChange(false)}
    >
      <div 
        ref={drawerRef}
        className={`fixed bg-neutral-950 p-6 shadow-xl flex flex-col justify-between overflow-y-auto ${sideClasses[side]} ${className}`}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-label={title}
      >
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between border-b border-neutral-900 pb-3">
            <h3 className="text-sm font-bold uppercase tracking-wider text-neutral-200">{title || "Curation Tools"}</h3>
            <Button 
              variant="ghost" 
              size="sm" 
              className="!p-1.5 rounded-xl border border-transparent text-neutral-500 hover:text-neutral-300"
              onClick={() => onOpenChange(false)}
              aria-label="Close drawer"
            >
              <X className="w-4 h-4" />
            </Button>
          </div>

          {/* Drawer Content */}
          <div className="text-xs text-neutral-300">
            {children}
          </div>
        </div>
      </div>
    </div>
  );
}
