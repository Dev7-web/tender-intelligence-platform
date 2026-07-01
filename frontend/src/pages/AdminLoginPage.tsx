import { useState } from "react";
import { useNavigate, Link } from "react-router-dom";
import { Eye, EyeOff } from "lucide-react";

import { clearAuth, setRefreshToken, setToken, setUser } from "@/lib/auth";
import { fetchMe, login } from "@/services/tenderAgentApi";

// AUTH MIGRATION (Firebase -> central auth gateway):
// Admin login uses the same gateway login as regular users; admin authorization
// is decided by the `is_admin` flag on the synced profile (from /auth/me),
// which the backend derives from the gateway JWT `role == "admin"` claim.

const AdminLoginPage = () => {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [showPassword, setShowPassword] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const navigate = useNavigate();

  const handleSubmit = async () => {
    setError("");
    if (!email.trim() || !password) {
      setError("Please enter your email and password.");
      return;
    }

    setLoading(true);
    try {
      const result = await login({ email: email.trim().toLowerCase(), password });
      if (!result?.id_token) {
        setError("Invalid email or password.");
        return;
      }
      setToken(result.id_token);
      if (result.refresh_token) {
        setRefreshToken(result.refresh_token);
      }

      const user = await fetchMe();
      if (!user?.is_admin) {
        clearAuth("manual");
        setError("You do not have admin access.");
        return;
      }
      setUser(user);
      navigate("/admin/dashboard");
    } catch {
      setError("Invalid email or password.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen items-center justify-center bg-[#f5f6f9]">
      <div className="w-full max-w-[440px] rounded-2xl border border-[#dbdee8] bg-white p-9 shadow-sm">
        <h1 className="text-center text-3xl font-semibold text-[#252a39]">Admin Login</h1>
        <p className="mt-1 text-center text-sm text-[#68708a]">Sign in to the admin dashboard</p>

        <div className="mt-8 space-y-4">
          <div>
            <label className="mb-2 block text-sm font-medium text-[#232836]">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="admin@example.com"
              className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 text-base outline-none focus:border-[#4040E0]"
              autoComplete="email"
              onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
            />
          </div>

          <div>
            <label className="mb-2 block text-sm font-medium text-[#232836]">Password</label>
            <div className="relative">
              <input
                type={showPassword ? "text" : "password"}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                className="h-12 w-full rounded-md border border-[#e0e3eb] bg-[#eef0f4] px-3 pr-10 text-base outline-none focus:border-[#4040E0]"
                autoComplete="current-password"
                onKeyDown={(e) => e.key === "Enter" && handleSubmit()}
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

          {error && <p className="text-sm text-red-500">{error}</p>}
        </div>

        <button
          onClick={handleSubmit}
          disabled={loading}
          className="mt-6 h-12 w-full rounded-md bg-[#4040E0] text-base font-medium text-white disabled:opacity-60"
        >
          {loading ? "Signing in..." : "Sign In"}
        </button>

        <div className="mt-6 border-t border-[#e8eaf0] pt-4 text-center">
          <Link to="/auth" className="text-xs text-[#4040E0] hover:text-[#2f2fbc] transition-colors">
            ← Back to main login
          </Link>
        </div>
      </div>
    </div>
  );
};

export default AdminLoginPage;
