/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        brand: {
          primary: "var(--color-primary)",
          secondary: "var(--color-secondary)",
        },
      },
      boxShadow: {
        panel: "0 12px 40px rgba(15, 23, 42, 0.08)",
      },
    },
  },
  plugins: [],
};
