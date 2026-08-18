import { useState, useEffect, useCallback } from "react";
import { attendanceApi } from "../../api/client";

const TABS = [
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

export default function LeaveInboxPage() {
  const [tab, setTab] = useState("pending");
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);
  const [noteDrafts, setNoteDrafts] = useState({});

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await attendanceApi.get("/leave/inbox", { params: { status: tab } });
      setRequests(res.data.items);
    } catch {
      setRequests([]);
    } finally {
      setLoading(false);
    }
  }, [tab]);

  useEffect(() => {
    load();
  }, [load]);

  async function handleReview(id, approve) {
    setActioningId(id);
    try {
      await attendanceApi.post(`/leave/${id}/review`, {
        approve,
        review_note: noteDrafts[id] || null,
      });
      load();
    } catch {
    } finally {
      setActioningId(null);
    }
  }

  return (
    <div className="p-8 max-w-4xl">
      <h1 className="text-2xl font-semibold text-slate-800 mb-6">Leave Inbox</h1>

      <div className="flex gap-1 mb-4 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`px-4 py-2 text-sm font-medium border-b-2 transition-colors ${
              tab === t.value
                ? "border-blue-600 text-blue-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-slate-500">Loading...</p>}
      {!loading && requests.length === 0 && (
        <p className="text-sm text-slate-500">No {tab} leave requests.</p>
      )}

      <div className="space-y-3">
        {requests.map((r) => (
          <div key={r.id} className="bg-white rounded-lg border border-slate-200 p-4">
            <div className="flex items-start justify-between">
              <div>
                <p className="text-sm font-medium text-slate-800">
                  {r.start_date} → {r.end_date}
                </p>
                <p className="text-xs text-slate-500 mt-0.5">Employee: {r.user_id}</p>
                <p className="text-sm text-slate-600 mt-2">{r.reason}</p>
              </div>
            </div>

            {tab === "pending" && (
              <div className="mt-3 flex items-center gap-2">
                <input
                  type="text"
                  placeholder="Optional note"
                  value={noteDrafts[r.id] || ""}
                  onChange={(e) => setNoteDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                  className="flex-1 rounded-md border border-slate-300 px-3 py-1.5 text-sm"
                />
                <button
                  onClick={() => handleReview(r.id, true)}
                  disabled={actioningId === r.id}
                  className="text-sm font-medium px-3 py-1.5 rounded-md bg-green-600 hover:bg-green-700 disabled:bg-green-300 text-white transition-colors"
                >
                  Approve
                </button>
                <button
                  onClick={() => handleReview(r.id, false)}
                  disabled={actioningId === r.id}
                  className="text-sm font-medium px-3 py-1.5 rounded-md bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white transition-colors"
                >
                  Reject
                </button>
              </div>
            )}

            {r.review_note && (
              <p className="text-xs text-slate-400 mt-2">Note: {r.review_note}</p>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
