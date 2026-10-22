import { useState } from "react";
import { login } from "../services/dashboardApi";
import type { User } from "../types/dashboard";
import "./login.css";

interface LoginPageProps {
  onLoginSuccess: (user: User) => void;
}

export function LoginPage({ onLoginSuccess }: LoginPageProps) {
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

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
      const msg = err instanceof Error ? err.message : "Authentication failed.";
      setError(msg);
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
