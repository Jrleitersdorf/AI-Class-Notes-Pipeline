/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        bg:        "var(--bg)",
        elevated:  "var(--bg-elevated)",
        surface:   "var(--surface)",
        border:    "var(--border)",
        "border-accent": "var(--border-accent)",
        accent:    "var(--accent)",
        "accent-hover": "var(--accent-hover)",
        success:   "var(--success)",
        warning:   "var(--warning)",
        error:     "var(--error)",
      },
      textColor: {
        DEFAULT:   "var(--text)",
        muted:     "var(--text-muted)",
        faint:     "var(--text-faint)",
      },
      fontFamily: {
        sans: ["Inter", "-apple-system", "system-ui", "sans-serif"],
        mono: ["JetBrains Mono", "ui-monospace", "monospace"],
      },
    },
  },
  plugins: [],
};
