import { useEffect, useLayoutEffect, useRef, useState } from "react";
import {
  AlertIcon,
  CameraIcon,
  DetectionIcon,
  GridIcon,
  ReportIcon,
  UsersIcon,
} from "../common/Icons";

type Section =
  | "dashboard"
  | "cctv"
  | "detections"
  | "alerts"
  | "reports"
  | "users";

type NavigationItem = {
  id: Section;
  label: string;
  target: string;
  icon: React.ReactNode;
};

const navigationItems: NavigationItem[] = [
  {
    id: "dashboard",
    label: "Dashboard",
    target: "dashboard",
    icon: <GridIcon />,
  },
  {
    id: "cctv",
    label: "Live CCTV",
    target: "live-cctv",
    icon: <CameraIcon />,
  },
  {
    id: "alerts",
    label: "Alert Center",
    target: "alerts",
    icon: <AlertIcon />,
  },
  {
    id: "detections",
    label: "Detection Results",
    target: "detection-results",
    icon: <DetectionIcon />,
  },
  {
    id: "reports",
    label: "Reports",
    target: "reports",
    icon: <ReportIcon />,
  },
  {
    id: "users",
    label: "User Management",
    target: "user-management",
    icon: <UsersIcon />,
  },
];

function getSectionFromHash(): Section {
  const hash = window.location.hash.replace("#", "");
  const matchingItem = navigationItems.find((item) => item.target === hash);
  return matchingItem?.id ?? "dashboard";
}

interface SidebarProps {
  activeAlertCount?: number;
}

function Sidebar({ activeAlertCount = 0 }: SidebarProps) {
  const [activeSection, setActiveSection] = useState<Section>(getSectionFromHash);
  const navigationRef = useRef<HTMLElement>(null);
  const activeIndicatorRef = useRef<HTMLSpanElement>(null);

  useLayoutEffect(() => {
    const updateIndicator = () => {
      const navigation = navigationRef.current;
      const indicator = activeIndicatorRef.current;
      const activeItem = navigation?.querySelector<HTMLElement>(".nav-item.active");

      if (!navigation || !indicator || !activeItem) {
        return;
      }

      indicator.style.height = `${activeItem.offsetHeight}px`;
      indicator.style.transform = `translateY(${activeItem.offsetTop}px)`;
    };

    updateIndicator();
    window.addEventListener("resize", updateIndicator);

    return () => {
      window.removeEventListener("resize", updateIndicator);
    };
  }, [activeSection]);

  useEffect(() => {
    const mainContent = document.querySelector<HTMLElement>(".main-content");
    if (!mainContent) {
      return;
    }

    const handleScroll = () => {
      const activationPoint =
        mainContent.getBoundingClientRect().top +
        mainContent.clientHeight * 0.3;
      const currentSection = [...navigationItems].reverse().find((item) => {
        const target = document.getElementById(item.target);
        return (
          target !== null &&
          target.getBoundingClientRect().top <= activationPoint
        );
      });

      setActiveSection(currentSection?.id ?? "dashboard");
    };

    mainContent.addEventListener("scroll", handleScroll, { passive: true });
    handleScroll();

    return () => {
      mainContent.removeEventListener("scroll", handleScroll);
    };
  }, []);

  return (
    <aside className="sidebar">
      <div className="sidebar-brand">
        <div className="brand-mark">F</div>

        <div className="sidebar-brand-copy">
          <h2>FISHER</h2>
          <span>AI INTELLIGENCE PLATFORM</span>
        </div>
      </div>

      <nav
        ref={navigationRef}
        className="sidebar-nav"
        aria-label="Primary navigation"
      >
        <span
          ref={activeIndicatorRef}
          className="sidebar-active-indicator"
          aria-hidden="true"
        />
        <span className="nav-label">OPERATIONS</span>

        {navigationItems.map((item) => (
          <a
            key={item.id}
            href={`#${item.target}`}
            aria-label={item.label}
            className={
              activeSection === item.id ? "nav-item active" : "nav-item"
            }
            aria-current={activeSection === item.id ? "page" : undefined}
          >
            <span className="nav-icon">{item.icon}</span>

            <span className="nav-text">{item.label}</span>

            {item.id === "alerts" && activeAlertCount > 0 && (
              <span className="nav-alert-badge">{activeAlertCount}</span>
            )}
          </a>
        ))}
      </nav>

      <div className="sidebar-status">
        <span className="status-dot"></span>

        <div>
          <strong>System Operational</strong>
          <small>AI surveillance defense active</small>
        </div>
      </div>
    </aside>
  );
}

export default Sidebar;
