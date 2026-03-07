# Spark Plugin for GitHub Copilot

Spark provides opinionated, production-ready defaults for building web applications with GitHub Copilot. When you ask Copilot to build a web app, Spark supplies the technical foundation, design direction, and implementation patterns needed to go from idea to functional application quickly.

## Overview

| | |
|---|---|
| **Provider** | GitHub |
| **Type** | Skill |
| **Requires** | Node.js 18+, pnpm |

## What Spark Can Do

Spark gives Copilot the context to scaffold and build complete web applications from a single prompt:

- **Stack selection:** Chooses the right technology variation based on your application's type and complexity
- **Project scaffolding:** Provides step-by-step setup commands to initialize a working project
- **Design guidance:** Supplies typography pairings, OKLCH color palettes, and layout patterns
- **Implementation patterns:** Covers routing, data fetching, form handling, and state management
- **Reference documentation:** Includes detailed design system, performance, and component pattern references used during generation

## Skills

### `spark-app-template`

Activates when you want to build a new web application. Provides stack selection, project scaffolding, design guidance, and implementation patterns tailored to your use case.

**Trigger examples:**

- "Build me a web app for..."
- "Create a dashboard that..."
- "What stack should I use?"
- "Start a new React project"

## Tech Stack

All Spark applications share a common foundation:

| Category | Technology |
|----------|------------|
| Build tool | Vite |
| Framework | React 19+ |
| Language | TypeScript |
| Package manager | pnpm |
| Routing | TanStack Router (file-based, type-safe) |
| Data fetching | TanStack Query |
| Styling | Tailwind CSS v4+ |
| Component library | shadcn/ui (New York style) |
| Forms | react-hook-form + Zod |
| Icons | Lucide React |
| Animation | Motion |
| Linting | Biome |

## Stack Variations

Spark selects a stack variation based on your application's complexity:

| Variation | Use For | Additional Packages |
|-----------|---------|---------------------|
| **Default Web App** | General tools, utilities, simple CRUD apps, prototypes | None (base stack only) |
| **Data Dashboard** | Analytics panels, admin interfaces, reporting tools | Recharts, date-fns |
| **Content Showcase** | Marketing sites, portfolios, blogs, documentation | marked, dompurify |
| **Complex Application** | SaaS platforms, enterprise tools, multi-view apps | Zustand, date-fns |

## Design Principles

Spark enforces a set of design standards across all generated applications:

- **OKLCH color format** -- All color values use OKLCH for perceptual uniformity and wide-gamut support
- **Distinctive typography** -- Common overused fonts (Inter, Roboto, Arial) are avoided in favor of considered pairings
- **Single theme by default** -- Dark mode is opt-in, not the default
- **Core Web Vitals targets** -- INP < 200ms, LCP < 2.5s, CLS < 0.1
- **WCAG AA contrast** -- 4.5:1 for normal text, 3:1 for large text

## Reference Documentation

Spark includes detailed reference material used during code generation:

| File | Contents |
|------|----------|
| `skills/spark-app-template/references/design-system.md` | Design philosophy, spatial composition, backgrounds, micro-interactions |
| `skills/spark-app-template/references/typography-pairings.md` | Distinctive font combinations with personality guidance |
| `skills/spark-app-template/references/color-palettes.md` | Pre-curated OKLCH palettes with WCAG validation |
| `skills/spark-app-template/references/component-patterns.md` | Common shadcn/ui compositions and usage patterns |
| `skills/spark-app-template/references/performance-checklist.md` | Core Web Vitals optimization and React Compiler setup |
| `skills/spark-app-template/references/prd-template.md` | Simplified planning framework for new apps |
| `skills/spark-app-template/references/radix-migration-guide.md` | Migration path from Radix UI to Base UI or React Aria |

