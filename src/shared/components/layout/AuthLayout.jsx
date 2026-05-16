import { Outlet } from "react-router-dom";

export function AuthLayout() {
  return (
    <main className="min-h-screen bg-slate-50">
      <div className="mx-auto flex min-h-screen w-full items-center justify-center px-4 py-10">
        <Outlet />
      </div>
    </main>
  );
}
