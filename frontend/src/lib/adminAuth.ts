// AUTH MIGRATION (Firebase -> central auth gateway):
// Admin login now uses the same gateway login as regular users (see
// AdminLoginPage). Admin authorization is decided by the `is_admin` flag on the
// synced user profile (/auth/me), not by a Firebase custom claim.

// --- OLD (Firebase) — commented out ---
// import { signInWithEmailAndPassword, signOut } from "firebase/auth";
//
// import { auth } from "@/firebase";
//
// export const adminSignIn = (email: string, password: string) =>
//   signInWithEmailAndPassword(auth, email, password);
//
// export const adminSignOut = () => signOut(auth);

import { clearAuth } from "@/lib/auth";

// Sign the admin out by clearing the stored gateway tokens/profile.
export const adminSignOut = async (): Promise<void> => {
  clearAuth("manual");
};
