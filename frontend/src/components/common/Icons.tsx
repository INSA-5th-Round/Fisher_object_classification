type IconProps = {
  size?: number;
};

const iconProps = (size: number) => ({
  width: size,
  height: size,
  viewBox: "0 0 24 24",
  fill: "none",
  stroke: "currentColor",
  strokeWidth: 1.8,
  strokeLinecap: "round" as const,
  strokeLinejoin: "round" as const,
  "aria-hidden": true,
});

export function GridIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <rect x="3" y="3" width="7" height="7" rx="1.5" />
      <rect x="14" y="3" width="7" height="7" rx="1.5" />
      <rect x="3" y="14" width="7" height="7" rx="1.5" />
      <rect x="14" y="14" width="7" height="7" rx="1.5" />
    </svg>
  );
}

export function CameraIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <rect x="3" y="7" width="18" height="13" rx="2" />
      <path d="M8 7l1.5-3h5L16 7" />
      <circle cx="12" cy="13.5" r="3.2" />
    </svg>
  );
}

export function DetectionIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M8 3H5a2 2 0 0 0-2 2v3" />
      <path d="M16 3h3a2 2 0 0 1 2 2v3" />
      <path d="M8 21H5a2 2 0 0 1-2-2v-3" />
      <path d="M16 21h3a2 2 0 0 0 2-2v-3" />
      <circle cx="12" cy="12" r="3" />
    </svg>
  );
}

export function AlertIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M10.3 4.2 3.1 17a2 2 0 0 0 1.8 3h14.2a2 2 0 0 0 1.8-3L13.7 4.2a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4" />
      <path d="M12 16.5h.01" />
    </svg>
  );
}

export function ChartIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M4 19V5" />
      <path d="M4 19h16" />
      <path d="m7 15 3-4 3 2 5-7" />
    </svg>
  );
}

export function ReportIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M6 3h9l4 4v14H6z" />
      <path d="M15 3v5h4" />
      <path d="M9 12h6" />
      <path d="M9 16h6" />
    </svg>
  );
}

export function UsersIcon({ size = 19 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <circle cx="9" cy="8" r="3" />
      <path d="M3.5 20a5.5 5.5 0 0 1 11 0" />
      <circle cx="17" cy="9" r="2.3" />
      <path d="M15.5 15.5a4.5 4.5 0 0 1 5 4.5" />
    </svg>
  );
}

export function CheckIcon({ size = 16 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="m5 12 4 4L19 6" />
    </svg>
  );
}

export function CloseIcon({ size = 17 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="m6 6 12 12" />
      <path d="m18 6-12 12" />
    </svg>
  );
}

export function EyeIcon({ size = 16 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M2.5 12s3.2-5 9.5-5 9.5 5 9.5 5-3.2 5-9.5 5-9.5-5-9.5-5Z" />
      <circle cx="12" cy="12" r="2.3" />
    </svg>
  );
}

export function SendIcon({ size = 16 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="m21 3-7.2 18-3.5-7.3L3 10.2 21 3Z" />
      <path d="M10.3 13.7 21 3" />
    </svg>
  );
}

export function ShieldIcon({ size = 17 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M12 3 19 6v5.5c0 4.5-2.8 7.7-7 9.5-4.2-1.8-7-5-7-9.5V6l7-3Z" />
      <path d="m9 12 2 2 4-4" />
    </svg>
  );
}

export function SearchIcon({ size = 17 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <circle cx="10.5" cy="10.5" r="6.5" />
      <path d="m16 16 5 5" />
    </svg>
  );
}

export function PlayIcon({ size = 16 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="m8 5 11 7-11 7V5Z" />
    </svg>
  );
}

export function PauseIcon({ size = 16 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M8 5v14" />
      <path d="M16 5v14" />
    </svg>
  );
}

export function LocationIcon({ size = 15 }: IconProps) {
  return (
    <svg {...iconProps(size)}>
      <path d="M20 10c0 5-8 11-8 11S4 15 4 10a8 8 0 1 1 16 0Z" />
      <circle cx="12" cy="10" r="2.5" />
    </svg>
  );
}
