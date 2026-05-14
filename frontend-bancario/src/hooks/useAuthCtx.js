import { useContext } from "react";
import { AuthContext } from "../context/authContext";

export const useAuthCtx = () => {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuthCtx debe usarse dentro de un AuthProvider");
  return ctx;
};
