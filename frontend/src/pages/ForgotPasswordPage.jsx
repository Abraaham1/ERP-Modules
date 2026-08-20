import { useState } from "react";
import { Link } from "react-router-dom";
import { authApi } from "../api/client";

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState("");
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState("");

  async function handleSubmit(e) {
    e.preventDefault();
    setError("");
    setLoading(true);
    try {
      await authApi.post("/auth/forgot-password", { email });
      // Always show the same success state, whether or not the email
      // exists -- the backend intentionally never reveals this, and
      // the frontend shouldn't undermine that by branching on it.
      setSubmitted(true);
    } catch {
      setError("Something went wrong. Please try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-slate-50 px-4">
      <div className="w-full max-w-sm">
        <div className="mb-8 text-center">
          <div className="w-10 h-10 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold text-sm mx-auto mb-4 shadow-card">
            E
          </div>
          <h1 className="text-2xl font-bold text-slate-900">Forgot your password?</h1>
          <p className="text-sm text-slate-500 mt-1">
            Enter your email and we'll send you a reset link
          </p>
        </div>

        <div className="bg-white rounded-2xl shadow-card-hover border border-slate-100 p-8 animate-slide-up">
          {submitted ? (
            <div className="text-center">
              <div className="w-12 h-12 rounded-full bg-emerald-50 flex items-center justify-center mx-auto mb-4">
                <svg className="w-6 h-6 text-emerald-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                </svg>
              </div>
              <p className="text-sm text-slate-700 font-medium">Check your email</p>
              <p className="text-sm text-slate-500 mt-1">
                If an account exists for <span className="font-medium">{email}</span>, a reset
                link has been sent. It expires in 1 hour.
              </p>
              <Link
                to="/login"
                className="inline-block mt-6 text-sm font-medium text-brand-600 hover:text-brand-700"
              >
                Back to sign in
              </Link>
            </div>
          ) : (
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

              {error && (
                <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3.5 py-2.5">
                  {error}
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-gradient-to-r from-brand-600 to-brand-500 hover:from-brand-700 hover:to-brand-600 disabled:from-brand-300 disabled:to-brand-300 text-white text-sm font-semibold rounded-lg px-4 py-2.5 shadow-sm transition-all"
              >
                {loading ? "Sending..." : "Send reset link"}
              </button>

              <Link
                to="/login"
                className="block text-center text-sm font-medium text-slate-500 hover:text-slate-700 transition-colors"
              >
                Back to sign in
              </Link>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
