import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";
import { Building2 } from "lucide-react";
import { useEffect } from "react";
import { useForm, useWatch } from "react-hook-form";
import { useNavigate } from "react-router-dom";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { registerOrganization } from "../api";
import { onboardingSchema } from "../schemas";

const ONBOARDING_SUCCESS_MESSAGE = "Organizaci\u00f3n creada correctamente. Ya pod\u00e9s iniciar sesi\u00f3n.";

function normalizeSlug(value = "") {
  return value
    .normalize("NFD")
    .replace(/[\u0300-\u036f]/g, "")
    .toLowerCase()
    .trim()
    .replace(/\s+/g, "-")
    .replace(/[^a-z0-9-]/g, "")
    .replace(/-+/g, "-")
    .replace(/^-|-$/g, "");
}

function toOnboardingPayload(values) {
  return {
    organizacion: {
      nombre: values.organizacion.nombre,
      slug: normalizeSlug(values.organizacion.slug),
      email_contacto: values.organizacion.email_contacto,
    },
    owner: {
      nombre: values.owner.nombre,
      email: values.owner.email,
      password: values.owner.password,
    },
  };
}

export function OnboardingForm() {
  const navigate = useNavigate();

  const {
    control,
    register,
    handleSubmit,
    setError,
    setValue,
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
        confirmar_password: "",
      },
    },
  });

  const organizationName = useWatch({ control, name: "organizacion.nombre" });
  const slug = useWatch({ control, name: "organizacion.slug" });
  const slugField = register("organizacion.slug");

  useEffect(() => {
    if (!slug && organizationName) {
      setValue("organizacion.slug", normalizeSlug(organizationName), {
        shouldDirty: false,
        shouldValidate: false,
      });
    }
  }, [organizationName, setValue, slug]);

  const mutation = useMutation({
    mutationFn: registerOrganization,
    onSuccess: () => {
      window.setTimeout(
        () => navigate("/login", { replace: true, state: { message: ONBOARDING_SUCCESS_MESSAGE } }),
        700,
      );
    },
    onError: (error) => {
      const validationErrors = getApiValidationErrors(error);
      Object.entries(validationErrors).forEach(([field, message]) => {
        setError(field, { message });
      });
      setError("root", { message: getApiErrorMessage(error) });
    },
  });

  const onSubmit = (values) => {
    if (mutation.isPending) {
      return;
    }
    mutation.mutate(toOnboardingPayload(values));
  };

  return (
    <form className="space-y-6" onSubmit={handleSubmit(onSubmit)}>
      <div>
        <h2 className="text-sm font-semibold text-slate-950">Organizacion</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Input label="Nombre" error={errors.organizacion?.nombre?.message} {...register("organizacion.nombre")} />
          <Input
            label="Slug"
            error={errors.organizacion?.slug?.message}
            hint="ejemplo: mi-comercio"
            {...slugField}
            onChange={(event) => {
              event.target.value = normalizeSlug(event.target.value);
              slugField.onChange(event);
            }}
          />
          <Input label="Email contacto" type="email" containerClassName="sm:col-span-2" error={errors.organizacion?.email_contacto?.message} {...register("organizacion.email_contacto")} />
        </div>
      </div>
      <div>
        <h2 className="text-sm font-semibold text-slate-950">Owner</h2>
        <div className="mt-3 grid gap-4 sm:grid-cols-2">
          <Input label="Nombre" error={errors.owner?.nombre?.message} {...register("owner.nombre")} />
          <Input label="Email" type="email" error={errors.owner?.email?.message} {...register("owner.email")} />
          <Input label="Password" type="password" autoComplete="new-password" error={errors.owner?.password?.message} {...register("owner.password")} />
          <Input
            label="Confirmar password"
            type="password"
            autoComplete="new-password"
            error={errors.owner?.confirmar_password?.message}
            {...register("owner.confirmar_password")}
          />
        </div>
      </div>
      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
      {mutation.isSuccess ? <p className="rounded-md bg-emerald-50 px-3 py-2 text-sm font-medium text-emerald-700">{ONBOARDING_SUCCESS_MESSAGE}</p> : null}
      <Button type="submit" icon={Building2} loading={mutation.isPending}>
        Crear organizacion
      </Button>
    </form>
  );
}
