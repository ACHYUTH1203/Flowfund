// Format a decimal string like "12345.67" as "₹12,345.67" (Indian grouping).
export function formatRupees(value: string | number, digits = 2): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return "—";
  return `\u20B9${n.toLocaleString("en-IN", {
    minimumFractionDigits: digits,
    maximumFractionDigits: digits,
  })}`;
}

export function formatPercent(value: string | number, digits = 1): string {
  const n = typeof value === "string" ? parseFloat(value) : value;
  if (Number.isNaN(n)) return "—";
  return `${(n * 100).toFixed(digits)}%`;
}
