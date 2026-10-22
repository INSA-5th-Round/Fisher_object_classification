import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Dashboard from "../../pages/Dashboard";
import type { User } from "../../types/dashboard";

interface AppShellProps {
  currentUser?: User | null;
  onLogout?: () => void;
}

function AppShell({ currentUser, onLogout }: AppShellProps) {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Topbar initialUser={currentUser} onLogout={onLogout} />
        <Dashboard />

        <footer className="app-footer">
          FISHER • AI INTELLIGENCE PLATFORM • ETHIOPIA • 2026
        </footer>
      </main>
    </div>
  );
}

export default AppShell;
