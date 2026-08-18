import { createContext, useContext, useState, useCallback, useMemo } from "react";
import { jwtDecode } from "jwt-decode";
import { authApi } from "../api/client";

const AuthContext = createContext(null);

function decodeUser(accessToken) {
  try {
    const payload = jwtDecode(accessToken);
    return {
      id: payload.sub,
      role: payload.role, // "employee" | "hrm"
      employeeType: payload.employee_type,
      exp: payload.exp,
    };
  } catch {
    return null;
  }
}

export function AuthProvider({ children }) {
  const [accessToken, setAccessToken] = useState(() => localStorage.getItem("access_token"));
  const [refreshToken, setRefreshToken] = useState(() => localStorage.getItem("refresh_token"));

  const user = useMemo(() => (accessToken ? decodeUser(accessToken) : null), [accessToken]);

  const login = useCallback(async (email, password) => {
    const response = await authApi.post("/auth/login", { email, password });
    const { access_token, refresh_token } = response.data;

    localStorage.setItem("access_token", access_token);
    localStorage.setItem("refresh_token", refresh_token);
    setAccessToken(access_token);
    setRefreshToken(refresh_token);

    return decodeUser(access_token);
  }, []);

  const logout = useCallback(async () => {
    const rt = localStorage.getItem("refresh_token");
    try {
      if (rt) await authApi.post("/auth/logout", { refresh_token: rt });
    } catch {

    }
    localStorage.removeItem("access_token");
    localStorage.removeItem("refresh_token");
    setAccessToken(null);
    setRefreshToken(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      accessToken,
      refreshToken,
      isAuthenticated: !!user,
      isHrm: user?.role === "hrm",
      login,
      logout,
    }),
    [user, accessToken, refreshToken, login, logout]
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
