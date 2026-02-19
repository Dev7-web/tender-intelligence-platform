import { NavLink, useLocation } from "react-router-dom";

const navItems = [
  { label: "Dashboard", to: "/" },
  { label: "Tenders", to: "/tenders" },
  { label: "Companies", to: "/companies" },
  { label: "Search", to: "/search" },
  { label: "Jobs", to: "/jobs" },
  { label: "Settings", to: "/settings" },
];

const titleMap: Record<string, string> = {
  "/": "Dashboard",
  "/tenders": "Tenders",
  "/companies": "Companies",
  "/search": "Search",
  "/jobs": "Jobs",
  "/settings": "Settings",
};

const Header = () => {
  const location = useLocation();
  const basePath = "/" + location.pathname.split("/")[1];
  const title = titleMap[location.pathname] || titleMap[basePath] || "Tendorlelo";

  return (
    <header className="px-6 py-6 border-b border-border bg-white/80 backdrop-blur">
      <div className="mx-auto max-w-6xl flex flex-col gap-4">
        <p className="text-xs uppercase tracking-[0.2em] text-muted">Operations</p>
        <h2 className="text-3xl font-semibold text-text">{title}</h2>
        <nav className="flex gap-3 overflow-x-auto lg:hidden">
          {navItems.map((item) => (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "shrink-0 rounded-full border border-border px-3 py-1 text-xs font-semibold",
                  isActive ? "bg-primary text-white" : "bg-white text-muted",
                ].join(" ")
              }
            >
              {item.label}
            </NavLink>
          ))}
        </nav>
      </div>
    </header>
  );
};

export default Header;
