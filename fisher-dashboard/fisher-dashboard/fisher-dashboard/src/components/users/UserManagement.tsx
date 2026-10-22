import { useEffect, useState } from "react";
import {
  fetchUsers,
  createRemoteUser,
  updateRemoteUser,
} from "../../services/dashboardApi";
import { getUsers, updateUser, createUser } from "../../services/dashboardService";
import type { User } from "../../types/dashboard";

type UserRole = "admin" | "operator" | "viewer";
type UserStatus = "active" | "inactive";

const AUTHORIZED_EMAILS = [
  "admin@fisher.cctv",
  "operator@fisher.cctv",
  "supervisor@fisher.cctv",
];

function UserManagement() {
  const [showForm, setShowForm] = useState(false);
  const [userList, setUserList] = useState<User[]>(() => getUsers());
  const [isLoading, setIsLoading] = useState(false);

  // Form states
  const [userName, setUserName] = useState("");
  const [userEmail, setUserEmail] = useState(AUTHORIZED_EMAILS[0]);
  const [username, setUsername] = useState("");
  const [userPassword, setUserPassword] = useState("");
  const [userRole, setUserRole] = useState<UserRole>("operator");

  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);

  // Management / Edit states
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [editRole, setEditRole] = useState<UserRole>("operator");
  const [editStatus, setEditStatus] = useState<UserStatus>("active");
  const [saveMessage, setSaveMessage] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  const loadUsers = async () => {
    setIsLoading(true);
    try {
      const data = await fetchUsers();
      if (Array.isArray(data) && data.length > 0) {
        setUserList(data);
      } else {
        setUserList(getUsers());
      }
    } catch {
      setUserList(getUsers());
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadUsers();
  }, []);

  const selectedUser = userList.find((user) => user.id === selectedUserId);

  const handleToggleForm = () => {
    setShowForm((current) => !current);
    setFormError("");
    setFormSuccess("");
  };

  const handleAddUser = async (e: React.FormEvent) => {
    e.preventDefault();
    const trimmedName = userName.trim();
    const cleanEmail = userEmail.trim().toLowerCase();

    if (!trimmedName) {
      setFormError("Please enter a user full name.");
      setFormSuccess("");
      return;
    }

    if (!cleanEmail) {
      setFormError("Please provide an authorized email address.");
      setFormSuccess("");
      return;
    }

    if (!AUTHORIZED_EMAILS.includes(cleanEmail)) {
      setFormError(
        `Registration rejected: '${cleanEmail}' is not authorized. Permitted: ${AUTHORIZED_EMAILS.join(", ")}`,
      );
      setFormSuccess("");
      return;
    }

    setIsSubmitting(true);
    setFormError("");
    setFormSuccess("");

    try {
      const newUser = await createRemoteUser({
        name: trimmedName,
        email: cleanEmail,
        username: username.trim() || undefined,
        password: userPassword || undefined,
        role: userRole,
      });

      setFormSuccess(`User ${newUser.name} (${cleanEmail}) registered successfully.`);
      setUserName("");
      setUsername("");
      setUserPassword("");
      await loadUsers();
    } catch (err: unknown) {
      const message =
        err instanceof Error ? err.message : "Failed to register user in MongoDB.";
      setFormError(message);

      // Fallback local creation if running standalone offline
      if (message.includes("Failed to fetch") || message.includes("Network")) {
        const fallback = createUser(trimmedName, userRole);
        if (fallback) {
          setUserList([...getUsers()]);
          setFormSuccess(`User ${fallback.name} created locally.`);
        }
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleManageUser = (userId: string) => {
    const user = userList.find((item) => item.id === userId);
    if (!user) return;

    setSelectedUserId(userId);
    setEditRole(user.role);
    setEditStatus(user.status);
    setSaveMessage("");
  };

  const handleCloseUser = () => {
    setSelectedUserId(null);
    setSaveMessage("");
  };

  const handleSaveUser = async () => {
    if (!selectedUserId) return;

    setIsSaving(true);
    setSaveMessage("");

    try {
      await updateRemoteUser(selectedUserId, {
        role: editRole,
        status: editStatus,
      });
      setSaveMessage("User access permissions updated in database.");
      await loadUsers();
    } catch {
      // Fallback local update
      const updated = updateUser(selectedUserId, editRole, editStatus);
      if (updated) {
        setUserList([...getUsers()]);
        setSaveMessage("User changes saved locally.");
      }
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <div>
          <span className="eyebrow">SYSTEM ACCESS CONTROL</span>
          <h3>User Management</h3>
          <p>
            Manage authorized FISHER CCTV accounts. System access is strictly restricted to exactly 3 authorized email accounts.
          </p>
        </div>

        <button
          type="button"
          className="user-action"
          onClick={handleToggleForm}
        >
          {showForm ? "Close Form" : "Add Authorized User"}
        </button>
      </div>

      {showForm && (
        <form
          className="user-form"
          onSubmit={handleAddUser}
          style={{ gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr)) auto" }}
        >
          <div className="user-form-field">
            <label htmlFor="user-name">Full Name</label>
            <input
              id="user-name"
              type="text"
              value={userName}
              placeholder="e.g. Security Supervisor"
              onChange={(e) => setUserName(e.target.value)}
              required
            />
          </div>

          <div className="user-form-field">
            <label htmlFor="user-email">Authorized Email</label>
            <select
              id="user-email"
              value={userEmail}
              onChange={(e) => setUserEmail(e.target.value)}
            >
              {AUTHORIZED_EMAILS.map((email) => (
                <option key={email} value={email}>
                  {email}
                </option>
              ))}
            </select>
          </div>

          <div className="user-form-field">
            <label htmlFor="user-uname">Username</label>
            <input
              id="user-uname"
              type="text"
              value={username}
              placeholder="e.g. supervisor"
              onChange={(e) => setUsername(e.target.value)}
            />
          </div>

          <div className="user-form-field">
            <label htmlFor="user-pwd">Password</label>
            <input
              id="user-pwd"
              type="password"
              value={userPassword}
              placeholder="••••••••"
              onChange={(e) => setUserPassword(e.target.value)}
            />
          </div>

          <div className="user-form-field">
            <label htmlFor="user-role">Role</label>
            <select
              id="user-role"
              value={userRole}
              onChange={(e) => setUserRole(e.target.value as UserRole)}
            >
              <option value="admin">Admin</option>
              <option value="operator">Operator</option>
              <option value="viewer">Viewer</option>
            </select>
          </div>

          <button
            type="submit"
            className="user-save"
            disabled={isSubmitting}
            style={{ minHeight: "34px", alignSelf: "end" }}
          >
            {isSubmitting ? "Registering..." : "Create Account"}
          </button>

          {(formError || formSuccess) && (
            <div style={{ gridColumn: "1 / -1", marginTop: "8px" }}>
              {formError && (
                <p style={{ color: "#f87171", fontSize: "11px", margin: 0 }}>
                  {formError}
                </p>
              )}
              {formSuccess && (
                <p style={{ color: "#4ade80", fontSize: "11px", margin: 0 }}>
                  {formSuccess}
                </p>
              )}
            </div>
          )}
        </form>
      )}

      <div className="users-list">
        {isLoading && userList.length === 0 ? (
          <div style={{ padding: "24px", color: "#64748b", textAlign: "center" }}>
            Loading authorized accounts from MongoDB...
          </div>
        ) : userList.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">A</div>
            <h4>No users available</h4>
            <p>Create one of the 3 authorized FISHER CCTV dashboard accounts.</p>
          </div>
        ) : (
          userList.map((user) => (
            <div className="user-item" key={user.id}>
              <div className="user-management-avatar">
                {user.name.charAt(0).toUpperCase()}
              </div>

              <div className="user-info">
                <strong>{user.name}</strong>
                <span>
                  {user.id} {user.email ? `• ${user.email}` : ""} {user.username ? `(@${user.username})` : ""}
                </span>
              </div>

              <div className="user-role">
                <span>ROLE</span>
                <strong>{user.role}</strong>
              </div>

              <div
                className={
                  user.status === "active"
                    ? "user-status active"
                    : "user-status inactive"
                }
              >
                <span className="status-dot"></span>
                {user.status}
              </div>

              <button
                type="button"
                className="user-view"
                onClick={() => handleManageUser(user.id)}
              >
                Manage
              </button>
            </div>
          ))
        )}
      </div>

      {selectedUser && (
        <div className="user-details" style={{ marginTop: "18px" }}>
          <div className="user-details-header">
            <div>
              <span className="eyebrow">SELECTED USER DETAILS</span>
              <h4>{selectedUser.name}</h4>
              {selectedUser.email && (
                <span style={{ fontSize: "11px", color: "#64748b" }}>
                  Authorized Email: {selectedUser.email}
                </span>
              )}
            </div>

            <button
              type="button"
              className="user-close"
              onClick={handleCloseUser}
              aria-label="Close user details"
            >
              ×
            </button>
          </div>

          <div className="user-details-grid">
            <div>
              <span>User ID</span>
              <strong>{selectedUser.id}</strong>
            </div>

            <div>
              <span>Account Name</span>
              <strong>{selectedUser.name}</strong>
            </div>

            <div>
              <span>Role Authorization</span>
              <select
                className="user-edit-select"
                value={editRole}
                onChange={(e) => setEditRole(e.target.value as UserRole)}
              >
                <option value="admin">Admin</option>
                <option value="operator">Operator</option>
                <option value="viewer">Viewer</option>
              </select>
            </div>

            <div>
              <span>Account Status</span>
              <select
                className="user-edit-select"
                value={editStatus}
                onChange={(e) => setEditStatus(e.target.value as UserStatus)}
              >
                <option value="active">Active</option>
                <option value="inactive">Inactive</option>
              </select>
            </div>
          </div>

          <div className="user-management-actions">
            <button
              type="button"
              className="user-save-changes"
              onClick={handleSaveUser}
              disabled={isSaving}
            >
              {isSaving ? "Saving..." : "Save Changes"}
            </button>

            <button
              type="button"
              className="user-cancel-changes"
              onClick={handleCloseUser}
            >
              Close
            </button>

            {saveMessage && (
              <span className="user-save-message" style={{ color: "#4ade80" }}>
                {saveMessage}
              </span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
