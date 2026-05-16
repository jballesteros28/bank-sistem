import { Link, Navigate, useLocation } from "react-router-dom";

import { Card } from "../../../shared/components/ui/Card";
import { useAuth } from "../../../shared/hooks/useAuth";
import { APP_NAME } from "../../../shared/utils/constants";
import { LoginForm } from "../components/LoginForm";

export function LoginPage() {
  const { isAuthenticated } = useAuth();
  const location = useLocation();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="w-full max-w-md">
      <div className="mb-6">
        <p className="text-sm font-semibold text-brand-primary">{APP_NAME}</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-slate-950">Acceso a la consola</h1>
        <p className="mt-2 text-sm text-slate-500">Gestiona wallets, movimientos, integraciones y branding desde un unico lugar.</p>
      </div>
      <Card>
        {location.state?.onboardingSuccess ? (
          <p className="mb-4 rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">
            Organizacion creada. Ya puedes ingresar con el owner.
          </p>
        ) : null}
        <LoginForm />
      </Card>
      <p className="mt-5 text-center text-sm text-slate-500">
        Nueva organizacion?{" "}
        <Link className="font-medium text-brand-primary hover:underline" to="/onboarding">
          Crear onboarding
        </Link>
      </p>
    </div>
  );
}
