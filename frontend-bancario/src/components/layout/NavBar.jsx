import { useState } from "react";
import { Bell, Menu, X } from "lucide-react";
import { NavLink, Link, useNavigate } from "react-router-dom";
import ThemeToggle from "../ui/ThemeToggle";

export default function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false);
  const [dropdownOpen, setDropdownOpen] = useState(false);
  const navigate = useNavigate();

  // 🔹 Clases dinámicas para NavLink activo
  const navLinkClass = ({ isActive }) =>
    isActive
      ? "rounded-md bg-gray-900 px-3 py-2 text-sm font-medium text-white"
      : "rounded-md px-3 py-2 text-sm font-medium text-gray-300 hover:bg-gray-700 hover:text-white transition";

  // 🔹 Logout handler
  const handleLogout = () => {
    localStorage.removeItem("bank.jwt");
    navigate("/auth/login");
  };

  return (
    <nav
      className={`
        bg-gray-800/80 backdrop-blur-md text-white shadow-md
        dark:bg-gray-900/70 dark:shadow-gray-800/30 transition-colors
      `}
    >
      <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
        <div className="flex h-16 items-center justify-between">
          {/* --- Logo + Nombre --- */}
          <Link to="/auth/login" className="flex items-center gap-2">
            <img
              className="h-8 w-auto"
              src="data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSIyNCIgaGVpZ2h0PSIyNCIgdmlld0JveD0iMCAwIDI0IDI0IiBmaWxsPSJub25lIiBzdHJva2U9IiNmZmZmZmYiIHN0cm9rZS13aWR0aD0iMiIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBjbGFzcz0ibHVjaWRlIGx1Y2lkZS1sYW5kbWFyay1pY29uIGx1Y2lkZS1sYW5kbWFyayI+PHBhdGggZD0iTTEwIDE4di03Ii8+PHBhdGggZD0iTTExLjEyIDIuMTk4YTIgMiAwIDAgMSAxLjc2LjAwNmw3Ljg2NiAzLjg0N2MuNDc2LjIzMy4zMS45NDktLjIyLjk0OUgzLjQ3NGMtLjUzIDAtLjY5NS0uNzE2LS4yMi0uOTQ5eiIvPjxwYXRoIGQ9Ik0xNCAxOHYtNyIvPjxwYXRoIGQ9Ik0xOCAxOHYtNyIvPjxwYXRoIGQ9Ik0zIDIyaDE4Ii8+PHBhdGggZD0iTTYgMTh2LTciLz48L3N2Zz4="
              alt="Banco Virtual"
            />
            <span className="font-semibold text-lg tracking-wide">
              Banco Virtual
            </span>
          </Link>

          {/* --- Menú Desktop --- */}
          <div className="hidden sm:flex space-x-4">
            <NavLink to="/admin/dashboard" className={navLinkClass}>
              Dashboard
            </NavLink>
            <NavLink to="/cuentas/listar" className={navLinkClass}>
              Cuentas
            </NavLink>
            <NavLink to="/transacciones" className={navLinkClass}>
              Transacciones
            </NavLink>
            <NavLink to="/notificaciones/logs" className={navLinkClass}>
              Notificaciones
            </NavLink>
          </div>

          {/* --- Acciones derechas --- */}
          <div className="flex items-center space-x-4">
            {/* 🔔 Notificaciones */}
            <button
              type="button"
              className="p-2 rounded-full text-gray-400 hover:text-white hover:bg-gray-700"
            >
              <Bell className="h-5 w-5" />
              <span className="sr-only">Ver notificaciones</span>
            </button>

            {/* 🌗 Theme toggle */}
            <ThemeToggle />

            {/* 👤 Perfil usuario */}
            <div className="relative">
              <button
                onClick={() => setDropdownOpen(!dropdownOpen)}
                className="flex rounded-full focus:outline-none focus:ring-2 focus:ring-indigo-500"
              >
                <img
                  className="h-8 w-8 rounded-full object-cover"
                  src="https://images.unsplash.com/photo-1472099645785-5658abf4ff4e?q=80&w=256&h=256&auto=format&fit=facearea&facepad=2"
                  alt="Perfil"
                />
              </button>

              {/* --- Dropdown --- */}
              {dropdownOpen && (
                <div
                  className="absolute right-0 mt-2 w-48 rounded-lg 
                            bg-white/90 dark:bg-gray-800/90 backdrop-blur-md 
                            shadow-lg ring-1 ring-black/10 dark:ring-white/10 z-50"
                >
                  <Link
                    to="/usuarios/perfil"
                    className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100/70 dark:hover:bg-gray-700"
                  >
                    Perfil
                  </Link>
                  <Link
                    to="/usuarios/configuracion"
                    className="block px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100/70 dark:hover:bg-gray-700"
                  >
                    Configuración
                  </Link>
                  <button
                    onClick={handleLogout}
                    className="w-full text-left px-4 py-2 text-sm text-gray-700 dark:text-gray-200 hover:bg-gray-100/70 dark:hover:bg-gray-700"
                  >
                    Cerrar sesión
                  </button>
                </div>
              )}
            </div>

            {/* --- Botón Mobile --- */}
            <button
              onClick={() => setMenuOpen(!menuOpen)}
              className="sm:hidden p-2 rounded-md text-gray-400 hover:bg-gray-700 hover:text-white"
            >
              {menuOpen ? <X className="h-6 w-6" /> : <Menu className="h-6 w-6" />}
            </button>
          </div>
        </div>
      </div>

      {/* --- Menú Mobile --- */}
      {menuOpen && (
        <div className="sm:hidden px-2 pt-2 pb-3 space-y-1 bg-gray-800/95 backdrop-blur-md border-t border-gray-700/40">
          <NavLink to="/admin/dashboard" className={navLinkClass} onClick={() => setMenuOpen(false)}>
            Dashboard
          </NavLink>
          <NavLink to="/cuentas/listar" className={navLinkClass} onClick={() => setMenuOpen(false)}>
            Cuentas
          </NavLink>
          <NavLink to="/transacciones" className={navLinkClass} onClick={() => setMenuOpen(false)}>
            Transacciones
          </NavLink>
          <NavLink to="/notificaciones/logs" className={navLinkClass} onClick={() => setMenuOpen(false)}>
            Notificaciones
          </NavLink>
          <button
            onClick={() => {
              handleLogout();
              setMenuOpen(false);
            }}
            className="block w-full text-left rounded-md px-3 py-2 text-base font-medium text-gray-300 hover:bg-gray-700 hover:text-white"
          >
            Cerrar sesión
          </button>
        </div>
      )}
    </nav>
  );
}

