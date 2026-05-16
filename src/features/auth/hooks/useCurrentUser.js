import { useQuery } from "@tanstack/react-query";

import { isUnauthorizedError } from "../../../shared/api/apiError";
import { useAuth } from "../../../shared/hooks/useAuth";
import { getCurrentUser } from "../api";

export function useCurrentUser({ enabled = true } = {}) {
  const { token } = useAuth();

  return useQuery({
    queryKey: ["auth", "me", token],
    queryFn: getCurrentUser,
    enabled: Boolean(token) && enabled,
    retry: (failureCount, error) => {
      if (isUnauthorizedError(error)) {
        return false;
      }
      return failureCount < 1;
    },
    staleTime: 5 * 60_000,
  });
}
