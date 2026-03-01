import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { Bell, FileText, LogOut } from "lucide-react";

import { adminSignOut } from "@/lib/adminAuth";

const navLinkClass = ({ isActive }: { isActive: boolean }) =>
  `px-4 py-2 rounded-lg text-sm font-medium transition-colors ${
    isActive
      ? "bg-[#EEF2FF] text-[#4040E0] border border-[#C7D2FE]"
      : "text-[#68708a] hover:text-[#252a39] hover:bg-[#F5F6F9]"
  }`;

const AdminLayout = () => {
  const navigate = useNavigate();

  const handleSignOut = async () => {
    await adminSignOut();
    navigate("/admin/login");
  };

  return (
    <div className="min-h-screen bg-[#F5F5F5]">
      {/* Header */}
      <header className="bg-white border-b border-[#E5E7EB]">
        <div className="px-4 sm:px-8 h-16 flex items-center">
          {/* Logo */}
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-[#4040E0] rounded-lg flex items-center justify-center">
              <FileText className="w-4 h-4 text-white" />
            </div>
            <span className="font-bold text-[#252a39] text-lg">Tender Agent</span>
          </div>

          {/* Desktop: nav + icons on right */}
          <div className="ml-auto hidden sm:flex items-center gap-2">
            <nav className="flex items-center gap-1 mr-3">
              <NavLink to="/admin/dashboard" className={navLinkClass}>
                Dashboard
              </NavLink>
              <NavLink to="/admin/users" className={navLinkClass}>
                Manage Users
              </NavLink>
            </nav>
            <button className="w-9 h-9 rounded-full bg-[#F5F6F9] flex items-center justify-center text-[#68708a] hover:bg-[#E5E7EB]">
              <Bell className="w-5 h-5" />
            </button>
            <button
              onClick={handleSignOut}
              title="Sign out"
              className="w-9 h-9 rounded-full bg-[#F5F6F9] flex items-center justify-center text-[#68708a] hover:bg-[#E5E7EB]"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>

          {/* Mobile: icons only on right */}
          <div className="ml-auto flex sm:hidden items-center gap-2">
            <button className="w-9 h-9 rounded-full bg-[#F5F6F9] flex items-center justify-center text-[#68708a] hover:bg-[#E5E7EB]">
              <Bell className="w-5 h-5" />
            </button>
            <button
              onClick={handleSignOut}
              title="Sign out"
              className="w-9 h-9 rounded-full bg-[#F5F6F9] flex items-center justify-center text-[#68708a] hover:bg-[#E5E7EB]"
            >
              <LogOut className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Mobile nav row — below the logo bar */}
        <nav className="sm:hidden flex items-center gap-1 px-4 pb-2">
          <NavLink to="/admin/dashboard" className={navLinkClass}>
            Dashboard
          </NavLink>
          <NavLink to="/admin/users" className={navLinkClass}>
            Manage Users
          </NavLink>
        </nav>
      </header>

      {/* Page content */}
      <main className="px-4 py-6 sm:px-8 sm:py-8 max-w-7xl mx-auto">
        <Outlet />
      </main>
    </div>
  );
};

export default AdminLayout;
