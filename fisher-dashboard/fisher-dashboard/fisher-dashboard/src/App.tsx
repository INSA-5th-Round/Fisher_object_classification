import { useEffect, useState } from "react";
import AppShell from "./components/layout/AppShell";
import LoginPage from "./pages/LoginPage";
import {
  fetchCurrentUser,
  getAuthToken,
  clearAuthToken,
  getStoredUser,
} from "./services/dashboardApi";
import type { User } from "./types/dashboard";

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(() => {
    return Boolean(getAuthToken());
  });
  const [currentUser, setCurrentUser] = useState<User | null>(() => {
    return getStoredUser();
  });

  useEffect(() => {
    const token = getAuthToken();
    if (!token) {
      setIsAuthenticated(false);
      return;
    }

    fetchCurrentUser()
      .then((user) => {
        setCurrentUser(user);
        setIsAuthenticated(true);
      })
      .catch(() => {
        clearAuthToken();
        setIsAuthenticated(false);
      });
  }, []);

  const handleLoginSuccess = (user: User) => {
    setCurrentUser(user);
    setIsAuthenticated(true);
  };

  const handleLogout = () => {
    clearAuthToken();
    setCurrentUser(null);
    setIsAuthenticated(false);
  };

  if (!isAuthenticated) {
    return <LoginPage onLoginSuccess={handleLoginSuccess} />;
  }

  return <AppShell currentUser={currentUser} onLogout={handleLogout} />;
}

export default App;
