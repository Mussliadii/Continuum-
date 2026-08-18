import { ChatCircleDots, ClockCounterClockwise, BookOpen, Gear } from "@phosphor-icons/react/dist/ssr";

const NAV_ITEMS = [
  { label: "Chat", Icon: ChatCircleDots, active: true },
  { label: "Incident History", Icon: ClockCounterClockwise, active: false },
  { label: "Knowledge Base", Icon: BookOpen, active: false },
  { label: "Settings", Icon: Gear, active: false },
];

export function LeftRail() {
  return (
    <nav
      aria-label="Primary"
      className="hidden md:flex w-[200px] shrink-0 flex-col gap-1 border-r border-border bg-primary p-3"
    >
      {NAV_ITEMS.map(({ label, Icon, active }) => (
        <button
          key={label}
          type="button"
          disabled={!active}
          aria-current={active ? "page" : undefined}
          className={`flex items-center gap-3 rounded-md px-3 py-2.5 text-sm transition-colors ${
            active
              ? "bg-surface text-foreground border-l-[3px] border-accent -ml-[3px] pl-[15px]"
              : "text-muted-foreground cursor-not-allowed opacity-60"
          }`}
          title={active ? undefined : `${label} — coming soon`}
        >
          <Icon size={18} weight={active ? "fill" : "regular"} aria-hidden />
          {label}
        </button>
      ))}
    </nav>
  );
}
