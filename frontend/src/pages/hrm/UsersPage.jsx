import { useState, useEffect, useCallback } from "react";
import { authApi } from "../../api/client";
import Avatar from "../../components/Avatar";
import EmployeeTypeBadge from "../../components/EmployeeTypeBadge";

const EMPLOYEE_TYPES = [
  "swe", "ml_engineer", "devops_engineer", "sqa", "db_analyst",
  "backend_dev", "frontend_dev", "cto", "cpdo",
];

const emptyForm = {
  email: "",
  full_name: "",
  password: "",
  role: "employee",
  employee_type: "swe",
};

export default function UsersPage() {
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState(emptyForm);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await authApi.get("/users");
      setUsers(res.data.items);
    } catch {
      setUsers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  async function handleCreate(e) {
    e.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      const payload = { ...form };
      if (payload.role === "hrm") delete payload.employee_type;
      await authApi.post("/users", payload);
      setShowForm(false);
      setForm(emptyForm);
      load();
    } catch (err) {
      const detail = err.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Failed to create user.");
    } finally {
      setSubmitting(false);
    }
  }

  async function handleDeactivate(userId) {
    try {
      await authApi.delete(`/users/${userId}`);
      load();
    } catch {
    }
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-6">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Users</h1>
          <p className="text-sm text-slate-500 mt-1">Manage employee and HRM accounts</p>
        </div>
        <button
          onClick={() => setShowForm((v) => !v)}
          className="self-start sm:self-auto text-sm font-medium px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 text-white shadow-sm transition-colors"
        >
          {showForm ? "Cancel" : "+ New User"}
        </button>
      </div>

      {showForm && (
        <form
          onSubmit={handleCreate}
          className="bg-white rounded-xl border border-slate-200 p-4 sm:p-6 mb-6 space-y-4 shadow-card animate-slide-up"
        >
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-sm text-slate-600 mb-1">Email</label>
              <input
                type="email"
                required
                value={form.email}
                onChange={(e) => setForm({ ...form, email: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Full name</label>
              <input
                type="text"
                required
                value={form.full_name}
                onChange={(e) => setForm({ ...form, full_name: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Password</label>
              <input
                type="password"
                required
                minLength={8}
                value={form.password}
                onChange={(e) => setForm({ ...form, password: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              />
            </div>
            <div>
              <label className="block text-sm text-slate-600 mb-1">Role</label>
              <select
                value={form.role}
                onChange={(e) => setForm({ ...form, role: e.target.value })}
                className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
              >
                <option value="employee">Employee</option>
                <option value="hrm">HRM</option>
              </select>
            </div>
            {form.role === "employee" && (
              <div>
                <label className="block text-sm text-slate-600 mb-1">Employee type</label>
                <select
                  value={form.employee_type}
                  onChange={(e) => setForm({ ...form, employee_type: e.target.value })}
                  className="w-full rounded-lg border border-slate-300 px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-brand-500 focus:border-transparent"
                >
                  {EMPLOYEE_TYPES.map((t) => (
                    <option key={t} value={t}>
                      {t}
                    </option>
                  ))}
                </select>
              </div>
            )}
          </div>

          {error && (
            <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-3 py-2">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={submitting}
            className="text-sm font-medium px-4 py-2.5 rounded-lg bg-brand-600 hover:bg-brand-700 disabled:bg-brand-300 text-white transition-colors"
          >
            {submitting ? "Creating..." : "Create User"}
          </button>
        </form>
      )}

      {loading && <p className="text-sm text-slate-500">Loading...</p>}

      {!loading && (
        <div className="space-y-2">
          {users.map((u) => (
            <div
              key={u.id}
              className="flex flex-wrap items-center gap-x-4 gap-y-2 bg-white rounded-xl border border-slate-200 p-4 shadow-card"
            >
              <Avatar name={u.full_name} />
              <div className="flex-1 min-w-[140px]">
                <p className="text-sm font-semibold text-slate-800 truncate">{u.full_name}</p>
                <p className="text-xs text-slate-500 truncate">{u.email}</p>
              </div>
              <div className="flex flex-wrap items-center gap-2 ml-auto sm:ml-0">
                <span className="text-xs font-medium px-2.5 py-1 rounded-full bg-slate-100 text-slate-600 capitalize">
                  {u.role}
                </span>
                {u.employee_type && <EmployeeTypeBadge type={u.employee_type} />}
                <button
                  onClick={() => handleDeactivate(u.id)}
                  className="text-xs font-medium text-red-600 hover:text-red-700 shrink-0"
                >
                  Deactivate
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}