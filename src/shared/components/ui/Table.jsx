export function Table({ columns, rows, getRowKey, emptyMessage = "No hay datos para mostrar." }) {
  if (!rows?.length) {
    return <div className="rounded-md border border-dashed border-slate-300 p-6 text-center text-sm text-slate-500">{emptyMessage}</div>;
  }

  return (
    <div className="overflow-hidden rounded-lg border border-slate-200">
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-slate-200 text-sm">
          <thead className="bg-slate-50">
            <tr>
              {columns.map((column) => (
                <th key={column.key} scope="col" className="px-4 py-3 text-left font-semibold text-slate-700">
                  {column.header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-slate-100 bg-white">
            {rows.map((row, rowIndex) => (
              <tr key={getRowKey ? getRowKey(row) : row.id || rowIndex}>
                {columns.map((column) => (
                  <td key={column.key} className="px-4 py-3 text-slate-700">
                    {column.render ? column.render(row) : row[column.key]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
