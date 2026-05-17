import { Modal } from "../../../shared/components/ui/Modal";
import { RewardRuleForm } from "./RewardRuleForm";

export function RewardRuleModal({ open, rule, onClose }) {
  return (
    <Modal open={open} title={rule?.id ? "Editar regla" : "Crear regla"} onClose={onClose}>
      <RewardRuleForm rule={rule} onCancel={onClose} onSaved={onClose} />
    </Modal>
  );
}
