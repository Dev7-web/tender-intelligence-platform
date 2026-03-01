import { initializeApp } from "firebase/app";
import { getAuth } from "firebase/auth";

const firebaseConfig = {
  apiKey: "AIzaSyCbYUSaNzO5xt6yhHpYgvkfbr0xyFayy6c",
  authDomain: "tender-admin-9e194.firebaseapp.com",
  projectId: "tender-admin-9e194",
  storageBucket: "tender-admin-9e194.firebasestorage.app",
  messagingSenderId: "565321502967",
  appId: "1:565321502967:web:9b5b5e562fee7334bac3f2",
  measurementId: "G-0YCDX9QS43",
};

const app = initializeApp(firebaseConfig);
export const auth = getAuth(app);
