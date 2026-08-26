import React from "react";

export const TableContainer = React.forwardRef<HTMLDivElement, React.HTMLAttributes<HTMLDivElement>>(
  ({ className = "", ...props }, ref) => (
    <div ref={ref} className={`w-full overflow-x-auto rounded-2xl border border-neutral-900 bg-neutral-950/40 backdrop-blur-md ${className}`} {...props} />
  )
);
TableContainer.displayName = "TableContainer";

export const Table = React.forwardRef<HTMLTableElement, React.HTMLAttributes<HTMLTableElement>>(
  ({ className = "", ...props }, ref) => (
    <table ref={ref} className={`w-full text-xs text-left border-collapse ${className}`} {...props} />
  )
);
Table.displayName = "Table";

export const TableHeader = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className = "", ...props }, ref) => (
    <thead ref={ref} className={`border-b border-neutral-900 bg-neutral-900/30 text-neutral-500 font-bold uppercase tracking-wider text-[9px] ${className}`} {...props} />
  )
);
TableHeader.displayName = "TableHeader";

export const TableBody = React.forwardRef<HTMLTableSectionElement, React.HTMLAttributes<HTMLTableSectionElement>>(
  ({ className = "", ...props }, ref) => (
    <tbody ref={ref} className={`divide-y divide-neutral-900/50 ${className}`} {...props} />
  )
);
TableBody.displayName = "TableBody";

export const TableRow = React.forwardRef<HTMLTableRowElement, React.HTMLAttributes<HTMLTableRowElement>>(
  ({ className = "", ...props }, ref) => (
    <tr ref={ref} className={`hover:bg-neutral-900/40 transition-colors duration-150 ${className}`} {...props} />
  )
);
TableRow.displayName = "TableRow";

export const TableCell = React.forwardRef<HTMLTableCellElement, React.TdHTMLAttributes<HTMLTableCellElement>>(
  ({ className = "", ...props }, ref) => (
    <td ref={ref} className={`p-4 align-middle text-neutral-300 font-medium ${className}`} {...props} />
  )
);
TableCell.displayName = "TableCell";

export const TableHead = React.forwardRef<HTMLTableCellElement, React.ThHTMLAttributes<HTMLTableCellElement>>(
  ({ className = "", ...props }, ref) => (
    <th ref={ref} className={`p-4 align-middle font-bold text-neutral-400 ${className}`} {...props} />
  )
);
TableHead.displayName = "TableHead";
