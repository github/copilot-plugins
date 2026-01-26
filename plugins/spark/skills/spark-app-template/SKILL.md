---
name: spark-app-template
description: Comprehensive guidance for building web apps with opinionated defaults for tech stack, design system, and code standards. Use when user wants to create a new web application, dashboard, or interactive interface. Provides tech choices, styling guidance, project structure, and design philosophy to get users up and running quickly with a fully functional, beautiful web app.
---

# Spark App Template

## Purpose

Spark App Template provides defaults and guidance for building web applications. When a user asks to build a web app, this skill provides the technical foundation and design direction to create functional applications.

## When to Use This Skill

Activate Spark App Template when the user:
- Wants to build a new web application from scratch
- Asks "what stack should I use?"
- Needs guidance on design, styling, or tech choices
- Wants to start a dashboard, interactive tool, data app, or content site
- Requests help choosing between frameworks, libraries, or approaches

## Quick Start Workflow

**CRITICAL**: Follow this exact order to avoid configuration errors:

1. **Create project**: `pnpm create vite@latest my-app --template react-ts`
2. **Install base dependencies**: `pnpm install`
3. **Configure TypeScript path aliases** (tsconfig.json AND tsconfig.app.json - see Step 1 below)
4. **Install Tailwind and tooling**: `pnpm add -D tailwindcss @tailwindcss/vite @biomejs/biome`
5. **Configure vite.config.ts**: Add Tailwind plugin and path aliases
6. **Initialize shadcn**: `pnpm dlx shadcn@latest init` (will now succeed with proper aliases)
7. **Install required shadcn components**: `pnpm dlx shadcn add button card avatar ...` (BEFORE writing components)
8. **Install additional packages**: TanStack Router, Query, Zustand, etc.
9. **Write custom components** (NOW safe to import from `@/components/ui/*`)
10. **Configure routing and state management**
11. **Implement features**

**Steps 3, 6, and 7 must happen in this exact order** to avoid TypeScript errors and failed shadcn installations.

## Complexity Levels

Understanding complexity helps choose the right stack variation and design approach:

1. **Micro Tool** (single-purpose)
   - Examples: Calculator, converter, color picker, timer
   - Stack: `stacks/default-webapp.md`
   - Focus: Simple, focused UI with minimal state

2. **Content Showcase** (information-focused)
   - Examples: Landing page, portfolio, blog, documentation
   - Stack: `stacks/content-showcase.md`
   - Focus: Typography, reading experience, visual hierarchy

3. **Light Application** (multiple features with basic state)
   - Examples: Todo list, meal planner, expense tracker
   - Stack: `stacks/default-webapp.md`
   - Focus: Feature clarity, data persistence, user flows

4. **Complex Application** (advanced functionality, multiple views)
   - Examples: CRM, analytics dashboard, project management tool
   - Stack: `stacks/complex-application.md` or `stacks/data-dashboard.md`
   - Focus: Navigation, state management, performance optimization

## Core Tech Stack (Shared Foundation)

All Spark App Template applications use this foundation:

### Build & Development
- **Build Tool**: Vite (latest stable)
- **Framework**: React 19+ (leverages new compiler, hooks, and features)
- **Language**: TypeScript
- **Package Manager**: pnpm
- **Linting**: Biome (ESLint fallback for complex plugins)

### Routing & Data
- **Routing**: TanStack Router (file-based, type-safe)
- **Data Fetching**: TanStack Query
- **Forms**: react-hook-form + Zod validation

### Styling & UI
- **Styling**: Tailwind CSS v4+ (modern @import syntax)
- **Components**: shadcn/ui (New York style, 45+ components)
- **Icons**: Lucide React (1000+ icons)
- **Color System**: Radix Colors (OKLCH format)
- **Theme**: next-themes (single theme default, dark mode optional)

### Utilities & Enhancement
- **Animation**: Motion (formerly framer-motion)
- **Notifications**: Sonner
- **Utilities**: CVA (or Tailwind Variants) + clsx + tailwind-merge
- **Error Handling**: react-error-boundary

## Stack Variations

All variations share the core foundation above. These templates add specific packages and design guidance:

### Default Web App (`stacks/default-webapp.md`)
- **Use for**: Most applications, general-purpose tools
- **Additive packages**: None
- **Design focus**: Clean, modern, functional

### Data Dashboard (`stacks/data-dashboard.md`)
- **Use for**: Analytics, admin panels, data visualization
- **Additive packages**: Recharts (charts), date-fns (date handling)
- **Design focus**: Data density, hierarchical information, scanning patterns

### Content Showcase (`stacks/content-showcase.md`)
- **Use for**: Marketing sites, portfolios, blogs, documentation
- **Additive packages**: marked (markdown parsing)
- **Design focus**: Typography scale, reading experience, whitespace

### Complex Application (`stacks/complex-application.md`)
- **Use for**: Multi-view apps, SaaS platforms, enterprise tools
- **Additive packages**: Zustand (state management), date-fns
- **Design focus**: Navigation patterns, state architecture, performance

## React 19+ Features

Enable these modern React capabilities:

### React Compiler
- **Status**: Available in React 19+
- **Benefits**: Auto-memoization, significantly faster initial loads and interactions
- **Setup**: Compatible with React 17+, configure via compiler config

### useActionState Hook
- **Use for**: Form handling, async actions, loading states
- **Benefits**: Simplified state management, built-in async handling
- **Pattern**: Consolidates form state, pending state, and error handling

### useOptimistic Hook
- **Use for**: Instant UI updates before server confirmation
- **Benefits**: Improved perceived performance, better UX
- **Pattern**: Optimistic updates with automatic rollback on failure

### Server Components
- **Status**: Stable in React 19+ (framework mode only)
- **Frameworks**: Next.js, TanStack Start
- **Note**: For Vite + React SPA apps, use client-side rendering

## Project Structure Template

```
my-app/
├── index.html
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── biome.json
├── src/
│   ├── main.tsx              # App entry point
│   ├── App.tsx               # Root component
│   ├── index.css             # Global styles + theme
│   ├── components/
│   │   ├── ui/               # shadcn components (don't edit)
│   │   └── ...               # Custom components
│   ├── hooks/
│   │   └── use-mobile.tsx
│   ├── lib/
│   │   ├── utils.ts          # cn() utility
│   │   └── data.ts           # Data schemas (if needed)
│   └── routes/               # TanStack Router routes
│       └── __root.tsx
└── public/                   # Static assets
```

## Design Philosophy

Beautiful web applications transcend mere functionality - they evoke emotion and form memorable experiences. Follow these principles:

### Core Principles
1. **Simplicity Through Reduction**: Remove until reaching the simplest effective solution
2. **Material Honesty**: Digital materials have unique properties; embrace them
3. **Obsessive Detail**: Excellence emerges from hundreds of thoughtful decisions
4. **Coherent Design Language**: Every element should feel like part of a unified system
5. **Distinctive Visual Identity**: Create memorable aesthetics, not generic patterns

### Critical Requirements
- **Use OKLCH color format** (mandatory for 2026)
- **Avoid overused fonts**: Inter, Roboto, Arial, Space Grotesk
- **Choose distinctive typography**: See `references/typography-pairings.md`
- **Validate color contrast**: WCAG AA (4.5:1 normal, 3:1 large text)
- **Single theme by default**: No dark mode unless explicitly requested
- **Variable fonts**: Use single variable font files for performance

See `references/design-system.md` for comprehensive design guidance.

## Performance Targets (Core Web Vitals)

Optimize for these metrics:
- **INP** (Interaction to Next Paint): < 200ms
- **LCP** (Largest Contentful Paint): < 2.5s
- **CLS** (Cumulative Layout Shift): < 0.1

Tools to achieve targets:
- React Compiler for automatic memoization
- Vite code-splitting and lazy loading
- Image optimization (WebP, AVIF, lazy loading)
- Font optimization (variable fonts, font-display: swap)

See `references/performance-checklist.md` for detailed optimization strategies.

## References

Access detailed guidance in the `references/` directory:

1. **design-system.md** - Comprehensive design philosophy, spatial composition, backgrounds, micro-interactions
2. **typography-pairings.md** - Distinctive font combinations with personality guidance
3. **color-palettes.md** - Pre-curated OKLCH palettes with WCAG validation
4. **component-patterns.md** - Common shadcn compositions and usage patterns
5. **performance-checklist.md** - Web Vitals optimization, React Compiler setup
6. **prd-template.md** - Simplified planning framework for new apps
7. **radix-migration-guide.md** - Base UI migration path for Radix concerns

## Implementation Workflow

### Step 1: Initialize Project

**CRITICAL**: Configure path aliases BEFORE running `shadcn init` to avoid validation errors.

```bash
# Create Vite project
pnpm create vite@latest my-app --template react-ts
# Note: Working directory is now my-app/ - no need to cd

# Install dependencies
pnpm install

# Add Tailwind CSS and tooling
pnpm add -D tailwindcss@latest @tailwindcss/vite
pnpm add -D @biomejs/biome
pnpm add -D @tanstack/router-plugin
```

**Configure TypeScript Path Aliases** (Required for shadcn):

Update `tsconfig.json`*:
```json
{
  "files": [],
  "references": [
    { "path": "./tsconfig.app.json" },
    { "path": "./tsconfig.node.json" }
  ],
  "compilerOptions": {
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Update `tsconfig.app.json`*:
```json
{
  "compilerOptions": {
    // ... existing options ...
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

Update `vite.config.ts`*:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { TanStackRouterVite } from '@tanstack/router-plugin/vite'
import path from 'path'

export default defineConfig({
  plugins: [
    TanStackRouterVite(),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
})
```

_* Configuration samples based on Vite + React + TypeScript template structure_

**Now shadcn init will succeed**:

```bash
# Initialize shadcn (path aliases now configured)
pnpm dlx shadcn@latest init

# CRITICAL: Install shadcn components BEFORE writing custom components
# Identify which components you need first
pnpm dlx shadcn@latest add button card input form dialog avatar badge separator

# Add TanStack packages
pnpm add @tanstack/react-router @tanstack/react-query

# Add utilities
pnpm add lucide-react motion sonner react-hook-form zod @hookform/resolvers
pnpm add clsx tailwind-merge class-variance-authority
pnpm add react-error-boundary next-themes
```

### Step 2: Configure Project

See stack templates in `stacks/` for specific configuration examples.

### Step 3: Create PRD (Optional but Recommended)

Use `references/prd-template.md` to plan:
- Purpose and mission
- Complexity level
- Essential features
- Design direction
- Color and typography choices

### Step 4: Install shadcn Components FIRST

**CRITICAL: Component Installation Order**

ALWAYS install shadcn components BEFORE writing custom components that import them. This prevents TypeScript errors and failed builds.

❌ **WRONG ORDER** (causes errors):
```bash
# 1. Write PersonDetail.tsx that imports '@/components/ui/card'
# 2. Run pnpm dlx shadcn add card
# 3. Fix TypeScript errors 'Cannot find module @/components/ui/card'
```

✅ **CORRECT ORDER**:
```bash
# 1. Plan which shadcn components you need
#    Example: Card, Avatar, Badge, Separator, Button

# 2. Install ALL required shadcn components FIRST
pnpm dlx shadcn@latest add card avatar badge separator button

# 3. Verify installation
ls src/components/ui/  # Should show: card.tsx, avatar.tsx, badge.tsx, etc.

# 4. NOW write PersonDetail.tsx that imports from '@/components/ui/*'
#    TypeScript will have proper types and components will exist
```

**Planning Checklist**:
1. List all UI components needed for your app
2. Identify which are shadcn components (Card, Button, etc.)
3. Run single `shadcn add` command with all components
4. Verify they exist in `src/components/ui/`
5. Write your custom components that import them

### Step 5: Implement with Best Practices

- Follow shadcn component patterns
- Use OKLCH colors in `:root` CSS variables
- Implement responsive design (mobile-first)
- Add error boundaries
- Optimize images and fonts
- Test Core Web Vitals

## Common Patterns

### Theme Configuration (index.css)

```css
@import 'tailwindcss';

:root {
  /* OKLCH colors - mandatory format */
  --background: oklch(0.97 0.01 75);
  --foreground: oklch(0.25 0.02 55);
  --primary: oklch(0.52 0.14 155);
  --accent: oklch(0.72 0.13 55);

  /* Add more theme variables */
  --radius: 0.75rem;
}

@theme {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-primary: var(--primary);
  --color-accent: var(--accent);

  /* Radius system */
  --radius-sm: calc(var(--radius) * 0.5);
  --radius-md: var(--radius);
  --radius-lg: calc(var(--radius) * 1.5);
}
```

_Note: Uses Tailwind CSS v4+ @import syntax. For v3, use @tailwind directives instead._

### Form Handling

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';

const schema = z.object({
  email: z.string().email(),
  password: z.string().min(8)
});

function LoginForm() {
  const form = useForm({
    resolver: zodResolver(schema),
    defaultValues: { email: '', password: '' }
  });

  async function onSubmit(data: z.infer<typeof schema>) {
    // Handle form submission
  }

  return <form onSubmit={form.handleSubmit(onSubmit)}>...</form>;
}
```

### Data Fetching

```tsx
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';

function UserList() {
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: fetchUsers
  });

  const createUser = useMutation({
    mutationFn: createUserAPI,
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['users'] });
    }
  });

  if (isLoading) return <LoadingSpinner />;
  return <UserGrid users={data} onCreate={createUser.mutate} />;
}
```

## Troubleshooting

### Radix UI Maintenance Concerns

Radix UI is receiving fewer updates. For new projects or migration concerns:
- See `references/radix-migration-guide.md` for Base UI migration path
- shadcn/ui now supports Base UI as an alternative
- React Aria is another excellent option (Adobe-backed, superior accessibility)

### Performance Issues

If app feels slow:
1. Enable React Compiler for automatic memoization
2. Check Core Web Vitals in Chrome DevTools
3. Use `references/performance-checklist.md`
4. Consider code-splitting with TanStack Router's lazy loading

### Build Tool Alternatives

Newer Vite versions with Rolldown bundler may offer faster builds when stable. Monitor for stable releases.

## System Requirements

- **Node.js**: 18+ (or current LTS version)
- **Package Manager**: pnpm recommended for performance
- **OS**: macOS, Linux, or Windows with WSL2

## Next Steps

After scaffolding:
1. Review the stack template for your complexity level
2. Consult design references for styling
3. Create a PRD to plan features and design
4. Implement following best practices
5. Optimize for Core Web Vitals
6. Deploy to production (Vercel, Netlify, etc.)

---

**Remember**: The goal is functional and performant web applications. Start simple, iterate based on user needs, and prioritize user experience over technical complexity.
