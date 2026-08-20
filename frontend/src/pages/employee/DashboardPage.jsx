import { useState, useEffect, useCallback } from "react";
import { PieChart, Pie, Cell, Tooltip, Legend, ResponsiveContainer } from "recharts";
import { attendanceApi } from "../../api/client";

const STATUS_OPTIONS = [
  { value: "present", label: "Present" },
  { value: "absent", label: "Absent" },
  { value: "half_day", label: "Half Day" },
];

const COLORS = {
  Present: "#16a34a",
  Absent: "#dc2626",
  "Half Day": "#f59e0b",
  Leave: "#3b82f6",
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function DashboardPage() {
  const [workDate, setWorkDate] = useState(todayIso());
  const [status, setStatus] = useState("present");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  const now = new Date();
  const [year] = useState(now.getFullYear());
  const [month] = useState(now.getMonth() + 1);

  const [chartData, setChartData] = useState(null);
  const [chartLoading, setChartLoading] = useState(true);
  const [chartError, setChartError] = useState(null);

  const loadChart = useCallback(async () => {
    setChartLoading(true);
    setChartError(null);
    try {
      const res = await attendanceApi.get(`/attendance/me/chart/${year}/${month}`);
      setChartData(res.data);
    } catch {
      setChartError("Could not load attendance chart.");
    } finally {
      setChartLoading(false);
    }
  }, [year, month]);

  useEffect(() => {
    loadChart();
  }, [loadChart]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await attendanceApi.post("/attendance", { work_date: workDate, status });
      setMessage({ type: "success", text: "Attendance logged." });
      loadChart();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setMessage({ type: "error", text: typeof detail === "string" ? detail : "Failed to log attendance." });
    } finally {
      setSubmitting(false);
    }
  }

  const pieData = chartData?.slices.filter((s) => s.value > 0) ?? [];

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-card">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">Log Attendance</h2>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Date</label>
              <input
                type="date"
                value={workDate}
                max={todayIso()}
                onChange={(e) => setWorkDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>

            <div>
              <label className="block text-sm text-slate-600 mb-1">Status</label>
              <div className="flex gap-2">
                {STATUS_OPTIONS.map((opt) => (
                  <button
                    type="button"
                    key={opt.value}
                    onClick={() => setStatus(opt.value)}
                    className={`flex-1 text-sm rounded-lg px-3 py-2 border transition-colors ${
                      status === opt.value
                        ? "bg-brand-600 text-white border-brand-600"
                        : "bg-white text-slate-600 border-slate-300 hover:bg-slate-50"
                    }`}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            {message && (
              <div
                className={`text-sm rounded-lg px-3 py-2 border ${
                  message.type === "success"
                    ? "text-green-700 bg-green-50 border-green-200"
                    : "text-red-600 bg-red-50 border-red-200"
                }`}
              >
                {message.text}
              </div>
            )}

            <button
              type="submit"
              disabled={submitting}
              className="w-full bg-brand-600 hover:bg-brand-700 disabled:bg-brand-300 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors"
            >
              {submitting ? "Saving..." : "Log Attendance"}
            </button>
          </form>
        </div>

        <div className="bg-white rounded-xl border border-slate-200 p-6 shadow-card">
          <h2 className="text-sm font-semibold text-slate-700 mb-4">
            This Month's Attendance
          </h2>

          {chartLoading && <p className="text-sm text-slate-500">Loading...</p>}
          {chartError && <p className="text-sm text-red-600">{chartError}</p>}

          {!chartLoading && !chartError && pieData.length === 0 && (
            <p className="text-sm text-slate-500">No attendance logged yet this month.</p>
          )}

          {!chartLoading && !chartError && pieData.length > 0 && (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={pieData} dataKey="value" nameKey="label" outerRadius={80} label>
                  {pieData.map((entry) => (
                    <Cell key={entry.label} fill={COLORS[entry.label] || "#94a3b8"} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          )}
        </div>
      </div>
    </div>
  );
}