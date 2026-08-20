import { useState, useEffect, useCallback } from "react";
import { attendanceApi, authApi } from "../../api/client";
import Avatar from "../../components/Avatar";

const TABS = [
  { value: "pending", label: "Pending" },
  { value: "approved", label: "Approved" },
  { value: "rejected", label: "Rejected" },
];

const TAB_STYLES = {
  pending: "bg-amber-50 text-amber-700 border-amber-200",
  approved: "bg-emerald-50 text-emerald-700 border-emerald-200",
  rejected: "bg-red-50 text-red-700 border-red-200",
};

export default function LeaveInboxPage() {
  const [tab, setTab] = useState("pending");
  const [requests, setRequests] = useState([]);
  const [userMap, setUserMap] = useState({});
  const [loading, setLoading] = useState(true);
  const [actioningId, setActioningId] = useState(null);
  const [noteDrafts, setNoteDrafts] = useState({});

  useEffect(() => {
    async function loadUsers() {
      try {
        const res = await authApi.get("/users", { params: { page_size: 100, include_inactive: true } });
        const map = {};
        for (const u of res.data.items) map[u.id] = u;
        setUserMap(map);
      } catch {
      }
    }
    loadUsers();
  }, []);

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
    <div className="p-4 md:p-8 max-w-4xl">
      <h1 className="text-2xl font-bold text-slate-900 mb-1">Leave Inbox</h1>
      <p className="text-sm text-slate-500 mb-6">Review and respond to employee leave requests</p>

      <div className="flex gap-1 mb-6 border-b border-slate-200">
        {TABS.map((t) => (
          <button
            key={t.value}
            onClick={() => setTab(t.value)}
            className={`px-4 py-2.5 text-sm font-medium border-b-2 transition-colors ${
              tab === t.value
                ? "border-brand-600 text-brand-700"
                : "border-transparent text-slate-500 hover:text-slate-700"
            }`}
          >
            {t.label}
          </button>
        ))}
      </div>

      {loading && <p className="text-sm text-slate-500">Loading...</p>}
      {!loading && requests.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-500 text-sm">No {tab} leave requests.</p>
        </div>
      )}

      <div className="space-y-3">
        {requests.map((r) => {
          const employee = userMap[r.user_id];
          const displayName = employee?.full_name || "Unknown employee";

          return (
            <div
              key={r.id}
              className="bg-white rounded-xl border border-slate-200 p-4 sm:p-5 shadow-card animate-slide-up"
            >
              <div className="flex flex-wrap items-start justify-between gap-3">
                <div className="flex items-start gap-3 min-w-0">
                  <Avatar name={displayName} size="sm" />
                  <div className="min-w-0">
                    <p className="text-sm font-semibold text-slate-800 truncate">{displayName}</p>
                    <p className="text-xs text-slate-500">
                      {r.start_date} → {r.end_date}
                    </p>
                    <p className="text-sm text-slate-600 mt-2 break-words">{r.reason}</p>
                  </div>
                </div>

                <span
                  className={`shrink-0 text-xs font-medium px-2.5 py-1 rounded-full border ${TAB_STYLES[r.status]}`}
                >
                  {r.status}
                </span>
              </div>

              {tab === "pending" && (
                <div className="mt-4 flex flex-col sm:flex-row sm:items-center gap-2 sm:pl-11">
                  <input
                    type="text"
                    placeholder="Optional note"
                    value={noteDrafts[r.id] || ""}
                    onChange={(e) => setNoteDrafts((prev) => ({ ...prev, [r.id]: e.target.value }))}
                    className="flex-1 rounded-lg border border-slate-300 px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                  />
                  <div className="flex gap-2">
                    <button
                      onClick={() => handleReview(r.id, true)}
                      disabled={actioningId === r.id}
                      className="flex-1 sm:flex-none text-sm font-medium px-3 py-1.5 rounded-lg bg-emerald-600 hover:bg-emerald-700 disabled:bg-emerald-300 text-white transition-colors"
                    >
                      Approve
                    </button>
                    <button
                      onClick={() => handleReview(r.id, false)}
                      disabled={actioningId === r.id}
                      className="flex-1 sm:flex-none text-sm font-medium px-3 py-1.5 rounded-lg bg-red-600 hover:bg-red-700 disabled:bg-red-300 text-white transition-colors"
                    >
                      Reject
                    </button>
                  </div>
                </div>
              )}

              {r.review_note && (
                <p className="text-xs text-slate-400 mt-2 sm:pl-11 break-words">Note: {r.review_note}</p>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}