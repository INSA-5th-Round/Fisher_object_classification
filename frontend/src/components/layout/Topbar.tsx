import { useEffect, useState } from "react";

import { getAlerts } from "../../services/dashboardService";

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

function Topbar() {
  const [showNotifications, setShowNotifications] = useState(false);
  const [showProfile, setShowProfile] = useState(false);

  const [isLightMode, setIsLightMode] = useState(() => {
    return localStorage.getItem("fisher-theme") === "light";
  });

  const [readNotifications, setReadNotifications] = useState<string[]>([]);

  const alerts = getAlerts();

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

  const handleSignOut = () => {
    alert(
      "Sign out will be connected to the authentication system when the FISHER backend is available.",
    );
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
            <div className="user-avatar">A</div>

            <div className="user-profile-info">
              <strong>Administrator</strong>
              <span>System Operator</span>
            </div>

            <span className="profile-arrow">▾</span>
          </button>

          {showProfile && (
            <div className="profile-menu">
              <div className="profile-menu-header">
                <div className="profile-menu-avatar">A</div>

                <div>
                  <strong>Administrator</strong>
                  <span>System Operator</span>
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
                onClick={() =>
                  alert(
                    "Administrator profile settings will be connected to the backend authentication system.",
                  )
                }
              >
                <span>◉</span>
                Profile Settings
              </button>

              <button
                type="button"
                className="profile-menu-item"
                onClick={() =>
                  alert(
                    "Security settings will be connected to the FISHER authentication system.",
                  )
                }
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
    </header>
  );
}

export default Topbar;
