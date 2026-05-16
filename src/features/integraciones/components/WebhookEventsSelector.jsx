import { WEBHOOK_EVENT_OPTIONS } from "../schemas";

export function WebhookEventsSelector({ value = [], onChange, error, disabled = false }) {
  const selected = new Set(value);

  const toggleEvent = (event) => {
    if (disabled) {
      return;
    }

    const next = selected.has(event) ? value.filter((item) => item !== event) : [...value, event];
    onChange(next);
  };

  return (
    <div className="space-y-2">
      <div>
        <p className="text-sm font-medium text-slate-700">Eventos</p>
        <p className="mt-0.5 text-xs text-slate-500">El webhook recibira deliveries para los eventos seleccionados.</p>
      </div>
      <div className="grid gap-2 sm:grid-cols-2">
        {WEBHOOK_EVENT_OPTIONS.map((event) => (
          <label
            key={event.value}
            className={[
              "flex items-center gap-3 rounded-md border px-3 py-3 text-sm transition",
              selected.has(event.value) ? "border-brand-primary bg-brand-primary/5" : "border-slate-200 bg-white",
              disabled ? "cursor-not-allowed opacity-60" : "cursor-pointer hover:border-slate-300",
            ].join(" ")}
          >
            <input
              type="checkbox"
              className="h-4 w-4 rounded border-slate-300 text-brand-primary focus:ring-brand-primary"
              checked={selected.has(event.value)}
              disabled={disabled}
              onChange={() => toggleEvent(event.value)}
            />
            <span>
              <span className="block font-medium text-slate-800">{event.label}</span>
              <span className="mt-0.5 block text-xs text-slate-500">{event.value}</span>
            </span>
          </label>
        ))}
      </div>
      {error ? <p className="text-xs font-medium text-rose-600">{error}</p> : null}
    </div>
  );
}
