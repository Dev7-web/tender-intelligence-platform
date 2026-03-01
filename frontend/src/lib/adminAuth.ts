import { signInWithEmailAndPassword, signOut } from "firebase/auth";

import { auth } from "./firebase";

export const adminSignIn = (email: string, password: string) =>
  signInWithEmailAndPassword(auth, email, password);

export const adminSignOut = () => signOut(auth);
