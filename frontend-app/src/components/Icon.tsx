import type { ReactNode } from "react";
export type IconName =
  | "activity"
  | "alert"
  | "arrow"
  | "box"
  | "branch"
  | "check"
  | "chevron"
  | "cloud"
  | "code"
  | "command"
  | "database"
  | "docker"
  | "file"
  | "folder"
  | "grid"
  | "hex"
  | "layers"
  | "lock"
  | "menu"
  | "pulse"
  | "report"
  | "scan"
  | "search"
  | "server"
  | "settings"
  | "shield"
  | "spark"
  | "terminal"
  | "x"
  | "zap";

const iconPaths: Record<IconName, ReactNode> = {
  activity: <path d="M3 12h4l2.3-7 4.2 14 2.2-7H21" />,
  alert: (
    <>
      <path d="M10.3 2.9 1.8 17a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 2.9a2 2 0 0 0-3.4 0Z" />
      <path d="M12 9v4M12 17h.01" />
    </>
  ),
  arrow: <path d="M5 12h14M13 6l6 6-6 6" />,
  box: (
    <>
      <path d="m21 8-9 5-9-5 9-5 9 5Z" />
      <path d="m3 8 9 5 9-5M3 8v8l9 5 9-5V8M12 13v8" />
    </>
  ),
  branch: (
    <>
      <circle cx="6" cy="5" r="2" />
      <circle cx="18" cy="6" r="2" />
      <circle cx="6" cy="19" r="2" />
      <path d="M6 7v10M8 7c4 0 3 5 8 5V8" />
    </>
  ),
  check: <path d="m5 12 4 4L19 6" />,
  chevron: <path d="m9 18 6-6-6-6" />,
  cloud: <path d="M17.5 19H6a4 4 0 1 1 .7-7.9A6 6 0 0 1 18.3 9a5 5 0 0 1-.8 10Z" />,
  code: (
    <>
      <path d="m8 9-4 3 4 3M16 9l4 3-4 3M14 5l-4 14" />
    </>
  ),
  command: <path d="M9 6V5a3 3 0 1 0-3 3h12a3 3 0 1 0-3-3v14a3 3 0 1 0 3-3H6a3 3 0 1 0 3 3V6Z" />,
  database: (
    <>
      <ellipse cx="12" cy="5" rx="8" ry="3" />
      <path d="M4 5v7c0 1.7 3.6 3 8 3s8-1.3 8-3V5M4 12v7c0 1.7 3.6 3 8 3s8-1.3 8-3v-7" />
    </>
  ),
  docker: (
    <>
      <path d="M3 13h14c1.6 0 2.6-.6 3.4-1.7.8 3.8-1.9 7.7-7.1 7.7H9c-3.4 0-5.5-2-6-6Z" />
      <path d="M5 9h3v3H5zM9 9h3v3H9zM13 9h3v3h-3zM9 5h3v3H9zM13 5h3v3h-3z" />
    </>
  ),
  file: (
    <>
      <path d="M6 2h8l4 4v16H6z" />
      <path d="M14 2v5h5" />
    </>
  ),
  folder: <path d="M3 6h7l2 2h9v11H3z" />,
  grid: (
    <>
      <rect x="3" y="3" width="7" height="7" rx="2" />
      <rect x="14" y="3" width="7" height="7" rx="2" />
      <rect x="3" y="14" width="7" height="7" rx="2" />
      <rect x="14" y="14" width="7" height="7" rx="2" />
    </>
  ),
  hex: <path d="m12 2 9 5v10l-9 5-9-5V7z" />,
  layers: (
    <>
      <path d="m12 2 9 5-9 5-9-5 9-5Z" />
      <path d="m3 12 9 5 9-5M3 17l9 5 9-5" />
    </>
  ),
  lock: (
    <>
      <rect x="4" y="10" width="16" height="11" rx="2" />
      <path d="M8 10V7a4 4 0 0 1 8 0v3M12 14v3" />
    </>
  ),
  menu: <path d="M4 7h16M4 12h16M4 17h16" />,
  pulse: <path d="M2 12h4l2-7 4 14 2-7h8" />,
  report: (
    <>
      <path d="M5 3h14v18H5zM8 8h8M8 12h5M8 16h7" />
    </>
  ),
  scan: (
    <>
      <path d="M8 3H3v5M16 3h5v5M8 21H3v-5M16 21h5v-5M7 12h10" />
    </>
  ),
  search: (
    <>
      <circle cx="11" cy="11" r="7" />
      <path d="m20 20-4-4" />
    </>
  ),
  server: (
    <>
      <rect x="3" y="4" width="18" height="6" rx="2" />
      <rect x="3" y="14" width="18" height="6" rx="2" />
      <path d="M7 7h.01M7 17h.01M11 7h6M11 17h6" />
    </>
  ),
  settings: (
    <>
      <circle cx="12" cy="12" r="3" />
      <path d="M19 15.5 21 17l-4 4-1.5-2a8 8 0 0 1-3.5 1L11 23H7l-1-3a8 8 0 0 1-2-2l-3-1v-4l3-1a8 8 0 0 1 1-3L3 7l4-4 2 2a8 8 0 0 1 3-1l1-3h4l1 3a8 8 0 0 1 2 2l3 1v4l-3 1a8 8 0 0 1-1 3.5Z" />
    </>
  ),
  shield: (
    <>
      <path d="M12 22s8-3.8 8-10V5l-8-3-8 3v7c0 6.2 8 10 8 10Z" />
      <path d="m9 12 2 2 4-4" />
    </>
  ),
  spark: (
    <path d="m12 3-1.2 4.3a5 5 0 0 1-3.5 3.5L3 12l4.3 1.2a5 5 0 0 1 3.5 3.5L12 21l1.2-4.3a5 5 0 0 1 3.5-3.5L21 12l-4.3-1.2a5 5 0 0 1-3.5-3.5L12 3Z" />
  ),
  terminal: <path d="m4 7 5 5-5 5M12 17h8" />,
  x: <path d="m6 6 12 12M18 6 6 18" />,
  zap: <path d="M13 2 3 14h9l-1 8 10-12h-9l1-8Z" />,
};

export function Icon({ name, size = 18 }: { name: IconName; size?: number }) {
  return (
    <svg
      aria-hidden="true"
      className="icon"
      width={size}
      height={size}
      viewBox="0 0 24 24"
      fill="none"
      stroke="currentColor"
      strokeWidth="1.65"
      strokeLinecap="round"
      strokeLinejoin="round"
    >
      {iconPaths[name]}
    </svg>
  );
}
