import { HTMLAttributes } from "react";

import { cn } from "@/lib/utils";

const palette: Record<string, string> = {
  Low: "bg-[#ecfdf3] text-[#027a48]",
  Medium: "bg-[#fff7ed] text-[#c2410c]",
  High: "bg-[#fff1f2] text-[#be123c]",
  Critical: "bg-[#4a1018] text-white",
  default: "bg-[#eef2ff] text-[#1d4ed8]",
};

export function Badge({ className, children, ...props }: HTMLAttributes<HTMLSpanElement>) {
  const content = typeof children === "string" ? children : "default";
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-full px-3 py-1 text-xs font-semibold",
        palette[content] ?? palette.default,
        className,
      )}
      {...props}
    >
      {children}
    </span>
  );
}
