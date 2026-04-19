// Reusable card shell for the dashboard.
import type { ReactNode } from "react";

interface Props {
  title?: string;
  subtitle?: string;
  className?: string;
  children: ReactNode;
}

export default function Card({ title, subtitle, className = "", children }: Props) {
  return (
    <div
      className={`rounded-2xl border border-slate-200 bg-white p-5 shadow-sm ${className}`}
    >
      {title && (
        <div className="mb-3">
          <div className="text-xs font-medium uppercase tracking-wide text-slate-500">
            {title}
          </div>
          {subtitle && (
            <div className="text-xs text-slate-400">{subtitle}</div>
          )}
        </div>
      )}
      {children}
    </div>
  );
}
