import { useState, useEffect, useCallback } from "react";
import { attendanceApi } from "../../api/client";

const STATUS_STYLES = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  approved: "bg-green-50 text-green-700 border-green-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

function todayIso() {
  return new Date().toISOString().slice(0, 10);
}

export default function LeavePage() {
  const [startDate, setStartDate] = useState(todayIso());
  const [endDate, setEndDate] = useState(todayIso());
  const [reason, setReason] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [message, setMessage] = useState(null);

  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadRequests = useCallback(async () => {
    setLoading(true);
    try {
      const res = await attendanceApi.get("/leave/me");
      setRequests(res.data.items);
    } catch {
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadRequests();
  }, [loadRequests]);

  async function handleSubmit(e) {
    e.preventDefault();
    setSubmitting(true);
    setMessage(null);
    try {
      await attendanceApi.post("/leave", { start_date: startDate, end_date: endDate, reason });
      setMessage({ type: "success", text: "Leave request submitted." });
      setReason("");
      loadRequests();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setMessage({
        type: "error",
        text: typeof detail === "string" ? detail : "Failed to submit leave request.",
      });
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-slate-900 mb-6">Leave</h1>

      <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6 shadow-card mb-6">
        <h2 className="text-sm font-semibold text-slate-700 mb-4">Apply for Leave</h2>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Start date</label>
              <input
                type="date"
                required
                value={startDate}
                onChange={(e) => setStartDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">End date</label>
              <input
                type="date"
                required
                value={endDate}
                min={startDate}
                onChange={(e) => setEndDate(e.target.value)}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              />
            </div>
          </div>

          <div>
            <label className="block text-sm text-slate-600 mb-1">Reason</label>
            <textarea
              required
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              rows={3}
              className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm"
              placeholder="Let HRM know why you're requesting leave"
            />
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
            className="bg-brand-600 hover:bg-brand-700 disabled:bg-brand-300 text-white text-sm font-medium rounded-lg px-4 py-2 transition-colors"
          >
            {submitting ? "Submitting..." : "Submit Request"}
          </button>
        </form>
      </div>

      <div className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6 shadow-card">
        <h2 className="text-sm font-semibold text-slate-700 mb-4">My Requests</h2>

        {loading && <p className="text-sm text-slate-500">Loading...</p>}
        {!loading && requests.length === 0 && (
          <p className="text-sm text-slate-500">No leave requests yet.</p>
        )}

        {!loading && requests.length > 0 && (
          <div className="space-y-2">
            {requests.map((r) => (
              <div
                key={r.id}
                className="flex flex-wrap items-start justify-between gap-2 border border-slate-200 rounded-lg px-4 py-3"
              >
                <div className="min-w-0">
                  <p className="text-sm font-medium text-slate-800">
                    {r.start_date} → {r.end_date}
                  </p>
                  <p className="text-xs text-slate-500 mt-0.5 break-words">{r.reason}</p>
                  {r.review_note && (
                    <p className="text-xs text-slate-400 mt-0.5 break-words">HRM note: {r.review_note}</p>
                  )}
                </div>
                <span
                  className={`shrink-0 text-xs font-medium px-2 py-1 rounded-full border ${STATUS_STYLES[r.status]}`}
                >
                  {r.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}