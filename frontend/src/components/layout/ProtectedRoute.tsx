import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { getToken, setUser } from "@/lib/auth";
import { fetchMe } from "@/services/tenderAgentApi";

// AUTH MIGRATION (Firebase -> central auth gateway):
// Access is gated on the presence of a valid gateway token rather than a live
// Firebase auth listener. On mount we validate the stored token via /auth/me
// (which also refreshes the cached profile); an invalid/expired token fails the
// check and redirects to /auth.

type Status = "checking" | "authed" | "unauthed";

const ProtectedRoute = () => {
  const [status, setStatus] = useState<Status>("checking");
  const location = useLocation();

  useEffect(() => {
    let cancelled = false;

    if (!getToken()) {
      setStatus("unauthed");
      return;
    }

    fetchMe()
      .then((user) => {
        if (cancelled) return;
        setUser(user);
        setStatus("authed");
      })
      .catch(() => {
        if (!cancelled) setStatus("unauthed");
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

  if (status === "unauthed") {
    return <Navigate to="/auth" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default ProtectedRoute;
