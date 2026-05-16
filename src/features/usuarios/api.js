import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const usuariosQueryKeys = {
  all: ["usuarios"],
  list: (organizationId = "current") => ["usuarios", "list", organizationId || "current"],
  detail: (usuarioId) => ["usuarios", "detail", usuarioId],
};

export function getUsuarios(params) {
  return httpClient.get(endpoints.usuarios.list, { params });
}

export function createUsuario(payload) {
  return httpClient.post(endpoints.usuarios.list, payload);
}

export function updateUsuario(usuarioId, payload) {
  return httpClient.patch(endpoints.usuarios.detail(usuarioId), payload);
}

export function updateUsuarioRol(usuarioId, payload) {
  return updateUsuario(usuarioId, { rol: payload.rol });
}

export function updateUsuarioEstado(usuarioId, payload) {
  const esActivo = payload.es_activo ?? payload.estado === "activo";
  return updateUsuario(usuarioId, { es_activo: esActivo });
}
