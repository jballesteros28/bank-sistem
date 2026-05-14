// tailwind.config.js
export default {
  darkMode: 'class',              // ⬅️ IMPORTANTE
  content: ["./index.html","./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          50: "#f0f9ff",
          500: "#0284c7",
          600: "#0369a1",
        },
      },
      borderRadius: {
        xl: "1rem",
        "2xl": "1.25rem",
      },
    },
  },
  plugins: [],
}

