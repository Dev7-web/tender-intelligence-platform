import { useEffect, useRef, useState } from "react";
import { Eye, UserX, Trash2, Search, MoreVertical, X } from "lucide-react";

import {
  fetchUsers,
  fetchUser,
  toggleUserStatus,
  deleteUser,
  AdminUser,
} from "@/services/adminApi";

const PAGE_SIZE = 10;

const StatusBadge = ({ active }: { active: boolean }) => (
  <span
    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
      active ? "bg-[#ECFDF5] text-[#059669]" : "bg-[#FEF2F2] text-[#EF4444]"
    }`}
  >
    {active ? "Active" : "Inactive"}
  </span>
);

const RoleBadge = ({ role }: { role: string }) => (
  <span
    className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
      role === "Admin" ? "bg-[#EEF2FF] text-[#4040E0]" : "bg-[#F3F4F6] text-[#6B7280]"
    }`}
  >
    {role}
  </span>
);

type DropdownProps = {
  userId: string;
  isActive: boolean;
  onView: () => void;
  onToggle: () => void;
  onDelete: () => void;
};

const RowDropdown = ({ isActive, onView, onToggle, onDelete }: DropdownProps) => {
  const [open, setOpen] = useState(false);
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener("mousedown", handler);
    return () => document.removeEventListener("mousedown", handler);
  }, []);

  return (
    <div ref={ref} className="relative">
      <button
        onClick={() => setOpen((v) => !v)}
        className="w-8 h-8 rounded-md flex items-center justify-center text-[#9CA3AF] hover:bg-[#F3F4F6]"
      >
        <MoreVertical className="w-4 h-4" />
      </button>

      {open && (
        <div className="absolute right-0 top-9 z-20 w-44 bg-white border border-[#E5E7EB] rounded-lg shadow-lg py-1">
          <button
            onClick={() => { setOpen(false); onView(); }}
            className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-[#374151] hover:bg-[#F9FAFB]"
          >
            View Details
            <Eye className="w-4 h-4 text-[#6B7280]" />
          </button>
          <button
            onClick={() => { setOpen(false); onToggle(); }}
            className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-[#374151] hover:bg-[#F9FAFB]"
          >
            {isActive ? "Inactivate" : "Activate"}
            <UserX className="w-4 h-4 text-[#6B7280]" />
          </button>
          <button
            onClick={() => { setOpen(false); onDelete(); }}
            className="w-full flex items-center justify-between px-4 py-2.5 text-sm text-[#374151] hover:bg-[#F9FAFB]"
          >
            Delete
            <Trash2 className="w-4 h-4 text-[#EF4444]" />
          </button>
        </div>
      )}
    </div>
  );
};

type DetailField = { label: string; value: string | number };

const UserDetailModal = ({ user, onClose }: { user: AdminUser; onClose: () => void }) => {
  const fields: DetailField[] = [
    { label: "Full Name", value: user.name || "—" },
    { label: "User Name", value: user.name?.split(" ")[0] || "—" },
    { label: "Email", value: user.email },
    { label: "Phone Number", value: "—" },
    { label: "Role", value: "User" },
    { label: "Status", value: user.is_active === false ? "Inactive" : "Active" },
    { label: "Tenders Won", value: user.tender_stats?.won ?? 0 },
    { label: "Tenders Saved", value: user.tender_stats?.saved ?? 0 },
    { label: "Tenders Applied", value: user.tender_stats?.applied ?? 0 },
    { label: "Tenders Discarded", value: user.tender_stats?.discarded ?? 0 },
  ];

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
      <div className="bg-white rounded-2xl w-full max-w-lg mx-4 shadow-xl">
        {/* Modal header */}
        <div className="flex items-center justify-between px-6 pt-5 pb-5">
          <h2 className="text-xl font-bold text-[#252a39]">User Details</h2>
          <button
            onClick={onClose}
            className="w-8 h-8 rounded-full flex items-center justify-center text-[#9CA3AF] hover:bg-[#F3F4F6]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Fields — each value inside an input box */}
        <div className="px-6 pb-6 grid grid-cols-2 gap-x-5 gap-y-4">
          {fields.map(({ label, value }) => (
            <div key={label}>
              <p className="text-xs font-medium text-[#6B7280] mb-1.5">{label}</p>
              <div className="h-10 w-full rounded-lg border border-[#E5E7EB] bg-[#F9FAFB] px-3 flex items-center text-sm text-[#252a39]">
                {value}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

const ManageUsers = () => {
  const [users, setUsers] = useState<AdminUser[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");
  const [loading, setLoading] = useState(true);
  const [selectedUser, setSelectedUser] = useState<AdminUser | null>(null);
  const [loadingDetail, setLoadingDetail] = useState(false);

  const totalPages = Math.max(1, Math.ceil(total / PAGE_SIZE));

  const load = (p: number, q: string) => {
    setLoading(true);
    fetchUsers((p - 1) * PAGE_SIZE, PAGE_SIZE, q)
      .then((res) => {
        setUsers(res.users);
        setTotal(res.total);
      })
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    load(page, search);
  }, [page, search]);

  const handleSearch = () => {
    setPage(1);
    setSearch(searchInput);
  };

  const handleView = async (userId: string) => {
    setLoadingDetail(true);
    try {
      const user = await fetchUser(userId);
      setSelectedUser(user);
    } finally {
      setLoadingDetail(false);
    }
  };

  const handleToggle = async (userId: string) => {
    await toggleUserStatus(userId);
    load(page, search);
  };

  const handleDelete = async (userId: string) => {
    if (!window.confirm("Are you sure you want to delete this user?")) return;
    await deleteUser(userId);
    load(page, search);
  };

  return (
    <div className="space-y-5">
      {/* Page header */}
      <div>
        <h1 className="text-2xl font-bold text-[#252a39]">Manage Users</h1>
        <p className="text-sm text-[#68708a] mt-0.5">Monitor and manage user accounts</p>
      </div>

      {/* Toolbar */}
      <div className="flex flex-wrap items-center gap-3">
        <span className="inline-flex items-center px-3 py-1.5 rounded-full bg-[#EEF2FF] text-[#4040E0] text-sm font-medium">
          {total.toLocaleString()} Users
        </span>

        <div className="flex-1 max-w-sm relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-[#9CA3AF]" />
          <input
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
            placeholder="Search by name or email..."
            className="w-full h-9 pl-9 pr-3 rounded-lg border border-[#E5E7EB] bg-white text-sm outline-none focus:border-[#4040E0]"
          />
        </div>

        <button
          onClick={handleSearch}
          className="h-9 px-4 rounded-lg border border-[#E5E7EB] bg-white text-sm text-[#374151] hover:bg-[#F9FAFB] font-medium"
        >
          Search
        </button>
      </div>

      {/* Table */}
      <div className="bg-white rounded-xl shadow-sm">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-[#E5E7EB]">
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide">Name</th>
              <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide">Username</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide">Email</th>
              <th className="px-4 py-3 text-left text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide">Status</th>
              <th className="hidden sm:table-cell px-4 py-3 text-left text-xs font-semibold text-[#9CA3AF] uppercase tracking-wide">Account Type</th>
              <th className="px-4 py-3"></th>
            </tr>
          </thead>
          <tbody>
            {loading ? (
              Array.from({ length: 6 }).map((_, i) => (
                <tr key={i} className={i % 2 === 0 ? "bg-white" : "bg-[#FAFAFA]"}>
                  <td className="px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                  <td className="hidden sm:table-cell px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                  <td className="hidden sm:table-cell px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                  <td className="px-4 py-3"><div className="h-4 bg-[#F3F4F6] rounded animate-pulse" /></td>
                </tr>
              ))
            ) : users.length === 0 ? (
              <tr>
                <td colSpan={6} className="px-4 py-10 text-center text-sm text-[#9CA3AF]">
                  No users found.
                </td>
              </tr>
            ) : (
              users.map((user, i) => {
                const isActive = user.is_active !== false;
                const username = user.name?.split(" ")[0] ?? user.email.split("@")[0];
                return (
                  <tr
                    key={user.id}
                    className={`border-b border-[#F3F4F6] ${i % 2 === 0 ? "bg-white" : "bg-[#FAFAFA]"}`}
                  >
                    <td className="px-4 py-3 font-medium text-[#252a39]">
                      {user.name || "—"}
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3 text-[#6B7280]">{username}</td>
                    <td className="px-4 py-3 text-[#6B7280] max-w-[140px] truncate sm:max-w-none">{user.email}</td>
                    <td className="px-4 py-3">
                      <StatusBadge active={isActive} />
                    </td>
                    <td className="hidden sm:table-cell px-4 py-3">
                      <RoleBadge role="User" />
                    </td>
                    <td className="px-4 py-3">
                      <RowDropdown
                        userId={user.id}
                        isActive={isActive}
                        onView={() => handleView(user.id)}
                        onToggle={() => handleToggle(user.id)}
                        onDelete={() => handleDelete(user.id)}
                      />
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>

        {/* Pagination */}
        <div className="flex items-center justify-between px-4 py-3 border-t border-[#E5E7EB]">
          <p className="text-sm text-[#6B7280]">
            Page {page} of {totalPages}
          </p>
          <div className="flex gap-2">
            <button
              disabled={page <= 1}
              onClick={() => setPage((p) => p - 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-[#E5E7EB] text-[#374151] disabled:opacity-40 hover:bg-[#F9FAFB] disabled:cursor-not-allowed"
            >
              Previous
            </button>
            <button
              disabled={page >= totalPages}
              onClick={() => setPage((p) => p + 1)}
              className="px-3 py-1.5 text-sm rounded-md border border-[#E5E7EB] text-[#374151] disabled:opacity-40 hover:bg-[#F9FAFB] disabled:cursor-not-allowed"
            >
              Next
            </button>
          </div>
        </div>
      </div>

      {/* Loading detail overlay */}
      {loadingDetail && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30">
          <div className="bg-white rounded-xl px-8 py-5 text-sm text-[#68708a]">Loading user...</div>
        </div>
      )}

      {/* User detail modal */}
      {selectedUser && (
        <UserDetailModal user={selectedUser} onClose={() => setSelectedUser(null)} />
      )}
    </div>
  );
};

export default ManageUsers;
