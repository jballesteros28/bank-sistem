import { Loader2 } from "lucide-react";

const variants = {
  primary: "bg-brand-primary text-white hover:brightness-95 focus-visible:ring-brand-primary",
  secondary: "bg-white text-slate-900 ring-1 ring-slate-200 hover:bg-slate-50 focus-visible:ring-brand-primary",
  ghost: "bg-transparent text-slate-700 hover:bg-slate-100 focus-visible:ring-brand-primary",
  danger: "bg-rose-600 text-white hover:bg-rose-700 focus-visible:ring-rose-600",
};

const sizes = {
  sm: "h-9 px-3 text-sm",
  md: "h-10 px-4 text-sm",
  lg: "h-11 px-5 text-base",
};

export function Button({
  children,
  type = "button",
  variant = "primary",
  size = "md",
  loading = false,
  icon: Icon,
  className = "",
  disabled,
  ...props
}) {
  const classes = [
    "inline-flex items-center justify-center gap-2 rounded-md font-medium shadow-sm transition focus:outline-none focus-visible:ring-2 focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-60",
    variants[variant] || variants.primary,
    sizes[size] || sizes.md,
    className,
  ]
    .filter(Boolean)
    .join(" ");

  return (
    <button type={type} className={classes} disabled={disabled || loading} {...props}>
      {loading ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : Icon ? <Icon className="h-4 w-4" aria-hidden="true" /> : null}
      <span>{children}</span>
    </button>
  );
}
