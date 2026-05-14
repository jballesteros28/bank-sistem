// src/main.jsx
import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import { AuthProvider } from "./context/AuthProvider";
import AppRouter from "./routes/AppRouter";
import "./styles/globals.css";
import "./i18n";
import NavBar from"./components/layout/NavBar.jsx";



// sincronizar tema antes de render
const storedTheme = localStorage.getItem("bank.theme") || "light";
document.documentElement.classList.toggle("dark", storedTheme === "dark");

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AuthProvider>
      <BrowserRouter>
        <NavBar/>
        <AppRouter />
      </BrowserRouter>
    </AuthProvider>
  </React.StrictMode>
);
