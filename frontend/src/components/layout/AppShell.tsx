import { PropsWithChildren } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import notificationIcon from "@/assets/dashboard/notification-icon.svg";
import profileAvatar from "@/assets/dashboard/profile-avatar.svg";
import BrandMark from "@/components/layout/BrandMark";
import { clearAuth } from "@/lib/auth";

const navItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Finding Tenders", to: "/tenders" },
  { label: "My List", to: "/my-list" },
  { label: "My Organization", to: "/organization" },
  { label: "Help", to: "/help" },
];

const AppShell = ({ children }: PropsWithChildren) => {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-[#eceef3]">
      <header className="border-b border-[#d9dce5] bg-white">
        <div className="mx-auto flex h-[72px] max-w-[1280px] items-center px-8">
          <BrandMark />

          <nav className="ml-auto mr-6 flex max-w-[60%] items-center gap-2 overflow-x-auto text-xs text-[#4f5565] md:gap-5 md:text-[13px]">
            {navItems.map((item) => (
              <NavLink
                key={item.to}
                to={item.to}
                className={({ isActive }) =>
                  [
                    "rounded-md px-2 py-1 transition",
                    isActive ? "bg-[#eef0ff] text-[#4040E0]" : "hover:text-[#4040E0]",
                  ].join(" ")
                }
              >
                {item.label}
              </NavLink>
            ))}
          </nav>

          <div className="flex items-center gap-3">
            <div className="h-7 w-px bg-[#d6d9e3]" />
            <img src={notificationIcon} alt="Notifications" className="h-[25px] w-6 shrink-0" />
            <button
              className="h-10 w-10 overflow-hidden rounded-full"
              onClick={() => {
                clearAuth();
                navigate("/auth");
              }}
            >
              <img src={profileAvatar} alt="Account avatar" className="h-full w-full object-cover" />
            </button>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-8 py-7">{children}</main>
    </div>
  );
};

export default AppShell;
