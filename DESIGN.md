---
version: 1.0
name: AnimeTracker-design-system
description: >-
  A dark-vibrant anime discovery platform design system built for the ACG
  community. Deep indigo canvases anchor neon-purple and cyan accents, creating
  a cinematic feel that lets anime poster artwork breathe. Cards are rounded
  and elevated; typography pairs Inter's readability with Noto Sans SC for
  CJK; UI chrome uses glassmorphism overlays and micro-interactions rather than
  heavy borders. The system covers both the public-facing discovery surfaces
  (home, seasonal browse, search, detail) and the admin back-office.

colors:
  # Brand & Interactive
  primary: "#7C3AED"
  primary-hover: "#6D28D9"
  primary-light: "#A78BFA"
  primary-on-dark: "#C4B5FD"
  accent: "#06B6D4"
  accent-hover: "#0891B2"
  accent-light: "#67E8F9"

  # Semantic
  success: "#10B981"
  success-bg: "#064E3B"
  warning: "#F59E0B"
  warning-bg: "#78350F"
  error: "#EF4444"
  error-bg: "#7F1D1D"
  info: "#3B82F6"

  # Surfaces (Dark — primary theme)
  canvas: "#0F0F23"
  canvas-alt: "#1A1A2E"
  surface: "#1C1C2E"
  surface-hover: "#252538"
  surface-active: "#2E2E42"
  surface-elevated: "#252538"
  surface-card: "#1E1E32"
  surface-overlay: "rgba(15, 15, 35, 0.85)"
  surface-nav: "rgba(15, 15, 35, 0.92)"
  surface-glass: "rgba(28, 28, 46, 0.72)"

  # Surfaces (Light — secondary theme)
  light-canvas: "#FAFAFE"
  light-canvas-alt: "#F4F4FA"
  light-surface: "#FFFFFF"
  light-surface-hover: "#F0EFFA"
  light-surface-elevated: "#FFFFFF"
  light-surface-card: "#FFFFFF"
  light-surface-overlay: "rgba(0, 0, 0, 0.45)"
  light-surface-nav: "rgba(250, 250, 254, 0.92)"

  # Text — Dark
  text-primary: "#F1F1F6"
  text-secondary: "#A1A1B5"
  text-muted: "#6B6B80"
  text-disabled: "#3E3E52"
  text-link: "#A78BFA"
  text-on-primary: "#FFFFFF"
  text-on-accent: "#0F0F23"

  # Text — Light
  light-text-primary: "#1A1A2E"
  light-text-secondary: "#5A5A70"
  light-text-muted: "#9292A8"
  light-text-disabled: "#C2C2D0"
  light-text-link: "#6D28D9"

  # Borders & Dividers
  border: "#2A2A40"
  border-light: "#3A3A50"
  border-focus: "#7C3AED"
  divider: "#222238"
  hairline: "rgba(255, 255, 255, 0.06)"
  light-border: "#E2E2EC"
  light-divider: "#EAEAF2"

  # Accent Gradients
  gradient-brand: "linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%)"
  gradient-hero: "linear-gradient(180deg, rgba(15,15,35,0) 0%, rgba(15,15,35,0.92) 100%)"
  gradient-card-overlay: "linear-gradient(180deg, rgba(15,15,35,0) 50%, rgba(15,15,35,0.95) 100%)"
  gradient-glow: "linear-gradient(135deg, rgba(124,58,237,0.3) 0%, rgba(6,182,212,0.15) 100%)"
  light-gradient-brand: "linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%)"

typography:
  font-family:
    sans: "'Inter', 'Noto Sans SC', system-ui, -apple-system, sans-serif"
    display: "'Outfit', 'Noto Sans SC', system-ui, -apple-system, sans-serif"
    mono: "'JetBrains Mono', 'Fira Code', monospace"

  # Display / Headlines
  hero-display:
    fontFamily: "{typography.font-family.display}"
    fontSize: 48px
    fontWeight: 800
    lineHeight: 1.1
    letterSpacing: -0.03em
  display-xl:
    fontFamily: "{typography.font-family.display}"
    fontSize: 40px
    fontWeight: 700
    lineHeight: 1.15
    letterSpacing: -0.02em
  display-lg:
    fontFamily: "{typography.font-family.display}"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: -0.02em
  display-md:
    fontFamily: "{typography.font-family.display}"
    fontSize: 28px
    fontWeight: 700
    lineHeight: 1.25
    letterSpacing: -0.01em

  # Headings
  h1:
    fontFamily: "{typography.font-family.display}"
    fontSize: 24px
    fontWeight: 700
    lineHeight: 1.3
    letterSpacing: -0.01em
  h2:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 20px
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: -0.01em
  h3:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 18px
    fontWeight: 600
    lineHeight: 1.4
    letterSpacing: 0
  h4:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1.45
    letterSpacing: 0

  # Body
  body-lg:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 16px
    fontWeight: 400
    lineHeight: 1.65
    letterSpacing: 0
  body:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 14px
    fontWeight: 400
    lineHeight: 1.6
    letterSpacing: 0
  body-sm:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: 0

  # UI
  label:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 14px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0.01em
  label-sm:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 12px
    fontWeight: 500
    lineHeight: 1.4
    letterSpacing: 0.02em
  caption:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 12px
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: 0.01em

  # Special
  button:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 14px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.01em
  button-lg:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 16px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.01em
  button-sm:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 13px
    fontWeight: 500
    lineHeight: 1
    letterSpacing: 0
  badge:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 12px
    fontWeight: 600
    lineHeight: 1
    letterSpacing: 0.02em
  overline:
    fontFamily: "{typography.font-family.sans}"
    fontSize: 11px
    fontWeight: 700
    lineHeight: 1
    letterSpacing: 0.08em
    textTransform: uppercase
  mono:
    fontFamily: "{typography.font-family.mono}"
    fontSize: 13px
    fontWeight: 400
    lineHeight: 1.5
    letterSpacing: 0

rounded:
  none: 0px
  xs: 4px
  sm: 6px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 20px
  3xl: 24px
  pill: 9999px
  full: 9999px

spacing:
  px: 1px
  0.5: 2px
  1: 4px
  1.5: 6px
  2: 8px
  2.5: 10px
  3: 12px
  3.5: 14px
  4: 16px
  5: 20px
  6: 24px
  7: 28px
  8: 32px
  9: 36px
  10: 40px
  11: 44px
  12: 48px
  14: 56px
  16: 64px
  20: 80px
  24: 96px

shadow:
  xs: "0 1px 2px rgba(0, 0, 0, 0.3)"
  sm: "0 1px 3px rgba(0, 0, 0, 0.35), 0 1px 2px rgba(0, 0, 0, 0.25)"
  md: "0 4px 6px rgba(0, 0, 0, 0.3), 0 2px 4px rgba(0, 0, 0, 0.2)"
  lg: "0 10px 15px rgba(0, 0, 0, 0.3), 0 4px 6px rgba(0, 0, 0, 0.2)"
  xl: "0 20px 25px rgba(0, 0, 0, 0.35), 0 10px 10px rgba(0, 0, 0, 0.2)"
  2xl: "0 25px 50px rgba(0, 0, 0, 0.4)"
  glow-primary: "0 0 20px rgba(124, 58, 237, 0.3)"
  glow-accent: "0 0 20px rgba(6, 182, 212, 0.3)"
  inner: "inset 0 2px 4px rgba(0, 0, 0, 0.2)"
  light-xs: "0 1px 2px rgba(0, 0, 0, 0.05)"
  light-sm: "0 1px 3px rgba(0, 0, 0, 0.06), 0 1px 2px rgba(0, 0, 0, 0.04)"
  light-md: "0 4px 6px rgba(0, 0, 0, 0.05), 0 2px 4px rgba(0, 0, 0, 0.03)"
  light-lg: "0 10px 15px rgba(0, 0, 0, 0.06), 0 4px 6px rgba(0, 0, 0, 0.03)"

blur:
  sm: 4px
  md: 8px
  lg: 12px
  xl: 16px
  2xl: 24px

components:
  # ─── Navigation ───────────────────────────────
  top-nav:
    backgroundColor: "{colors.surface-nav}"
    textColor: "{colors.text-primary}"
    typography: "{typography.label-sm}"
    height: 56px
    backdropFilter: blur(16px)
    borderBottom: "1px solid {colors.hairline}"

  admin-sidebar:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
    width: 240px
    borderRight: "1px solid {colors.border}"

  # ─── Cards ────────────────────────────────────
  subject-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.xl}"
    shadow: "{shadow.md}"
    padding: 0
    border: "1px solid {colors.border}"
    hover:
      shadow: "{shadow.lg}"
      borderColor: "{colors.border-light}"
      translateY: -2px

  subject-card-image:
    rounded: "{rounded.xl} {rounded.xl} 0 0"
    aspectRatio: 3 / 4
    objectFit: cover
    gradient: "{colors.gradient-card-overlay}"

  subject-card-light:
    backgroundColor: "{colors.light-surface-card}"
    textColor: "{colors.light-text-primary}"
    rounded: "{rounded.xl}"
    shadow: "{shadow.light-md}"
    padding: 0
    border: "1px solid {colors.light-border}"
    hover:
      shadow: "{shadow.light-lg}"

  # ─── Buttons ──────────────────────────────────
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
    minHeight: 40px
    hover:
      backgroundColor: "{colors.primary-hover}"
      shadow: "{shadow.glow-primary}"
    active:
      transform: scale(0.97)
    disabled:
      opacity: 0.4
      cursor: not-allowed

  button-secondary:
    backgroundColor: transparent
    textColor: "{colors.primary-light}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "9px 19px"
    minHeight: 40px
    border: "1.5px solid {colors.primary}"
    hover:
      backgroundColor: "rgba(124, 58, 237, 0.1)"
    active:
      transform: scale(0.97)

  button-ghost:
    backgroundColor: transparent
    textColor: "{colors.text-secondary}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    minHeight: 36px
    hover:
      backgroundColor: "{colors.surface-hover}"
      textColor: "{colors.text-primary}"

  button-accent:
    backgroundColor: "{colors.accent}"
    textColor: "{colors.text-on-accent}"
    typography: "{typography.button}"
    rounded: "{rounded.md}"
    padding: "10px 20px"
    minHeight: 40px
    hover:
      backgroundColor: "{colors.accent-hover}"
      shadow: "{shadow.glow-accent}"

  button-icon:
    backgroundColor: transparent
    textColor: "{colors.text-secondary}"
    rounded: "{rounded.md}"
    size: 36px
    hover:
      backgroundColor: "{colors.surface-hover}"
      textColor: "{colors.text-primary}"

  button-pill:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-on-primary}"
    typography: "{typography.button}"
    rounded: "{rounded.pill}"
    padding: "8px 24px"
    minHeight: 36px
    hover:
      backgroundColor: "{colors.primary-hover}"
    active:
      transform: scale(0.97)

  # ─── Inputs ───────────────────────────────────
  input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    placeholderColor: "{colors.text-muted}"
    rounded: "{rounded.md}"
    padding: "10px 14px"
    minHeight: 40px
    border: "1.5px solid {colors.border}"
    focus:
      borderColor: "{colors.border-focus}"
      shadow: "0 0 0 3px rgba(124, 58, 237, 0.15)"
    disabled:
      opacity: 0.4
    error:
      borderColor: "{colors.error}"

  input-light:
    backgroundColor: "{colors.light-surface}"
    textColor: "{colors.light-text-primary}"
    placeholderColor: "{colors.light-text-muted}"
    border: "1.5px solid {colors.light-border}"
    focus:
      borderColor: "{colors.border-focus}"

  search-input:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    placeholderColor: "{colors.text-muted}"
    rounded: "{rounded.pill}"
    padding: "10px 18px 10px 40px"
    minHeight: 40px
    border: "1.5px solid {colors.border}"
    focus:
      borderColor: "{colors.border-focus}"
      shadow: "0 0 0 3px rgba(124, 58, 237, 0.15)"

  # ─── Tags / Badges ────────────────────────────
  tag-badge:
    backgroundColor: "rgba(124, 58, 237, 0.15)"
    textColor: "{colors.primary-light}"
    typography: "{typography.badge}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
    border: "1px solid rgba(124, 58, 237, 0.2)"

  tag-badge-hoverable:
    backgroundColor: "rgba(124, 58, 237, 0.15)"
    textColor: "{colors.primary-light}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
    border: "1px solid rgba(124, 58, 237, 0.2)"
    hover:
      backgroundColor: "{colors.primary}"
      textColor: "{colors.text-on-primary}"

  status-badge-air:
    backgroundColor: "rgba(16, 185, 129, 0.15)"
    textColor: "{colors.success}"
    typography: "{typography.badge}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"

  status-badge-today:
    backgroundColor: "rgba(245, 158, 11, 0.15)"
    textColor: "{colors.warning}"
    typography: "{typography.badge}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"

  status-badge-na:
    backgroundColor: "rgba(107, 107, 128, 0.15)"
    textColor: "{colors.text-muted}"
    typography: "{typography.badge}"
    rounded: "{rounded.pill}"
    padding: "2px 8px"

  # ─── Season Picker ────────────────────────────
  season-chip:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    padding: "8px 16px"
    border: "1.5px solid {colors.border}"
    hover:
      backgroundColor: "{colors.surface-hover}"
    selected:
      backgroundColor: "rgba(124, 58, 237, 0.2)"
      textColor: "{colors.primary-light}"
      borderColor: "{colors.primary}"

  # ─── Pagination ───────────────────────────────
  pagination-button:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label}"
    rounded: "{rounded.md}"
    minSize: 36px
    border: "1px solid {colors.border}"
    hover:
      backgroundColor: "{colors.surface-hover}"
      textColor: "{colors.text-primary}"
    active:
      backgroundColor: "{colors.primary}"
      textColor: "{colors.text-on-primary}"
      borderColor: "{colors.primary}"

  # ─── Empty / Error / Skeleton ─────────────────
  empty-state:
    textColor: "{colors.text-muted}"
    typography: "{typography.body}"
    iconColor: "{colors.text-disabled}"

  error-state:
    backgroundColor: "rgba(239, 68, 68, 0.08)"
    textColor: "{colors.error}"
    typography: "{typography.body}"
    rounded: "{rounded.lg}"
    padding: "24px"

  skeleton:
    backgroundColor: "{colors.surface-hover}"
    rounded: "{rounded.md}"
    shimmerColor: "rgba(255, 255, 255, 0.04)"

  # ─── Tables ──────────────────────────────────
  table-header:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-secondary}"
    typography: "{typography.label-sm}"
    borderBottom: "1px solid {colors.divider}"
    padding: "12px 16px"

  table-row:
    backgroundColor: transparent
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    borderBottom: "1px solid {colors.divider}"
    padding: "12px 16px"
    hover:
      backgroundColor: "{colors.surface-hover}"

  # ─── AI Assistant ─────────────────────────────
  ai-assistant-window:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xl} {rounded.xl} 0 0"
    shadow: "{shadow.xl}"
    border: "1px solid {colors.border}"
    width: 380px
    maxHeight: 600px

  ai-message-user:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.text-on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.lg} {rounded.lg} 2px {rounded.lg}"
    padding: "10px 14px"
    maxWidth: 80%

  ai-message-assistant:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.lg} {rounded.lg} {rounded.lg} 2px"
    padding: "10px 14px"
    maxWidth: 85%

  # ─── Admin ────────────────────────────────────
  admin-stat-card:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xl}"
    padding: "20px"
    border: "1px solid {colors.border}"
    shadow: "{shadow.sm}"

  admin-stat-value:
    fontFamily: "{typography.font-family.display}"
    fontSize: 32px
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: -0.02em

  admin-table:
    backgroundColor: "{colors.surface-card}"
    textColor: "{colors.text-primary}"
    rounded: "{rounded.xl}"
    padding: 0
    border: "1px solid {colors.border}"
    shadow: "{shadow.sm}"

  # ─── Global ───────────────────────────────────
  divider:
    backgroundColor: "{colors.divider}"
    height: 1px
    margin: 0

  glass-overlay:
    backgroundColor: "{colors.surface-glass}"
    backdropFilter: blur(12px)
    border: "1px solid rgba(255, 255, 255, 0.06)"

  scrollbar:
    width: 6px
    trackColor: transparent
    thumbColor: "{colors.border}"
    thumbHoverColor: "{colors.border-light}"

---

## Overview

AnimeTracker is a personal anime discovery and tracking platform for the ACG community. The design system bridges two worlds: the **cinematic, vibrant energy of anime culture** (neon purples, cyan glows, gradient overlays) and the **functional clarity of a content-discovery tool** (clean grids, clear hierarchy, responsive cards).

The visual language is **dark-first with vibrant accents**. Deep indigo-navy canvases (`{colors.canvas}` — #0F0F23) serve as the foundation, letting anime poster artwork — with its inherently bright, saturated colors — take visual priority. UI chrome uses subtle glassmorphism (`backdrop-filter: blur`), thin hairlines, and elevation changes rather than heavy borders. The result is a platform that feels like browsing a well-lit gallery at night: the content glows, the UI recedes.

**Key Characteristics:**
- **Dark-first, light-optional** — the default theme is a deep indigo-navy canvas. A light variant is available but secondary.
- **Vibrant dual-accent system** — Purple (`{colors.primary}` — #7C3AED) carries primary interactivity; Cyan (`{colors.accent}` — #06B6D4) handles secondary highlights, AI assistant signals, and data visualizations. The two sit on opposite sides of the color wheel, creating a complementary energy.
- **Image-dominant cards** — `{component.subject-card}` is the core atom of the discovery experience. Anime poster art fills the card top with a soft gradient overlay for text legibility.
- **Glassmorphism for overlays** — Navigation, modals, and the AI assistant use `backdrop-filter: blur` with semi-transparent backgrounds, creating depth without occlusion.
- **Outfit + Inter typography** — Outfit's geometric character for display sizes; Inter's neutral clarity for body text. Noto Sans SC provides comprehensive CJK support for Chinese content.
- **Micro-interactions on every interactive element** — hover elevation, scale transforms on press, focus rings with the brand purple glow.
- **Skeleton-first loading** — Every data surface uses skeleton components, not spinners, for perceived performance.
- **Three density modes** — spacious browsing (home/search), compact detail (episode lists), dense data (admin tables).

---

## Colors

> **Philosophy:** The canvas is a dark stage for anime artwork. Purple and cyan create an energetic, slightly futuristic brand identity that resonates with the ACG audience. Colors are defined as semantic tokens — never raw hex values in components.

### Brand & Interactive

- **Primary Purple** (`{colors.primary}` — #7C3AED): The single brand-level interactive color. All primary buttons, active navigation indicators, focus rings, and interactive tag badges. Inspired by the "aura" and "magic" tropes common in anime visual identity.
- **Primary Hover** (`{colors.primary-hover}` — #6D28D9): A deeper variant used on hover/press states for primary buttons and links.
- **Primary Light** (`{colors.primary-light}` — #A78BFA): Used for text on transparent/ghost buttons, tag badge text, and decorative accents on dark surfaces.
- **Primary On Dark** (`{colors.primary-on-dark}` — #C4B5FD): A brighter, softer purple used exclusively for inline links and label text on dark-tinted surfaces where the standard purple would feel heavy.
- **Accent Cyan** (`{colors.accent}` — #06B6D4): The secondary brand energy. Used for AI assistant signals, "Today" airing badges, seasonal highlights, and secondary decorative elements (gradients, loading bars). Cyan sits opposite purple on the color wheel, creating visual tension.
- **Accent Hover** (`{colors.accent-hover}` — #0891B2): Press state for cyan-accented elements.
- **Accent Light** (`{colors.accent-light}` — #67E8F9): Used for subtle cyan glows, AI "thinking" indicators, and as the light end of brand gradients.

### Semantic

| Token | Hex | Use |
|-------|-----|-----|
| `{colors.success}` | #10B981 | "Aired" status badges, success toasts, import completion |
| `{colors.success-bg}` | #064E3B | Success state background (dark) |
| `{colors.warning}` | #F59E0B | "Airing Today" badges, warning states |
| `{colors.warning-bg}` | #78350F | Warning state background (dark) |
| `{colors.error}` | #EF4444 | Error messages, destructive actions, validation errors |
| `{colors.error-bg}` | #7F1D1D | Error state background (dark) |
| `{colors.info}` | #3B82F6 | Informational banners |

### Surfaces

#### Dark Theme (Default)

- **Canvas** (`{colors.canvas}` — #0F0F23): The deepest background — page-level canvas, admin sidebar. A near-black indigo that avoids true `#000000` for a cooler, more cinematic feel.
- **Canvas Alt** (`{colors.canvas-alt}` — #1A1A2E): A step up — used for alternating sections, footer backgrounds.
- **Surface** (`{colors.surface}` — #1C1C2E): The default component surface — inputs, dropdowns, AI message bubbles.
- **Surface Hover** (`{colors.surface-hover}` — #252538): Hover state for surfaces, ghost button backgrounds.
- **Surface Active** (`{colors.surface-active}` — #2E2E42): Active/pressed state for interactive surfaces.
- **Surface Card** (`{colors.surface-card}` — #1E1E32): The primary card surface — subject cards, admin stat cards, tables.
- **Surface Elevated** (`{colors.surface-elevated}` — #252538): Cards/modals that sit above the default surface — dropdowns, tooltips.
- **Surface Glass** (`{colors.surface-glass}` — rgba(28, 28, 46, 0.72)): Glassmorphism overlay for modals and the AI assistant with backdrop blur.
- **Surface Nav** (`{colors.surface-nav}` — rgba(15, 15, 35, 0.92)): The top navigation bar — nearly opaque with blur.
- **Surface Overlay** (`{colors.surface-overlay}` — rgba(15, 15, 35, 0.85)): Modal scrim.

#### Light Theme (Secondary)

- **Light Canvas** (`{colors.light-canvas}` — #FAFAFE): The light theme page background. A very faint violet tint that preserves the brand's cool identity.
- **Light Surface** (`{colors.light-surface}` — #FFFFFF): Pure white component surface.
- **Light Surface Card** (`{colors.light-surface-card}` — #FFFFFF): Card surface in light mode.
- **Light Surface Nav** (`{colors.light-surface-nav}` — rgba(250, 250, 254, 0.92)): Navigation bar in light mode.

### Text

#### Dark Theme
- **Text Primary** (`{colors.text-primary}` — #F1F1F6): Headlines, body copy, labels. A warm off-white that reads softer than pure white.
- **Text Secondary** (`{colors.text-secondary}` — #A1A1B5): Secondary copy, metadata, navigation items.
- **Text Muted** (`{colors.text-muted}` — #6B6B80): Placeholders, disabled text, captions.
- **Text Disabled** (`{colors.text-disabled}` — #3E3E52): Disabled UI elements.
- **Text Link** (`{colors.text-link}` — #A78BFA): Inline links.

#### Light Theme
- **Light Text Primary** (`{colors.light-text-primary}` — #1A1A2E): Matches the dark canvas tone for brand consistency.
- **Light Text Secondary** (`{colors.light-text-secondary}` — #5A5A70)
- **Light Text Muted** (`{colors.light-text-muted}` — #9292A8)

### Borders & Hairlines

- **Border** (`{colors.border}` — #2A2A40): Default component border — cards, inputs, tables.
- **Border Light** (`{colors.border-light}` — #3A3A50): Hover state border, elevated surface borders.
- **Border Focus** (`{colors.border-focus}` — #7C3AED): Focus ring color on inputs and interactive elements.
- **Divider** (`{colors.divider}` — #222238): Section dividers, list separators.
- **Hairline** (`{colors.hairline}` — rgba(255, 255, 255, 0.06)): Ultra-thin separators on dark surfaces — the lightest touch of structure.

### Brand Gradient

- **Brand Gradient** (`{colors.gradient-brand}`): `linear-gradient(135deg, #7C3AED 0%, #06B6D4 100%)` — the signature brand gradient. Used on hero sections, the AI assistant header, and decorative brand elements.
- **Hero Gradient** (`{colors.gradient-hero}`): `linear-gradient(180deg, rgba(15,15,35,0) 0%, rgba(15,15,35,0.92) 100%)` — applied over hero imagery for text legibility.
- **Card Overlay** (`{colors.gradient-card-overlay}`): `linear-gradient(180deg, rgba(15,15,35,0) 50%, rgba(15,15,35,0.95) 100%)` — gradient on card images so title text is always readable.
- **Glow Gradient** (`{colors.gradient-glow}`): `linear-gradient(135deg, rgba(124,58,237,0.3) 0%, rgba(6,182,212,0.15) 100%)` — subtle background ambiance for hero sections or the AI assistant.

---

## Typography

### Font Family

- **Display** (`{typography.font-family.display}`): `'Outfit', 'Noto Sans SC', system-ui, -apple-system, sans-serif` — Outfit's geometric, slightly futuristic character suits the anime-tech identity. At display sizes (20px+), its open apertures and uniform stroke contrast create a clean, modern headline voice.
- **Body / UI** (`{typography.font-family.sans}`): `'Inter', 'Noto Sans SC', system-ui, -apple-system, sans-serif` — Inter's neutral, highly legible design is ideal for body copy, labels, and UI text at all sizes.
- **Mono** (`{typography.font-family.mono}`): `'JetBrains Mono', 'Fira Code', monospace` — for episode sort numbers, data display, code blocks.
- **CJK Support**: All font stacks include `'Noto Sans SC'` as the first CJK fallback. Noto Sans SC covers Simplified Chinese characters used in anime titles (`nameCn`), summaries, and UI labels. The `font-family` order ensures Latin text renders in Outfit/Inter while Chinese text seamlessly switches to Noto Sans SC with matching x-height and weight.

### Hierarchy

| Token | Size | Weight | Line Height | Letter Spacing | Use |
|-------|------|--------|-------------|----------------|-----|
| `{typography.hero-display}` | 48px | 800 | 1.10 | -0.03em | Home hero headline |
| `{typography.display-xl}` | 40px | 700 | 1.15 | -0.02em | Section hero, 404 page |
| `{typography.display-lg}` | 32px | 700 | 1.20 | -0.02em | Page titles, admin dashboard |
| `{typography.display-md}` | 28px | 700 | 1.25 | -0.01em | Subject detail title |
| `{typography.h1}` | 24px | 700 | 1.30 | -0.01em | Section headings |
| `{typography.h2}` | 20px | 600 | 1.35 | -0.01em | Card group titles |
| `{typography.h3}` | 18px | 600 | 1.40 | 0 | Card titles, modal headers |
| `{typography.h4}` | 16px | 600 | 1.45 | 0 | Subsection heads |
| `{typography.body-lg}` | 16px | 400 | 1.65 | 0 | Body paragraphs, summaries |
| `{typography.body}` | 14px | 400 | 1.60 | 0 | Default body, table cells |
| `{typography.body-sm}` | 13px | 400 | 1.55 | 0 | Compact body, metadata |
| `{typography.label}` | 14px | 500 | 1.40 | 0.01em | Form labels, nav items |
| `{typography.label-sm}` | 12px | 500 | 1.40 | 0.02em | Small labels, table headers |
| `{typography.caption}` | 12px | 400 | 1.45 | 0.01em | Secondary captions |
| `{typography.button}` | 14px | 600 | 1.00 | 0.01em | Default button text |
| `{typography.button-lg}` | 16px | 600 | 1.00 | 0.01em | Large/hero buttons |
| `{typography.button-sm}` | 13px | 500 | 1.00 | 0 | Small/compact buttons |
| `{typography.badge}` | 12px | 600 | 1.00 | 0.02em | Tags, status badges |
| `{typography.overline}` | 11px | 700 | 1.00 | 0.08em | Section overlines, uppercase |
| `{typography.mono}` | 13px | 400 | 1.50 | 0 | Episode counts, data values |

### Principles

- **Display sizes use negative tracking.** Every headline at 20px and above carries a sight letter-spacing tighten (`-0.01em → -0.03em`). This creates the modern, slightly compressed headline feel that distinguishes the brand from generic sans-serif.
- **Body copy at 14px with generous line-height.** The default body size (14px) is supplemented by a 1.60 line-height — wider than typical — for comfortable reading of anime summaries and descriptions.
- **Weight 800 for hero display only.** The `{typography.hero-display}` token at 800 weight is reserved for the home page hero. All other display sizes use 700 for a slightly softer impact.
- **Weight 500 for labels, not body.** Form labels and nav items use 500 weight to stand out without using 600 (reserved for buttons). Body copy is always 400.
- **CJK spacing accommodation.** Chinese text at display sizes needs slightly more `letter-spacing: 0.02em` to prevent character crowding. The Noto Sans SC font handles this natively, but the system design recognizes that Chinese-dominated text blocks may need `tracking-wider` utility class adjustments.
- **Tabular figures for data columns.** The mono stack (`{typography.mono}`) uses tabular figures for episode counts, scores, and ranks so numbers align in table columns.

### CJK Typography Note

AnimeTracker is built for a Chinese-speaking audience. Key CJK considerations:

- **Noto Sans SC at weight 400** maps to the system's body weight. Weight 700 maps to display weight. The font's CJK character set covers all Chinese anime titles and UI labels.
- **Mixed Latin/CJK text** — anime titles frequently mix Japanese romanization ("Chobits"), Chinese name ("人形电脑天使心"), and English. The `font-family` stack ensures Latin renders in Outfit/Inter and Chinese in Noto Sans SC without开发者 explicit switching.
- **Line-height for CJK** — Chinese text at 14px with 1.6 line-height is proportionally tighter than Latin at the same size. For CJK-only blocks, consider `leading-relaxed` (1.625) for equivalent readability.

---

## Layout

### Spacing System

- **Base unit:** 4px (`{spacing.1}`). All spacing values are multiples of 4: 4 · 8 · 12 · 16 · 20 · 24 · 28 · 32 · 36 · 40 · 44 · 48 · 56 · 64 · 80 · 96.
- **Component padding:** Cards use `{spacing.6}` (24px) internal padding; compact views use `{spacing.4}` (16px).
- **Section vertical rhythm:** Page sections use `{spacing.16}` (64px) between them; hero sections use `{spacing.20}` (80px).
- **Button padding:** 10px × 20px (primary), 8px × 16px (compact), 12px × 28px (large).
- **Card grid gap:** `{spacing.5}` (20px) between cards in a grid; `{spacing.6}` (24px) on desktop.

### Grid & Container

- **Max content width:** `1280px` for page content; `1536px` for admin tables; `full-bleed` for hero sections.
- **Column patterns:** 6-column grid for subject cards (desktop) → 4-col (tablet) → 2-col (mobile). Admin uses 12-column grid.
- **Gutters:** 20px between cards; 24px between sections.
- **Card grid:** CSS Grid with `grid-template-columns: repeat(auto-fill, minmax(180px, 1fr))` — auto-filling, responsive, no media queries needed for intermediate states.

### Breakpoints

| Name | Width | Key Changes |
|------|-------|-------------|
| Small phone | ≤ 374px | Single column cards; nav collapses to icon-only; hero text 24px |
| Phone | 375–639px | 2-column card grid; compact nav bar; body text at 14px |
| Tablet portrait | 640–767px | 3-column card grid; full nav labels appear |
| Tablet landscape | 768–1023px | 4-column grid; season picker row layout |
| Small desktop | 1024–1279px | 5-column grid; admin sidebar visible by default |
| Desktop | 1280–1535px | 6-column grid; max content width 1280px |
| Wide | ≥ 1536px | Content locks; margins absorb extra width |

### Whitespace Philosophy

AnimeTracker uses generous whitespace in discovery surfaces to let poster artwork breathe. Each subject card has `{rounded.xl}` (16px) radius and 20px gap from neighbors. Section spacing uses 64px vertical padding, creating clear visual breaks between the hero, season grid, and tag sections.

Admin surfaces are intentionally denser — 12px table cell padding, 16px card padding — reflecting the tool's focus on data density over visual breathing room.

---

## Elevation & Depth

| Level | Treatment | Use |
|-------|-----------|-----|
| Flat | 0 shadow, 1px `{colors.border}` | Admin tables, stat cards, inputs |
| Raised | `{shadow.sm}` (subtle drop) | Subject cards, tag badges |
| Elevated | `{shadow.md}` | Dropdowns, hover state cards |
| Floating | `{shadow.lg}` | Modals, AI assistant window |
| Glass | `backdrop-filter: blur(16px)` + rgba surface | Top nav, AI assistant header, modals |
| Glow | `{shadow.glow-primary}` / `{shadow.glow-accent}` | Focused inputs, active AI states, hover CTAs |

**Shadow philosophy.** Shadows on dark themes are inherently more visible than on light themes. The system uses slightly deeper shadows (higher opacity) than typical dark-theme systems — `rgba(0,0,0,0.3–0.4)` — to ensure elevation is legible. On hover, cards lift 2px (`translateY(-2px)`) and gain a glow shadow, creating a clear "reaching for" affordance.

Glassmorphism (`{component.glass-overlay}`) uses `backdrop-filter: blur(12px)` with `rgba(28, 28, 46, 0.72)` background, creating depth through translucency rather than shadow. This is applied to the top navigation, the AI assistant window, and modal overlays.

---

## Shapes

### Border Radius Scale

| Token | Value | Use |
|-------|-------|-----|
| `{rounded.none}` | 0px | Full-bleed images, admin layout edges |
| `{rounded.xs}` | 4px | Mini indicators |
| `{rounded.sm}` | 6px | Inline detail images |
| `{rounded.md}` | 8px | Buttons, inputs, badges — the default interactive radius |
| `{rounded.lg}` | 12px | Cards, modals, AI messages |
| `{rounded.xl}` | 16px | Subject cards, admin cards, AI window |
| `{rounded.2xl}` | 20px | Hero sections, large containers |
| `{rounded.3xl}` | 24px | Very large containers |
| `{rounded.pill}` | 9999px | Search input, pill tags, status badges |

### Image Geometry

- **Subject card images** use `aspect-ratio: 3/4` (portrait poster ratio) with `object-fit: cover`. This matches Bangumi's standard poster aspect ratio and ensures consistent grid alignment.
- **Episode thumbnails** use `aspect-video` (16:9) for landscape screenshot display.
- **Avatar images** use `{rounded.full}` for circular display, 36–48px diameter.
- **Hero imagery** on the home page is full-bleed with `{rounded.none}` and the `{colors.gradient-hero}` overlay.
- All images use `loading="lazy"` with `loading="eager"` reserved for the initial hero.

---

## Components

### Navigation

**`top-nav`** — Persistent, glassmorphism nav bar pinned to the top of every page. Background `{colors.surface-nav}` with `backdrop-filter: blur(16px)`, height 56px, bottom hairline `{colors.hairline}`. Left: brand mark / logo. Center: primary navigation links in `{typography.label-sm}` (12px / 500). Right: search icon, avatar/user menu (login-dependent). Active nav item uses `{colors.primary}` underline indicator. On ≤ 768px, center links collapse to hamburger.

**`admin-sidebar`** — Dark sidebar for admin surfaces. Background `{colors.canvas}` (#0F0F23), width 240px, right border `{colors.border}`. Contains vertical nav items in `{typography.label}` (14px / 500) with `{colors.primary}` active state. Features a collapsible toggle at the bottom. On ≤ 1024px, collapses to icon-only mode (64px width).

### Cards

**`subject-card`** — The core discovery atom. Background `{colors.surface-card}`, rounded `{rounded.xl}` (16px), border `1px solid {colors.border}`, shadow `{shadow.md}`. Composition:
1. **Image region** — 3:4 aspect ratio poster, `object-fit: cover`, `{rounded.xl} {rounded.xl} 0 0` top rounding, `{colors.gradient-card-overlay}` at the bottom for text legibility.
2. **Overlay content** — positioned absolutely over the bottom of the image: score badge (top-right), episode count.
3. **Info region** — padding `{spacing.3}` (12px) below the image: title (1-2 lines, `line-clamp-2`), metadata row (type, year, tags).

Hover: `translateY(-2px)`, `{shadow.lg}`, border `{colors.border-light}`. Transition: `all 200ms ease-out`.

**`subject-card-light`** — Light theme variant with white background, `{shadow.light-md}`, and `{colors.light-border}`.

### Buttons

**`button-primary`** — The primary action. Background `{colors.primary}` (#7C3AED), text `{colors.text-on-primary}` in `{typography.button}` (14px / 600), rounded `{rounded.md}` (8px), padding 10px × 20px, min-height 40px.
- Hover: `{colors.primary-hover}` + `{shadow.glow-primary}`.
- Active: `transform: scale(0.97)`.
- Focus: `box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.25)`.
- Disabled: `opacity: 0.4`, `cursor: not-allowed`.

**`button-secondary`** — Outlined action. Background transparent, 1.5px solid `{colors.primary}` border, text `{colors.primary-light}`. Same dimensions as primary. Hover adds `rgba(124, 58, 237, 0.1)` background fill.

**`button-ghost`** — Minimal action. No background, text `{colors.text-secondary}`. Hover adds `{colors.surface-hover}` fill and `{colors.text-primary}` text. Used for icon buttons, "View All" links.

**`button-accent`** — Cyan accent action. Used for the AI assistant CTA, "Today" highlights, and secondary promotional actions. Same pattern as primary but with `{colors.accent}` → `{colors.accent-hover}` + `{shadow.glow-accent}`.

**`button-pill`** — Pill-shaped variant of primary. Used for "Login", "Sign Up", and the search submit button. Same pattern as primary but `{rounded.pill}` for a more playful feel.

**`button-icon`** — Icon-only button. 36 × 36px, `{rounded.md}`, transparent background, `{colors.text-secondary}`. Hover: `{colors.surface-hover}` + `{colors.text-primary}`.

### Inputs & Forms

**`input`** — Default text input. Background `{colors.surface}`, text `{colors.text-primary}`, placeholder `{colors.text-muted}`, border 1.5px solid `{colors.border}`, rounded `{rounded.md}`, padding 10px × 14px, min-height 40px.
- Focus: border `{colors.border-focus}` + `box-shadow: 0 0 0 3px rgba(124, 58, 237, 0.15)`.
- Error: border `{colors.error}`.
- Disabled: `opacity: 0.4`.

**`search-input`** — Pill-shaped search. Same as `{component.input}` but with:
- `{rounded.pill}` for the distinctive search pill shape.
- Leading icon (search magnifier) at position 14px left.
- Text padding 10px 18px 10px 40px to accommodate the icon.
- Used on the home page hero and the search page.

**`input-light`** — Light theme variant with white background and `{colors.light-border}`.

### Tags & Badges

**`tag-badge`** — Default tag pill. Background `rgba(124, 58, 237, 0.15)`, text `{colors.primary-light}`, `{rounded.pill}`, padding 3px × 10px, `{typography.badge}` (12px / 600). 1px border `rgba(124, 58, 237, 0.2)`. Used for inline tag display on subject cards and the tags page.

**`tag-badge-hoverable`** — Interactive tag. Same as `{component.tag-badge}` but on hover fills with `{colors.primary}` and white text. Used on the tag listing page where tags are clickable filters.

**`status-badge-air`** / **`status-badge-today`** / **`status-badge-na`** — Episode status indicators. Green (Aired), Amber (Today), Gray (Not Aired). Each uses the same pill shape with 15% opacity background of the semantic color.

### Season Picker

**`season-chip`** — Selectable season item. Background `{colors.surface}`, text `{colors.text-secondary}`, `{typography.label}` (14px / 500), rounded `{rounded.md}`, padding 8px × 16px, 1.5px border `{colors.border}`. Selected state: purple border, purple-tinted background, `{colors.primary-light}` text.

Arranged in a horizontal row: Winter · Spring · Summer · Autumn, with year navigation arrows on the sides. On mobile, collapses to a dropdown selector.

### Pagination

**`pagination-button`** — 36 × 36px square button, `{rounded.md}`, background `{colors.surface}`, 1px border `{colors.border}`, text `{colors.text-secondary}`. Active page fills with `{colors.primary}` and white text. Hover: `{colors.surface-hover}` + `{colors.text-primary}`. Previous/next arrows use `{component.button-icon}`.

### Empty / Error / Skeleton States

**`empty-state`** — Centered column layout: large muted icon (64px) in `{colors.text-disabled}`, message in `{colors.text-muted}`, optional action button. Used for "No results found", "No episodes this season", "No tags yet".

**`error-state`** — Red-tinted container with `rgba(239, 68, 68, 0.08)` background, `{colors.error}` text and border. Contains error message and a "Retry" button using `{component.button-ghost}`.

**`skeleton`** — Shimmer-based loading placeholder. Background `{colors.surface-hover}` with a moving gradient highlight (`rgba(255,255,255,0.04)` shimmer). Components: `SubjectCardSkeleton` (matches card dimensions), `ListSkeleton` (rows), `DetailSkeleton` (detail page layout), `TableSkeleton` (admin table rows).

### Tables

**`table-header`** — Background `{colors.surface}`, text `{colors.text-secondary}`, `{typography.label-sm}` (12px / 500), bottom border `{colors.divider}`, padding 12px × 16px.

**`table-row`** — Background transparent, text `{colors.text-primary}`, `{typography.body}` (14px / 400), bottom border `{colors.divider}`. Hover adds `{colors.surface-hover}`. Last row omits bottom border.

Admin tables use `{component.admin-table}` — a container with `{colors.surface-card}` background, `{rounded.xl}`, `{border}`, and `{shadow.sm}`.

### AI Assistant

**`ai-assistant-window`** — Floating glassmorphism window anchored at the bottom-right of the viewport. Width 380px, max-height 600px. Background `{colors.surface-card}` with `{colors.surface-glass}` as backdrop. Top header: brand gradient background, Claude/AI avatar, session title, close button.

**`ai-message-user`** — User message bubble. Background `{colors.primary}`, text `{colors.text-on-primary}`, `{rounded.lg}` with 2px bottom-right, max-width 80%.

**`ai-message-assistant`** — AI response bubble. Background `{colors.surface}`, text `{colors.text-primary}`, `{rounded.lg}` with 2px bottom-left, max-width 85%. Contains markdown-rendered content, tool call references in `{colors.accent-light}`.

### Footer

Background `{colors.canvas-alt}` (#1A1A2E), top border `{colors.divider}`, text `{colors.text-muted}` in `{typography.caption}` (12px). Three-column layout: project info/description, navigation links, tech stack mentions. Max-width `1280px`, centered with `mx-auto`. Vertical padding 48px.

---

## Animation & Motion

### Duration & Timing

| Event | Duration | Easing | Notes |
|-------|----------|--------|-------|
| Card hover | 200ms | ease-out | transform + shadow |
| Button press | 100ms | ease-out | scale(0.97) |
| Page transition | 250ms | ease-in-out | fade |
| Modal enter/exit | 250ms / 200ms | ease-out / ease-in | scale + fade |
| Skeleton shimmer | 1500ms | linear | infinite loop |
| AI streaming cursor | 800ms | ease-in-out | infinite pulse |

### Principles

- **Micro-interactions stay ≤ 250ms.** Hover states, button presses, and focus rings resolve within 200ms for immediate feedback.
- **Exit animations are faster than enter.** Modals exit at 200ms but enter at 250ms — the "exit faster than enter" principle keeps the UI feeling responsive.
- **Transform and opacity only.** Animations use `transform` and `opacity` exclusively — never `width`, `height`, `top`, or `left` — to leverage GPU compositing.
- **Card hover uses translateY, not scale.** Cards lift 2px (`translateY(-2px)`) on hover rather than scaling, to avoid reflow and maintain grid alignment.
- **Skeleton shimmer is subtle.** The shimmer highlight is `rgba(255,255,255,0.04)` on dark surfaces — barely perceptible but enough to indicate activity. Not the aggressive white flash of older skeleton patterns.
- **Respects `prefers-reduced-motion`.** All animations degrade gracefully: hover transitions resolve instantly (0ms), skeleton shimmers become static, and page transitions become instant.
- **No decorative-only animation.** Every animated element has a functional purpose: indicating interactivity (hover), conveying state change (toggle), or providing feedback (button press).

---

## Light Mode

The light theme is a first-class citizen, not an afterthought. Key differences from the dark theme:

| Token Group | Dark | Light |
|-------------|------|-------|
| Canvas | `{colors.canvas}` #0F0F23 | `{colors.light-canvas}` #FAFAFE |
| Surface | `{colors.surface}` #1C1C2E | `{colors.light-surface}` #FFFFFF |
| Card | `{colors.surface-card}` #1E1E32 | `{colors.light-surface-card}` #FFFFFF |
| Text Primary | `{colors.text-primary}` #F1F1F6 | `{colors.light-text-primary}` #1A1A2E |
| Text Muted | `{colors.text-muted}` #6B6B80 | `{colors.light-text-muted}` #9292A8 |
| Border | `{colors.border}` #2A2A40 | `{colors.light-border}` #E2E2EC |
| Shadows | Dark, high-opacity | Light, low-opacity |

**Brand colors are identical in both themes.** Purple (#7C3AED) and cyan (#06B6D4) stay the same — only the surfaces and text change.

**Implementation:** Use CSS custom properties scoped to `.theme-dark` / `.theme-light` classes on `<html>`. Tailwind's `dark:` prefix maps to `.theme-dark`. The system defaults to dark; users can toggle via a sun/moon icon in the top nav.

---

## Do's and Don'ts

### Do
- Use `{colors.primary}` (Purple #7C3AED) for all primary interactive elements — CTAs, active nav states, focus rings.
- Use `{colors.accent}` (Cyan #06B6D4) sparingly for AI interactions, "Today" highlights, and secondary decorative moments. Cyan is the "smart" accent; don't let it compete with purple for primary actions.
- Make `{component.subject-card}` the dominant visual element on discovery pages — poster art drives engagement.
- Use `{component.glass-overlay}` for navigational chrome (nav bar, modals, AI window) to create depth hierarchy.
- Apply `{colors.gradient-card-overlay}` to subject card images so titles remain legible regardless of poster brightness.
- Use `{component.skeleton}` components (never spinners) for loading states on data surfaces.
- Default to dark theme; provide a light toggle in the top nav for accessibility.
- Respect `prefers-reduced-motion` — disable all transitions and shimmer animations when the user requests it.
- Use `Noto Sans SC` for all Chinese text — anime `nameCn` fields, UI labels, search queries.

### Don't
- Don't use `{colors.accent}` (Cyan) as a primary CTA color — it's the supporting accent. Purple carries primary actions.
- Don't use emoji as icons — use Lucide icons (already in the project stack) for every icon need.
- Don't add shadows to text or decorative elements — shadow is for cards, modals, and interactive elements only.
- Don't make `{component.subject-card}` images stretch or distort — maintain 3:4 aspect ratio with `object-fit: cover`.
- Don't use spinners for page content — use skeleton components for every data-loading surface.
- Don't nest scroll regions — page scroll is the primary scroll; avoid `overflow-y: scroll` in modals unless the content genuinely exceeds the modal height.
- Don't use `{colors.error}` (red) for anything other than actual errors or destructive actions.
- Don't forget light mode — test both themes before shipping any surface.
- Don't set CJK text below 12px — Chinese characters become illegible below `{typography.caption}` size.
- Don't use `font-weight: 300` for CJK text — Noto Sans SC at weight 300 is difficult to read at body sizes.

---

## Accessibility

- **Color contrast**: All text/background pairs meet WCAG AA (4.5:1). Primary text on surfaces: `#F1F1F6` on `#1C1C2E` = 12.3:1. Secondary text: `#A1A1B5` on `#1C1C2E` = 6.8:1.
- **Touch targets**: Minimum 40px for all interactive elements (buttons, inputs, tags). Icon-only buttons at 36px pass with adequate spacing.
- **Focus indicators**: All interactive elements show a 2px `{colors.border-focus}` ring with 3px purple glow offset. Use `focus-visible` to show only for keyboard users.
- **Reduced motion**: The `.motion-reduce` class disables all animations (hover transitions become instant, skeleton shimmers become static, page transitions become instant).
- **Screen reader support**: All icon-only buttons carry `aria-label`. Image cards use `alt` text from the anime title. Dynamic content regions announce via `aria-live="polite"`.
- **Keyboard navigation**: Tab order follows visual layout. Search has a skip-to-content link. All filters, pagination, and season navigation are keyboard-accessible.
- **ARIA**: Form fields have associated labels. Tables have proper `role` and `aria-sort` on sortable columns. Modals trap focus and restore on close.

---

## Responsive Behavior

### Breakpoint System

| Name | Width | Grid | Nav | Card Size |
|------|-------|------|-----|-----------|
| Small phone | < 375px | 1-col | Icon-only | Compact (140px) |
| Phone | 375–639px | 2-col | Icon-only + brand | Standard |
| Tablet portrait | 640–767px | 3-col | Full labels | Standard |
| Tablet landscape | 768–1023px | 4-col | Full nav | Standard |
| Desktop | 1024–1279px | 5-col | Full nav + sidebar optional | Standard |
| Wide desktop | ≥ 1280px | 6-col | Full nav + sidebar | Standard |

### Collapsing Strategy

- **Top nav**: Full link row on desktop → collapses to hamburger at ≤ 768px → icon-only brand at ≤ 374px.
- **Subject card grid**: 6-col → 4-col → 3-col → 2-col → 1-col. Uses `auto-fill, minmax(180px, 1fr)` CSS Grid — no media queries needed for intermediate column counts.
- **Admin sidebar**: 240px full width on desktop → 64px icon-only at ≤ 1024px → hidden by hamburger at ≤ 768px.
- **Season picker**: Horizontal chip row on tablet+ → dropdown selector on mobile.
- **AI assistant**: 380px floating window on desktop → full-width bottom sheet on mobile (≤ 640px).
- **Hero typography**: `{typography.hero-display}` (48px) → `{typography.display-xl}` (40px) at 768px → `{typography.display-lg}` (32px) at 640px → `{typography.h1}` (24px) at 375px.

### Touch Targets

- Minimum 40 × 40px for all mobile interactive elements. `{component.button-primary}` lands at ~40 × 80px.
- Card tap targets extend to the full card area for the primary action (navigate to detail).
- The AI assistant FAB is 48 × 48px — exceeds the 44pt Apple minimum.
- Pagination buttons are 36 × 36px — pass with adequate spacing (8px gap).
- Tag badges are 24px tall minimum — clickable with adequate hit area via padding.

---

## Implementation Guide

### Tailwind CSS Configuration

All design tokens map directly to Tailwind CSS configuration. The `colors`, `fontFamily`, `fontSize`, `borderRadius`, `spacing`, `boxShadow`, and `backdropBlur` sections in the config extend the default Tailwind theme with the tokens defined in this document.

```js
// tailwind.config.js — key extensions
module.exports = {
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        brand: {
          primary: '#7C3AED',
          'primary-hover': '#6D28D9',
          'primary-light': '#A78BFA',
          accent: '#06B6D4',
          'accent-hover': '#0891B2',
        },
        surface: {
          canvas: '#0F0F23',
          DEFAULT: '#1C1C2E',
          card: '#1E1E32',
          hover: '#252538',
        },
        // ... full mapping
      },
      fontFamily: {
        sans: ["'Inter', 'Noto Sans SC', 'system-ui', 'sans-serif'"],
        display: ["'Outfit', 'Noto Sans SC', 'system-ui', 'sans-serif'"],
        mono: ["'JetBrains Mono', 'Fira Code', 'monospace'"],
      },
    },
  },
}
```

### Dark/Light Mode Strategy

Use Tailwind's `class` dark mode strategy. Toggle via `document.documentElement.classList.toggle('dark')`. Store preference in `localStorage`. Default to `prefers-color-scheme: dark` media query match.

Light mode tokens are accessed via `light:` variants or through CSS custom properties that swap based on the `.dark` class.

### SVG Icon Strategy

Use Lucide icons (already in the project stack). All icons use `stroke-width: 2` — consistent across the entire UI. Icon sizes: 16px (inline), 20px (UI controls), 24px (nav items), 32px (empty states), 48px+ (decorative).

### CSS Custom Properties

For runtime theme switching and component-level overrides, expose all token categories as CSS custom properties on `:root` / `.dark`:

```css
:root {
  --color-canvas: #0F0F23;
  --color-surface: #1C1C2E;
  --color-primary: #7C3AED;
  /* ... */
}

.light {
  --color-canvas: #FAFAFE;
  --color-surface: #FFFFFF;
  /* ... */
}
```

---

## Known Gaps

- **Collection/lists feature** (Phase 2) may introduce a new state — "In My Collection" — that needs a visual indicator on `{component.subject-card}` (e.g., a checkmark overlay or badge).
- **Form validation messages** need specific color and placement rules beyond the error-state token. Document error message typography and positioning per input type.
- **Mobile bottom navigation** — currently the top nav collapses to hamburger on mobile. Evaluate whether a bottom tab bar would improve one-handed navigation for the core flows (Home, Search, Season, Profile).
- **Print styles** — the admin surfaces (dashboard, tables) may need a print-friendly stylesheet for report export.
- **High-contrast mode** — a future enhancement could provide an accessibility-focused high-contrast variant with stronger borders and heavier text weights.
- **Emoji in anime titles** — some anime titles contain emoji characters. Ensure CJK font stacks gracefully fall back for any unsupported glyphs.
