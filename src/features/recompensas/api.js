import { endpoints } from "../../shared/api/endpoints";
import { httpClient } from "../../shared/api/httpClient";

export const rewardQueryKeys = {
  all: ["recompensas"],
  rewardRules: (organizationId = "current") => ["recompensas", "rewardRules", organizationId || "current"],
  rewardRule: (id) => ["recompensas", "rewardRules", "detail", id],
  rewardApplications: (organizationId = "current", params = {}) => [
    "recompensas",
    "rewardApplications",
    organizationId || "current",
    params,
  ],
  myRewardApplications: (organizationId = "current", params = {}) => [
    "recompensas",
    "myRewardApplications",
    organizationId || "current",
    params,
  ],
  rewardSimulation: (payload = {}) => ["recompensas", "rewardSimulation", payload],
};

export function getRewardRules(params) {
  return httpClient.get(endpoints.recompensas.reglas, { params });
}

export function getRewardRuleById(id) {
  return httpClient.get(endpoints.recompensas.regla(id));
}

export function createRewardRule(payload) {
  return httpClient.post(endpoints.recompensas.reglas, payload);
}

export function updateRewardRule(id, payload) {
  return httpClient.patch(endpoints.recompensas.regla(id), payload);
}

export function simulateReward(payload, params) {
  return httpClient.post(endpoints.recompensas.simular, payload, { params });
}

export function applyReward(payload) {
  return httpClient.post(endpoints.recompensas.aplicar, payload);
}

export function getRewardApplications(params) {
  return httpClient.get(endpoints.recompensas.aplicaciones, { params });
}

export function getMyRewardApplications(params) {
  return httpClient.get(endpoints.recompensas.misAplicaciones, { params });
}
