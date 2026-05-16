export function Card({ children, className = "", as: Component = "section" }) {
  return (
    <Component className={["rounded-lg border border-slate-200 bg-white p-5 shadow-sm", className].filter(Boolean).join(" ")}>
      {children}
    </Component>
  );
}

export function CardHeader({ title, description, action }) {
  return (
    <div className="mb-5 flex flex-col gap-3 sm:flex-row sm:items-start sm:justify-between">
      <div>
        <h2 className="text-base font-semibold text-slate-950">{title}</h2>
        {description ? <p className="mt-1 text-sm text-slate-500">{description}</p> : null}
      </div>
      {action ? <div className="shrink-0">{action}</div> : null}
    </div>
  );
}
