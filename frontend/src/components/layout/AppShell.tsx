import { PropsWithChildren, useEffect, useRef, useState } from "react";
import { NavLink, useNavigate } from "react-router-dom";

import notificationIcon from "@/assets/dashboard/notification-icon.svg";
import profileAvatar from "@/assets/dashboard/profile-avatar.svg";
import BrandMark from "@/components/layout/BrandMark";
import { clearAuth, getUser } from "@/lib/auth";
import { useToastSimple } from "@/components/ui/toaster-simple";

const navItems = [
  { label: "Dashboard", to: "/dashboard" },
  { label: "Finding Tenders", to: "/tenders" },
  { label: "My List", to: "/my-list" },
  { label: "My Organization", to: "/organization" },
  { label: "Help", to: "/help" },
];

const AppShell = ({ children }: PropsWithChildren) => {
  const navigate = useNavigate();
  const [menuOpen, setMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement | null>(null);
  const buttonRef = useRef<HTMLButtonElement | null>(null);
  const user = getUser();
  const displayName = user?.name || user?.email || "Account";
  const displayEmail = user?.name ? user?.email : null;
  const { pushToast } = useToastSimple();

  useEffect(() => {
    if (!menuOpen) return;

    const handleClickOutside = (event: MouseEvent) => {
      const target = event.target as Node;
      if (menuRef.current?.contains(target)) return;
      if (buttonRef.current?.contains(target)) return;
      setMenuOpen(false);
    };

    const handleEscape = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setMenuOpen(false);
      }
    };

    document.addEventListener("mousedown", handleClickOutside);
    document.addEventListener("keydown", handleEscape);
    return () => {
      document.removeEventListener("mousedown", handleClickOutside);
      document.removeEventListener("keydown", handleEscape);
    };
  }, [menuOpen]);

  useEffect(() => {
    const handleAuthCleared = (event: Event) => {
      const detail = (event as CustomEvent<{ reason?: string }>).detail;
      if (detail?.reason === "session-expired") {
        pushToast("Session expired. Please sign in again.", "info");
        navigate("/auth");
      }
    };

    window.addEventListener("ta:auth:cleared", handleAuthCleared as EventListener);
    return () => {
      window.removeEventListener("ta:auth:cleared", handleAuthCleared as EventListener);
    };
  }, [navigate, pushToast]);

  const handleNavigate = (path: string) => {
    navigate(path);
    setMenuOpen(false);
  };

  const handleSignOut = () => {
    clearAuth("manual");
    navigate("/auth");
  };

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
            <div className="relative">
              <button
                ref={buttonRef}
                type="button"
                className="h-10 w-10 overflow-hidden rounded-full"
                aria-haspopup="menu"
                aria-expanded={menuOpen}
                aria-controls="account-menu"
                onClick={(event) => {
                  event.preventDefault();
                  event.stopPropagation();
                  setMenuOpen((prev) => !prev);
                }}
              >
                <img src={profileAvatar} alt="Account avatar" className="h-full w-full object-cover" />
              </button>
              {menuOpen && (
                <div
                  id="account-menu"
                  ref={menuRef}
                  role="menu"
                  className="absolute right-0 z-20 mt-2 w-56 rounded-xl border border-[#d9dce5] bg-white p-2 shadow-lg"
                >
                  <div className="px-3 py-2">
                    <p className="text-[10px] font-semibold uppercase tracking-[0.18em] text-[#9aa1b2]">Account</p>
                    <p className="mt-1 text-sm font-semibold text-[#2c3243]">{displayName}</p>
                    {displayEmail && <p className="text-xs text-[#6f7687]">{displayEmail}</p>}
                  </div>
                  <div className="my-1 h-px bg-[#e6e9f2]" />
                  <button
                    type="button"
                    role="menuitem"
                    className="flex w-full items-center rounded-md px-3 py-2 text-sm text-[#303543] hover:bg-[#f2f4fb]"
                    onClick={() => handleNavigate("/organization")}
                  >
                    My Organization
                  </button>
                  <button
                    type="button"
                    role="menuitem"
                    className="flex w-full items-center rounded-md px-3 py-2 text-sm text-[#303543] hover:bg-[#f2f4fb]"
                    onClick={() => handleNavigate("/help")}
                  >
                    Help
                  </button>
                  <div className="my-1 h-px bg-[#e6e9f2]" />
                  <button
                    type="button"
                    role="menuitem"
                    className="flex w-full items-center rounded-md px-3 py-2 text-sm font-semibold text-[#cc3b3b] hover:bg-[#feecec]"
                    onClick={handleSignOut}
                  >
                    Sign out
                  </button>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1280px] px-8 py-7">{children}</main>
    </div>
  );
};

export default AppShell;
