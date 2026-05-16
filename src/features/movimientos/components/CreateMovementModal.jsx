import { useMemo, useState } from "react";

import { Modal } from "../../../shared/components/ui/Modal";
import { canCreateClientPayment, canCreateFinancialMovement } from "../../../shared/utils/roles";
import { getMovementTypeLabel } from "../movementUtils";
import { MovementForm } from "./MovementForm";

const financialOptions = ["deposito", "retiro", "transferencia", "pago_organizacion", "cashback", "ajuste_admin"];
const clientOptions = ["pago_organizacion"];

export function CreateMovementModal({
  open,
  onClose,
  user,
  allWallets = [],
  userWallets = [],
  organizationWallets = [],
}) {
  const options = useMemo(() => {
    if (canCreateFinancialMovement(user)) {
      return financialOptions;
    }
    if (canCreateClientPayment(user)) {
      return clientOptions;
    }
    return [];
  }, [user]);

  const [movementType, setMovementType] = useState("");
  const selectedMovementType = options.includes(movementType) ? movementType : options[0] || "";

  return (
    <Modal open={open} title="Crear movimiento" onClose={onClose}>
      {options.length ? (
        <div className="space-y-5">
          <div className="flex flex-wrap gap-2">
            {options.map((option) => (
              <button
                key={option}
                type="button"
                className={[
                  "rounded-md px-3 py-2 text-sm font-medium ring-1 transition",
                  selectedMovementType === option
                    ? "bg-brand-primary text-white ring-brand-primary"
                    : "bg-white text-slate-700 ring-slate-200 hover:bg-slate-50",
                ].join(" ")}
                onClick={() => setMovementType(option)}
              >
                {getMovementTypeLabel(option)}
              </button>
            ))}
          </div>
          {selectedMovementType ? (
            <MovementForm
              key={selectedMovementType}
              movementType={selectedMovementType}
              allWallets={allWallets}
              userWallets={userWallets}
              organizationWallets={organizationWallets}
              onCreated={onClose}
              onCancel={onClose}
            />
          ) : null}
        </div>
      ) : (
        <p className="text-sm text-slate-500">No tenes permisos para crear movimientos.</p>
      )}
    </Modal>
  );
}
