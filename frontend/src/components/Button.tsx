import type { ButtonHTMLAttributes } from "react";
import { cn } from "../lib/cn";

type Variant = "primary" | "secondary" | "ghost" | "danger";

export function Button({
  variant = "primary",
  className,
  ...props
}: ButtonHTMLAttributes<HTMLButtonElement> & { variant?: Variant }) {
  return (
    <button
      {...props}
      className={cn(
        "px-3 py-1.5 text-[12px] rounded-md font-medium transition-colors",
        "disabled:opacity-50 disabled:cursor-not-allowed",
        variant === "primary" &&
          "bg-accent text-white hover:bg-accent-hover",
        variant === "secondary" &&
          "border border-border text-[color:var(--text)] hover:bg-surface",
        variant === "ghost" &&
          "text-[color:var(--text-muted)] hover:text-[color:var(--text)]",
        variant === "danger" &&
          "text-error hover:bg-error/10",
        className
      )}
    />
  );
}
