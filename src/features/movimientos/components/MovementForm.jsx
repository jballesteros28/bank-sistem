import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Send } from "lucide-react";
import { Controller, useForm, useWatch } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Input } from "../../../shared/components/ui/Input";
import { walletQueryKeys } from "../../wallets/api";
import {
  createAjusteAdmin,
  createCashback,
  createDeposito,
  createPagoOrganizacion,
  createRetiro,
  createTransferencia,
  movementQueryKeys,
} from "../api";
import { getMovementTypeLabel } from "../movementUtils";
import { movementSchemas } from "../schemas";
import { WalletSelect } from "./WalletSelect";

const mutationByType = {
  deposito: createDeposito,
  retiro: createRetiro,
  transferencia: createTransferencia,
  pago_organizacion: createPagoOrganizacion,
  cashback: createCashback,
  ajuste_admin: createAjusteAdmin,
};

const defaultValuesByType = {
  deposito: {
    wallet_destino_id: "",
    monto: "",
    descripcion: "",
    referencia_externa: "",
  },
  retiro: {
    wallet_origen_id: "",
    monto: "",
    descripcion: "",
    referencia_externa: "",
  },
  transferencia: {
    wallet_origen_id: "",
    wallet_destino_id: "",
    monto: "",
    descripcion: "",
    referencia_externa: "",
  },
  pago_organizacion: {
    wallet_origen_id: "",
    wallet_destino_id: "",
    monto: "",
    descripcion: "",
    referencia_externa: "",
  },
  cashback: {
    wallet_destino_id: "",
    monto: "",
    descripcion: "",
  },
  ajuste_admin: {
    wallet_id: "",
    operacion: "credito",
    monto: "",
    descripcion: "",
  },
};

function SelectField({ label, error, children, ...props }) {
  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <select
        className={[
          "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
          error ? "border-rose-300" : "border-slate-200",
        ].join(" ")}
        {...props}
      >
        {children}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}

function cleanPayload(payload) {
  return Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== undefined && value !== ""));
}

function toPayload(type, values) {
  if (type === "ajuste_admin") {
    return cleanPayload({
      wallet_id: values.wallet_id,
      operacion: values.operacion,
      monto: values.monto,
      descripcion: values.descripcion,
      motivo: values.descripcion,
    });
  }

  return cleanPayload(values);
}

function activeWallets(wallets) {
  return wallets.filter((wallet) => wallet.estado === "activa");
}

export function MovementForm({
  movementType,
  allWallets = [],
  userWallets = [],
  organizationWallets = [],
  onCreated,
  onCancel,
}) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const schema = movementSchemas[movementType];

  const {
    control,
    register,
    handleSubmit,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(schema),
    defaultValues: defaultValuesByType[movementType],
  });

  const originWalletId = useWatch({ control, name: "wallet_origen_id" });
  const availableAllWallets = activeWallets(allWallets);
  const availableUserWallets = activeWallets(userWallets);
  const availableOrganizationWallets = activeWallets(organizationWallets);
  const originWallet = availableAllWallets.find((wallet) => wallet.id === originWalletId);
  const sameCurrency = (wallet) => !originWallet || wallet.moneda === originWallet.moneda;
  const notOrigin = (wallet) => wallet.id !== originWalletId;

  const mutation = useMutation({
    mutationFn: (values) => mutationByType[movementType](toPayload(movementType, values)),
    onSuccess: (movement) => {
      queryClient.invalidateQueries({ queryKey: movementQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: walletQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      showToast({
        title: "Movimiento creado",
        message: `${getMovementTypeLabel(movementType)} registrado correctamente.`,
      });
      onCreated?.(movement);
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
    mutation.mutate(values);
  };

  const renderWalletFields = () => {
    if (movementType === "deposito") {
      return (
        <Controller
          control={control}
          name="wallet_destino_id"
          render={({ field }) => (
            <WalletSelect wallets={availableAllWallets} label="Wallet destino" error={errors.wallet_destino_id?.message} {...field} />
          )}
        />
      );
    }

    if (movementType === "retiro") {
      return (
        <Controller
          control={control}
          name="wallet_origen_id"
          render={({ field }) => (
            <WalletSelect wallets={availableAllWallets} label="Wallet origen" error={errors.wallet_origen_id?.message} {...field} />
          )}
        />
      );
    }

    if (movementType === "transferencia") {
      return (
        <div className="grid gap-4 sm:grid-cols-2">
          <Controller
            control={control}
            name="wallet_origen_id"
            render={({ field }) => (
              <WalletSelect wallets={availableAllWallets} label="Wallet origen" error={errors.wallet_origen_id?.message} {...field} />
            )}
          />
          <Controller
            control={control}
            name="wallet_destino_id"
            render={({ field }) => (
              <WalletSelect
                wallets={availableAllWallets}
                label="Wallet destino"
                error={errors.wallet_destino_id?.message}
                filter={(wallet) => notOrigin(wallet) && sameCurrency(wallet)}
                {...field}
              />
            )}
          />
        </div>
      );
    }

    if (movementType === "pago_organizacion") {
      const destinationWallets = availableOrganizationWallets.filter((wallet) => notOrigin(wallet) && sameCurrency(wallet));

      return (
        <div className="grid gap-4 sm:grid-cols-2">
          <Controller
            control={control}
            name="wallet_origen_id"
            render={({ field }) => (
              <WalletSelect wallets={availableUserWallets} label="Wallet origen usuario" error={errors.wallet_origen_id?.message} {...field} />
            )}
          />
          {destinationWallets.length ? (
            <Controller
              control={control}
              name="wallet_destino_id"
              render={({ field }) => (
                <WalletSelect wallets={destinationWallets} label="Wallet destino organizacion" error={errors.wallet_destino_id?.message} {...field} />
              )}
            />
          ) : (
            <Input
              label="Wallet destino organizacion ID"
              error={errors.wallet_destino_id?.message}
              hint="No hay wallets de organizacion disponibles para seleccionar con tu sesion."
              {...register("wallet_destino_id")}
            />
          )}
        </div>
      );
    }

    if (movementType === "cashback") {
      return (
        <Controller
          control={control}
          name="wallet_destino_id"
          render={({ field }) => (
            <WalletSelect wallets={availableUserWallets} label="Wallet destino usuario" error={errors.wallet_destino_id?.message} {...field} />
          )}
        />
      );
    }

    if (movementType === "ajuste_admin") {
      return (
        <div className="grid gap-4 sm:grid-cols-2">
          <Controller
            control={control}
            name="wallet_id"
            render={({ field }) => (
              <WalletSelect wallets={availableAllWallets} label="Wallet" error={errors.wallet_id?.message} {...field} />
            )}
          />
          <SelectField label="Operacion" error={errors.operacion?.message} {...register("operacion")}>
            <option value="credito">Credito</option>
            <option value="debito">Debito</option>
          </SelectField>
        </div>
      );
    }

    return null;
  };

  return (
    <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
      {renderWalletFields()}
      <Input label="Monto" inputMode="decimal" placeholder="1000.00" error={errors.monto?.message} {...register("monto")} />
      <Input
        label={movementType === "ajuste_admin" ? "Descripcion / motivo" : "Descripcion"}
        error={errors.descripcion?.message}
        hint={movementType === "ajuste_admin" ? "Requerida para auditoria." : "Opcional"}
        {...register("descripcion")}
      />
      {["deposito", "retiro", "transferencia", "pago_organizacion"].includes(movementType) ? (
        <Input
          label="Referencia externa"
          error={errors.referencia_externa?.message}
          hint="Opcional"
          {...register("referencia_externa")}
        />
      ) : null}
      {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
      <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
        <Button type="button" variant="secondary" onClick={onCancel} disabled={mutation.isPending}>
          Cancelar
        </Button>
        <Button type="submit" icon={Send} loading={mutation.isPending}>
          Crear movimiento
        </Button>
      </div>
    </form>
  );
}
