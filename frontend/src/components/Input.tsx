import type { InputHTMLAttributes } from "react";
import { cn } from "../lib/cn";

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      {...props}
      className={cn(
        "w-full bg-surface border border-border rounded-[5px] px-2.5 py-1.5",
        "text-[12px] text-[color:var(--text)] placeholder:text-faint",
        "focus:outline-none focus:border-[color:var(--border-accent)]",
        className
      )}
    />
  );
}
