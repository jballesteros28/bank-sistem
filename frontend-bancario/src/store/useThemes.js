import { create } from "zustand";

export const useTheme = create((set) => ({
  theme: localStorage.getItem("bank.theme") || "light",

  setTheme: (newTheme) => {
    localStorage.setItem("bank.theme", newTheme);
    document.documentElement.classList.toggle("dark", newTheme === "dark");
    set({ theme: newTheme });
  },

  toggleTheme: () =>
    set((state) => {
      const newTheme = state.theme === "dark" ? "light" : "dark";
      localStorage.setItem("bank.theme", newTheme);
      document.documentElement.classList.toggle("dark", newTheme === "dark");
      return { theme: newTheme };
    }),
}));
