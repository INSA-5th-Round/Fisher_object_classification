import { useState } from "react";
import { CameraIcon, LocationIcon, PauseIcon, PlayIcon } from "../common/Icons";

interface CCTVFeedProps {
  cameraName: string;
  location: string;
  status: "online" | "offline";
  streamUrl?: string;
  cameraId?: string;
}

function CCTVFeed({
  cameraName,
  location,
  status,
  streamUrl,
  cameraId = "CAM-001",
}: CCTVFeedProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [streamError, setStreamError] = useState(false);

  const effectiveStreamUrl =
    streamUrl || `/api/cameras/${encodeURIComponent(cameraId)}/stream`;

  const handleToggle = () => {
    if (status === "online") {
      setIsExpanded((current) => !current);
    }
  };

  const handlePause = () => {
    if (status === "online") {
      setIsPaused((current) => !current);
    }
  };

  return (
    <div className={isExpanded ? "cctv-feed expanded" : "cctv-feed"}>
      <div className="cctv-header">
        <div>
          <span className="eyebrow">LIVE CAMERA</span>
          <h3>{cameraName}</h3>
        </div>

        <div className={`camera-status ${status}`}>
          <span className="status-dot"></span>
          {status === "online" ? "LIVE" : "OFFLINE"}
        </div>
      </div>

      <div
        className="cctv-screen"
        onClick={handleToggle}
        style={{ cursor: status === "online" ? "pointer" : "not-allowed" }}
        role="button"
        tabIndex={status === "online" ? 0 : -1}
        aria-label={
          status === "online"
            ? `Open ${cameraName} camera feed`
            : `${cameraName} is offline`
        }
      >
        {status === "online" ? (
          isPaused ? (
            <div className="camera-placeholder">
              <div className="camera-icon">
                <CameraIcon />
              </div>
              <strong>Stream Paused</strong>
              <span className="camera-location">
                <LocationIcon />
                {location}
              </span>
              <small>Click Resume Stream below to continue live monitoring</small>
            </div>
          ) : streamError ? (
            <div className="camera-placeholder">
              <div className="camera-icon">
                <CameraIcon />
              </div>
              <strong>Connecting to Live Camera Stream...</strong>
              <span className="camera-location">
                <LocationIcon />
                {location}
              </span>
              <small>Stream source: {effectiveStreamUrl}</small>
            </div>
          ) : (
            <img
              src={effectiveStreamUrl}
              alt={`${cameraName} Live Stream`}
              className="cctv-live-img"
              onError={() => setStreamError(true)}
              onLoad={() => setStreamError(false)}
            />
          )
        ) : (
          <div className="camera-placeholder">
            <div className="camera-icon offline">
              <CameraIcon />
            </div>
            <strong>Camera Offline</strong>
            <span className="camera-location">
              <LocationIcon />
              {location}
            </span>
            <small>No signal available</small>
          </div>
        )}

        <div className="camera-overlay">
          <span>{cameraName}</span>
          <span>
            {status === "online" ? (isPaused ? "PAUSED" : "LIVE") : "NO SIGNAL"}
          </span>
        </div>
      </div>

      {status === "online" && (
        <div className="cctv-controls">
          <button type="button" className="cctv-control" onClick={handlePause}>
            {isPaused ? <PlayIcon /> : <PauseIcon />}
            {isPaused ? "Resume Stream" : "Pause Stream"}
          </button>

          <span className="cctv-location">{location}</span>
        </div>
      )}
    </div>
  );
}

export default CCTVFeed;
