import { useState, useEffect, useCallback } from "react";
import { payrollApi } from "../../api/client";

function formatCurrency(n) {
  return new Intl.NumberFormat(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 }).format(n);
}

export default function PayrollPage() {
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await payrollApi.get("/payroll/me");
      setSummary(res.data);
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Could not load salary information.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="p-4 md:p-8 max-w-2xl">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Payroll</h1>

      {loading && <p className="text-sm text-slate-500">Loading...</p>}
      {error && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {!loading && !error && summary && (
        <div className="bg-gradient-to-br from-brand-600 to-brand-700 rounded-xl p-5 sm:p-8 text-white shadow-sm">
          <p className="text-brand-100 text-sm font-medium mb-1">
            Salary so far this month ({summary.year}-{String(summary.month).padStart(2, "0")})
          </p>
          <p className="text-3xl sm:text-4xl font-bold mb-6">{formatCurrency(summary.salary_so_far)}</p>

          <div className="grid grid-cols-3 gap-3 sm:gap-4 pt-4 border-t border-white/20 text-sm">
            <div>
              <p className="text-brand-100">Fixed Salary</p>
              <p className="font-semibold">{formatCurrency(summary.fixed_salary)}</p>
            </div>
            <div>
              <p className="text-brand-100">Absences</p>
              <p className="font-semibold">{summary.num_absents}</p>
            </div>
            <div>
              <p className="text-brand-100">Deduction</p>
              <p className="font-semibold">{formatCurrency(summary.deduction)}</p>
            </div>
          </div>

          <p className="text-xs text-brand-200 mt-6">
            Resets to full salary at the start of next month. Recalculated live.
          </p>
        </div>
      )}
    </div>
  );
}