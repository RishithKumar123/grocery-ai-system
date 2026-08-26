import React from "react";
import { Loader2, Inbox, AlertTriangle } from "lucide-react";
import { Button } from "./button";

// 1. Loading screen / Spinner
export function LoadingState({ message = "Retrieving workspace data...", height = "min-h-[200px]" }) {
  return (
    <div className={`flex flex-col items-center justify-center gap-3 p-6 text-center ${height}`}>
      <Loader2 className="w-6 h-6 animate-spin text-emerald-400" />
      <span className="text-xs font-mono text-neutral-400 animate-pulse">{message}</span>
    </div>
  );
}

// 2. Empty state panel
interface EmptyStateProps {
  title?: string;
  description?: string;
  actionLabel?: string;
  onAction?: () => void;
  icon?: React.ReactNode;
}

export function EmptyState({ 
  title = "No Records Available", 
  description = "No items have been registered or indexed in this section yet.", 
  actionLabel, 
  onAction,
  icon
}: EmptyStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 border border-dashed border-neutral-900 rounded-3xl bg-neutral-950/20 text-center space-y-4">
      <div className="w-12 h-12 rounded-2xl bg-neutral-900/60 border border-neutral-850 flex items-center justify-center text-neutral-600 mx-auto">
        {icon || <Inbox className="w-6 h-6" />}
      </div>
      <div className="space-y-1">
        <h4 className="text-xs font-bold text-neutral-200 uppercase tracking-wider">{title}</h4>
        <p className="text-[11px] text-neutral-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      </div>
      {actionLabel && onAction && (
        <Button variant="outline" size="sm" onClick={onAction}>
          {actionLabel}
        </Button>
      )}
    </div>
  );
}

// 3. Error state panel
interface ErrorStateProps {
  title?: string;
  description?: string;
  retryLabel?: string;
  onRetry?: () => void;
}

export function ErrorState({ 
  title = "Database Sync Failed", 
  description = "An error occurred while fetching or saving data from remote services.", 
  retryLabel = "Attempt Reconnection", 
  onRetry 
}: ErrorStateProps) {
  return (
    <div className="flex flex-col items-center justify-center p-8 border border-red-950/20 bg-red-950/5 rounded-3xl text-center space-y-4">
      <div className="w-12 h-12 rounded-2xl bg-red-500/10 border border-red-500/20 flex items-center justify-center text-red-500 mx-auto">
        <AlertTriangle className="w-6 h-6" />
      </div>
      <div className="space-y-1">
        <h4 className="text-xs font-bold text-red-400 uppercase tracking-wider">{title}</h4>
        <p className="text-[11px] text-neutral-500 max-w-sm mx-auto leading-relaxed">{description}</p>
      </div>
      {onRetry && (
        <Button variant="destructive" size="sm" onClick={onRetry}>
          {retryLabel}
        </Button>
      )}
    </div>
  );
}
