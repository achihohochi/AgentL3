# AgentL3 Frontend Redesign Plan

## Context

The current frontend (`frontend/index.html`) is a functional single-file HTML app using Tailwind CSS + vanilla JS. It works but looks like a prototype -- pastel backgrounds on a gray-500 body, no icons, no animations, basic typography. The goal is to transform it into a **production-grade SRE/DevOps tool** with a dark theme, modern design patterns, and polished interactions, while preserving the exact same backend API contract and single-file architecture.

---

## Design Direction

**Aesthetic:** Dark ops-tool theme inspired by Datadog, Grafana, PagerDuty -- professional, information-dense, easy on eyes during incidents.

---

## 1. Color Palette

| Token | Value | Usage |
|---|---|---|
| Body bg | `#0f1117` | Near-black with blue tint |
| Surface | `#161b26` | Card backgrounds |
| Surface raised | `#1e2433` | Hover states, elevated cards |
| Glass | `rgba(22,27,38,0.7)` + backdrop-blur | Header, overlays |
| Border | `rgba(255,255,255,0.06)` | Subtle card borders |
| Text primary | slate-200 (`#e2e8f0`) | Main content |
| Text secondary | slate-400 (`#94a3b8`) | Muted/labels |
| Accent indigo | `#6366f1` | Primary actions, links |
| Accent emerald | `#10b981` | Success, high confidence |
| Accent amber | `#f59e0b` | Warnings, medium confidence |
| Accent rose | `#f43f5e` | Errors, low confidence |
| Accent cyan | `#06b6d4` | Info, timeline markers |

**Gradients:**
- Header text: `bg-gradient-to-r from-indigo-400 to-cyan-400`
- Progress bar: `bg-gradient-to-r from-indigo-500 to-cyan-500`
- Analyze button: `bg-gradient-to-r from-indigo-600 to-indigo-500`

---

## 2. Layout Changes

```
Current: flat stack of 5 pastel cards, space-y-16 (huge gaps)

Proposed:
+----------------------------------------------------------+
| HEADER (sticky, glassmorphism)  |  health dot indicator   |
+----------------------------------------------------------+
| UPLOAD ZONE (drag-drop, collapsible after submit)         |
+----------------------------------------------------------+
| PIPELINE STEPPER (horizontal dots + progress bar)         |
+----------------------------------------------------------+
| RESULTS (collapsible sub-sections, SVG confidence gauge)  |
+----------------------------------------------------------+
| Q&A (chat-style, typing indicator, citations)             |
+----------------------------------------------------------+
| DEBUG (collapsible terminal-style panel)                  |
+----------------------------------------------------------+
```

- Reduce spacing from `space-y-16` to `space-y-6`
- Sticky header with `backdrop-blur-xl`
- All cards: dark surface bg + subtle border + slight hover lift

---

## 3. Component Redesign Details

### 3.1 Header
- Sticky bar with glassmorphism (`bg-[rgba(22,27,38,0.7)] backdrop-blur-xl border-b border-white/5`)
- Left: Lucide `shield-alert` icon + "AgentL3" in gradient text + subtitle in slate-500
- Right: Pulsing green/red dot health indicator with env tag pills

### 3.2 Upload Section
- **Drag-and-drop zone**: dashed border, upload-cloud icon, hover glow effect
- File list as removable chips (file icon + name + size + X button)
- Gradient analyze button with hover lift
- Collapses to compact summary after submission

### 3.3 Pipeline Status
- **Horizontal stepper**: 6 dots (queued > triage > retrieve > root_cause > synthesize > done)
- Active dot gets pulsing ring animation
- Connecting lines: completed = indigo, future = slate-700
- Gradient progress bar below stepper
- Copyable job ID badge

### 3.4 Results Section
- **SVG confidence gauge** (arc) with color coding: rose < 0.4 < amber < 0.7 < emerald
- Collapsible sub-sections with chevron rotation animation
- **Timeline**: vertical line with dot markers and timestamps
- **References**: terminal-style code blocks with log syntax highlighting
- Staggered slide-up animation on reveal

### 3.5 Q&A Section
- Chat-style interface with message bubbles
- Send button with arrow-up icon inside input container
- Typing indicator (3 animated dots) while waiting for response
- Citations with log syntax highlighting

### 3.6 Debug Section
- Collapsible `<details>` styled as a dev console
- Terminal aesthetic: `bg-[#0d1117] text-emerald-400 font-mono`
- Copy-to-clipboard button

---

## 4. Icons

**Library:** Lucide Icons via CDN (pinned version)
```html
<script src="https://unpkg.com/lucide@0.344.0/dist/umd/lucide.min.js"></script>
```

Key icons: `shield-alert`, `upload-cloud`, `file-text`, `play`, `clock`, `search`, `target`, `list-checks`, `library`, `book-open`, `arrow-up`, `terminal`, `copy`, `chevron-down`, `circle-check`, `circle-x`

Call `lucide.createIcons()` after every dynamic DOM update.

---

## 5. Animations

| Animation | Purpose | Duration |
|---|---|---|
| `pulse-ring` | Active pipeline stage glow | 1.5s infinite |
| `slide-up` | Section reveal (opacity + translateY) | 400ms ease-out |
| `fade-in` | Subtle element appearance | 300ms ease |
| `typing-dot` | Q&A loading indicator | 1.4s infinite |
| Chevron rotation | Collapsible section toggle | 200ms |
| Gauge fill | SVG confidence arc on load | 1s ease-out |
| Hover lift | Cards/buttons on hover | `-translate-y-0.5` |

---

## 6. Interactive Enhancements

- **Drag-and-drop** file upload with visual feedback
- **Collapsible sections** in results with item count badges
- **Copy-to-clipboard** for job ID and debug query
- **Log syntax highlighting**: timestamps (cyan), ERROR/FATAL (rose), WARN (amber), INFO (cyan), metrics (emerald)
- **Typing indicator** in Q&A while awaiting response

---

## 7. Typography

| Role | Classes |
|---|---|
| Page title | `text-xl font-bold tracking-tight` |
| Section heading | `text-base font-semibold text-slate-100` |
| Sub-heading | `text-sm font-semibold text-slate-200 uppercase tracking-wider` |
| Body text | `text-sm text-slate-300 leading-relaxed` |
| Caption/meta | `text-xs text-slate-500` |
| Mono/code | `font-mono text-xs` |

---

## 8. Files to Modify

| File | Action |
|---|---|
| `frontend/index.html` | **Complete rewrite** -- sole target of this redesign |
| `backend/app/schemas.py` | **Read-only reference** -- response shapes |
| `backend/app/main.py` | **Read-only reference** -- API contract |

---

## 9. Implementation Order

1. **Foundation** -- CDN imports, Tailwind config, CSS variables, dark body bg
2. **Header** -- Sticky glassmorphism bar, health indicator, icons
3. **Upload** -- Drop zone, drag-and-drop JS, file chips, gradient button
4. **Pipeline** -- Horizontal stepper, pulse animation, gradient progress bar
5. **Results** -- Collapsible sections, SVG gauge, timeline, log highlighting
6. **Q&A** -- Chat interface, typing indicator, citation styling
7. **Debug** -- Terminal panel, copy button
8. **Polish** -- Responsive testing, animation smoothing, final review

---

## 10. Verification Checklist

- [ ] Page loads, dark theme renders correctly
- [ ] Health check shows green/red indicator
- [ ] File selection via click works
- [ ] File selection via drag-and-drop works
- [ ] File removal works
- [ ] Analyze button disabled when no files
- [ ] Upload triggers job, stepper animates through stages
- [ ] Progress bar fills correctly
- [ ] Results render all sections (summary, gauge, timeline, evidence, root causes, next steps, related cases, references)
- [ ] Collapsible sections toggle open/close
- [ ] Q&A works with answer + citations
- [ ] Debug query loads and displays
- [ ] Copy-to-clipboard works
- [ ] Responsive at 375px, 768px, 1280px
- [ ] All `fetch()` calls unchanged (same URLs, methods, payloads)
- [ ] `escapeHtml()` still used on user content
- [ ] No XSS regressions

---

## 11. Risks & Mitigations

- **Tailwind CDN compatibility**: Use `tailwind.config` inline script for custom animations; test `@apply` directives still work
- **Lucide CDN**: Pin to specific version to avoid breaking changes
- **File size**: Will grow from ~387 to ~650-700 lines -- acceptable for single-file app
- **XSS**: Maintain `escapeHtml()` usage; `highlightLog()` only applied to trusted server data
- **Performance**: Use `transform`/`opacity` for animations (GPU-accelerated); avoid animating layout properties
