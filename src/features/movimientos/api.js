import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const movementQueryKeys = {
  all: ["movimientos"],
  list: (organizationId = "current") => ["movimientos", "list", organizationId || "current"],
  detail: (movimientoId) => ["movimientos", "detail", movimientoId],
};

export function listMovimientos(params) {
  return httpClient.get(endpoints.movimientos.list, { params });
}

export function getMovimientos(params) {
  return listMovimientos(params);
}

export function getMovimientoById(id) {
  return httpClient.get(endpoints.movimientos.detail(id));
}

export function createDeposito(payload) {
  return httpClient.post(endpoints.movimientos.deposito, payload);
}

export function createRetiro(payload) {
  return httpClient.post(endpoints.movimientos.retiro, payload);
}

export function createTransferencia(payload) {
  return httpClient.post(endpoints.movimientos.transferencia, payload);
}

export function createPago(payload) {
  return httpClient.post(endpoints.movimientos.pago, payload);
}

export function createPagoOrganizacion(payload) {
  return httpClient.post(endpoints.movimientos.pagoOrganizacion, payload);
}

export function createCashback(payload) {
  return httpClient.post(endpoints.movimientos.cashback, payload);
}

export function createAjusteAdmin(payload) {
  return httpClient.post(endpoints.movimientos.ajusteAdmin, payload);
}

export function createReversa(movimientoId, payload) {
  return httpClient.post(endpoints.movimientos.reversa(movimientoId), payload);
}
