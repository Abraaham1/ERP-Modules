import { useState, useEffect, useMemo } from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import { authApi } from "../../api/client";
import Avatar from "../../components/Avatar";
import { employeeTypeLabel } from "../../components/EmployeeTypeBadge";

export default function RoleEmployeesPage() {
  const { type } = useParams();
  const navigate = useNavigate();

  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");

  useEffect(() => {
    async function load() {
      setLoading(true);
      try {
        const res = await authApi.get("/users", { params: { page_size: 100 } });
        setUsers(res.data.items.filter((u) => u.employee_type === type));
      } finally {
        setLoading(false);
      }
    }
    load();
  }, [type]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    if (!q) return users;
    return users.filter(
      (u) => u.full_name.toLowerCase().includes(q) || u.email.toLowerCase().includes(q)
    );
  }, [users, search]);

  return (
    <div className="p-8 max-w-4xl">
      <button
        onClick={() => navigate("/hrm")}
        className="text-sm text-slate-500 hover:text-slate-700 mb-4 inline-flex items-center gap-1"
      >
        ← Back to Team Overview
      </button>

      <div className="mb-6">
        <h1 className="text-2xl font-bold text-slate-900">{employeeTypeLabel(type)}</h1>
        <p className="text-sm text-slate-500 mt-1">{users.length} employees</p>
      </div>

      <div className="relative mb-6">
        <svg
          className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
          />
        </svg>
        <input
          type="text"
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search by name or email..."
          className="w-full rounded-lg border border-slate-300 pl-10 pr-4 py-2.5 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
        />
      </div>

      {loading && <p className="text-sm text-slate-500">Loading...</p>}

      {!loading && filtered.length === 0 && (
        <div className="bg-white rounded-xl border border-slate-200 p-12 text-center">
          <p className="text-slate-500 text-sm">No employees match your search.</p>
        </div>
      )}

      <div className="space-y-2">
        {filtered.map((u) => (
          <Link
            key={u.id}
            to={`/hrm/employees/${u.id}`}
            className="flex items-center gap-4 bg-white rounded-xl border border-slate-200 p-4 shadow-card hover:shadow-card-hover hover:border-brand-300 transition-all duration-150"
          >
            <Avatar name={u.full_name} />
            <div className="flex-1 min-w-0">
              <p className="text-sm font-semibold text-slate-800 truncate">{u.full_name}</p>
              <p className="text-xs text-slate-500 truncate">{u.email}</p>
            </div>
            <svg className="w-5 h-5 text-slate-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
            </svg>
          </Link>
        ))}
      </div>
    </div>
  );
}
