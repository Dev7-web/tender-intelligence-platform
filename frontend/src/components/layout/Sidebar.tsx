import { NavLink } from "react-router-dom";
import {
  LayoutDashboard,
  FileText,
  Building2,
  Search,
  Activity,
  Settings,
} from "lucide-react";

const navItems = [
  { label: "Dashboard", to: "/", icon: LayoutDashboard },
  { label: "Tenders", to: "/tenders", icon: FileText },
  { label: "Companies", to: "/companies", icon: Building2 },
  { label: "Search", to: "/search", icon: Search },
  { label: "Jobs", to: "/jobs", icon: Activity },
  { label: "Settings", to: "/settings", icon: Settings },
];

const Sidebar = () => {
  return (
    <aside className="hidden lg:flex lg:flex-col lg:w-64 lg:sticky lg:top-0 lg:h-screen bg-white/70 backdrop-blur border-r border-border px-5 py-8 shadow-soft">
      <div className="mb-10">
        <p className="text-xs uppercase tracking-[0.2em] text-muted">Tendorlelo</p>
        <h1 className="text-2xl font-semibold text-text">Tender Matching</h1>
      </div>
      <nav className="flex flex-col gap-2">
        {navItems.map((item) => {
          const Icon = item.icon;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) =>
                [
                  "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition",
                  isActive
                    ? "bg-primary text-white shadow-card"
                    : "text-muted hover:text-text hover:bg-white",
                ].join(" ")
              }
            >
              <Icon size={18} />
              {item.label}
            </NavLink>
          );
        })}
      </nav>
      <div className="mt-auto text-xs text-muted">
        <p>Live system monitor</p>
        <p>v0.1</p>
      </div>
    </aside>
  );
};

export default Sidebar;
