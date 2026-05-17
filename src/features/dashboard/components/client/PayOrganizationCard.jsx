import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send } from "lucide-react";
import { Controller, useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../../shared/api/apiError";
import { useToast } from "../../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../../shared/components/ui/Button";
import { Card, CardHeader } from "../../../../shared/components/ui/Card";
import { EmptyState } from "../../../../shared/components/ui/EmptyState";
import { Input } from "../../../../shared/components/ui/Input";
import { createPagoOrganizacion, movementQueryKeys } from "../../../movimientos/api";
import { WalletSelect } from "../../../movimientos/components/WalletSelect";
import { pagoOrganizacionSchema } from "../../../movimientos/schemas";
import { walletQueryKeys } from "../../../wallets/api";

function activeWallets(wallets) {
  return wallets.filter((wallet) => wallet.estado === "activa");
}

function toPayload(values) {
  return {
    wallet_origen_id: values.wallet_origen_id,
    wallet_destino_id: values.wallet_destino_id.trim(),
    monto: values.monto,
    descripcion: values.descripcion,
    referencia_externa: values.referencia_externa,
  };
}

export function PayOrganizationCard({ wallets = [], loading = false }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const availableWallets = activeWallets(wallets);

  const {
    control,
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(pagoOrganizacionSchema),
    defaultValues: {
      wallet_origen_id: "",
      wallet_destino_id: "",
      monto: "",
      descripcion: "",
      referencia_externa: "",
    },
  });

  const mutation = useMutation({
    mutationFn: (values) => createPagoOrganizacion(toPayload(values)),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: movementQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: walletQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      showToast({
        title: "Pago registrado",
        message: "El pago a la organizacion se registro correctamente.",
      });
      reset();
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
    if (mutation.isPending || availableWallets.length === 0) {
      return;
    }
    mutation.mutate(values);
  };

  return (
    <Card>
      <CardHeader title="Pagar a organizacion" description="Usa una wallet propia y el ID de la wallet destino." />
      {loading ? <div className="h-64 animate-pulse rounded-md bg-slate-100" /> : null}
      {!loading && availableWallets.length === 0 ? (
        <EmptyState title="No hay wallet activa para pagar" description="Necesitas una wallet activa asignada para iniciar un pago." />
      ) : null}
      {!loading && availableWallets.length > 0 ? (
        <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
          <Controller
            control={control}
            name="wallet_origen_id"
            render={({ field }) => (
              <WalletSelect wallets={availableWallets} label="Wallet origen" error={errors.wallet_origen_id?.message} {...field} />
            )}
          />
          <Input
            label="Wallet destino organizacion ID"
            error={errors.wallet_destino_id?.message}
            hint="Pedile este ID a la organizacion si no aparece en tus movimientos."
            {...register("wallet_destino_id")}
          />
          <Input label="Monto" inputMode="decimal" placeholder="1000.00" error={errors.monto?.message} {...register("monto")} />
          <Input label="Descripcion" error={errors.descripcion?.message} hint="Opcional" {...register("descripcion")} />
          <Input
            label="Referencia externa"
            error={errors.referencia_externa?.message}
            hint="Opcional"
            {...register("referencia_externa")}
          />
          {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
          <div className="flex justify-end">
            <Button type="submit" icon={Send} loading={mutation.isPending}>
              Pagar
            </Button>
          </div>
        </form>
      ) : null}
    </Card>
  );
}
