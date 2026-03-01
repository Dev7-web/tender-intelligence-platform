import { PropsWithChildren } from "react";
import { Bell, ChevronDown, LogOut } from "lucide-react";
import { NavLink, useNavigate } from "react-router-dom";

import BrandMark from "@/components/layout/BrandMark";
import { clearAuth } from "@/lib/auth";

const navItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Tenders", to: "/tenders" },
  { label: "My List", to: "/my-list" },
  { label: "My Organization", to: "/organization" },
  { label: "Help", to: "/help" },
];

const AppShell = ({ children }: PropsWithChildren) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#eceef3]">
      <header className="border-b border-[#d9dce5] bg-white">
        <div className="mx-auto flex h-16 max-w-[1280px] items-center justify-between px-4 sm:px-8">
          <BrandMark />

          <nav className="hidden items-center gap-1 text-[13px] text-[#4f5565] md:flex">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "whitespace-nowrap rounded-md px-3 py-1.5 font-medium transition",
                    isActive
                      ? "bg-[#eef0ff] text-[#4040E0]"
                      : "text-[#4f5565] hover:bg-[#f4f5fb] hover:text-[#4040E0]",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <button className="flex h-8 w-8 items-center justify-center rounded-full hover:bg-[#f4f5fb]">
              <Bell size={16} className="text-[#6a7186]" />
            </button>
            <button
              className="flex items-center gap-2 rounded-full border border-[#d6d9e3] bg-white px-3 py-1.5 text-xs text-[#5f6577] transition hover:border-[#bbbfcc] hover:bg-[#f9f9fb]"
              onClick={() => {
                clearAuth();
                navigate("/auth");
              }}
            >
              <div className="flex h-6 w-6 items-center justify-center rounded-full bg-[#4040E0] text-[10px] font-semibold text-white">
                A
              </div>
              <span className="hidden sm:inline">Account</span>
              <ChevronDown size={12} />
            </button>
          </div>
        </div>

        {/* Mobile nav */}
        <div className="flex items-center gap-1 overflow-x-auto px-4 pb-2 md:hidden">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "shrink-0 rounded-full px-3 py-1 text-xs font-medium transition",
                  isActive
                    ? "bg-[#4040E0] text-white"
                    : "bg-[#f0f1f7] text-[#5f6577] hover:text-[#4040E0]",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-4 py-6 sm:px-8 sm:py-7">{children}</main>
    </div>
  );
};

export default AppShell;
