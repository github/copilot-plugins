# Default Web App Stack

## Overview

The default web app stack is the most versatile foundation for general-purpose applications. Use this for 80% of web app projects including tools, utilities, simple dashboards, and interactive applications.

## When to Use

- General-purpose web applications
- Interactive tools (calculators, converters, generators)
- Simple CRUD applications
- Prototypes and MVPs
- Most "build me a web app for X" requests

## Core Stack

All packages from the shared Spark App Template foundation:

### Build & Development
```json
{
  "devDependencies": {
    "vite": "^7.3.1",
    "@vitejs/plugin-react-swc": "^4.2.2",
    "typescript": "~5.9.0",
    "@tailwindcss/vite": "^4.1.11",
    "tailwindcss": "^4.1.11",
    "biome": "^2.3.0",
    "@tanstack/router-plugin": "^1.139.13"
  }
}
```

### Core Dependencies
```json
{
  "dependencies": {
    "react": "^19.0.0",
    "react-dom": "^19.0.0",
    "@tanstack/react-router": "^1.139.13",
    "@tanstack/react-query": "^5.90.0",
    "react-hook-form": "^7.54.0",
    "@hookform/resolvers": "^4.1.3",
    "zod": "^3.25.0"
  }
}
```

### UI & Styling
```json
{
  "dependencies": {
    "lucide-react": "^0.484.0",
    "motion": "^11.11.12",
    "sonner": "^2.0.1",
    "next-themes": "^0.4.6",
    "react-error-boundary": "^6.0.0",
    "@radix-ui/colors": "^3.0.0",
    "clsx": "^2.1.1",
    "tailwind-merge": "^3.0.2",
    "class-variance-authority": "^0.7.1"
  }
}
```

### shadcn/ui Components (Install as Needed)
```bash
pnpm dlx shadcn@latest add button
pnpm dlx shadcn@latest add card
pnpm dlx shadcn@latest add input
pnpm dlx shadcn@latest add form
pnpm dlx shadcn@latest add dialog
pnpm dlx shadcn@latest add select
pnpm dlx shadcn@latest add checkbox
pnpm dlx shadcn@latest add label
pnpm dlx shadcn@latest add toast
pnpm dlx shadcn@latest add tabs
```

## Project Setup

### 1. Initialize Project

```bash
# Create Vite project
pnpm create vite@latest my-app --template react-ts
cd my-app

# Install core dependencies
pnpm install

# Add Tailwind
pnpm add -D tailwindcss@latest @tailwindcss/vite

# Add TanStack Router
pnpm add @tanstack/react-router
pnpm add -D @tanstack/router-plugin

# Add TanStack Query
pnpm add @tanstack/react-query

# Add form handling
pnpm add react-hook-form @hookform/resolvers zod

# Initialize shadcn
pnpm dlx shadcn@latest init
# Choose: New York style, neutral base color, CSS variables: yes

# Add common components
pnpm dlx shadcn@latest add button card input form dialog

# Add utilities
pnpm add lucide-react motion sonner next-themes react-error-boundary
pnpm add @radix-ui/colors clsx tailwind-merge class-variance-authority

# Add linting
pnpm add -D biome
```

### 2. Configure Vite (vite.config.ts)

```typescript
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react-swc';
import tailwindcss from '@tailwindcss/vite';
import { TanStackRouterVite } from '@tanstack/router-plugin/vite';
import path from 'path';

export default defineConfig({
  plugins: [
    TanStackRouterVite({
      target: 'react',
      autoCodeSplitting: true,
    }),
    react(),
    tailwindcss(),
  ],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
});
```

### 3. Configure Tailwind (tailwind.config.js)

```javascript
export default {
  content: ['./index.html', './src/**/*.{js,ts,jsx,tsx}'],
  theme: {
    extend: {},
  },
};
```

### 4. Global Styles (src/index.css)

```css
@import 'tailwindcss';

@layer base {
  * {
    @apply border-border;
  }

  body {
    font-family: 'Source Sans 3', sans-serif;
  }

  h1, h2, h3, h4, h5, h6 {
    font-family: 'IBM Plex Sans', sans-serif;
  }
}

:root {
  /* Base colors - OKLCH format mandatory */
  --background: oklch(0.98 0.01 75);
  --foreground: oklch(0.20 0.02 55);

  --card: oklch(1 0 0);
  --card-foreground: oklch(0.20 0.02 55);

  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.20 0.02 55);

  /* Action colors */
  --primary: oklch(0.45 0.15 265);
  --primary-foreground: oklch(0.99 0 0);

  --secondary: oklch(0.94 0.02 85);
  --secondary-foreground: oklch(0.30 0.02 55);

  --accent: oklch(0.68 0.16 30);
  --accent-foreground: oklch(0.20 0.02 55);

  --destructive: oklch(0.55 0.20 25);
  --destructive-foreground: oklch(0.98 0 0);

  /* Supporting colors */
  --muted: oklch(0.95 0.01 75);
  --muted-foreground: oklch(0.48 0.02 55);

  --border: oklch(0.88 0.02 75);
  --input: oklch(0.90 0.01 75);
  --ring: oklch(0.45 0.15 265);

  --radius: 0.5rem;
}

@theme {
  --color-background: var(--background);
  --color-foreground: var(--foreground);
  --color-card: var(--card);
  --color-card-foreground: var(--card-foreground);
  --color-popover: var(--popover);
  --color-popover-foreground: var(--popover-foreground);
  --color-primary: var(--primary);
  --color-primary-foreground: var(--primary-foreground);
  --color-secondary: var(--secondary);
  --color-secondary-foreground: var(--secondary-foreground);
  --color-muted: var(--muted);
  --color-muted-foreground: var(--muted-foreground);
  --color-accent: var(--accent);
  --color-accent-foreground: var(--accent-foreground);
  --color-destructive: var(--destructive);
  --color-destructive-foreground: var(--destructive-foreground);
  --color-border: var(--border);
  --color-input: var(--input);
  --color-ring: var(--ring);

  --radius-sm: calc(var(--radius) * 0.5);
  --radius-md: var(--radius);
  --radius-lg: calc(var(--radius) * 1.5);
  --radius-xl: calc(var(--radius) * 2);
  --radius-2xl: calc(var(--radius) * 3);
  --radius-full: 9999px;
}
```

### 5. Add Google Fonts (index.html)

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>My App</title>

    <!-- Google Fonts - Variable fonts preferred -->
    <link rel="preconnect" href="https://fonts.googleapis.com" />
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
    <link
      href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=Source+Sans+3:wght@400;500;600&display=swap"
      rel="stylesheet"
    />
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

## Design Guidance

### Layout Patterns

**Clean & Functional**: Modern minimalist aesthetic focusing on clarity and usability.

- Use generous whitespace (padding: 6-8, gap: 4-6)
- Card-based layouts for content organization
- Clear visual hierarchy (headings, subheadings, body)
- Subtle shadows for depth (prefer subtle over dramatic)

### Component Usage

**Common Patterns**:
- **Forms**: Use Form + Input + Label + Button components
- **Actions**: Primary Button for main actions, secondary/ghost for others
- **Feedback**: Sonner toast for notifications
- **Overlays**: Dialog for modals, Sheet for mobile drawers
- **Navigation**: Tabs for content switching

### Color Application

Use the OKLCH palette defined in `index.css`:
- **Background**: Main page background
- **Primary**: Key actions, links, focus states
- **Accent**: Highlights, badges, important elements
- **Muted**: Disabled states, placeholders, subtle backgrounds
- **Destructive**: Delete actions, error states

### Typography Scale

```css
/* Suggested scale */
h1: 2rem (32px), font-weight: 700
h2: 1.5rem (24px), font-weight: 600
h3: 1.25rem (20px), font-weight: 600
h4: 1.125rem (18px), font-weight: 600
body: 1rem (16px), font-weight: 400
small: 0.875rem (14px), font-weight: 400
```

## Example Component Structure

### App.tsx (Root)

```tsx
import { ErrorBoundary } from 'react-error-boundary';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { RouterProvider, createRouter } from '@tanstack/react-router';
import { routeTree } from './routeTree.gen';
import { Toaster } from '@/components/ui/sonner';

const queryClient = new QueryClient();
const router = createRouter({ routeTree });

function ErrorFallback({ error }: { error: Error }) {
  return (
    <div className="flex min-h-screen items-center justify-center p-4">
      <div className="text-center">
        <h1 className="text-2xl font-bold">Something went wrong</h1>
        <p className="mt-2 text-muted-foreground">{error.message}</p>
      </div>
    </div>
  );
}

export default function App() {
  return (
    <ErrorBoundary FallbackComponent={ErrorFallback}>
      <QueryClientProvider client={queryClient}>
        <RouterProvider router={router} />
        <Toaster />
      </QueryClientProvider>
    </ErrorBoundary>
  );
}
```

## Performance Optimization

### Code Splitting

TanStack Router handles automatic code-splitting. Each route is lazy-loaded:

```tsx
// routes/dashboard.tsx
export const Route = createFileRoute('/dashboard')({
  component: () => <Dashboard />
});
```

### Image Optimization

```tsx
// Use native lazy loading
<img src="/image.jpg" loading="lazy" alt="Description" />

// Or use responsive images
<img
  srcSet="/image-small.jpg 480w, /image-large.jpg 1024w"
  sizes="(max-width: 768px) 480px, 1024px"
  src="/image-large.jpg"
  alt="Description"
/>
```

### Font Optimization

Already configured with `display=swap` in Google Fonts URL for optimal loading.

## Testing

### Run Development Server

```bash
pnpm dev
```

### Build for Production

```bash
pnpm build
pnpm preview
```

### Lint & Format

```bash
pnpm biome check --write .
```

## Deployment

### Vercel (Recommended)

```bash
# Install Vercel CLI
pnpm add -g vercel

# Deploy
vercel
```

### Netlify

```bash
# Build command: pnpm build
# Publish directory: dist
```

### Other Platforms

Build outputs to `dist/` directory. Deploy as static site on any platform.

## Next Steps

1. Define your app's features and data model
2. Create additional routes in `src/routes/`
3. Build out components in `src/components/`
4. Add data fetching with TanStack Query
5. Implement forms with react-hook-form
6. Test and optimize for Core Web Vitals
