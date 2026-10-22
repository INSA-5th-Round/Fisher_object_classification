import { useState } from "react";
import { login } from "../services/dashboardApi";
import type { User } from "../types/dashboard";
import "./login.css";

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

const AUTHORIZED_ACCOUNTS = [
  { username: "admin", email: "admin@fisher.cctv", role: "Administrator", defaultPass: "admin123" },
  { username: "operator", email: "operator@fisher.cctv", role: "Operator", defaultPass: "operator123" },
  { username: "supervisor", email: "supervisor@fisher.cctv", role: "Supervisor", defaultPass: "supervisor123" },
];

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [username, setUsername] = useState("admin");
  const [email, setEmail] = useState("admin@fisher.cctv");
  const [password, setPassword] = useState("admin123");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectAccount = (acc: typeof AUTHORIZED_ACCOUNTS[0]) => {
    setUsername(acc.username);
    setEmail(acc.email);
    setPassword(acc.defaultPass);
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    if (!username.trim() || !email.trim() || !password) {
      setError("Please fill in username, authorized email, and password.");
      return;
    }

    setLoading(true);
    try {
      const response = await login(username.trim(), email.trim(), password);
      if (response && response.user) {
        onLoginSuccess(response.user);
      } else {
        setError("Invalid credentials or server error.");
      }
    } catch (err: unknown) {
      const rawMsg = err instanceof Error ? err.message : "Authentication failed.";
      if (rawMsg.toLowerCase().includes("failed to fetch") || rawMsg.toLowerCase().includes("networkerror")) {
        setError(
          "Unable to connect to the backend server (127.0.0.1:8000). Please check that python server.py is running."
        );
      } else {
        setError(rawMsg);
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page-container">
      <div className="login-card">
        <div className="login-header">
          <div className="login-brand">
            <div className="login-brand-mark">F</div>
            <div className="login-title-wrap">
              <h1>FISHER CCTV</h1>
              <span>AI Intelligence Platform</span>
            </div>
          </div>
          <p className="login-subtitle">
            Sign in with your authorized credentials to access live camera surveillance.
          </p>
          <div className="login-auth-badge">
            Authorized Personnel Access Only
          </div>
        </div>

        {/* Quick Account Selector */}
        <div style={{ marginBottom: "16px" }}>
          <div style={{ fontSize: "11px", color: "#94a3b8", marginBottom: "8px", textTransform: "uppercase", letterSpacing: "0.5px" }}>
            Select Authorized Account:
          </div>
          <div style={{ display: "flex", gap: "6px" }}>
            {AUTHORIZED_ACCOUNTS.map((acc) => (
              <button
                key={acc.username}
                type="button"
                onClick={() => selectAccount(acc)}
                style={{
                  flex: 1,
                  padding: "6px 8px",
                  borderRadius: "6px",
                  fontSize: "11px",
                  fontWeight: 600,
                  cursor: "pointer",
                  border: username === acc.username ? "1px solid #1597e5" : "1px solid #334155",
                  background: username === acc.username ? "rgba(21, 151, 229, 0.2)" : "#1e293b",
                  color: username === acc.username ? "#38bdf8" : "#cbd5e1",
                  transition: "all 0.15s ease",
                }}
              >
                {acc.username}
              </button>
            ))}
          </div>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="login-alert-msg error">{error}</div>}

          <div className="login-form-group">
            <label htmlFor="login-username">Username</label>
            <input
              id="login-username"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="e.g. admin"
              autoComplete="username"
              required
            />
          </div>

          <div className="login-form-group">
            <label htmlFor="login-email">Authorized Email Address</label>
            <input
              id="login-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="e.g. admin@fisher.cctv"
              autoComplete="email"
              required
            />
          </div>

          <div className="login-form-group">
            <label htmlFor="login-password">Password</label>
            <input
              id="login-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          <button
            type="submit"
            className="login-btn-submit"
            disabled={loading}
          >
            {loading ? "Verifying Credentials..." : "Sign In to CCTV Dashboard"}
          </button>
        </form>

        <div className="login-footer-info">
          <span>FISHER • ETHIOPIAN AI DEFENSE & SURVEILLANCE • 2026</span>
          <span>Access strictly restricted to approved system administrators</span>
          <div className="login-ethiopian-strip" aria-hidden="true">
            <span></span>
            <span></span>
            <span></span>
          </div>
        </div>
      </div>
    </div>
  );
}

export default LoginPage;
