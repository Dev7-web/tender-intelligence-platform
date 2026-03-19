import { useEffect, useState } from "react";
import { Eye, EyeOff } from "lucide-react";
import { useNavigate } from "react-router-dom";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { clearAuth, getUser, setUser } from "@/lib/auth";
import { signOutUser } from "@/lib/firebaseAuth";
import { useToastSimple } from "@/components/ui/toaster-simple";
import {
  changePassword,
  deleteAccount,
  fetchMe,
  updateNotifications,
  updateProfile,
} from "@/services/tenderAgentApi";

const inputClass =
  "h-11 w-full rounded-lg border border-[#d6dbe8] bg-[#f5f6fa] px-4 text-sm text-[#2c3243] placeholder:text-[#a3aabe] focus:border-[#4040E0] focus:outline-none";

const labelClass = "mb-1 block text-xs font-medium text-[#4a5068]";

const ProfilePage = () => {
  const navigate = useNavigate();
  const { pushToast } = useToastSimple();
  const queryClient = useQueryClient();

  // --- Profile state ---
  const [name, setName] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [profession, setProfession] = useState("");
  const [location, setLocation] = useState("");
  const [aboutMe, setAboutMe] = useState("");

  // --- Password state ---
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [showCurrentPassword, setShowCurrentPassword] = useState(false);
  const [showNewPassword, setShowNewPassword] = useState(false);

  // --- Notification state ---
  const [tenderUpdates, setTenderUpdates] = useState(true);
  const [matchingTenders, setMatchingTenders] = useState(false);
  const [expiringTenders, setExpiringTenders] = useState(false);

  // --- Delete confirmation ---
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  // Fetch user from API
  const { data: userData } = useQuery({
    queryKey: ["currentUser"],
    queryFn: fetchMe,
  });

  // Populate form when user data loads
  useEffect(() => {
    const user = userData || getUser();
    if (!user) return;
    setName(user.name || "");
    setUsername(user.username || "");
    setEmail(user.email || "");
    setPhone(user.phone || "");
    setProfession(user.profession || "");
    setLocation(user.location || "");
    setAboutMe(user.about_me || "");
    setTenderUpdates(user.notification_preferences?.tender_updates ?? true);
    setMatchingTenders(user.notification_preferences?.matching_tenders ?? false);
    setExpiringTenders(user.notification_preferences?.expiring_tenders ?? false);
  }, [userData]);

  // --- Mutations ---
  const profileMutation = useMutation({
    mutationFn: () =>
      updateProfile({
        name: name.trim() || undefined,
        username: username.trim() || undefined,
        phone: phone.trim() || undefined,
        profession: profession.trim() || undefined,
        location: location.trim() || undefined,
        about_me: aboutMe.trim() || undefined,
      }),
    onSuccess: (updatedUser) => {
      setUser(updatedUser);
      queryClient.invalidateQueries({ queryKey: ["currentUser"] });
      pushToast("Profile updated successfully", "success");
    },
    onError: (err: any) => {
      pushToast(err?.response?.data?.detail || "Failed to update profile", "error");
    },
  });

  const passwordMutation = useMutation({
    mutationFn: () =>
      changePassword({
        current_password: currentPassword,
        new_password: newPassword,
      }),
    onSuccess: () => {
      setCurrentPassword("");
      setNewPassword("");
      pushToast("Password changed successfully", "success");
    },
    onError: (err: any) => {
      pushToast(err?.response?.data?.detail || "Failed to change password", "error");
    },
  });

  const notificationMutation = useMutation({
    mutationFn: (prefs: {
      tender_updates?: boolean;
      matching_tenders?: boolean;
      expiring_tenders?: boolean;
    }) => updateNotifications(prefs),
    onSuccess: () => {
      pushToast("Notification preferences saved", "success");
    },
    onError: () => {
      pushToast("Failed to save notification preferences", "error");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: deleteAccount,
    onSuccess: async () => {
      try {
        await signOutUser();
      } finally {
        clearAuth("manual");
        navigate("/auth");
      }
    },
    onError: (err: any) => {
      pushToast(err?.response?.data?.detail || "Failed to delete account", "error");
    },
  });

  const handleSaveProfile = () => {
    profileMutation.mutate();
  };

  const handleChangePassword = () => {
    if (!currentPassword) {
      pushToast("Please enter your current password", "error");
      return;
    }
    if (newPassword.length < 8) {
      pushToast("New password must be at least 8 characters", "error");
      return;
    }
    passwordMutation.mutate();
  };

  const handleSaveNotifications = () => {
    notificationMutation.mutate({
      tender_updates: tenderUpdates,
      matching_tenders: matchingTenders,
      expiring_tenders: expiringTenders,
    });
  };

  const handleDeleteAccount = () => {
    deleteMutation.mutate();
  };

  return (
    <div>
      <h1 className="mb-6 text-2xl font-semibold text-[#1f2533]">Profile</h1>

      {/* ── Profile Section ── */}
      <section className="mb-6 rounded-2xl border border-[#e3e6ef] bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-5 text-xl font-semibold text-[#1f2533]">Profile</h2>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Full name</label>
            <input
              className={inputClass}
              placeholder="Enter full name"
              value={name}
              onChange={(e) => setName(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>Username</label>
            <input
              className={inputClass}
              placeholder="Enter username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>Email</label>
            <input
              className={inputClass}
              placeholder="Enter email"
              value={email}
              disabled
              title="Email cannot be changed"
            />
          </div>
          <div>
            <label className={labelClass}>Phone number</label>
            <div className="flex">
              <span className="flex h-11 items-center rounded-l-lg border border-r-0 border-[#d6dbe8] bg-[#eef0f5] px-3 text-sm font-medium text-[#4a5068]">
                +91
              </span>
              <input
                className="h-11 w-full rounded-r-lg border border-[#d6dbe8] bg-[#f5f6fa] px-4 text-sm text-[#2c3243] placeholder:text-[#a3aabe] focus:border-[#4040E0] focus:outline-none"
                placeholder="Enter phone number"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
              />
            </div>
          </div>
          <div>
            <label className={labelClass}>Profession</label>
            <input
              className={inputClass}
              placeholder="Enter profession"
              value={profession}
              onChange={(e) => setProfession(e.target.value)}
            />
          </div>
          <div>
            <label className={labelClass}>Location</label>
            <input
              className={inputClass}
              placeholder="Enter location"
              value={location}
              onChange={(e) => setLocation(e.target.value)}
            />
          </div>
        </div>

        <div className="mt-4">
          <label className={labelClass}>About me</label>
          <textarea
            className="w-full rounded-lg border border-[#d6dbe8] bg-[#f5f6fa] px-4 py-3 text-sm text-[#2c3243] placeholder:text-[#a3aabe] focus:border-[#4040E0] focus:outline-none"
            rows={3}
            placeholder="Enter a short intro"
            value={aboutMe}
            onChange={(e) => setAboutMe(e.target.value)}
          />
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={handleSaveProfile}
            disabled={profileMutation.isPending}
            className="rounded-lg bg-[#4040E0] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#3535c5] disabled:opacity-60"
          >
            {profileMutation.isPending ? "Saving..." : "Save information"}
          </button>
        </div>
      </section>

      {/* ── Change Password Section ── */}
      <section className="mb-6 rounded-2xl border border-[#e3e6ef] bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-2 text-xl font-semibold text-[#1f2533]">Change Password</h2>
        <p className="mb-5 text-sm text-[#6b7280]">
          To update your password, please enter your current password for verification. This ensures
          the security of your account. Without it, you cannot proceed with the change.
        </p>

        <div className="grid gap-4 sm:grid-cols-2">
          <div>
            <label className={labelClass}>Current password</label>
            <div className="relative">
              <input
                type={showCurrentPassword ? "text" : "password"}
                className={inputClass}
                placeholder="Enter current password"
                value={currentPassword}
                onChange={(e) => setCurrentPassword(e.target.value)}
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8a93a8]"
                onClick={() => setShowCurrentPassword((v) => !v)}
              >
                {showCurrentPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
          <div>
            <label className={labelClass}>New Password</label>
            <div className="relative">
              <input
                type={showNewPassword ? "text" : "password"}
                className={inputClass}
                placeholder="Enter new password"
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
              />
              <button
                type="button"
                className="absolute right-3 top-1/2 -translate-y-1/2 text-[#8a93a8]"
                onClick={() => setShowNewPassword((v) => !v)}
              >
                {showNewPassword ? <EyeOff size={18} /> : <Eye size={18} />}
              </button>
            </div>
          </div>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={handleChangePassword}
            disabled={passwordMutation.isPending}
            className="rounded-lg bg-[#4040E0] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#3535c5] disabled:opacity-60"
          >
            {passwordMutation.isPending ? "Updating..." : "Update Password"}
          </button>
        </div>
      </section>

      {/* ── Notifications Section ── */}
      <section className="mb-6 rounded-2xl border border-[#e3e6ef] bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-5 text-xl font-semibold text-[#1f2533]">Notifications</h2>

        <div className="space-y-4">
          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={tenderUpdates}
              onChange={(e) => setTenderUpdates(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-[#d6dbe8] accent-[#4040E0]"
            />
            <div>
              <p className="text-sm font-medium text-[#2c3243]">Receive Tender updates via email</p>
              <p className="text-xs text-[#8a93a8]">Get notified about new updates</p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={matchingTenders}
              onChange={(e) => setMatchingTenders(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-[#d6dbe8] accent-[#4040E0]"
            />
            <div>
              <p className="text-sm font-medium text-[#2c3243]">Receive alerts on matching tenders via email</p>
              <p className="text-xs text-[#8a93a8]">Get notified on matching tenders on email</p>
            </div>
          </label>

          <label className="flex items-start gap-3 cursor-pointer">
            <input
              type="checkbox"
              checked={expiringTenders}
              onChange={(e) => setExpiringTenders(e.target.checked)}
              className="mt-0.5 h-4 w-4 rounded border-[#d6dbe8] accent-[#4040E0]"
            />
            <div>
              <p className="text-sm font-medium text-[#2c3243]">Receive alerts on expiring tenders</p>
              <p className="text-xs text-[#8a93a8]">Get notified on tender application deadlines</p>
            </div>
          </label>
        </div>

        <div className="mt-5 flex justify-end">
          <button
            onClick={handleSaveNotifications}
            disabled={notificationMutation.isPending}
            className="rounded-lg bg-[#4040E0] px-6 py-2.5 text-sm font-medium text-white hover:bg-[#3535c5] disabled:opacity-60"
          >
            {notificationMutation.isPending ? "Saving..." : "Save information"}
          </button>
        </div>
      </section>

      {/* ── Account Controls Section ── */}
      <section className="mb-6 rounded-2xl border border-[#e3e6ef] bg-white p-6 shadow-sm md:p-8">
        <h2 className="mb-4 text-xl font-semibold text-[#1f2533]">Account Controls</h2>

        <div className="rounded-xl border border-[#fecaca] bg-[#fef2f2] p-5">
          <p className="text-sm font-semibold text-[#1f2533]">Delete your account</p>
          <p className="mt-1 text-sm text-[#6b7280]">
            Deleting your account will sign you out, halt all notifications, and deactivate your
            profile. Please be aware that all of your data will be permanently erased.
          </p>

          {!showDeleteConfirm ? (
            <div className="mt-4 flex justify-end">
              <button
                onClick={() => setShowDeleteConfirm(true)}
                className="rounded-lg border border-[#ef8f93] px-5 py-2 text-sm font-medium text-[#dd5056] hover:bg-[#fddcdb]"
              >
                Delete account
              </button>
            </div>
          ) : (
            <div className="mt-4 flex items-center justify-end gap-3">
              <p className="text-sm font-medium text-[#b91c1c]">Are you sure? This cannot be undone.</p>
              <button
                onClick={() => setShowDeleteConfirm(false)}
                className="rounded-lg border border-[#d6dbe8] px-4 py-2 text-sm font-medium text-[#4a5068] hover:bg-[#f5f6fa]"
              >
                Cancel
              </button>
              <button
                onClick={handleDeleteAccount}
                disabled={deleteMutation.isPending}
                className="rounded-lg bg-[#dd5056] px-5 py-2 text-sm font-medium text-white hover:bg-[#c43e44] disabled:opacity-60"
              >
                {deleteMutation.isPending ? "Deleting..." : "Yes, delete"}
              </button>
            </div>
          )}
        </div>
      </section>
    </div>
  );
};

export default ProfilePage;
