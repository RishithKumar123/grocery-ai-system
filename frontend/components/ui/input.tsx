import React from "react";

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string;
  error?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", label, error, leftIcon, rightIcon, id, type = "text", ...props }, ref) => {
    return (
      <div className="space-y-1.5 w-full text-xs">
        {label && (
          <label htmlFor={id} className="block text-[10px] font-bold text-neutral-500 uppercase tracking-wider">
            {label}
          </label>
        )}
        <div className="relative">
          {leftIcon && (
            <div className="absolute left-3.5 top-1/2 -translate-y-1/2 flex items-center justify-center text-neutral-600">
              {leftIcon}
            </div>
          )}
          <input
            ref={ref}
            id={id}
            type={type}
            className={`w-full px-4 py-2.5 rounded-xl border bg-neutral-950 text-neutral-300 placeholder-neutral-600 focus:outline-none transition-all duration-200 ${
              leftIcon ? "pl-10" : ""
            } ${rightIcon ? "pr-10" : ""} ${
              error 
                ? "border-red-500/50 focus:border-red-500 focus:ring-1 focus:ring-red-500/30" 
                : "border-neutral-900 focus:border-emerald-500/40 focus:ring-1 focus:ring-emerald-500/20"
            } ${className}`}
            {...props}
          />
          {rightIcon && (
            <div className="absolute right-3.5 top-1/2 -translate-y-1/2 flex items-center justify-center text-neutral-600">
              {rightIcon}
            </div>
          )}
        </div>
        {error && (
          <span className="text-[10px] font-bold text-red-500/80 block mt-1">
            {error}
          </span>
        )}
      </div>
    );
  }
);
Input.displayName = "Input";
