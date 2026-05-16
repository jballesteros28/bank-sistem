import { forwardRef } from "react";

export const Input = forwardRef(function Input(
  { label, error, hint, id, className = "", containerClassName = "", ...props },
  ref,
) {
  const inputId = id || props.name;
  const classes = [
    "block h-11 w-full rounded-md border bg-white px-3 text-sm text-slate-900 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-primary focus:ring-2 focus:ring-brand-primary/20",
    error ? "border-rose-300" : "border-slate-200",
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <label className={["block space-y-1.5", containerClassName].filter(Boolean).join(" ")} htmlFor={inputId}>
      {label ? <span className="text-sm font-medium text-slate-700">{label}</span> : null}
      <input id={inputId} ref={ref} className={classes} {...props} />
      {error ? <span className="block text-xs font-medium text-rose-600">{error}</span> : null}
      {!error && hint ? <span className="block text-xs text-slate-500">{hint}</span> : null}
    </label>
  );
});
