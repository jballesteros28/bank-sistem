import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { useForm } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { getApiErrorMessage } from "../../../shared/api/apiError";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { registerOrganization } from "../api";
import { onboardingSchema } from "../schemas";

export function OnboardingForm() {
  const navigate = useNavigate();

  const {
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(onboardingSchema),
    defaultValues: {
      organizacion: {
        nombre: "",
        slug: "",
        email_contacto: "",
      },
      owner: {
        nombre: "",
        email: "",
        password: "",
      },
    },
  });

  const mutation = useMutation({
    mutationFn: registerOrganization,
    onSuccess: () => {
      window.setTimeout(() => navigate("/login", { replace: true, state: { onboardingSuccess: true } }), 700);
    },
    onError: (error) => {
      setError("root", { message: getApiErrorMessage(error) });
    },
  });

  return (
    <form className="space-y-6" onSubmit={handleSubmit((values) => mutation.mutate(values))}>
      <div>
        <h2 className="text-sm font-semibold text-slate-950">Organizacion</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Input label="Nombre" error={errors.organizacion?.nombre?.message} {...register("organizacion.nombre")} />
          <Input label="Slug" error={errors.organizacion?.slug?.message} hint="ejemplo: mi-comercio" {...register("organizacion.slug")} />
          <Input label="Email contacto" type="email" containerClassName="sm:col-span-2" error={errors.organizacion?.email_contacto?.message} {...register("organizacion.email_contacto")} />
        </div>
      </div>
      <div>
        <h2 className="text-sm font-semibold text-slate-950">Owner</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Input label="Nombre" error={errors.owner?.nombre?.message} {...register("owner.nombre")} />
          <Input label="Email" type="email" error={errors.owner?.email?.message} {...register("owner.email")} />
          <Input label="Password" type="password" containerClassName="sm:col-span-2" error={errors.owner?.password?.message} {...register("owner.password")} />
        </div>
      </div>
      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
      {mutation.isSuccess ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">Organizacion creada correctamente.</p> : null}
      <Button type="submit" icon={Building2} loading={mutation.isPending}>
        Crear organizacion
      </Button>
    </form>
  );
}
