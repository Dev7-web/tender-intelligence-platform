import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { isAxiosError } from "axios";

import AuthShell from "@/components/layout/AuthShell";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { AuthUser, setToken, setUser } from "@/lib/auth";
import { authGoogleStart, authSignIn, authSignUp } from "@/services/tenderAgentApi";

type AuthMode = "signup" | "signin";

type ApiErrorBody = {
  detail?: string;
  error?: { message?: string };
};

const EMAIL_RE = /^\S+@\S+\.\S+$/;
const HAS_LETTER_RE = /[A-Za-z]/;
const HAS_DIGIT_RE = /[0-9]/;

const AuthPage = () => {
  const [mode, setMode] = useState<AuthMode>("signup");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const { pushToast } = useToastSimple();
  const navigate = useNavigate();

  const getApiErrorMessage = (error: unknown): string | null => {
    if (!isAxiosError<ApiErrorBody>(error)) return null;
    if (typeof error.response?.data?.detail === "string") {
      return error.response.data.detail;
    }
    if (typeof error.response?.data?.error?.message === "string") {
      return error.response.data.error.message;
    }
    return null;
  };

  const resetFields = () => {
    setPassword("");
    setConfirmPassword("");
  };

  const completeLogin = (token: string, user: AuthUser) => {
    setToken(token);
    setUser(user);
    pushToast(mode === "signup" ? "Account created successfully" : "Signed in successfully", "success");

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
        const response = await authSignUp({ email: normalized, password });
        completeLogin(response.token, response.user);
      } else {
        const response = await authSignIn({ email: normalized, password });
        completeLogin(response.token, response.user);
      }
    } catch (error: unknown) {
      pushToast(
        getApiErrorMessage(error) || (mode === "signup" ? "Unable to create account" : "Unable to sign in"),
        "error"
      );
    } finally {
      setLoading(false);
    }
  };

  const handleGoogle = async () => {
    setGoogleLoading(true);
    try {
      const response = await authGoogleStart();
      if (response.enabled && response.auth_url) {
        window.location.href = response.auth_url;
        return;
      }
      pushToast(response.message || "Google OAuth is not configured", "info");
    } catch (error: unknown) {
      pushToast(getApiErrorMessage(error) || "Unable to start Google sign-in", "error");
    } finally {
      setGoogleLoading(false);
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
            <input
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="Enter password"
              className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 text-base"
              autoComplete={mode === "signup" ? "new-password" : "current-password"}
              onKeyDown={(event) => {
                if (event.key === "Enter") {
                  handleSubmit();
                }
              }}
            />
          </div>

          {mode === "signup" ? (
            <div>
              <label className="mb-2 block text-sm font-medium text-[#232836]">Confirm password</label>
              <input
                type="password"
                value={confirmPassword}
                onChange={(event) => setConfirmPassword(event.target.value)}
                placeholder="Re-enter password"
                className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 text-base"
                autoComplete="new-password"
                onKeyDown={(event) => {
                  if (event.key === "Enter") {
                    handleSubmit();
                  }
                }}
              />
            </div>
          ) : null}

          <p className="text-xs text-[#68708a]">Use at least 8 characters with one letter and one number.</p>
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading || googleLoading}
          className="mt-6 h-12 w-full rounded-md bg-[#4040E0] text-lg font-medium text-white disabled:opacity-60"
        >
          {loading ? "Please wait..." : mode === "signup" ? "Sign Up" : "Sign In"}
        </button>

        <p className="mt-4 text-center text-sm text-[#767f95]">OR</p>

        <button
          className="mt-3 h-11 w-full rounded-md bg-[#dd4b39] text-base font-medium text-white disabled:opacity-60"
          onClick={handleGoogle}
          disabled={loading || googleLoading}
        >
          {googleLoading ? "Opening Google..." : "Continue with Google"}
        </button>

        <p className="mt-8 text-center text-sm text-[#6d7487]">
          {mode === "signup" ? "Already have an account?" : "Need an account?"}{" "}
          <button
            type="button"
            onClick={toggleMode}
            className="font-medium text-[#4040E0]"
            disabled={loading || googleLoading}
          >
            {mode === "signup" ? "Sign in" : "Sign up"}
          </button>
        </p>

        <div className="mt-2 text-center text-xs text-[#8a90a4]">
          Google login requires backend OAuth configuration before it can be used in production.
        </div>
      </div>
    </AuthShell>
  );
};

export default AuthPage;
