import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import Avatar from "./Avatar";

const ICONS = {
  home: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"
    />
  ),
  inbox: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M3 8l4-4h10l4 4m-18 0v10a1 1 0 001 1h16a1 1 0 001-1V8m-18 0h5a2 2 0 002 2h4a2 2 0 002-2h5"
    />
  ),
  users: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M17 20h5v-2a4 4 0 00-3-3.87M9 20H4v-2a4 4 0 013-3.87m6-1.13a4 4 0 10-4-4 4 4 0 004 4zm6-2a4 4 0 11-3-3.87"
    />
  ),
  chart: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M9 19V6m0 13H5.6a1.6 1.6 0 01-1.6-1.6V13a1.6 1.6 0 011.6-1.6H9m0 7.6h6.4a1.6 1.6 0 001.6-1.6v-3.6a1.6 1.6 0 00-1.6-1.6H9m0-6V4.6A1.6 1.6 0 0110.6 3h2.8A1.6 1.6 0 0115 4.6V11"
    />
  ),
  calendar: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z"
    />
  ),
  wallet: (
    <path
      strokeLinecap="round"
      strokeLinejoin="round"
      d="M21 12V7H5a2 2 0 010-4h14v4M3 5v14a2 2 0 002 2h16v-5M18 12a2 2 0 000 4h4v-4h-4z"
    />
  ),
};

function Icon({ name }) {
  return (
    <svg className="w-[18px] h-[18px]" fill="none" stroke="currentColor" strokeWidth={1.8} viewBox="0 0 24 24">
      {ICONS[name]}
    </svg>
  );
}

function NavItem({ to, children, icon }) {
  return (
    <NavLink
      to={to}
      end
      className={({ isActive }) =>
        `flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
          isActive ? "bg-brand-50 text-brand-700" : "text-slate-600 hover:bg-slate-100"
        }`
      }
    >
      <Icon name={icon} />
      {children}
    </NavLink>
  );
}

export default function Layout() {
  const { isHrm, logout } = useAuth();
  const navigate = useNavigate();

  async function handleLogout() {
    await logout();
    navigate("/login", { replace: true });
  }

  return (
    <div className="min-h-screen flex bg-slate-50">
      <aside className="w-60 shrink-0 bg-white border-r border-slate-200 flex flex-col">
        <div className="px-5 py-5 border-b border-slate-200 flex items-center gap-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brand-500 to-brand-700 flex items-center justify-center text-white font-bold text-sm">
            E
          </div>
          <div>
            <h1 className="text-sm font-bold text-slate-900">ERP Modules</h1>
          </div>
        </div>

        <nav className="flex-1 px-3 py-4 space-y-1">
          {isHrm ? (
            <>
              <div className="px-3 pb-2 text-[11px] font-semibold text-slate-400 uppercase tracking-wider">
                HRM
              </div>
              <NavItem to="/hrm" icon="home">
                Team Overview
              </NavItem>
              <NavItem to="/hrm/leave-inbox" icon="inbox">
                Leave Inbox
              </NavItem>
              <NavItem to="/hrm/users" icon="users">
                Users
              </NavItem>
            </>
          ) : (
            <>
              <NavItem to="/" icon="chart">
                Dashboard
              </NavItem>
              <NavItem to="/leave" icon="calendar">
                Leave
              </NavItem>
              <NavItem to="/payroll" icon="wallet">
                Payroll
              </NavItem>
            </>
          )}
        </nav>

        <div className="px-3 py-4 border-t border-slate-200">
          <div className="flex items-center gap-2.5 px-2 mb-3">
            <Avatar name={isHrm ? "HR Manager" : "You"} size="sm" />
            <div className="min-w-0">
              <p className="text-xs font-semibold text-slate-700 truncate">
                {isHrm ? "HR Manager" : "Employee"}
              </p>
            </div>
          </div>
          <button
            onClick={handleLogout}
            className="w-full text-left px-3 py-2 rounded-lg text-sm font-medium text-slate-500 hover:bg-slate-100 hover:text-slate-700 transition-colors"
          >
            Log out
          </button>
        </div>
      </aside>

      <main className="flex-1 overflow-y-auto animate-fade-in">
        <Outlet />
      </main>
    </div>
  );
}
