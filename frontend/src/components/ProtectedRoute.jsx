import { Navigate, useLocation } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ children, hrmOnly = false }) {
  const { isAuthenticated, isHrm } = useAuth();
  const location = useLocation();

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (hrmOnly && !isHrm) {
    return <Navigate to="/" replace />;
  }

  return children;
}
