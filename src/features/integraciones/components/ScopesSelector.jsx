import { API_KEY_SCOPE_OPTIONS } from "../schemas";

export function ScopesSelector({ value = [], onChange, error, disabled = false }) {
  const selected = new Set(value);

  const toggleScope = (scope) => {
    if (disabled) {
      return;
    }

    const next = selected.has(scope) ? value.filter((item) => item !== scope) : [...value, scope];
    onChange(next);
  };

  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm font-medium text-slate-700">Scopes</p>
        <p className="mt-0.5 text-xs text-slate-500">Selecciona los permisos disponibles para esta API Key.</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {API_KEY_SCOPE_OPTIONS.map((scope) => (
          <label
            key={scope.value}
            className={[
              "flex min-h-20 items-start gap-3 rounded-md border px-3 py-3 text-sm transition",
              selected.has(scope.value) ? "border-brand-primary bg-brand-primary/5" : "border-slate-200 bg-white",
              disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:border-slate-300",
            ].join(" ")}
          >
            <input
              type="checkbox"
              className="mt-1 h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
              checked={selected.has(scope.value)}
              disabled={disabled}
              onChange={() => toggleScope(scope.value)}
            />
            <span>
              <span className="block font-medium text-slate-800">{scope.label}</span>
              <span className="mt-0.5 block text-xs text-slate-500">{scope.description}</span>
            </span>
          </label>
        ))}
      </div>
      {error ? <p className="text-xs font-medium text-rose-600">{error}</p> : null}
    </div>
  );
}
