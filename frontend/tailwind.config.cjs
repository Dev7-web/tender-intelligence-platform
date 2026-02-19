module.exports = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        primary: "var(--primary)",
        primaryHover: "var(--primary-hover)",
        success: "var(--success)",
        warning: "var(--warning)",
        error: "var(--error)",
        background: "var(--background)",
        card: "var(--card)",
        text: "var(--text)",
        muted: "var(--muted)",
        border: "var(--border)",
      },
      fontFamily: {
        sans: ["var(--font-body)", "sans-serif"],
        display: ["var(--font-display)", "sans-serif"],
      },
      boxShadow: {
        soft: "0 20px 60px -40px rgba(15, 23, 42, 0.4)",
        card: "0 12px 40px -20px rgba(15, 23, 42, 0.35)",
      },
      keyframes: {
        rise: {
          "0%": { opacity: "0", transform: "translateY(12px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
      animation: {
        rise: "rise 0.6s ease-out",
      },
    },
  },
  plugins: [],
};
