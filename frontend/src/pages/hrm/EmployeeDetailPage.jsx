import { useState, useEffect, useCallback } from "react";
import { useParams, useNavigate } from "react-router-dom";
import { authApi, attendanceApi, payrollApi } from "../../api/client";
import Avatar from "../../components/Avatar";
import EmployeeTypeBadge from "../../components/EmployeeTypeBadge";

function formatCurrency(n) {
  return new Intl.NumberFormat(undefined, {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  }).format(n);
}

const MONTH_NAMES = [
  "January",
  "February",
  "March",
  "April",
  "May",
  "June",
  "July",
  "August",
  "September",
  "October",
  "November",
  "December",
];

export default function EmployeeDetailPage() {
  const { userId } = useParams();
  const navigate = useNavigate();

  const now = new Date();
  const [year, setYear] = useState(now.getFullYear());
  const [month, setMonth] = useState(now.getMonth() + 1);

  const [profile, setProfile] = useState(null);
  const [stats, setStats] = useState(null);
  const [salary, setSalary] = useState(null);

  const [loading, setLoading] = useState(true);
  const [profileLoading, setProfileLoading] = useState(true);
  const [statsLoading, setStatsLoading] = useState(true);
  const [salaryLoading, setSalaryLoading] = useState(true);

  const [profileError, setProfileError] = useState(null);
  const [statsError, setStatsError] = useState(null);
  const [salaryError, setSalaryError] = useState(null);

  const load = useCallback(async () => {
    setLoading(true);

    setStats(null);
    setSalary(null);
    setStatsError(null);
    setSalaryError(null);

    setProfileLoading(true);
    setProfileError(null);

    try {
      const profileRes = await authApi.get(`/users/${userId}`);

      console.log("Profile response:", profileRes.data);

      setProfile(profileRes.data);
    } catch (err) {
      console.error("Profile loading error:", err);
      console.error("Profile response:", err.response?.data);
      console.error("Profile status:", err.response?.status);
      console.error("Profile URL:", err.config?.url);

      setProfileError(
        err.response?.data?.detail || "Could not load employee profile."
      );
    } finally {
      setProfileLoading(false);
    }

    setStatsLoading(true);

    try {
      const statsRes = await attendanceApi.get(
        `/attendance/user/${userId}/stats/${year}/${month}`
      );

      console.log("Attendance response:", statsRes.data);

      setStats(statsRes.data);
    } catch (err) {
      console.error("Attendance loading error:", err);
      console.error("Attendance response:", err.response?.data);
      console.error("Attendance status:", err.response?.status);
      console.error("Attendance URL:", err.config?.url);

      setStatsError(
        err.response?.data?.detail || "Could not load attendance data."
      );
    } finally {
      setStatsLoading(false);
    }

    setSalaryLoading(true);

    try {
      const salaryRes = await payrollApi.get(`/payroll/user/${userId}`, {
        params: {
          year,
          month,
        },
      });

      console.log("Payroll response:", salaryRes.data);

      setSalary(salaryRes.data);
    } catch (err) {
      console.error("Payroll loading error:", err);
      console.error("Payroll response:", err.response?.data);
      console.error("Payroll status:", err.response?.status);
      console.error("Payroll URL:", err.config?.url);

      setSalaryError(
        err.response?.data?.detail || "Could not load payroll data."
      );
    } finally {
      setSalaryLoading(false);
    }

    setLoading(false);
  }, [userId, year, month]);

  useEffect(() => {
    load();
  }, [load]);

  function shiftMonth(delta) {
    let newMonth = month + delta;
    let newYear = year;

    if (newMonth > 12) {
      newMonth = 1;
      newYear += 1;
    } else if (newMonth < 1) {
      newMonth = 12;
      newYear -= 1;
    }

    setMonth(newMonth);
    setYear(newYear);
  }

  return (
    <div className="p-4 md:p-8 max-w-4xl">
      {/* Back button */}
      <button
        onClick={() => navigate(-1)}
        className="text-sm text-slate-500 hover:text-slate-700 mb-4 inline-flex items-center gap-1"
      >
        ← Back
      </button>

      {profileLoading && (
        <p className="text-sm text-slate-500 mb-6">
          Loading employee profile...
        </p>
      )}

      {profileError && (
        <div className="text-sm text-red-600 bg-red-50 border border-red-200 rounded-lg px-4 py-3 mb-6">
          {profileError}
        </div>
      )}

      {profile && (
        <>
          <div className="flex items-center gap-4 mb-8">
            <Avatar name={profile.full_name} size="lg" />

            <div>
              <h1 className="text-2xl font-bold text-slate-900">
                {profile.full_name}
              </h1>

              <p className="text-sm text-slate-500">
                {profile.email}
              </p>

              <div className="mt-2">
                <EmployeeTypeBadge type={profile.employee_type} />
              </div>
            </div>
          </div>


          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 mb-4">
            <h2 className="text-sm font-semibold text-slate-700">
              Monthly Summary
            </h2>

            <div className="flex items-center gap-3 bg-white border border-slate-200 rounded-lg px-2 py-1 self-start sm:self-auto">
              <button
                onClick={() => shiftMonth(-1)}
                className="text-slate-400 hover:text-slate-600 px-1"
              >
                ←
              </button>

              <span className="text-sm font-medium text-slate-700 min-w-[110px] text-center">
                {MONTH_NAMES[month - 1]} {year}
              </span>

              <button
                onClick={() => shiftMonth(1)}
                className="text-slate-400 hover:text-slate-600 px-1"
              >
                →
              </button>
            </div>
          </div>

          {statsLoading && (
            <p className="text-sm text-slate-500 mb-4">
              Loading attendance...
            </p>
          )}

          {statsError && (
            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-4">
              {statsError}
            </div>
          )}

          {stats && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
              <StatCard
                label="Present"
                value={stats.present_days}
                color="text-emerald-600"
              />

              <StatCard
                label="Absent"
                value={stats.raw_absent_days}
                color="text-red-600"
              />

              <StatCard
                label="Half Days"
                value={stats.half_days}
                color="text-amber-600"
              />

              <StatCard
                label="Leave"
                value={stats.leave_days}
                color="text-sky-600"
              />
            </div>
          )}

          {salaryLoading && (
            <p className="text-sm text-slate-500 mb-4">
              Loading salary...
            </p>
          )}

          {salaryError && (
            <div className="text-sm text-amber-700 bg-amber-50 border border-amber-200 rounded-lg px-4 py-3 mb-4">
              {salaryError}
            </div>
          )}

          {salary && (
            <div className="bg-gradient-to-br from-brand-600 to-brand-700 rounded-xl p-5 sm:p-8 text-white shadow-card">
              <p className="text-brand-100 text-sm font-medium mb-1">
                Salary this month
              </p>

              <p className="text-3xl sm:text-4xl font-bold mb-6">
                {formatCurrency(salary.salary_so_far)}
              </p>

              <div className="grid grid-cols-3 gap-3 sm:gap-4 pt-4 border-t border-white/20 text-sm">
                <div>
                  <p className="text-brand-100">Fixed Salary</p>
                  <p className="font-semibold">
                    {formatCurrency(salary.fixed_salary)}
                  </p>
                </div>

                <div>
                  <p className="text-brand-100">Absences</p>
                  <p className="font-semibold">
                    {salary.num_absents}
                  </p>
                </div>

                <div>
                  <p className="text-brand-100">Deduction</p>
                  <p className="font-semibold">
                    {formatCurrency(salary.deduction)}
                  </p>
                </div>
              </div>
            </div>
          )}
        </>
      )}

      {!profileLoading && !profile && !profileError && (
        <p className="text-sm text-slate-500">
          Employee not found.
        </p>
      )}
    </div>
  );
}

function StatCard({ label, value, color }) {
  return (
    <div className="bg-white rounded-xl border border-slate-200 p-4 shadow-card">
      <p className={`text-2xl font-bold ${color}`}>
        {value}
      </p>

      <p className="text-xs text-slate-500 mt-1">
        {label}
      </p>
    </div>
  );
}