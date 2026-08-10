# EPI Labs — Impeccable Design System

Design language and visual tokens for EPI Labs infrastructure, web interfaces, and verification portals based on [Impeccable Design Language](https://github.com/pbakaus/impeccable).

---

## 1. Core Principles

- **Infrastructure-Grade**: Design like high-security, high-reliability cryptographic software (Tailscale, Cloudflare, Linear, Stripe).
- **File-First Clarity**: Evidence is a portable `.epi` file — not a closed dashboard lock-in.
- **Zero AI Slop**: No generic Inter-only stacks, no un-tinted grays, no nested "carditis", no purple-blue SaaS linear gradients, no cookie-cutter rounded icon boxes.
- **WCAG AAA Accessibility**: Ultra-crisp typography contrast in dark slate (`#0B0F19`) and clean light slate (`#F8FAFC`).

---

## 2. Typography Pairings

- **Display & Headings**: `Plus Jakarta Sans`, sans-serif (Weights: 700, 800)
- **Body & Paragraphs**: `Inter`, `Public Sans`, sans-serif (Weights: 400, 500, 600; Line Height: 1.6)
- **Monospace, Hashes & Code**: `JetBrains Mono`, `Fira Code`, monospace (Weights: 500, 700)

```html
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&family=Plus+Jakarta+Sans:wght@600;700;800&display=swap" rel="stylesheet">
```

---

## 3. Color System (Cryptographic Slate)

### Dark Mode (Default)
- **Canvas / Background**: `#0B0F19` (Deep Slate)
- **Surface Elevation 1**: `#111827` (Card / Panel Slate)
- **Surface Elevation 2**: `#1E293B` (Border / Inset Slate)
- **Text Primary**: `#F8FAFC` (Pure Slate White, 98% opacity)
- **Text Secondary**: `#94A3B8` (Muted Blue Slate, 80% opacity)
- **Text Code**: `#38BDF8` (Cyan Monospace)

### Brand & Status Accents
- **Radiant Cyan (Primary Accent)**: `#06B6D4` (Hero glows, CTA buttons, active states)
- **Verification Emerald (Seal PASSED)**: `#10B981` (Verification OK, 100% integrity, valid signature)
- **Cyber Amber (Seal ADVISORY / WARN)**: `#F59E0B` (Heuristic warning, unsigned trace)
- **Critical Crimson (Seal FAIL)**: `#EF4444` (Signature mismatch, byte tampering, policy violation)

---

## 4. Layout & Surface Rules

- **No Carditis**: Do not nest cards inside cards. Use subtle 1px slate borders (`rgba(255, 255, 255, 0.08)`), asymmetric column spans, and generous breathing room (padding: `3rem` to `5rem`).
- **Interactive Verification Widget**: Prominent drag-and-drop target in hero section with live visual feedback, instant JSON inspector, and status badges.
- **Glassmorphism & Glows**: Radial background sweeps (`radial-gradient(circle, rgba(6, 182, 212, 0.12) 0%, transparent 70%)`) and glowing hover states on interactive buttons.

---

## 5. Motion & Interaction

- **Transitions**: `all 0.2s cubic-bezier(0.16, 1, 0.3, 1)` (ease-out-expo; clean and instant).
- **Hover Micro-Interactions**: Subtle elevation transform (`translateY(-2px)`), radiant border glow expansion, code copy pill feedback.
