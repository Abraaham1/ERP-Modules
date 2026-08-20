import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

import LoginPage from "./pages/LoginPage";
import ForgotPasswordPage from "./pages/ForgotPasswordPage";
import ResetPasswordPage from "./pages/ResetPasswordPage";
import DashboardPage from "./pages/employee/DashboardPage";
import LeavePage from "./pages/employee/LeavePage";
import PayrollPage from "./pages/employee/PayrollPage";
import LeaveInboxPage from "./pages/hrm/LeaveInboxPage";
import UsersPage from "./pages/hrm/UsersPage";
import HrmHomePage from "./pages/hrm/HrmHomePage";
import RoleEmployeesPage from "./pages/hrm/RoleEmployeesPage";
import EmployeeDetailPage from "./pages/hrm/EmployeeDetailPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/forgot-password" element={<ForgotPasswordPage />} />
          <Route path="/reset-password" element={<ResetPasswordPage />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            {/* Employee-only personal dashboards */}
            <Route
              path="/"
              element={
                <ProtectedRoute employeeOnly>
                  <DashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/leave"
              element={
                <ProtectedRoute employeeOnly>
                  <LeavePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/payroll"
              element={
                <ProtectedRoute employeeOnly>
                  <PayrollPage />
                </ProtectedRoute>
              }
            />

            {/* HRM-only */}
            <Route
              path="/hrm"
              element={
                <ProtectedRoute hrmOnly>
                  <HrmHomePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hrm/roles/:type"
              element={
                <ProtectedRoute hrmOnly>
                  <RoleEmployeesPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hrm/employees/:userId"
              element={
                <ProtectedRoute hrmOnly>
                  <EmployeeDetailPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hrm/leave-inbox"
              element={
                <ProtectedRoute hrmOnly>
                  <LeaveInboxPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/hrm/users"
              element={
                <ProtectedRoute hrmOnly>
                  <UsersPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}
