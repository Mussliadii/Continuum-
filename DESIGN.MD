# DESIGN.MD — Continuum (Never-Down SRE/Incident Copilot)

> Working product name: **Continuum** — "Institutional memory that never goes down."
> The name is a placeholder; swap it freely, but keep the tagline's promise (continuity of memory through failure) as the design's anchor idea.

---

## 1. Design Concept

This is not a chatbot with a sidebar bolted on. It is an **operations instrument** — the visual language of a tool an SRE already trusts at 3 AM (Grafana, Datadog, PagerDuty), built around one idea: **the agent's memory is visibly, provably alive**, even while everything else is on fire.

Every screen should answer three questions at a glance:
1. What is happening right now?
2. Has this happened before, and what fixed it?
3. Is the memory layer itself healthy?

Design principles:
- **Dense, not cluttered.** SREs scan, they don't read. Optimize for scan-speed (data-dense layout, dial: density 8/10).
- **Calm by default, urgent when it matters.** Neutral dark surface at rest; status color only appears where it's semantically true (never decorative).
- **Proof over claims.** Don't say "always-on memory" in copy — show a live, pulsing cluster-health indicator that's still ticking through the demo's simulated node failure.

---

## 2. Visual Identity

### 2.1 Color System (dark-first; this is an ops tool, dark mode is the primary/default theme, light mode is secondary)

Base palette (from "terminal dark + success green" — Coding Bootcamp / Financial Dashboard family):

| Token | Hex | Usage |
|---|---|---|
| `--color-background` | `#020617` | App shell background |
| `--color-surface` | `#0E1223` | Cards, panels, sidebar |
| `--color-surface-raised` | `#1A1E2F` | Modals, popovers, hovered cards |
| `--color-border` | `#334155` | Dividers, card borders |
| `--color-foreground` | `#F8FAFC` | Primary text |
| `--color-muted-foreground` | `#94A3B8` | Secondary text, timestamps, labels |
| `--color-primary` | `#0F172A` | Primary surfaces (nav, top bar) |
| `--color-accent` | `#3B82F6` | Links, active nav item, focus ring, primary CTA |

Semantic status colors (never used decoratively — always paired with an icon or label, per accessibility rule `color-not-only`):

| Status | Hex | Meaning |
|---|---|---|
| `--status-healthy` | `#22C55E` | Node/service healthy, incident resolved |
| `--status-warning` | `#F59E0B` | Degraded, elevated latency, hypothesis unconfirmed |
| `--status-critical` | `#EF4444` | Node down, active incident, destructive action |
| `--status-info` | `#3B82F6` | Informational, agent is reasoning/searching |

Light mode (secondary, offered for accessibility/preference — not the default): invert to `background #F8FAFC`, `surface #FFFFFF`, `foreground #0F172A`, keep the same status hues (re-tested for 4.5:1 contrast against white).

### 2.2 Typography

- **Headings / data / code:** Fira Code (monospace) — reinforces "this is a technical instrument," used for incident IDs, timestamps, metrics, node names, log snippets.
- **Body / UI text:** Fira Sans — used for chat messages, descriptions, labels.

```css
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600;700&family=Fira+Sans:wght@300;400;500;600;700&display=swap');
```

Type scale: `12 / 14 / 16 / 18 / 24 / 32` px. Body minimum 16px (chat text), 14px for dense metadata (timestamps, tags), never below 12px.

### 2.3 Iconography

- Icon set: **Phosphor Icons** (`@phosphor-icons/react`), duotone/regular weight for status icons, bold for active nav state. No emoji anywhere in the UI.
- Consistent 24px icon size in nav/toolbar, 16px inline with text (severity tags, timestamps).
- Status is always icon + color + text label together (e.g. a filled circle icon in `--status-critical` red next to the word "Critical" — never color alone).

### 2.4 Spacing & Density

Density dial 8/10 (dashboard-tight): spacing scale `4 / 8 / 12 / 16 / 24 / 32` px. Card padding 16px, section gaps 24px, page margin 32px on desktop.

### 2.5 Effects

- Soft elevation (not flat, not neumorphic): `box-shadow: 0 1px 2px rgba(0,0,0,0.4)` resting, `0 4px 12px rgba(0,0,0,0.5)` on hover/raised.
- Border radius: 8px cards, 6px buttons/inputs, 4px tags/badges — consistent scale, never mixed arbitrarily.
- Live-status pulse: a 2px glowing dot animation (`opacity 0.6→1, scale 0.9→1.1`, 2s loop, `ease-in-out`) on the cluster-health indicator only — the one piece of ambient motion that's allowed to run continuously, because it *is* the product's core claim made visible. Respects `prefers-reduced-motion` (falls back to a static solid dot, no pulse).

---

## 3. Layout Structure (desktop ≥1024px, 3-column app shell)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  ⬡ CONTINUUM   [● Incident #INC-142 · Critical]      ⬤ Cluster: Healthy │  ← top bar, 56px
├───────────┬───────────────────────────────────┬───────────────────────┤
│           │                                    │  SIMILAR INCIDENTS    │
│  ⌂ Chat   │   [Incident context banner]        │  ┌──────────────────┐ │
│  ⏱ History│   ─────────────────────────────    │  │ INC-081 · 94%    │ │
│  ▤ KB     │   Agent: I found 3 similar          │  │ conn pool exhaust │ │
│  ⚙ Config │   incidents. Here's what fixed      │  └──────────────────┘ │
│           │   INC-081...                        │  ┌──────────────────┐ │
│  (72px    │                                     │  │ INC-054 · 81%    │ │
│  icon-    │   You: what changed 10 min ago?     │  └──────────────────┘ │
│  only,    │                                     │                        │
│  expand   │   [chat continues, scrollable] ↕    │  CLUSTER HEALTH        │
│  on       │                                     │  ● us-east node: OK   │
│  hover)   │                                     │  ● us-west node: OK   │
│           │  ┌─────────────────────────────┐   │  ● eu node: DEGRADED  │
│           │  │ Type a message...        [→]│   │  p99 latency: 12ms ~  │
│           │  └─────────────────────────────┘   │                        │
│           │                                     │  TIMELINE              │
│           │                                     │  10:41 hypothesis #2  │
│           │                                     │  10:38 checked pool   │
│           │                                     │  10:35 incident open  │
├───────────┴───────────────────────────────────┴───────────────────────┤
│  240px sidebar (expanded)    center chat (flex, min 480px)   360px rail │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.1 Top Bar (fixed, 56px)
- Left: product mark + name.
- Center-left: active incident pill (only rendered when an incident is open) — severity color, ID, one-line title, click to jump to timeline.
- Right: **cluster health indicator** — small pulsing dot + "Cluster: Healthy / Degraded / Node Down" — this is the always-visible proof-of-life for CockroachDB, fed live via MCP Server calls. This is the most important single UI element in the product; never let it be visually secondary.

### 3.2 Left Rail (72px collapsed / 240px expanded on hover or pin)
Icon + label nav: **Chat** (default/home), **Incident History** (past incidents, searchable), **Knowledge Base** (runbooks/postmortems), **Settings**. Active item: accent-colored left border (3px) + icon fill, per `nav-state-active`.

### 3.3 Center — Chat Panel
- **Incident context banner** (only when an incident is active): severity-colored top border on the chat container, showing incident ID/title/duration-so-far, sticky at top of the chat scroll region.
- Message list: agent messages left-aligned with a small mark icon, user messages right-aligned, monospace used inline for log snippets/queries the agent quotes. Agent messages that cite a past incident render an inline **citation chip** (e.g. `[INC-081]`) that's clickable and scrolls the right rail to that card — ties chat reasoning directly to the memory layer instead of feeling like a black box.
- Composer: fixed bottom, multiline textarea, send button, and a secondary "Attach log" affordance. Disabled + spinner state while the agent is retrieving/reasoning (`loading-buttons` rule) — never a silent wait.
- Empty state (no active incident): a calm "All systems normal" state with a single prompt input ("Describe what you're seeing...") rather than a blank chat — avoids the generic-chatbot first impression.

### 3.4 Right Rail (360px, stacked panels — becomes tabs on tablet, bottom sheet on mobile)
1. **Similar Past Incidents** — cards: title, similarity % (from vector search), root-cause tag, resolution time. Ordered by similarity descending. Empty state: "No similar incidents yet — this may be a new pattern," not a blank panel.
2. **Cluster Health** — per-node status rows (region label + status dot + label, never dot alone), p99 query latency sparkline, replica count. This panel is the literal, real-time face of the MCP Server integration.
3. **Incident Timeline** — vertical timeline of the active incident's logged actions/hypotheses (the transactional state table), newest on top, timestamps in Fira Code.

### 3.5 Responsive Behavior
- **≥1024px:** full 3-column layout as above.
- **768–1023px (tablet):** right rail collapses into a tab switcher (Similar / Health / Timeline) docked below the chat; left rail stays icon-only, never auto-expands.
- **<768px (mobile):** single column — chat is primary; right-rail content becomes a bottom sheet triggered by a "Context" button in the top bar; left nav becomes a bottom nav bar (≤5 items, per `bottom-nav-limit`).
- No horizontal scroll at any breakpoint. `min-h-dvh`, not `100vh`.

---

## 4. Key Components

| Component | Notes |
|---|---|
| **Status pill** | icon + label + color, 4px radius, used for incident severity, node health, agent state |
| **Similarity card** | surface `#0E1223`, 8px radius, hover → `#1A1E2F` + 4px lift shadow, `cursor-pointer` |
| **Cluster health row** | dot (12px) + region label (Fira Code) + latency figure (tabular numerals, per `number-tabular`) |
| **Citation chip** | inline pill inside chat text, accent border, clickable, links reasoning → evidence |
| **Timeline entry** | timestamp (muted, Fira Code) + action text + connecting vertical line |
| **Live cluster dot** | the signature element — pulsing animation, reduced-motion fallback to static |

---

## 5. Accessibility & Motion Compliance

- Text contrast ≥4.5:1 in both themes (verified against the palette above); status colors always paired with icon + text (`color-not-only`).
- All interactive elements ≥44×44px hit area, visible focus ring (`--color-accent`, 2px), full keyboard nav — chat composer, citation chips, and timeline entries must all be tab-reachable.
- Motion budget: micro-interactions 150–300ms, `ease-out` entering / `ease-in` exiting; only the cluster-health pulse runs continuously, and it degrades gracefully under `prefers-reduced-motion`.
- Loading states: skeleton rows for similarity cards and cluster health while fetching (not a blank panel or spinner-only), per `progressive-loading`.
- No emoji as icons anywhere; Phosphor icons only, consistent stroke weight.

---

## 6. Design Tokens (CSS variables, ready to drop into the frontend)

```css
:root {
  --color-background: #020617;
  --color-surface: #0E1223;
  --color-surface-raised: #1A1E2F;
  --color-border: #334155;
  --color-foreground: #F8FAFC;
  --color-muted-foreground: #94A3B8;
  --color-primary: #0F172A;
  --color-accent: #3B82F6;

  --status-healthy: #22C55E;
  --status-warning: #F59E0B;
  --status-critical: #EF4444;
  --status-info: #3B82F6;

  --space-1: 4px;  --space-2: 8px;  --space-3: 12px;
  --space-4: 16px; --space-5: 24px; --space-6: 32px;

  --radius-sm: 4px; --radius-md: 6px; --radius-lg: 8px;

  --font-mono: 'Fira Code', ui-monospace, monospace;
  --font-sans: 'Fira Sans', system-ui, sans-serif;
}
```

---

## 7. Anti-Patterns to Avoid (from skill guidance)

- Flat design without depth — use the soft-elevation shadow scale, not pure flat cards.
- Text-heavy pages — favor cards, status rows, and timelines over paragraphs.
- Generic chatbot look (centered single column, no context) — this product must always show *evidence* (similar incidents, cluster state) alongside conversation, never chat in isolation.
- Color-only status signaling — always pair with icon + text.
