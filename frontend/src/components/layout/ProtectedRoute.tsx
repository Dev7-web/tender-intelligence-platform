import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getToken } from "@/lib/auth";

const ProtectedRoute = () => {
  const location = useLocation();
  const token = getToken();

  if (!token) {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
