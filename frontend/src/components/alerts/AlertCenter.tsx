import { createPortal } from "react-dom";
import { useEffect, useMemo, useState } from "react";
import {
  AlertIcon,
  CheckIcon,
  CloseIcon,
  EyeIcon,
  SendIcon,
  ShieldIcon,
} from "../common/Icons";
import { getAlerts, notifyAlert } from "../../services/dashboardService";
import type { Alert } from "../../types/dashboard";

type NotificationChannel = "sms" | "telegram";

type DeliveryState = "idle" | "sending" | "sent" | "failed";

type AlertWithDelivery = Alert & {
  imageUrl?: string;
  incidentUrl: string;
  read: boolean;
  delivery: {
    sms: DeliveryState;
    telegram: DeliveryState;
  };
};

type Filter = "all" | "new" | "acknowledged" | "critical";

const initialAlerts: AlertWithDelivery[] = getAlerts().map((alert) => ({
  ...alert,
  read: false,
  incidentUrl: `/alerts/${alert.id}`,
  delivery: {
    sms: "idle",
    telegram: "idle",
  },
}));

function AlertCenter() {
  const [alerts, setAlerts] = useState<AlertWithDelivery[]>(initialAlerts);

  const [filter, setFilter] = useState<Filter>("all");

  // Only one alert is shown initially.
  // The user can expand the list when needed.
  const [showAllAlerts, setShowAllAlerts] = useState(false);

  const [selectedAlert, setSelectedAlert] = useState<AlertWithDelivery | null>(
    null,
  );

  const [selectedChannels, setSelectedChannels] = useState<
    Record<string, NotificationChannel[]>
  >({
    "ALT-001": ["sms", "telegram"],
    "ALT-002": ["telegram"],
  });

  /*
   * Lock the dashboard behind the modal.
   *
   * Also allow Escape to close the modal.
   */
  useEffect(() => {
    if (!selectedAlert) {
      return;
    }

    const previousOverflow = document.body.style.overflow;

    document.body.style.overflow = "hidden";

    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === "Escape") {
        setSelectedAlert(null);
      }
    };

    document.addEventListener("keydown", handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      document.removeEventListener("keydown", handleKeyDown);
    };
  }, [selectedAlert]);

  const filteredAlerts = useMemo(() => {
    return alerts.filter((alert) => {
      if (filter === "all") {
        return true;
      }

      if (filter === "new") {
        return alert.status === "open";
      }

      if (filter === "acknowledged") {
        return alert.status === "reviewed";
      }

      if (filter === "critical") {
        return alert.severity === "critical";
      }

      return true;
    });
  }, [alerts, filter]);

  /*
   * SHOW ONE ALERT BY DEFAULT.
   *
   * This keeps the Alert Center compact.
   */
  const visibleAlerts = showAllAlerts
    ? filteredAlerts
    : filteredAlerts.slice(0, 1);

  const activeCount = alerts.filter((alert) => alert.status === "open").length;

  const criticalCount = alerts.filter(
    (alert) => alert.severity === "critical",
  ).length;

  const acknowledgedCount = alerts.filter(
    (alert) => alert.status === "reviewed",
  ).length;

  const unreadCount = alerts.filter((alert) => !alert.read).length;

  const updateAlert = (
    alertId: string,
    updates: Partial<AlertWithDelivery>,
  ) => {
    setAlerts((current) =>
      current.map((alert) =>
        alert.id === alertId ? { ...alert, ...updates } : alert,
      ),
    );

    setSelectedAlert((current) =>
      current?.id === alertId ? { ...current, ...updates } : current,
    );
  };

  const markAsRead = (alertId: string) => {
    updateAlert(alertId, {
      read: true,
    });
  };

  const acknowledgeAlert = (alertId: string) => {
    updateAlert(alertId, {
      status: "reviewed",
      read: true,
    });
  };

  const resolveAlert = (alertId: string) => {
    updateAlert(alertId, {
      status: "resolved",
      read: true,
    });
  };

  const toggleChannel = (alertId: string, channel: NotificationChannel) => {
    setSelectedChannels((current) => {
      const channels = current[alertId] ?? [];

      return {
        ...current,
        [alertId]: channels.includes(channel)
          ? channels.filter((item) => item !== channel)
          : [...channels, channel],
      };
    });
  };

  const sendAlert = async (alert: AlertWithDelivery) => {
    const channels = selectedChannels[alert.id] ?? [];

    if (channels.length === 0) {
      return;
    }

    updateAlert(alert.id, {
      delivery: {
        ...alert.delivery,
        ...(channels.includes("sms") && {
          sms: "sending",
        }),
        ...(channels.includes("telegram") && {
          telegram: "sending",
        }),
      },
    });

    try {
      await notifyAlert({
        channels,
        alertId: alert.id,
        title: alert.title,
        severity: alert.severity,
        cameraId: alert.cameraId,
        confidence: alert.confidence,
        imageUrl: alert.imageUrl,
        incidentUrl: alert.incidentUrl,
      });

      updateAlert(alert.id, {
        delivery: {
          ...alert.delivery,
          ...(channels.includes("sms") && {
            sms: "sent",
          }),
          ...(channels.includes("telegram") && {
            telegram: "sent",
          }),
        },
      });
    } catch {
      updateAlert(alert.id, {
        delivery: {
          ...alert.delivery,
          ...(channels.includes("sms") && {
            sms: "failed",
          }),
          ...(channels.includes("telegram") && {
            telegram: "failed",
          }),
        },
      });
    }
  };

  const markAllAsRead = () => {
    setAlerts((current) =>
      current.map((alert) => ({
        ...alert,
        read: true,
      })),
    );
  };

  const handleFilterChange = (nextFilter: Filter) => {
    setFilter(nextFilter);

    /*
     * Every filter starts compact.
     * The operator can expand it if necessary.
     */
    setShowAllAlerts(false);
  };

  return (
    <section className="alert-center">
      {/* HEADER */}
      <div className="alert-center-header">
        <div>
          <span className="eyebrow">SECURITY OPERATIONS</span>

          <h3>Alert Center</h3>

          <p>
            Monitor, investigate and respond to AI-generated security events.
          </p>
        </div>

        <div className="alert-live-status" role="status" aria-live="polite">
          <span className="status-dot"></span>
          Live Alerts
        </div>
      </div>

      {/* SUMMARY */}
      <div className="alert-summary">
        <div className="alert-summary-item">
          <div className="alert-summary-icon">
            <AlertIcon />
          </div>

          <div>
            <span>ACTIVE ALERTS</span>
            <strong>{activeCount}</strong>
          </div>
        </div>

        <div className="alert-summary-item critical-summary">
          <div className="alert-summary-icon">
            <ShieldIcon />
          </div>

          <div>
            <span>CRITICAL</span>
            <strong>{criticalCount}</strong>
          </div>
        </div>

        <div className="alert-summary-item">
          <div className="alert-summary-icon">
            <CheckIcon />
          </div>

          <div>
            <span>ACKNOWLEDGED</span>
            <strong>{acknowledgedCount}</strong>
          </div>
        </div>

        <div className="alert-summary-item">
          <div className="alert-summary-icon">
            <EyeIcon />
          </div>

          <div>
            <span>UNREAD</span>
            <strong>{unreadCount}</strong>
          </div>
        </div>
      </div>

      {/* TOOLBAR */}
      <div className="alert-toolbar">
        <div className="alert-filters">
          {(
            [
              ["all", "All"],
              ["new", "New"],
              ["acknowledged", "Acknowledged"],
              ["critical", "Critical"],
            ] as const
          ).map(([value, label]) => (
            <button
              key={value}
              type="button"
              className={
                filter === value ? "alert-filter active" : "alert-filter"
              }
              onClick={() => handleFilterChange(value)}
            >
              {label}

              {value === "new" && activeCount > 0 && <span>{activeCount}</span>}
            </button>
          ))}
        </div>

        <div className="alert-toolbar-actions">
          {filteredAlerts.length > 1 && (
            <button
              type="button"
              className="alert-view-toggle"
              onClick={() => setShowAllAlerts((current) => !current)}
            >
              {showAllAlerts
                ? "Show less"
                : `View all ${filteredAlerts.length} alerts`}
            </button>
          )}

          {unreadCount > 0 && (
            <button
              type="button"
              className="alert-mark-all"
              onClick={markAllAsRead}
            >
              Mark all as read
            </button>
          )}
        </div>
      </div>

      {/* ALERT LIST */}
      <div className="alert-list">
        {filteredAlerts.length === 0 ? (
          <div className="alert-empty">
            <div className="alert-empty-icon">
              <CheckIcon />
            </div>

            <h4>No alerts found</h4>

            <p>There are no security events matching this filter.</p>
          </div>
        ) : (
          visibleAlerts.map((alert) => (
            <AlertCard
              key={alert.id}
              alert={alert}
              channels={selectedChannels[alert.id] ?? []}
              toggleChannel={toggleChannel}
              onViewDetails={() => {
                markAsRead(alert.id);
                setSelectedAlert(alert);
              }}
              onAcknowledge={() => acknowledgeAlert(alert.id)}
              onResolve={() => resolveAlert(alert.id)}
              onSend={() => sendAlert(alert)}
            />
          ))
        )}
      </div>

      {/* ALERT DETAILS MODAL */}
      {selectedAlert &&
        createPortal(
          <AlertDetailsModal
            alert={selectedAlert}
            onClose={() => setSelectedAlert(null)}
            onAcknowledge={() => acknowledgeAlert(selectedAlert.id)}
            onResolve={() => resolveAlert(selectedAlert.id)}
            onSend={() => sendAlert(selectedAlert)}
          />,
          document.body,
        )}
    </section>
  );
}


function AlertCard({
  alert,
  channels,
  toggleChannel,
  onViewDetails,
  onAcknowledge,
  onResolve,
  onSend,
}: {
  alert: AlertWithDelivery;
  channels: NotificationChannel[];
  toggleChannel: (alertId: string, channel: NotificationChannel) => void;
  onViewDetails: () => void;
  onAcknowledge: () => void;
  onResolve: () => void;
  onSend: () => void;
}) {
  return (
    <article
      className={`alert-card alert-${alert.severity} ${
        alert.read ? "is-read" : "is-unread"
      }`}
    >
      <div className="alert-card-accent"></div>

      <div className="alert-card-main">
        {/* TOP */}
        <div className="alert-card-top">
          <div className="alert-card-identity">
            <div className={`alert-severity ${alert.severity}`}>
              <span></span>
              {alert.severity.toUpperCase()}
            </div>

            {!alert.read && <span className="alert-new-badge">NEW</span>}
          </div>

          <span className="alert-id">{alert.id}</span>
        </div>

        {/* CONTENT */}
        <div className="alert-content">
          <div className="alert-title-row">
            <div className="alert-title-block">
              <h4>{alert.title}</h4>

              <p>{alert.description}</p>
            </div>

            <span className={`alert-status ${alert.status}`}>
              {alert.status === "open"
                ? "OPEN"
                : alert.status === "reviewed"
                  ? "ACKNOWLEDGED"
                  : "RESOLVED"}
            </span>
          </div>

          <div className="alert-meta">
            <span>
              <strong>{alert.cameraId ?? "SYSTEM"}</strong>
            </span>

            <span>
              AI confidence <strong>{alert.confidence}%</strong>
            </span>

            <span>{alert.timestamp}</span>
          </div>
        </div>

        {/* NOTIFICATIONS */}
        <div className="alert-notification">
          <div className="notification-title">NOTIFICATION CHANNELS</div>

          <div className="notification-row">
            <div className="notification-channels">
              <label
                className={
                  channels.includes("sms")
                    ? "notification-channel selected"
                    : "notification-channel"
                }
              >
                <input
                  type="checkbox"
                  checked={channels.includes("sms")}
                  onChange={() => toggleChannel(alert.id, "sms")}
                />

                <span className="channel-mark">SMS</span>
              </label>

              <label
                className={
                  channels.includes("telegram")
                    ? "notification-channel selected"
                    : "notification-channel"
                }
              >
                <input
                  type="checkbox"
                  checked={channels.includes("telegram")}
                  onChange={() => toggleChannel(alert.id, "telegram")}
                />

                <span className="channel-mark">TG</span>
              </label>
            </div>

            <div className="delivery-status">
              <DeliveryStatus label="SMS" status={alert.delivery.sms} />

              <DeliveryStatus
                label="Telegram"
                status={alert.delivery.telegram}
              />
            </div>
          </div>
        </div>

        {/* ACTIONS */}
        <div className="alert-actions">
          <button
            type="button"
            className="secondary-action"
            onClick={onViewDetails}
          >
            <EyeIcon />
            Details
          </button>

          {alert.status === "open" && (
            <button
              type="button"
              className="secondary-action"
              onClick={onAcknowledge}
            >
              <CheckIcon />
              Acknowledge
            </button>
          )}

          {alert.status !== "resolved" && (
            <button
              type="button"
              className="secondary-action"
              onClick={onResolve}
            >
              Resolve
            </button>
          )}

          <button
            type="button"
            className="send-alert-button"
            onClick={onSend}
            disabled={channels.length === 0}
          >
            <SendIcon />
            Send Alert
          </button>
        </div>
      </div>
    </article>
  );
}

/* =========================================================
DELIVERY STATUS
========================================================= */

function DeliveryStatus({
  label,
  status,
}: {
  label: string;
  status: DeliveryState;
}) {
  if (status === "idle") {
    return <span className="delivery-status-item idle">{label} · Ready</span>;
  }

  if (status === "sending") {
    return (
      <span className="delivery-status-item sending">{label} · Sending</span>
    );
  }

  if (status === "sent") {
    return (
      <span className="delivery-status-item sent">
        <CheckIcon />
        {label} · Sent
      </span>
    );
  }

  return <span className="delivery-status-item failed">{label} · Failed</span>;
}

/* =========================================================
ALERT DETAILS MODAL
========================================================= */

function AlertDetailsModal({
  alert,
  onClose,
  onAcknowledge,
  onResolve,
  onSend,
}: {
  alert: AlertWithDelivery;
  onClose: () => void;
  onAcknowledge: () => void;
  onResolve: () => void;
  onSend: () => void;
}) {
  return (
    <div className="alert-modal-backdrop" onClick={onClose} role="presentation">
      <div
        className="alert-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="alert-modal-title"
        onClick={(event) => event.stopPropagation()}
      >
        {/* MODAL HEADER */}
        <div className="alert-modal-header">
          <div>
            <span className="eyebrow">ALERT INVESTIGATION</span>

            <div className="modal-title-row">
              <div className={`modal-severity ${alert.severity}`}>
                <AlertIcon />
              </div>

              <div>
                <h3 id="alert-modal-title">{alert.title}</h3>

                <span className="modal-alert-id">{alert.id}</span>
              </div>
            </div>
          </div>

          <button
            type="button"
            className="modal-close"
            onClick={onClose}
            aria-label="Close alert details"
            title="Close alert details"
          >
            <CloseIcon />
          </button>
        </div>

        {/* DETAILS */}
        <div className="modal-details-grid">
          <div>
            <span>SEVERITY</span>
            <strong>{alert.severity.toUpperCase()}</strong>
          </div>

          <div>
            <span>STATUS</span>
            <strong>{alert.status.toUpperCase()}</strong>
          </div>

          <div>
            <span>CAMERA</span>
            <strong>{alert.cameraId ?? "SYSTEM"}</strong>
          </div>

          <div>
            <span>AI CONFIDENCE</span>
            <strong>{alert.confidence}%</strong>
          </div>
        </div>

        {/* DESCRIPTION */}
        <div className="modal-description">
          <span>EVENT DESCRIPTION</span>

          <p>{alert.description}</p>
        </div>

        {/* INCIDENT */}
        <div className="modal-incident">
          <span>INCIDENT REFERENCE</span>

          <code>{alert.incidentUrl}</code>
        </div>

        {/* NOTIFICATIONS */}
        <div className="modal-notifications">
          <span>DELIVERY STATUS</span>

          <div className="modal-delivery-grid">
            <DeliveryStatus label="SMS" status={alert.delivery.sms} />

            <DeliveryStatus label="Telegram" status={alert.delivery.telegram} />
          </div>
        </div>

        {/* ACTIONS */}
        <div className="modal-actions">
          {alert.status === "open" && (
            <button
              type="button"
              className="modal-action secondary"
              onClick={onAcknowledge}
            >
              <CheckIcon />
              Acknowledge
            </button>
          )}

          {alert.status !== "resolved" && (
            <button
              type="button"
              className="modal-action secondary"
              onClick={onResolve}
            >
              Resolve
            </button>
          )}

          <button
            type="button"
            className="modal-action primary"
            onClick={onSend}
          >
            <SendIcon />
            Send Alert
          </button>
        </div>
      </div>
    </div>
  );
}

export default AlertCenter;
