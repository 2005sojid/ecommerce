import { useEffect, useState } from "react";
import { api, clearTokens, getToken, User } from "./api";

export function useAuth() {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!getToken()) {
      setLoading(false);
      return;
    }
    api
      .get<User>("/auth/me")
      .then((r) => setUser(r.data))
      .catch(() => clearTokens())
      .finally(() => setLoading(false));
  }, []);

  return { user, setUser, loading };
}
