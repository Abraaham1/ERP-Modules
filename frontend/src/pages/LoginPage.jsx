import { useState } from "react";
import { useNavigate, useLocation, Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import OrbitHub from "../components/OrbitHub";

function EyeIcon({ open }) {
  if (open) {
    return (
      <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5" stroke="currentColor" strokeWidth="1.8">
        <path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7-10-7-10-7Z" strokeLinecap="round" strokeLinejoin="round" />
        <circle cx="12" cy="12" r="3" strokeLinecap="round" strokeLinejoin="round" />
      </svg>
    );
  }
  return (
    <svg viewBox="0 0 24 24" fill="none" className="w-4.5 h-4.5" stroke="currentColor" strokeWidth="1.8">
      <path
        d="M3 3l18 18M10.6 10.7a2.5 2.5 0 0 0 3.5 3.5M6.7 6.9C4.2 8.4 2 12 2 12s3.5 7 10 7c1.8 0 3.4-.5 4.7-1.2M9.9 5.2A9.9 9.9 0 0 1 12 5c6.5 0 10 7 10 7a15.6 15.6 0 0 1-2.3 3.2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [errorKey, setErrorKey] = useState(0);

  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();

  const from = location.state?.from?.pathname || "/";

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      await login(email, password);
      navigate(from, { replace: true });
    } catch (err) {
      const detail = err.response?.data?.detail;
      let message = "Login failed. Check your email and password.";
      if (err.response?.status === 429) {
        message = "Too many login attempts. Please try again later.";
      } else if (typeof detail === "string") {
        message = detail;
      }
      setError(message);
      setErrorKey((k) => k + 1);
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex flex-col lg:flex-row bg-slate-50">
      {/* Hero / system visual */}
      <div className="relative overflow-hidden bg-[#0b1020] px-8 py-10 lg:w-1/2 lg:px-14 lg:py-14 lg:min-h-screen flex flex-col">
        <div className="absolute inset-0 grid-pattern motion-safe:animate-grid-pan opacity-60" />
        <div className="absolute -top-10 -left-10 w-64 h-64 rounded-full bg-brand-500/20 blur-3xl motion-safe:animate-float" />
        <div
          className="absolute bottom-0 right-0 w-72 h-72 rounded-full bg-emerald-400/10 blur-3xl motion-safe:animate-float"
          style={{ animationDelay: "2.5s" }}
        />

        <div className="relative flex items-center gap-3">
          <div className="w-9 h-9 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold text-sm shadow-card">
            E
          </div>
          <span className="text-white font-semibold tracking-tight">ERP Modules</span>
        </div>

        <div className="relative flex-1 flex items-center justify-center py-6 lg:py-10">
          <OrbitHub />
        </div>

        <div className="relative">
          <h1 className="text-2xl lg:text-3xl font-bold text-white tracking-tight leading-snug">
            One system.
            <br />
            Every department runs through it.
          </h1>
        </div>
      </div>

      {/* Form */}
      <div className="flex-1 flex items-center justify-center px-4 py-12 lg:py-10">
        <div className="w-full max-w-sm">
          <div className="mb-8">
            <h2 className="text-2xl font-bold text-slate-900">Welcome back</h2>
            <p className="text-sm text-slate-500 mt-1">Sign in to access your workspace</p>
          </div>

          <div className="bg-white rounded-2xl shadow-card-hover border border-slate-100 p-8 animate-slide-up">
            <form onSubmit={handleSubmit} className="space-y-5">
              <div className="relative">
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder=" "
                  className="peer w-full rounded-lg border border-slate-300 bg-white px-3.5 pt-5 pb-2 text-sm text-slate-900 placeholder-transparent focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"
                />
                <label
                  htmlFor="email"
                  className="absolute left-3.5 top-2 text-xs text-slate-500 transition-all pointer-events-none peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-sm peer-placeholder-shown:text-slate-400 peer-focus:top-2 peer-focus:text-xs peer-focus:text-brand-600"
                >
                  Email address
                </label>
              </div>

              <div className="relative">
                <input
                  id="password"
                  type={showPassword ? "text" : "password"}
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder=" "
                  className="peer w-full rounded-lg border border-slate-300 bg-white px-3.5 pt-5 pb-2 pr-11 text-sm text-slate-900 placeholder-transparent focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent transition-shadow"
                />
                <label
                  htmlFor="password"
                  className="absolute left-3.5 top-2 text-xs text-slate-500 transition-all pointer-events-none peer-placeholder-shown:top-3.5 peer-placeholder-shown:text-sm peer-placeholder-shown:text-slate-400 peer-focus:top-2 peer-focus:text-xs peer-focus:text-brand-600"
                >
                  Password
                </label>
                <button
                  type="button"
                  onClick={() => setShowPassword((s) => !s)}
                  className="absolute right-3 top-0 h-full flex items-center text-slate-400 hover:text-slate-600 transition-colors"
                  aria-label={showPassword ? "Hide password" : "Show password"}
                >
                  <EyeIcon open={showPassword} />
                </button>
              </div>

              <div className="flex justify-end -mt-1">
                <Link
                  to="/forgot-password"
                  className="text-xs font-medium text-brand-600 hover:text-brand-700 transition-colors"
                >
                  Forgot password?
                </Link>
              </div>

              {error && (
                <div
                  key={errorKey}
                  className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5 animate-shake"
                >
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-600 disabled:from-brand-300 disabled:to-brand-300 text-white text-sm font-semibold rounded-lg px-4 py-2.5 shadow-sm transition-all hover:shadow-card-hover active:scale-[0.98] flex items-center justify-center gap-2"
              >
                {loading && (
                  <svg className="w-4 h-4 animate-spin" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
                  </svg>
                )}
                {loading ? "Signing in..." : "Sign in"}
              </button>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}