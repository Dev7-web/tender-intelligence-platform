// AUTH MIGRATION (Firebase -> central auth gateway):
// The Firebase SDK wrappers are commented out. The app now logs in via the
// backend `/auth/login` endpoint (which proxies to the auth gateway) and stores
// the returned tokens in localStorage. These exports are kept with the same
// names so existing importers (api.ts, adminApi.ts, AppShell, ProfilePage)
// keep working against the new token-based model.

// --- OLD (Firebase) — commented out ---
// import {
//   createUserWithEmailAndPassword,
//   signInWithEmailAndPassword,
//   signInWithPopup,
//   signOut,
// } from "firebase/auth";
//
// import { auth, googleProvider } from "@/firebase";
//
// export const signUpEmail = (email: string, password: string) =>
//   createUserWithEmailAndPassword(auth, email, password);
//
// export const signInEmail = (email: string, password: string) =>
//   signInWithEmailAndPassword(auth, email, password);
//
// export const signInGoogle = () => signInWithPopup(auth, googleProvider);
//
// export const signOutUser = () => signOut(auth);
//
// export const getIdToken = async () => {
//   const user = auth.currentUser;
//   if (!user) return null;
//   return user.getIdToken();
// };

// --- NEW: token-based helpers backed by the auth gateway ---
import { clearAuth, getToken } from "@/lib/auth";

/**
 * Returns the stored auth-gateway id_token (previously the live Firebase ID
 * token). Kept async for call-site compatibility (`await getIdToken()`).
 */
export const getIdToken = async (): Promise<string | null> => getToken();

/**
 * Sign-out no longer needs to talk to Firebase. Callers typically follow this
 * with `clearAuth(...)`; this remains a safe no-op-ish helper that clears local
 * auth state so any lone caller still logs the user out.
 */
export const signOutUser = async (): Promise<void> => {
  clearAuth("manual");
};
