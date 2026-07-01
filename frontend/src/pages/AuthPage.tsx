import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import AuthShell from "@/components/layout/AuthShell";
import { useToastSimple } from "@/components/ui/toaster-simple";
import { setRefreshToken, setToken, setUser } from "@/lib/auth";
import { fetchMe, login } from "@/services/tenderAgentApi";

// AUTH MIGRATION (Firebase -> central auth gateway):
// Login now posts email/password to the backend `/auth/login` (which proxies to
// the company auth gateway) and stores the returned id_token + refresh_token.
// The gateway is login-only, so self-service sign-up and Google sign-in have
// been removed (accounts are provisioned via the gateway) — the old Firebase
// flow is preserved in git history / commented below.

const EMAIL_RE = /^\S+@\S+\.\S+$/;

const AuthPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const { pushToast } = useToastSimple();
  const navigate = useNavigate();

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
    if (!password) {
      pushToast("Please enter your password", "error");
      return;
    }

    setLoading(true);
    try {
      const result = await login({ email: normalized, password });
      if (!result?.id_token) {
        throw new Error("no-token");
      }
      setToken(result.id_token);
      if (result.refresh_token) {
        setRefreshToken(result.refresh_token);
      }
      await completeLogin("Signed in successfully");
    } catch {
      pushToast("Invalid email or password.", "error");
    } finally {
      setLoading(false);
    }
  };

  // --- OLD (Firebase signup / Google sign-in) — commented out ---
  // const handleGoogleSignIn = async () => { await signInGoogle(); await completeLogin(...); };
  // signup mode toggled between createUserWithEmailAndPassword / signInWithEmailAndPassword.

  return (
    <AuthShell>
      <div className="w-full max-w-[560px] rounded-2xl border border-[#dbdee8] bg-[#f5f6f9] p-9 shadow-sm">
        <h1 className="text-center text-3xl font-semibold text-[#252a39] md:text-4xl">Welcome back</h1>
        <p className="mt-1 text-center text-base text-[#68708a] md:text-xl">Sign in to continue</p>

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
                autoComplete="current-password"
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
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="mt-6 h-12 w-full rounded-md bg-[#4040E0] text-lg font-medium text-white disabled:opacity-60"
        >
          {loading ? "Please wait..." : "Sign In"}
        </button>

        {/* --- OLD: "Continue with Google" button removed with the auth-gateway migration --- */}

        <div className="mt-8 border-t border-[#e8eaf0] pt-4 text-center">
          <Link to="/admin/login" className="text-xs text-[#4040E0] hover:text-[#2f2fbc] transition-colors">
            Login as Admin
          </Link>
        </div>
      </div>
    </AuthShell>
  );
};

export default AuthPage;
