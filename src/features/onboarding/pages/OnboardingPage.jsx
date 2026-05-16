import { Link, Navigate } from "react-router-dom";

import { Card } from "../../../shared/components/ui/Card";
import { useAuth } from "../../../shared/hooks/useAuth";
import { APP_NAME } from "../../../shared/utils/constants";
import { OnboardingForm } from "../components/OnboardingForm";

export function OnboardingPage() {
  const { isAuthenticated } = useAuth();

  if (isAuthenticated) {
    return <Navigate to="/dashboard" replace />;
  }

  return (
    <div className="w-full max-w-3xl">
      <div className="mb-6">
        <p className="text-sm font-semibold text-brand-primary">{APP_NAME}</p>
        <h1 className="mt-2 text-2xl font-semibold tracking-normal text-slate-950">Alta de organizacion</h1>
        <p className="mt-2 text-sm text-slate-500">Crea el tenant inicial, owner y wallets base para empezar a operar.</p>
      </div>
      <Card>
        <OnboardingForm />
      </Card>
      <p className="mt-5 text-center text-sm text-slate-500">
        Ya tienes cuenta?{" "}
        <Link className="font-medium text-brand-primary hover:underline" to="/login">
          Ir a login
        </Link>
      </p>
    </div>
  );
}
