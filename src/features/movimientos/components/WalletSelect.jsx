import { formatCurrency } from "../../../shared/utils/formatters";
import { walletDisplayName } from "../movementUtils";

function optionLabel(wallet) {
  const owner = wallet.owner_type === "organizacion" ? "org" : "usuario";
  const type = wallet.tipo || "wallet";
  const balance = formatCurrency(wallet.saldo, wallet.moneda);
  return `${walletDisplayName(wallet)} - ${type} - ${wallet.moneda} - ${balance} - ${owner}`;
}

export function WalletSelect({
  wallets = [],
  label,
  value,
  onChange,
  filter,
  error,
  disabled = false,
  placeholder = "Selecciona una wallet",
}) {
  const options = typeof filter === "function" ? wallets.filter(filter) : wallets;

  return (
    <label className="block space-y-1.5">
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <select
        className={[
          "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
          error ? "border-rose-300" : "border-slate-200",
        ].join(" ")}
        value={value || ""}
        onChange={(event) => onChange(event.target.value)}
        disabled={disabled}
      >
        <option value="">{placeholder}</option>
        {options.map((wallet) => (
          <option key={wallet.id} value={wallet.id}>
            {optionLabel(wallet)}
          </option>
        ))}
      </select>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
      {!error && !options.length ? <span className="block text-xs text-slate-500">No hay wallets disponibles.</span> : null}
    </label>
  );
}
