import { useState } from "react";
import {
  createUser,
  getUsers,
  updateUser,
} from "../../services/dashboardService";

type UserRole = "admin" | "operator" | "viewer";
type UserStatus = "active" | "inactive";

function UserManagement() {
  const [showForm, setShowForm] = useState(false);

  const [userName, setUserName] = useState("");
  const [userRole, setUserRole] = useState<UserRole>("operator");

  const [formError, setFormError] = useState("");
  const [formSuccess, setFormSuccess] = useState("");

  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);

  const [editRole, setEditRole] = useState<UserRole>("operator");

  const [editStatus, setEditStatus] = useState<UserStatus>("active");

  const [saveMessage, setSaveMessage] = useState("");

  const [userList, setUserList] = useState(() => getUsers());

  const selectedUser = userList.find((user) => user.id === selectedUserId);

  const handleAddUser = () => {
    const trimmedName = userName.trim();

    if (!trimmedName) {
      setFormError("Please enter a user name.");
      setFormSuccess("");
      return;
    }

    const newUser = createUser(trimmedName, userRole);

    if (!newUser) {
      setFormError("Unable to create the user.");
      setFormSuccess("");
      return;
    }

    setUserList([...getUsers()]);
    setUserName("");
    setUserRole("operator");
    setFormError("");
    setFormSuccess(`${newUser.name} was created successfully.`);
  };

  const handleToggleForm = () => {
    setShowForm((current) => !current);
    setFormError("");
    setFormSuccess("");
  };

  const handleManageUser = (userId: string) => {
    const user = userList.find((item) => item.id === userId);

    if (!user) {
      return;
    }

    setSelectedUserId(userId);
    setEditRole(user.role);
    setEditStatus(user.status);
    setSaveMessage("");
  };

  const handleCloseUser = () => {
    setSelectedUserId(null);
    setSaveMessage("");
  };

  const handleSaveUser = () => {
    if (!selectedUserId) {
      return;
    }

    const updated = updateUser(selectedUserId, editRole, editStatus);

    if (!updated) {
      return;
    }

    setUserList([...getUsers()]);
    setSaveMessage("User changes saved successfully.");
  };

  return (
    <div className="user-management">
      <div className="user-management-header">
        <div>
          <span className="eyebrow">SYSTEM ACCESS</span>

          <h3>User Management</h3>

          <p>Manage FISHER users, roles, and account access.</p>
        </div>

        <button
          type="button"
          className="user-action"
          onClick={handleToggleForm}
        >
          {showForm ? "Close" : "Add User"}
        </button>
      </div>

      {showForm && (
        <div className="user-form">
          <div className="user-form-field">
            <label htmlFor="user-name">User Name</label>

            <input
              id="user-name"
              type="text"
              value={userName}
              placeholder="Enter user name"
              onChange={(event) => setUserName(event.target.value)}
            />
          </div>

          <div className="user-form-field">
            <label htmlFor="user-role">Role</label>

            <select
              id="user-role"
              value={userRole}
              onChange={(event) => setUserRole(event.target.value as UserRole)}
            >
              <option value="admin">Admin</option>

              <option value="operator">Operator</option>

              <option value="viewer">Viewer</option>
            </select>
          </div>

          <button type="button" className="user-save" onClick={handleAddUser}>
            Create User
          </button>

          {formError && <p className="user-form-error">{formError}</p>}

          {formSuccess && <p className="user-form-success">{formSuccess}</p>}
        </div>
      )}

      <div className="users-list">
        {userList.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">A</div>

            <h4>No users available</h4>

            <p>Create the first FISHER dashboard user.</p>
          </div>
        ) : (
          userList.map((user) => (
            <div className="user-item" key={user.id}>
              <div className="user-management-avatar">
                {user.name.charAt(0).toUpperCase()}
              </div>

              <div className="user-info">
                <strong>{user.name}</strong>

                <span>{user.id}</span>
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
        <div className="user-details">
          <div className="user-details-header">
            <div>
              <span className="eyebrow">SELECTED USER</span>

              <h4>{selectedUser.name}</h4>
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
              <span>Name</span>
              <strong>{selectedUser.name}</strong>
            </div>

            <div>
              <span>Role</span>

              <select
                className="user-edit-select"
                value={editRole}
                onChange={(event) =>
                  setEditRole(event.target.value as UserRole)
                }
              >
                <option value="admin">Admin</option>

                <option value="operator">Operator</option>

                <option value="viewer">Viewer</option>
              </select>
            </div>

            <div>
              <span>Status</span>

              <select
                className="user-edit-select"
                value={editStatus}
                onChange={(event) =>
                  setEditStatus(event.target.value as UserStatus)
                }
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
            >
              Save Changes
            </button>

            <button
              type="button"
              className="user-cancel-changes"
              onClick={handleCloseUser}
            >
              Close
            </button>

            {saveMessage && (
              <span className="user-save-message">{saveMessage}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}

export default UserManagement;
