"use client";

import React, { createContext, useContext, useState, useCallback } from "react";
import { CheckCircle, AlertCircle, Info, X } from "lucide-react";
import { Button } from "./button";

export interface ToastMessage {
  id: string;
  title: string;
  description?: string;
  type?: "success" | "warning" | "info" | "error";
}

interface ToastContextType {
  toast: (message: Omit<ToastMessage, "id">) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<ToastMessage[]>([]);

  const toast = useCallback(({ title, description, type = "info" }: Omit<ToastMessage, "id">) => {
    const id = Math.random().toString(36).substring(2, 9);
    setToasts((prev) => [...prev, { id, title, description, type }]);
    
    // Auto-remove after 4 seconds
    setTimeout(() => {
      setToasts((prev) => prev.filter((t) => t.id !== id));
    }, 4000);
  }, []);

  const removeToast = (id: string) => {
    setToasts((prev) => prev.filter((t) => t.id !== id));
  };

  const icons = {
    success: <CheckCircle className="w-4.5 h-4.5 text-emerald-400 shrink-0" />,
    warning: <AlertCircle className="w-4.5 h-4.5 text-yellow-400 shrink-0" />,
    error: <AlertCircle className="w-4.5 h-4.5 text-red-400 shrink-0" />,
    info: <Info className="w-4.5 h-4.5 text-blue-400 shrink-0" />
  };

  const borders = {
    success: "border-emerald-500/20 bg-emerald-950/20",
    warning: "border-yellow-500/20 bg-yellow-950/20",
    error: "border-red-500/20 bg-red-950/20",
    info: "border-blue-500/20 bg-blue-950/20"
  };

  return (
    <ToastContext.Provider value={{ toast }}>
      {children}
      
      {/* Toast container floating portal */}
      <div className="fixed bottom-6 right-6 z-50 flex flex-col gap-3 max-w-sm w-full">
        {toasts.map((t) => (
          <div
            key={t.id}
            className={`p-4 rounded-2xl border backdrop-blur-md shadow-lg flex gap-3 justify-between items-start animate-slide-in-right ${borders[t.type || "info"]}`}
            role="alert"
          >
            <div className="flex gap-2.5 items-start">
              {icons[t.type || "info"]}
              <div className="text-xs space-y-0.5">
                <span className="font-bold text-neutral-100 block">{t.title}</span>
                {t.description && <span className="text-neutral-400 text-[10px] leading-relaxed block">{t.description}</span>}
              </div>
            </div>
            
            <Button
              variant="ghost"
              size="sm"
              className="!p-1 rounded-lg text-neutral-500 hover:text-neutral-300 -mt-1 -mr-1"
              onClick={() => removeToast(t.id)}
              aria-label="Close notification"
            >
              <X className="w-3.5 h-3.5" />
            </Button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const context = useContext(ToastContext);
  if (!context) {
    throw new Error("useToast must be used within a ToastProvider");
  }
  return context;
}
