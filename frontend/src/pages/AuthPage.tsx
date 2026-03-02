import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";
import { isAxiosError } from "axios";

import AuthShell from "@/components/layout/AuthShell";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { AuthUser, setToken, setUser } from "@/lib/auth";
import { authSignIn, authSignUp } from "@/services/tenderAgentApi";

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
  const [showPassword, setShowPassword] = useState(false);
  const [showConfirmPassword, setShowConfirmPassword] = useState(false);
  const [loading, setLoading] = useState(false);
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

  // Google sign-in is intentionally disabled for now.
  // We can re-enable `authGoogleStart` flow once OAuth is finalized.

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

        {/* <div className="mt-4 rounded-md border border-[#e2e5ef] bg-[#eef0f6] px-3 py-2 text-center text-xs text-[#7a8094]">
          Continue with Google is temporarily disabled.
        </div> */}

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
