import { useQuery } from "@tanstack/react-query";
import { LockKeyhole } from "lucide-react";
import { useMemo, useState } from "react";

import { Card, CardHeader } from "../../../shared/components/ui/Card";
import { EmptyState } from "../../../shared/components/ui/EmptyState";
import { useAuth } from "../../../shared/hooks/useAuth";
import { canManageEcommerce, canViewEcommerce } from "../../../shared/utils/roles";
import { ecommerceQueryKeys, getEcommerceOrders } from "../api";
import { EcommerceCurlExample } from "../components/EcommerceCurlExample";
import { EcommerceFilters } from "../components/EcommerceFilters";
import { EcommerceOrderDetailModal } from "../components/EcommerceOrderDetailModal";
import { EcommerceOrdersTable } from "../components/EcommerceOrdersTable";
import { EcommerceSummary } from "../components/EcommerceSummary";
import { getProcessingState } from "../schemas";

const initialFilters = {
  search: "",
  proveedor: "",
  status: "",
  processing: "",
};

const emptyArray = [];
const listParams = { skip: 0, limit: 100 };

function filterOrders(orders, filters) {
  const search = filters.search.trim().toLowerCase();

  return orders.filter((order) => {
    const providerMatches = !filters.proveedor || order.proveedor === filters.proveedor;
    const statusMatches = !filters.status || order.status === filters.status;
    const processingMatches = !filters.processing || getProcessingState(order) === filters.processing;
    const searchTarget = [
      order.id,
      order.external_order_id,
      order.customer_email,
      order.customer_name,
      order.recompensa_aplicada_id,
      order.error_procesamiento,
    ]
      .filter(Boolean)
      .join(" ")
      .toLowerCase();
    const searchMatches = !search || searchTarget.includes(search);

    return providerMatches && statusMatches && processingMatches && searchMatches;
  });
}

function hasActiveFilters(filters) {
  return Boolean(filters.search || filters.proveedor || filters.status || filters.processing);
}

export function EcommercePage() {
  const { token, user } = useAuth();
  const [filters, setFilters] = useState(initialFilters);
  const [selectedOrder, setSelectedOrder] = useState(null);

  const canView = canViewEcommerce(user);
  const canManage = canManageEcommerce(user);
  const organizationId = user?.organizacion_id || "current";

  const ordersQuery = useQuery({
    queryKey: ecommerceQueryKeys.orders(organizationId, listParams),
    queryFn: () => getEcommerceOrders(listParams),
    enabled: Boolean(token) && canView,
    retry: false,
  });

  const orders = ordersQuery.data || emptyArray;
  const filteredOrders = useMemo(() => filterOrders(orders, filters), [filters, orders]);
  const filtersActive = hasActiveFilters(filters);

  if (!canView) {
    return (
      <div className="space-y-6">
        <div>
          <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Ecommerce</h1>
          <p className="mt-1 text-sm text-slate-500">
            Recibi compras pagadas desde tiendas externas y aplica recompensas automaticamente.
          </p>
        </div>
        <Card>
          <CardHeader title="Sin permisos" description="La auditoria ecommerce esta limitada por rol." />
          <EmptyState
            icon={LockKeyhole}
            title="No tenes permisos para ver Ecommerce."
            description="Los clientes no acceden a la auditoria de ordenes externas."
          />
        </Card>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-semibold tracking-normal text-slate-950">Ecommerce</h1>
        <p className="mt-1 text-sm text-slate-500">
          Recibi compras pagadas desde tiendas externas y aplica recompensas automaticamente.
        </p>
      </div>

      <EcommerceSummary orders={orders} loading={ordersQuery.isLoading} />
      <EcommerceCurlExample canManage={canManage} />

      <Card>
        <CardHeader
          title="Ordenes recibidas"
          description="Audita eventos order-paid, procesamiento, errores y recompensas asociadas."
        />
        <div className="space-y-4">
          <EcommerceFilters filters={filters} onChange={setFilters} />
          <EcommerceOrdersTable
            orders={filteredOrders}
            loading={ordersQuery.isLoading}
            error={ordersQuery.error}
            onRetry={() => ordersQuery.refetch()}
            onView={setSelectedOrder}
            emptyTitle={filtersActive ? "Sin resultados con estos filtros" : undefined}
            emptyDescription={
              filtersActive
                ? "Ajusta la busqueda, proveedor, status o procesamiento para ver mas ordenes."
                : undefined
            }
          />
        </div>
      </Card>

      <EcommerceOrderDetailModal order={selectedOrder} onClose={() => setSelectedOrder(null)} />
    </div>
  );
}
