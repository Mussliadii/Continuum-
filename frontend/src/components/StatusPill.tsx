import { CheckCircle, Warning, XCircle, Info } from "@phosphor-icons/react/dist/ssr";
import type { Severity } from "@/lib/types";

const SEVERITY_CONFIG: Record<
  Severity,
  { label: string; colorVar: string; Icon: typeof CheckCircle }
> = {
  critical: { label: "Critical", colorVar: "var(--color-status-critical)", Icon: XCircle },
  warning: { label: "Warning", colorVar: "var(--color-status-warning)", Icon: Warning },
  info: { label: "Info", colorVar: "var(--color-status-info)", Icon: Info },
};

export function SeverityPill({ severity }: { severity: Severity }) {
  const { label, colorVar, Icon } = SEVERITY_CONFIG[severity];
  return (
    <span
      className="inline-flex items-center gap-1 rounded text-xs font-medium px-2 py-0.5"
      style={{ color: colorVar, backgroundColor: `color-mix(in srgb, ${colorVar} 15%, transparent)` }}
    >
      <Icon size={14} weight="bold" aria-hidden />
      {label}
    </span>
  );
}

export function HealthPill({
  healthy,
  label,
}: {
  healthy: boolean;
  label: string;
}) {
  const colorVar = healthy ? "var(--color-status-healthy)" : "var(--color-status-critical)";
  return (
    <span className="inline-flex items-center gap-1.5 text-xs font-medium" style={{ color: colorVar }}>
      <span
        className={`inline-block h-2 w-2 rounded-full ${healthy ? "cluster-pulse" : ""}`}
        style={{ backgroundColor: colorVar }}
        aria-hidden
      />
      {label}
    </span>
  );
}
