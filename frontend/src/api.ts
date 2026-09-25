/* ── API client with auth interceptors ── */
import axios from "axios";

const baseURL = import.meta.env.VITE_API_URL || "/api";
const api = axios.create({ baseURL });

// Attach JWT token from localStorage
api.interceptors.request.use((config) => {
  const token = localStorage.getItem("waste_token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Handle 401s
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem("waste_token");
      // Don't redirect if already on login
      if (!window.location.pathname.includes("/login")) {
        window.location.href = "/login";
      }
    }
    return Promise.reject(err);
  }
);

export default api;
