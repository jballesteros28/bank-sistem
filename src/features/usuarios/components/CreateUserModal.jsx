import { Modal } from "../../../shared/components/ui/Modal";
import { CreateUserForm } from "./CreateUserForm";

export function CreateUserModal({ open, onClose }) {
  return (
    <Modal open={open} title="Crear usuario" onClose={onClose}>
      <CreateUserForm onCreated={onClose} onCancel={onClose} />
    </Modal>
  );
}
