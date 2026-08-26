import React, { useEffect, useRef } from "react";
import { X } from "lucide-react";
import { Button } from "./button";

export interface DialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  title?: string;
  description?: string;
  children: React.ReactNode;
  className?: string;
}

export function Dialog({ open, onOpenChange, title, description, children, className = "" }: DialogProps) {
  const dialogRef = useRef<HTMLDivElement>(null);

  // Close dialog on Escape key down
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

  return (
    <div 
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-sm animate-fade-in"
      role="dialog"
      aria-modal="true"
      aria-labelledby={title ? "dialog-title" : undefined}
      aria-describedby={description ? "dialog-desc" : undefined}
      onClick={() => onOpenChange(false)}
    >
      <div 
        ref={dialogRef}
        className={`relative w-full max-w-lg p-6 bg-neutral-950 border border-neutral-900 rounded-3xl shadow-xl animate-scale-in max-h-[90vh] overflow-y-auto ${className}`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Close Button */}
        <Button 
          variant="ghost" 
          size="sm" 
          className="absolute right-4 top-4 !p-1.5 rounded-xl border border-transparent hover:border-neutral-800 text-neutral-500 hover:text-neutral-300"
          onClick={() => onOpenChange(false)}
          aria-label="Close dialog"
        >
          <X className="w-4 h-4" />
        </Button>

        {/* Dialog Header */}
        {(title || description) && (
          <div className="mb-4 space-y-1">
            {title && (
              <h2 id="dialog-title" className="text-sm font-bold uppercase tracking-wider text-neutral-200">
                {title}
              </h2>
            )}
            {description && (
              <p id="dialog-desc" className="text-xs text-neutral-500 font-medium leading-relaxed">
                {description}
              </p>
            )}
          </div>
        )}

        {/* Dialog Content */}
        <div className="text-xs text-neutral-300">
          {children}
        </div>
      </div>
    </div>
  );
}
