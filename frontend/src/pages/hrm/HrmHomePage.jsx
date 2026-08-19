import { useState, useEffect, useMemo } from "react";
import { useNavigate } from "react-router-dom";
import { authApi } from "../../api/client";
import { employeeTypeLabel } from "../../components/EmployeeTypeBadge";

const CARD_ACCENTS = [
  "bg-rose-50 text-rose-600",
  "bg-amber-50 text-amber-600",
  "bg-emerald-50 text-emerald-600",
  "bg-sky-50 text-sky-600",
  "bg-violet-50 text-violet-600",
  "bg-fuchsia-50 text-fuchsia-600",
  "bg-cyan-50 text-cyan-600",
  "bg-orange-50 text-orange-600",
  "bg-teal-50 text-teal-600",
];

function accentFor(type) {
  let hash = 0;
  for (let i = 0; i < type.length; i++) hash = type.charCodeAt(i) + ((hash << 5) - hash);
  return CARD_ACCENTS[Math.abs(hash) % CARD_ACCENTS.length];
}

export default function HrmHomePage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();

  useEffect(() => {
    async function load() {
      try {
        const res = await authApi.get("/users", { params: { page_size: 100 } });
        setUsers(res.data.items.filter((u) => u.role === "employee" && u.employee_type));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const categories = useMemo(() => {
    const counts = {};
    for (const u of users) {
      counts[u.employee_type] = (counts[u.employee_type] || 0) + 1;
    }
    return Object.entries(counts).sort((a, b) => b[1] - a[1]);
  }, [users]);

  return (
    <div className="p-8 max-w-6xl">
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-slate-900">Team Overview</h1>
        <p className="text-sm text-slate-500 mt-1">
          Browse employees by role · {users.length} active total
        </p>
      </div>

      {loading && <p className="text-sm text-slate-500">Loading...</p>}

      {!loading && categories.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-500 text-sm">No employees yet. Create one from the Users page.</p>
        </div>
      )}

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
        {categories.map(([type, count]) => {
          const label = employeeTypeLabel(type);
          return (
            <button
              key={type}
              onClick={() => navigate(`/hrm/roles/${type}`)}
              className="group text-left bg-white rounded-xl border border-slate-200 p-6 shadow-card hover:shadow-card-hover hover:border-brand-300 transition-all duration-150"
            >
              <div className="flex items-start justify-between mb-4">
                <div
                  className={`w-11 h-11 rounded-xl flex items-center justify-center font-bold text-sm ${accentFor(
                    type
                  )}`}
                >
                  {label.slice(0, 2).toUpperCase()}
                </div>
                <span className="text-2xl font-bold text-slate-900">{count}</span>
              </div>
              <h3 className="text-sm font-semibold text-slate-800">{label}</h3>
              <p className="text-xs text-slate-500 mt-0.5">
                {count} {count === 1 ? "employee" : "employees"}
              </p>
            </button>
          );
        })}
      </div>
    </div>
  );
}
