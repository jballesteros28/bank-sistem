import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { RotateCcw } from "lucide-react";
import { useEffect } from "react";
import { useForm } from "react-hook-form";

import { getApiErrorMessage, getApiValidationErrors } from "../../../shared/api/apiError";
import { useToast } from "../../../shared/components/feedback/ToastProvider";
import { Button } from "../../../shared/components/ui/Button";
import { Modal } from "../../../shared/components/ui/Modal";
import { walletQueryKeys } from "../../wallets/api";
import { createReversa, movementQueryKeys } from "../api";
import { reversaSchema } from "../schemas";

export function ReverseMovementModal({ movement, onClose }) {
  const queryClient = useQueryClient();
  const { showToast } = useToast();
  const {
    register,
    handleSubmit,
    reset,
    setError,
    formState: { errors },
  } = useForm({
    resolver: zodResolver(reversaSchema),
    defaultValues: {
      motivo_reversa: "",
    },
  });

  useEffect(() => {
    if (movement) {
      reset({ motivo_reversa: "" });
    }
  }, [movement, reset]);

  const mutation = useMutation({
    mutationFn: (values) => createReversa(movement.id, values),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: movementQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: walletQueryKeys.all });
      queryClient.invalidateQueries({ queryKey: ["dashboard"] });
      showToast({
        title: "Movimiento revertido",
        message: "La reversa fue registrada correctamente.",
      });
      onClose();
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
    if (!movement || mutation.isPending) {
      return;
    }
    mutation.mutate(values);
  };

  return (
    <Modal open={Boolean(movement)} title="Revertir movimiento" onClose={onClose}>
      <form className="space-y-5" onSubmit={handleSubmit(onSubmit)}>
        <p className="text-sm text-slate-500">
          La reversa genera un nuevo movimiento contable y marca el movimiento original como revertido.
        </p>
        <label className="block space-y-1.5">
          <span className="text-sm font-medium text-slate-700">Motivo de reversa</span>
          <textarea
            className={[
              "min-h-28 w-full rounded-md border bg-white px-3 py-2 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
              errors.motivo_reversa ? "border-rose-300" : "border-slate-200",
            ].join(" ")}
            placeholder="Error operativo, ajuste solicitado..."
            {...register("motivo_reversa")}
          />
          {errors.motivo_reversa?.message ? (
            <span className="block text-xs font-medium text-rose-600">{errors.motivo_reversa.message}</span>
          ) : null}
        </label>
        {errors.root?.message ? <p className="rounded-md bg-rose-50 px-3 py-2 text-sm font-medium text-rose-700">{errors.root.message}</p> : null}
        <div className="flex flex-col-reverse gap-3 sm:flex-row sm:justify-end">
          <Button type="button" variant="secondary" onClick={onClose} disabled={mutation.isPending}>
            Cancelar
          </Button>
          <Button type="submit" icon={RotateCcw} loading={mutation.isPending}>
            Revertir
          </Button>
        </div>
      </form>
    </Modal>
  );
}
