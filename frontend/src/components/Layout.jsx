import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

function NavItem({ to, children }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `block px-3 py-2 rounded-md text-sm font-medium transition-colors ${
          isActive ? "bg-blue-50 text-blue-700" : "text-slate-600 hover:bg-slate-100"
        }`
      }
    >
      {children}
    </NavLink>
  );
}

export default function Layout() {
  const { user, isHrm, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-56 shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-4 py-5 border-b border-slate-200">
          <h1 className="text-base font-semibold text-slate-800">ERP Modules</h1>
          <p className="text-xs text-slate-500 mt-0.5">{isHrm ? "HRM" : "Employee"}</p>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          <NavItem to="/">Dashboard</NavItem>
          <NavItem to="/leave">Leave</NavItem>
          <NavItem to="/payroll">Payroll</NavItem>

          {isHrm && (
            <>
              <div className="pt-4 pb-1 px-3 text-xs font-semibold text-slate-400 uppercase tracking-wide">
                HRM
              </div>
              <NavItem to="/hrm/leave-inbox">Leave Inbox</NavItem>
              <NavItem to="/hrm/users">Users</NavItem>
            </>
          )}
        </nav>

        <div className="px-3 py-4 border-t border-slate-200">
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-md text-sm font-medium text-slate-600 hover:bg-slate-100 transition-colors"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto">
        <Outlet />
      </main>
    </div>
  );
}
