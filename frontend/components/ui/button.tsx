import React from "react";
import { Loader2 } from "lucide-react";

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "default" | "primary" | "secondary" | "destructive" | "outline" | "ghost" | "link";
  size?: "sm" | "md" | "lg";
  loading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ className = "", variant = "default", size = "md", loading = false, leftIcon, rightIcon, children, disabled, ...props }, ref) => {
    
    // Base style with focus ring & transitions
    const baseStyle = "inline-flex items-center justify-center font-semibold rounded-xl transition-all duration-200 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/50 disabled:opacity-50 disabled:pointer-events-none select-none cursor-pointer";
    
    // Variants classes
    const variants = {
      default: "bg-neutral-850 hover:bg-neutral-800 text-neutral-100 border border-neutral-800",
      primary: "bg-emerald-500 hover:bg-emerald-400 text-neutral-950 shadow-md shadow-emerald-500/10 active:scale-[0.98]",
      secondary: "bg-neutral-900/80 hover:bg-neutral-850 text-neutral-300 border border-neutral-800/80",
      destructive: "bg-red-500 hover:bg-red-400 text-neutral-950 shadow-md shadow-red-500/10 active:scale-[0.98]",
      outline: "border border-neutral-800 hover:border-neutral-700 bg-transparent text-neutral-300 hover:text-neutral-100",
      ghost: "hover:bg-neutral-900 text-neutral-400 hover:text-neutral-100",
      link: "text-emerald-400 hover:text-emerald-300 underline-offset-4 hover:underline p-0 bg-transparent"
    };

    // Sizes classes
    const sizes = {
      sm: "px-3 py-1.5 text-xs gap-1.5",
      md: "px-4.5 py-2.5 text-xs gap-2",
      lg: "px-6 py-3.5 text-sm gap-2.5"
    };

    return (
      <button
        ref={ref}
        disabled={disabled || loading}
        className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`}
        aria-busy={loading}
        {...props}
      >
        {loading && <Loader2 className="w-3.5 h-3.5 animate-spin shrink-0" />}
        {!loading && leftIcon && <span className="shrink-0">{leftIcon}</span>}
        <span>{children}</span>
        {!loading && rightIcon && <span className="shrink-0">{rightIcon}</span>}
      </button>
    );
  }
);

Button.displayName = "Button";
