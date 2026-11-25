import type { ReactNode } from "react";
import {Icon,type IconName} from "./Icon";
export function StatusTag({
  children,
  tone = "muted",
}: {
  children: ReactNode;
  tone?: "muted" | "cyan" | "emerald" | "amber";
}) {
  return (
    <span className={`status-tag ${tone}`}>
      <i />
      {children}
    </span>
  );
}

export function EmptySignal({
  icon,
  title,
  copy,
  compact = false,
}: {
  icon: IconName;
  title: string;
  copy: string;
  compact?: boolean;
}) {
  return (
    <div className={`empty-signal ${compact ? "compact" : ""}`}>
      <span>
        <Icon name={icon} size={compact ? 16 : 21} />
      </span>
      <strong>{title}</strong>
      <p>{copy}</p>
    </div>
  );
}

export function Panel({
  children,
  className = "",
  label,
}: {
  children: ReactNode;
  className?: string;
  label?: string;
}) {
  return (
    <section className={`glass-panel ${className}`} aria-label={label}>
      {children}
    </section>
  );
}

export function PanelHeader({
  icon,
  kicker,
  title,
  actions,
}: {
  icon?: IconName;
  kicker: string;
  title: string;
  actions?: ReactNode;
}) {
  return (
    <header className="panel-header">
      <div className="panel-title">
        {icon && (
          <span>
            <Icon name={icon} size={16} />
          </span>
        )}
        <div>
          <small>{kicker}</small>
          <h2>{title}</h2>
        </div>
      </div>
      {actions && <div className="panel-actions">{actions}</div>}
    </header>
  );
}
