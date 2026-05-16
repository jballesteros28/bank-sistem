function formatValidationError(item) {
  const message = item?.msg || item?.message;
  if (!message) {
    return null;
  }
  const path = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : item.field;
  return path ? `${path}: ${message}` : message;
}

export function getApiErrorMessage(error) {
  const data = error?.response?.data;
  if (data?.message) {
    return data.message;
  }
  if (typeof data?.detail === "string") {
    return data.detail;
  }
  if (Array.isArray(data?.detail) && data.detail.length > 0) {
    const messages = data.detail.map(formatValidationError).filter(Boolean);
    if (messages.length > 0) {
      return messages.join(" ");
    }
    return "Revisa los campos marcados e intenta nuevamente.";
  }
  if (typeof data?.error === "string") {
    return data.error;
  }
  if (error?.message) {
    return error.message;
  }
  return "Ocurrio un error inesperado.";
}

export function getApiValidationErrors(error) {
  const details = error?.response?.data?.details || error?.response?.data?.detail;
  if (!Array.isArray(details)) {
    return {};
  }
  return details.reduce((acc, item) => {
    const path = Array.isArray(item.loc) ? item.loc.filter((part) => part !== "body").join(".") : item.field;
    if (path) {
      acc[path] = item.msg || item.message || "Valor invalido.";
    }
    return acc;
  }, {});
}

export function isUnauthorizedError(error) {
  return error?.response?.status === 401;
}
