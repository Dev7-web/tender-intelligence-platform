import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getToken, setUser } from "@/lib/auth";
import { fetchMe } from "@/services/tenderAgentApi";

// AUTH MIGRATION (Firebase -> central auth gateway):
// Admin access is gated on the `is_admin` flag from the synced profile
// (/auth/me), which the backend derives from the gateway JWT `role` claim —
// replacing the old Firebase custom-claim check.

type Status = "checking" | "admin" | "denied";

const AdminProtectedRoute = () => {
  const [status, setStatus] = useState<Status>("checking");
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    if (!getToken()) {
      setStatus("denied");
      return;
    }

    fetchMe()
      .then((user) => {
        if (cancelled) return;
        if (user?.is_admin) {
          setUser(user);
          setStatus("admin");
        } else {
          setStatus("denied");
        }
      })
      .catch(() => {
        if (!cancelled) setStatus("denied");
      });

    return () => {
      cancelled = true;
    };
  }, []);

  if (status === "checking") {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f6f9]">
        <p className="text-[#68708a]">Loading...</p>
      </div>
    );
  }

  if (status === "denied") {
    return <Navigate to="/admin/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default AdminProtectedRoute;
