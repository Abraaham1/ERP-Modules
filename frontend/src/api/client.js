import axios from "axios";

const BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8090";

const rawAuthClient = axios.create({ baseURL: `${BASE_URL}/api/auth` });

let refreshPromise = null;

async function refreshAccessToken() {
  const refreshToken = sessionStorage.getItem("refresh_token");
  if (!refreshToken) throw new Error("No refresh token available");
  if (!refreshPromise) {
    refreshPromise = rawAuthClient
      .post("/auth/refresh", { refresh_token: refreshToken })
      .then((res) => {
        sessionStorage.setItem("access_token", res.data.access_token);
        return res.data.access_token;
      })
      .finally(() => {
        refreshPromise = null;
      });
  }
  return refreshPromise;
}

function createClient(prefix) {
  const client = axios.create({
    baseURL: `${BASE_URL}/api/${prefix}`,
  });

  client.interceptors.request.use((config) => {
    const token = sessionStorage.getItem("access_token");
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });

  client.interceptors.response.use(
    (response) => response,
    async (error) => {
      const originalRequest = error.config;

      if (error.response?.status === 401 && !originalRequest._retry) {
        originalRequest._retry = true;
        try {
          const newToken = await refreshAccessToken();
          originalRequest.headers.Authorization = `Bearer ${newToken}`;
          return client(originalRequest);
        } catch {
          sessionStorage.removeItem("access_token");
          sessionStorage.removeItem("refresh_token");
          window.location.href = "/login";
        }
      }

      return Promise.reject(error);
    }
  );

  return client;
}

export const authApi = createClient("auth");
export const attendanceApi = createClient("attendance");
export const payrollApi = createClient("payroll");
