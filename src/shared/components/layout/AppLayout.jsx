import { useEffect } from "react";
import { Outlet } from "react-router-dom";

import { useBranding } from "../../../features/organizacion/api";
import { Sidebar } from "./Sidebar";
import { Topbar } from "./Topbar";

function applyBranding(branding) {
  if (!branding) {
    return;
  }
  const root = document.documentElement;
  if (branding.color_primario) {
    root.style.setProperty("--color-primary", branding.color_primario);
  }
  if (branding.color_secundario) {
    root.style.setProperty("--color-secondary", branding.color_secundario);
  }
}

export function AppLayout() {
  const brandingQuery = useBranding();
  const branding = brandingQuery.data;

  useEffect(() => {
    applyBranding(branding);
  }, [branding]);

  return (
    <div className="flex min-h-screen bg-slate-50 text-slate-900">
      <Sidebar branding={branding} />
      <div className="flex min-w-0 flex-1 flex-col">
        <Topbar branding={branding} />
        <main className="flex-1 px-4 py-6 lg:px-8">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
