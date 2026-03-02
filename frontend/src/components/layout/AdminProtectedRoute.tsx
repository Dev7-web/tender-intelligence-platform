import { useEffect, useState } from "react";
import { Navigate, Outlet, useLocation } from "react-router-dom";

import { onAuthStateChanged, User } from "firebase/auth";
import { auth } from "@/firebase";

const AdminProtectedRoute = () => {
  const [user, setUser] = useState<User | null>(null);
  const [isAdmin, setIsAdmin] = useState(false);
  const [checking, setChecking] = useState(true);
  const location = useLocation();

  useEffect(() => {
    const unsubscribe = onAuthStateChanged(auth, async (firebaseUser) => {
      setUser(firebaseUser);
      if (!firebaseUser) {
        setIsAdmin(false);
        setChecking(false);
        return;
      }

      try {
        const tokenResult = await firebaseUser.getIdTokenResult(true);
        setIsAdmin(tokenResult.claims.admin === true);
      } catch {
        setIsAdmin(false);
      } finally {
        setChecking(false);
      }
    });
    return unsubscribe;
  }, []);

  if (checking) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-[#f5f6f9]">
        <p className="text-[#68708a]">Loading...</p>
      </div>
    );
  }

  if (!user || !isAdmin) {
    return <Navigate to="/admin/login" replace state={{ from: location }} />;
  }

  return <Outlet />;
};

export default AdminProtectedRoute;
