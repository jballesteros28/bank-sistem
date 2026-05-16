import { Modal } from "../../../shared/components/ui/Modal";
import { CreateOrganizationWalletForm } from "./CreateOrganizationWalletForm";

export function CreateOrganizationWalletModal({ open, onClose }) {
  return (
    <Modal open={open} title="Crear wallet de organizacion" onClose={onClose}>
      <CreateOrganizationWalletForm onCreated={onClose} onCancel={onClose} />
    </Modal>
  );
}
