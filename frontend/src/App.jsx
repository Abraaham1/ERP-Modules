import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ProtectedRoute from "./components/ProtectedRoute";
import Layout from "./components/Layout";

import LoginPage from "./pages/LoginPage";
import DashboardPage from "./pages/employee/DashboardPage";
import LeavePage from "./pages/employee/LeavePage";
import PayrollPage from "./pages/employee/PayrollPage";
import LeaveInboxPage from "./pages/hrm/LeaveInboxPage";
import UsersPage from "./pages/hrm/UsersPage";

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route path="/" element={<DashboardPage />} />
            <Route path="/leave" element={<LeavePage />} />
            <Route path="/payroll" element={<PayrollPage />} />

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
