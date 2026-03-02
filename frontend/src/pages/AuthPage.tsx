import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import AuthShell from "@/components/layout/AuthShell";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { setUser } from "@/lib/auth";
import { signInEmail, signInGoogle, signUpEmail } from "@/lib/firebaseAuth";
import { fetchMe } from "@/services/tenderAgentApi";

type AuthMode = "signup" | "signin";

const EMAIL_RE = /^\S+@\S+\.\S+$/;
const HAS_LETTER_RE = /[A-Za-z]/;
const HAS_DIGIT_RE = /[0-9]/;

const getFirebaseErrorMessage = (error: unknown) => {
  const code = (error as { code?: string })?.code;
  switch (code) {
    case "auth/email-already-in-use":
      return "Email already in use. Please sign in instead.";
    case "auth/invalid-email":
      return "Please enter a valid email.";
    case "auth/weak-password":
      return "Password is too weak.";
    case "auth/user-not-found":
    case "auth/wrong-password":
    case "auth/invalid-credential":
      return "Invalid email or password.";
    case "auth/popup-closed-by-user":
      return "Google sign-in was cancelled.";
    case "auth/network-request-failed":
      return "Network error. Please try again.";
    case "auth/account-exists-with-different-credential":
      return "This email is linked to another sign-in method.";
    default:
      return null;
  }
};

const AuthPage = () => {
  const [mode, setMode] = useState<AuthMode>("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { pushToast } = useToastSimple();
  const navigate = useNavigate();

  const resetFields = () => {
    setPassword("");
    setConfirmPassword("");
  };

  const completeLogin = async (message: string) => {
    const user = await fetchMe();
    setUser(user);
    pushToast(message, "success");

    if (user.company_id) {
      navigate("/dashboard");
      return;
    }
    navigate("/onboarding/company");
  };

  const handleSubmit = async () => {
    const normalized = email.trim().toLowerCase();
    if (!EMAIL_RE.test(normalized)) {
      pushToast("Please enter a valid email", "error");
      return;
    }
    if (password.length < 8) {
      pushToast("Password must be at least 8 characters", "error");
      return;
    }
    if (!HAS_LETTER_RE.test(password) || !HAS_DIGIT_RE.test(password)) {
      pushToast("Password must include at least one letter and one number", "error");
      return;
    }
    if (mode === "signup" && password !== confirmPassword) {
      pushToast("Passwords do not match", "error");
      return;
    }

    setLoading(true);
    try {
      if (mode === "signup") {
        await signUpEmail(normalized, password);
      } else {
        await signInEmail(normalized, password);
      }
      await completeLogin(mode === "signup" ? "Account created successfully" : "Signed in successfully");
    } catch (error: unknown) {
      pushToast(
        getFirebaseErrorMessage(error) || (mode === "signup" ? "Unable to create account" : "Unable to sign in"),
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    setLoading(true);
    try {
      await signInGoogle();
      await completeLogin("Signed in with Google");
    } catch (error: unknown) {
      pushToast(getFirebaseErrorMessage(error) || "Unable to sign in with Google", "error");
    } finally {
      setLoading(false);
    }
  };

  const toggleMode = () => {
    setMode((prev) => (prev === "signup" ? "signin" : "signup"));
    resetFields();
  };

  return (
    <AuthShell>
      <div className="w-full max-w-[560px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-9 shadow-sm">
        <h1 className="text-center text-3xl font-semibold text-[#252a39] md:text-4xl">
          {mode === "signup" ? "Create account" : "Welcome back"}
        </h1>
        <p className="mt-1 text-center text-base text-[#68708a] md:text-xl">
          {mode === "signup" ? "Sign up with email and password" : "Sign in to continue"}
        </p>

        <div className="mt-10 space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-[#232836]">Email</label>
            <input
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="Enter email"
              className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 text-base"
              autoComplete="email"
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSubmit();
                }
              }}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-[#232836]">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                placeholder="Enter password"
                className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 pr-10 text-base"
                autoComplete={mode === "signup" ? "new-password" : "current-password"}
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSubmit();
                  }
                }}
              />
              <button
                type="button"
                tabIndex={-1}
                onClick={() => setShowPassword((v) => !v)}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]"
              >
                {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
              </button>
            </div>
          </div>

          {mode === "signup" ? (
            <div>
              <label className="mb-2 block text-sm font-medium text-[#232836]">Confirm password</label>
              <div className="relative">
                <input
                  type={showConfirmPassword ? "text" : "password"}
                  value={confirmPassword}
                  onChange={(event) => setConfirmPassword(event.target.value)}
                  placeholder="Re-enter password"
                  className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 pr-10 text-base"
                  autoComplete="new-password"
                  onKeyDown={(event) => {
                    if (event.key === "Enter") {
                      handleSubmit();
                    }
                  }}
                />
                <button
                  type="button"
                  tabIndex={-1}
                  onClick={() => setShowConfirmPassword((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-[#9CA3AF] hover:text-[#6B7280]"
                >
                  {showConfirmPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>
          ) : null}

          <p className="text-xs text-[#68708a]">Use at least 8 characters with one letter and one number.</p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="mt-6 h-12 w-full rounded-md bg-[#4040E0] text-lg font-medium text-white disabled:opacity-60"
        >
          {loading ? "Please wait..." : mode === "signup" ? "Sign Up" : "Sign In"}
        </button>

        <button
          type="button"
          onClick={handleGoogleSignIn}
          disabled={loading}
          className="mt-4 h-12 w-full rounded-md border border-[#d9dce5] bg-white text-sm font-semibold text-[#232836] hover:bg-[#f4f5fb] disabled:opacity-60"
        >
          Continue with Google
        </button>

        <p className="mt-8 text-center text-sm text-[#6d7487]">
          {mode === "signup" ? "Already have an account?" : "Need an account?"}{" "}
          <button
            type="button"
            onClick={toggleMode}
            className="font-medium text-[#4040E0]"
            disabled={loading}
          >
            {mode === "signup" ? "Sign in" : "Sign up"}
          </button>
        </p>

        <div className="mt-6 border-t border-[#e8eaf0] pt-4 text-center">
          <Link
            to="/admin/login"
            className="text-xs text-[#4040E0] hover:text-[#2f2fbc] transition-colors"
          >
            Login as Admin
          </Link>
        </div>
      </div>
    </AuthShell>
  );
};

export default AuthPage;
