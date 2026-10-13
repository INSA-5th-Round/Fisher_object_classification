import Sidebar from "./Sidebar";
import Topbar from "./Topbar";
import Dashboard from "../../pages/Dashboard";

function AppShell() {
  return (
    <div className="app-shell">
      <Sidebar />

      <main className="main-content">
        <Topbar />
        <Dashboard />

        <footer className="app-footer">
          FISHER • AI INTELLIGENCE PLATFORM • ETHIOPIA • 2026
        </footer>
      </main>
    </div>
  );
}

export default AppShell;
