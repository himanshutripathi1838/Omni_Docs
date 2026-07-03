export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ['"Plus Jakarta Sans"', "Inter", "system-ui", "sans-serif"],
      },
      colors: {
        ink: "#0f172a",
        brand: "#2563eb",
        slatepanel: "#1e293b",
        line: "#e4e5e7",
      },
      boxShadow: {
        soft: "0 16px 45px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
