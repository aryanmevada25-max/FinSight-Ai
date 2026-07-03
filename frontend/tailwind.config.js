/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        void: "#050816",
        panel: "#0F172A",
        primary: "#3B82F6",
        cyan: "#22D3EE",
        success: "#10B981",
        warning: "#F59E0B",
        danger: "#EF4444",
        ink: "#F8FAFC",
        muted: "#94A3B8",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px rgba(59, 130, 246, .18)",
        cyan: "0 0 35px rgba(34, 211, 238, .16)",
      },
    },
  },
  plugins: [],
};
