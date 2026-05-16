export function ColorInput({ label, error, value, onChange, onBlur, name, disabled = false }) {
  const isHex = /^#(?:[0-9a-fA-F]{3}|[0-9a-fA-F]{6})$/.test(value || "");
  const colorValue = isHex ? value : "#0f766e";

  return (
    <label className="block space-y-1.5">
      <span className="text-sm font-medium text-slate-700">{label}</span>
      <div className="flex gap-2">
        <input
          type="color"
          name={name}
          className="h-11 w-14 shrink-0 rounded-md border border-slate-200 bg-white p-1 shadow-sm disabled:cursor-not-allowed disabled:opacity-60"
          value={colorValue}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
        />
        <input
          name={name}
          className={[
            "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20 disabled:cursor-not-allowed disabled:bg-slate-50 disabled:text-slate-500",
            error ? "border-rose-300" : "border-slate-200",
          ].join(" ")}
          value={value || ""}
          onChange={onChange}
          onBlur={onBlur}
          disabled={disabled}
        />
      </div>
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
    </label>
  );
}
