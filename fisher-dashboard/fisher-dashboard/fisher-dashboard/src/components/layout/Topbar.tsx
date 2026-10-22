import { useEffect, useState } from "react";
import {
  fetchAlerts,
  fetchCurrentUser,
  updateProfile,
  changePassword,
  logout,
} from "../../services/dashboardApi";
import type { Alert, User } from "../../types/dashboard";

function SunIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <circle cx="12" cy="12" r="4" />
      <path d="M12 2.5v2" />
      <path d="M12 19.5v2" />
      <path d="m4.93 4.93 1.42 1.42" />
      <path d="m17.65 17.65 1.42 1.42" />
      <path d="M2.5 12h2" />
      <path d="M19.5 12h2" />
      <path d="m4.93 19.07 1.42-1.42" />
      <path d="m17.65 6.35 1.42-1.42" />
    </svg>
  );
}

function MoonIcon() {
  return (
    <svg
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M20.5 15.2A8.5 8.5 0 0 1 8.8 3.5 8.5 8.5 0 1 0 20.5 15.2Z" />
    </svg>
  );
}

function BellIcon() {
  return (
    <svg
      className="notification-bell"
      viewBox="0 0 24 24"
      aria-hidden="true"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.9"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      <path d="M18 9a6 6 0 0 0-12 0c0 7-3 7-3 9h18c0-2-3-2-3-9" />
      <path d="M10 21h4" />
    </svg>
  );
}

interface TopbarProps {
  initialUser?: User | null;
  onLogout?: () => void;
}

function Topbar({ initialUser, onLogout }: TopbarProps) {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  // Modals
  const [showProfileModal, setShowProfileModal] = useState(false);
  const [showSecurityModal, setShowSecurityModal] = useState(false);

  // User state
  const [user, setUser] = useState<User>(() => initialUser || {
    id: "USR-001",
    name: "Administrator",
    username: "admin",
    email: "admin@fisher.cctv",
    role: "admin",
    status: "active",
  });

  // Profile Form State
  const [profileName, setProfileName] = useState(user.name);
  const [profileEmail, setProfileEmail] = useState(user.email || "admin@fisher.cctv");
  const [profileSaving, setProfileSaving] = useState(false);
  const [profileMsg, setProfileMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

  // Security Form State
  const [currentPassword, setCurrentPassword] = useState("");
  const [newPassword, setNewPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [securitySaving, setSecuritySaving] = useState(false);
  const [securityMsg, setSecurityMsg] = useState<{ text: string; type: "success" | "error" } | null>(null);

  const [isLightMode, setIsLightMode] = useState(() => {
    return localStorage.getItem("fisher-theme") === "light";
  });

  const [readNotifications, setReadNotifications] = useState<string[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);

  // Load User Profile on Mount
  useEffect(() => {
    let active = true;
    fetchCurrentUser()
      .then((currUser) => {
        if (active && currUser) {
          setUser(currUser);
          setProfileName(currUser.name);
          if (currUser.email) setProfileEmail(currUser.email);
        }
      })
      .catch(() => {});
    return () => {
      active = false;
    };
  }, []);

  // Sync Alerts periodically
  useEffect(() => {
    let active = true;
    const syncAlerts = () => {
      fetchAlerts()
        .then((res) => {
          if (active && Array.isArray(res)) setAlerts(res);
        })
        .catch(() => {});
    };
    syncAlerts();
    const intervalId = setInterval(syncAlerts, 3000);
    return () => {
      active = false;
      clearInterval(intervalId);
    };
  }, []);

  const unreadAlerts = alerts.filter(
    (alert) => !readNotifications.includes(alert.id),
  );

  useEffect(() => {
    document.documentElement.classList.toggle("light-mode", isLightMode);
    localStorage.setItem("fisher-theme", isLightMode ? "light" : "dark");
  }, [isLightMode]);

  const handleToggleNotifications = () => {
    setShowNotifications((current) => !current);
    setShowProfile(false);
  };

  const handleToggleProfile = () => {
    setShowProfile((current) => !current);
    setShowNotifications(false);
  };

  const handleToggleTheme = () => {
    setIsLightMode((current) => !current);
    setShowProfile(false);
  };

  const handleMarkAsRead = (alertId: string) => {
    setReadNotifications((current) => {
      if (current.includes(alertId)) {
        return current;
      }
      return [...current, alertId];
    });
  };

  const handleMarkAllAsRead = () => {
    setReadNotifications(alerts.map((alert) => alert.id));
  };

  // Profile Settings Open
  const handleOpenProfileModal = () => {
    setShowProfile(false);
    setProfileName(user.name);
    setProfileEmail(user.email || "admin@fisher.cctv");
    setProfileMsg(null);
    setShowProfileModal(true);
  };

  // Save Profile to Backend
  const handleSaveProfile = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!profileName.trim()) {
      setProfileMsg({ text: "Name cannot be empty.", type: "error" });
      return;
    }
    setProfileSaving(true);
    setProfileMsg(null);
    try {
      const res = await updateProfile({ name: profileName.trim(), email: profileEmail.trim() });
      if (res && res.user) {
        setUser((prev) => ({ ...prev, ...res.user }));
      }
      setProfileMsg({ text: "Profile updated successfully.", type: "success" });
      setTimeout(() => setShowProfileModal(false), 1200);
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : "Failed to update profile";
      setProfileMsg({ text: errMessage, type: "error" });
    } finally {
      setProfileSaving(false);
    }
  };

  // Security Open
  const handleOpenSecurityModal = () => {
    setShowProfile(false);
    setCurrentPassword("");
    setNewPassword("");
    setConfirmPassword("");
    setSecurityMsg(null);
    setShowSecurityModal(true);
  };

  // Change Password in Backend
  const handleSavePassword = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!currentPassword) {
      setSecurityMsg({ text: "Current password is required.", type: "error" });
      return;
    }
    if (newPassword.length < 6) {
      setSecurityMsg({ text: "New password must be at least 6 characters.", type: "error" });
      return;
    }
    if (newPassword !== confirmPassword) {
      setSecurityMsg({ text: "New passwords do not match.", type: "error" });
      return;
    }

    setSecuritySaving(true);
    setSecurityMsg(null);
    try {
      const res = await changePassword({ currentPassword, newPassword });
      setSecurityMsg({ text: res.message || "Password changed successfully.", type: "success" });
      setCurrentPassword("");
      setNewPassword("");
      setConfirmPassword("");
      setTimeout(() => setShowSecurityModal(false), 1400);
    } catch (err: unknown) {
      const errMessage = err instanceof Error ? err.message : "Failed to change password";
      setSecurityMsg({ text: errMessage, type: "error" });
    } finally {
      setSecuritySaving(false);
    }
  };

  // Sign Out
  const handleSignOut = async () => {
    setShowProfile(false);
    try {
      await logout();
    } catch {}
    if (onLogout) {
      onLogout();
    }
  };

  return (
    <header className="topbar">
      <div className="topbar-title">
        <span className="breadcrumb">FISHER / OPERATIONS</span>
        <h1>Dashboard</h1>
      </div>

      <div className="topbar-actions">
        <button
          type="button"
          className="theme-toggle"
          onClick={handleToggleTheme}
          aria-label={
            isLightMode ? "Switch to dark mode" : "Switch to light mode"
          }
          title={isLightMode ? "Switch to dark mode" : "Switch to light mode"}
        >
          <span className="theme-toggle-icon">
            {isLightMode ? <MoonIcon /> : <SunIcon />}
          </span>
        </button>

        <div className="topbar-notifications">
          <button
            type="button"
            className="topbar-button notification-button"
            aria-label="Notifications"
            onClick={handleToggleNotifications}
          >
            <BellIcon />

            {unreadAlerts.length > 0 && (
              <span className="notification-count" aria-live="polite">
                {unreadAlerts.length}
              </span>
            )}
          </button>

          {showNotifications && (
            <div className="notification-panel">
              <div className="notification-header">
                <div>
                  <span className="eyebrow">FISHER ALERT CENTER</span>
                  <h3>Notifications</h3>
                </div>

                {unreadAlerts.length > 0 && (
                  <button
                    type="button"
                    className="notification-mark-all"
                    onClick={handleMarkAllAsRead}
                  >
                    Mark all read
                  </button>
                )}
              </div>

              <div className="notification-list">
                {alerts.length === 0 ? (
                  <div className="notification-empty">
                    <strong>No active notifications</strong>
                    <span>The alert center is clear.</span>
                  </div>
                ) : (
                  alerts.map((alert) => {
                    const isRead = readNotifications.includes(alert.id);

                    return (
                      <button
                        type="button"
                        className={
                          isRead
                            ? "notification-item read"
                            : "notification-item"
                        }
                        key={alert.id}
                        onClick={() => handleMarkAsRead(alert.id)}
                      >
                        <div
                          className={`notification-severity ${alert.severity}`}
                        ></div>

                        <div className="notification-content">
                          <strong>{alert.title}</strong>

                          <span>
                            {alert.cameraId ? alert.cameraId : "FISHER System"}
                          </span>

                          <small>{alert.timestamp}</small>
                        </div>

                        {!isRead && (
                          <span className="notification-unread">NEW</span>
                        )}
                      </button>
                    );
                  })
                )}
              </div>
            </div>
          )}
        </div>

        <div className="topbar-profile">
          <button
            type="button"
            className="user-profile"
            onClick={handleToggleProfile}
            aria-label="Open administrator profile"
          >
            <div className="user-avatar">{user.name.charAt(0).toUpperCase()}</div>

            <div className="user-profile-info">
              <strong>{user.name}</strong>
              <span>{user.role === "admin" ? "System Administrator" : user.role.toUpperCase()}</span>
            </div>

            <span className="profile-arrow">▾</span>
          </button>

          {showProfile && (
            <div className="profile-menu">
              <div className="profile-menu-header">
                <div className="profile-menu-avatar">{user.name.charAt(0).toUpperCase()}</div>

                <div>
                  <strong>{user.name}</strong>
                  <span>{user.role === "admin" ? "System Administrator" : user.role.toUpperCase()}</span>
                </div>
              </div>

              <div className="profile-status">
                <span className="status-dot"></span>

                <div>
                  <strong>Account Active</strong>
                  <span>Full dashboard access</span>
                </div>
              </div>

              <button
                type="button"
                className="profile-menu-item"
                onClick={handleOpenProfileModal}
              >
                <span>◉</span>
                Profile Settings
              </button>

              <button
                type="button"
                className="profile-menu-item"
                onClick={handleOpenSecurityModal}
              >
                <span>⌘</span>
                Security
              </button>

              <button
                type="button"
                className="profile-menu-item theme-menu-item"
                onClick={handleToggleTheme}
              >
                <span>{isLightMode ? "☾" : "☀"}</span>
                {isLightMode ? "Dark Mode" : "Light Mode"}
              </button>

              <div className="profile-menu-divider"></div>

              <button
                type="button"
                className="profile-menu-item danger"
                onClick={handleSignOut}
              >
                <span>↪</span>
                Sign Out
              </button>
            </div>
          )}
        </div>
      </div>

      {/* --------------------------------------------------------- */}
      {/* PROFILE SETTINGS MODAL                                    */}
      {/* --------------------------------------------------------- */}
      {showProfileModal && (
        <div className="fisher-modal-backdrop" onClick={() => setShowProfileModal(false)}>
          <div
            className="fisher-modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="fisher-modal-header">
              <div>
                <span className="eyebrow">ACCOUNT MANAGEMENT</span>
                <h3>Profile Settings</h3>
              </div>
              <button
                type="button"
                className="fisher-modal-close"
                onClick={() => setShowProfileModal(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSaveProfile} className="fisher-modal-form">
              {profileMsg && (
                <div className={`fisher-alert-msg ${profileMsg.type}`}>
                  {profileMsg.text}
                </div>
              )}

              <div className="fisher-form-group">
                <label>User ID</label>
                <input
                  type="text"
                  className="fisher-form-input"
                  value={user.id}
                  disabled
                />
              </div>

              <div className="fisher-form-row">
                <div className="fisher-form-group">
                  <label>Username</label>
                  <input
                    type="text"
                    className="fisher-form-input"
                    value={user.username || "admin"}
                    disabled
                  />
                </div>
                <div className="fisher-form-group">
                  <label>Role</label>
                  <input
                    type="text"
                    className="fisher-form-input"
                    value={user.role.toUpperCase()}
                    disabled
                  />
                </div>
              </div>

              <div className="fisher-form-group">
                <label>Full Display Name</label>
                <input
                  type="text"
                  className="fisher-form-input"
                  value={profileName}
                  onChange={(e) => setProfileName(e.target.value)}
                  placeholder="Enter full name"
                  required
                />
              </div>

              <div className="fisher-form-group">
                <label>Authorized Email Address</label>
                <input
                  type="email"
                  className="fisher-form-input"
                  value={profileEmail}
                  onChange={(e) => setProfileEmail(e.target.value)}
                  placeholder="e.g. admin@fisher.cctv"
                  required
                />
              </div>

              <div className="fisher-modal-actions">
                <button
                  type="button"
                  className="fisher-btn-secondary"
                  onClick={() => setShowProfileModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="fisher-btn-primary"
                  disabled={profileSaving}
                >
                  {profileSaving ? "Saving..." : "Save Changes"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* --------------------------------------------------------- */}
      {/* SECURITY SETTINGS MODAL                                   */}
      {/* --------------------------------------------------------- */}
      {showSecurityModal && (
        <div className="fisher-modal-backdrop" onClick={() => setShowSecurityModal(false)}>
          <div
            className="fisher-modal"
            onClick={(e) => e.stopPropagation()}
            role="dialog"
            aria-modal="true"
          >
            <div className="fisher-modal-header">
              <div>
                <span className="eyebrow">SYSTEM SECURITY</span>
                <h3>Security Settings</h3>
              </div>
              <button
                type="button"
                className="fisher-modal-close"
                onClick={() => setShowSecurityModal(false)}
                aria-label="Close"
              >
                ×
              </button>
            </div>

            <form onSubmit={handleSavePassword} className="fisher-modal-form">
              {securityMsg && (
                <div className={`fisher-alert-msg ${securityMsg.type}`}>
                  {securityMsg.text}
                </div>
              )}

              <div className="fisher-form-group">
                <label>Current Password</label>
                <input
                  type="password"
                  className="fisher-form-input"
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                  required
                />
              </div>

              <div className="fisher-form-group">
                <label>New Password</label>
                <input
                  type="password"
                  className="fisher-form-input"
                  value={newPassword}
                  onChange={(e) => setNewPassword(e.target.value)}
                  placeholder="Minimum 6 characters"
                  required
                />
              </div>

              <div className="fisher-form-group">
                <label>Confirm New Password</label>
                <input
                  type="password"
                  className="fisher-form-input"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  placeholder="Re-enter new password"
                  required
                />
              </div>

              <div className="fisher-modal-actions">
                <button
                  type="button"
                  className="fisher-btn-secondary"
                  onClick={() => setShowSecurityModal(false)}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="fisher-btn-primary"
                  disabled={securitySaving}
                >
                  {securitySaving ? "Updating..." : "Update Password"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </header>
  );
}

export default Topbar;
