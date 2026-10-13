import { useState } from "react";
import { CameraIcon, LocationIcon, PauseIcon, PlayIcon } from "../common/Icons";

interface CCTVFeedProps {
  cameraName: string;
  location: string;
  status: "online" | "offline";
}

function CCTVFeed({ cameraName, location, status }: CCTVFeedProps) {
  const [isExpanded, setIsExpanded] = useState(false);
  const [isPaused, setIsPaused] = useState(false);

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

      <button
        type="button"
        className="cctv-screen"
        onClick={handleToggle}
        disabled={status === "offline"}
        aria-label={
          status === "online"
            ? `Open ${cameraName} camera`
            : `${cameraName} is offline`
        }
      >
        {status === "online" ? (
          <div className="camera-placeholder">
            <div className="camera-icon">
              <CameraIcon />
            </div>

            <strong>
              {isPaused
                ? "Stream Paused"
                : isExpanded
                  ? "Camera View Active"
                  : "Live CCTV Stream"}
            </strong>

            <span className="camera-location">
              <LocationIcon />
              {location}
            </span>

            <small>
              {isPaused
                ? "Use the control below to resume"
                : isExpanded
                  ? "Expanded monitoring view"
                  : "Click to expand"}
            </small>
          </div>
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
      </button>

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
