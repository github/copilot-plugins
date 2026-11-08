# Complex Application Stack

## Overview

The complex application stack is designed for sophisticated multi-view applications requiring advanced state management, complex navigation, and robust architecture. Use for SaaS platforms, enterprise tools, and feature-rich applications.

## When to Use

- SaaS platforms
- Enterprise applications
- Multi-user systems
- Complex workflows with many views
- Applications requiring centralized state
- Tools with advanced features and interactions

## Extends Default Stack

This stack includes ALL packages from `default-webapp.md` PLUS the following additive packages.

## Additional Packages

### State Management
```bash
pnpm add zustand  # Lightweight, flexible state management
```

### Date & Time Handling
```bash
pnpm add date-fns
```

### Additional Utilities
```bash
pnpm add uuid  # Generate unique IDs
pnpm add react-resizable-panels  # Resizable layouts (often in shadcn)
```

### Additional shadcn Components
```bash
# Navigation & Layout
pnpm dlx shadcn@latest add navigation-menu
pnpm dlx shadcn@latest add breadcrumb
pnpm dlx shadcn@latest add sidebar
pnpm dlx shadcn@latest add resizable
pnpm dlx shadcn@latest add sheet

# Data & Forms
pnpm dlx shadcn@latest add table
pnpm dlx shadcn@latest add select
pnpm dlx shadcn@latest add combobox
pnpm dlx shadcn@latest add command
pnpm dlx shadcn@latest add calendar
pnpm dlx shadcn@latest add popover
pnpm dlx shadcn@latest add dropdown-menu

# Feedback
pnpm dlx shadcn@latest add alert
pnpm dlx shadcn@latest add alert-dialog
pnpm dlx shadcn@latest add toast
pnpm dlx shadcn@latest add progress
pnpm dlx shadcn@latest add skeleton
```

## Architecture Patterns

### State Management with Zustand

Create stores for different domains:

```tsx
// src/stores/useAuthStore.ts
import { create } from 'zustand';
import { persist } from 'zustand/middleware';

interface User {
  id: string;
  name: string;
  email: string;
}

interface AuthState {
  user: User | null;
  token: string | null;
  login: (user: User, token: string) => void;
  logout: () => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      user: null,
      token: null,
      login: (user, token) => set({ user, token }),
      logout: () => set({ user: null, token: null }),
    }),
    {
      name: 'auth-storage',
    }
  )
);
```

```tsx
// src/stores/useAppStore.ts
import { create } from 'zustand';

interface AppState {
  sidebarOpen: boolean;
  currentView: string;
  toggleSidebar: () => void;
  setView: (view: string) => void;
}

export const useAppStore = create<AppState>((set) => ({
  sidebarOpen: true,
  currentView: 'dashboard',
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setView: (view) => set({ currentView: view }),
}));
```

### Application Layout

```tsx
// src/components/AppLayout.tsx
import { Outlet } from '@tanstack/react-router';
import { Sidebar } from './Sidebar';
import { Header } from './Header';
import { useAppStore } from '@/stores/useAppStore';

export function AppLayout() {
  const sidebarOpen = useAppStore((state) => state.sidebarOpen);

  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      {sidebarOpen && (
        <aside className="w-64 border-r bg-card">
          <Sidebar />
        </aside>
      )}

      {/* Main content */}
      <div className="flex-1">
        <Header />
        <main className="p-6">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
```

## Layout Scrolling Patterns

Complex applications often need independent scrolling areas (sidebar, main content, modals). Getting scrolling right requires understanding flexbox constraints and when to use ScrollArea vs native overflow.

### Core Principle: Flexbox Container Pattern

For scrolling to work in constrained spaces, follow this pattern:

```tsx
<div className="flex flex-col h-screen">  {/* Define height constraint */}
  <header className="flex-shrink-0">Fixed header</header>
  <div className="flex-1 overflow-auto">Scrollable content</div>
  <footer className="flex-shrink-0">Fixed footer</footer>
</div>
```

**Key rules:**
- Parent must have explicit height (`h-screen`, `h-full`, or `flex-1` from its parent)
- Fixed elements use `flex-shrink-0`
- Scrollable element uses `flex-1` to fill remaining space
- Scrollable element needs `overflow-auto` or be a `ScrollArea` component

### Split-Pane Layout (Sidebar + Content)

Most complex apps use this pattern:

```tsx
// Full-height split pane with independent scrolling
export function AppShell() {
  return (
    <div className="flex h-screen overflow-hidden">
      {/* Left Sidebar */}
      <div className="w-80 flex flex-col border-r bg-card">
        <div className="p-4 border-b flex-shrink-0">
          <h2 className="font-bold">Sidebar Header</h2>
        </div>
        <div className="flex-1 overflow-auto">
          <nav className="p-4">
            {/* Sidebar content */}
          </nav>
        </div>
      </div>

      {/* Right Content */}
      <div className="flex-1 flex flex-col overflow-hidden">
        <header className="p-6 border-b bg-card flex-shrink-0">
          <h1 className="text-2xl font-bold">Page Header</h1>
        </header>
        <div className="flex-1 overflow-auto">
          <main className="p-6">
            {/* Main content that scrolls */}
          </main>
        </div>
      </div>
    </div>
  );
}
```

**Why this works:**
- Root uses `h-screen overflow-hidden` to constrain total height
- Both panes use `flex flex-col` to stack header + scrollable area
- Headers use `flex-shrink-0` to prevent compression
- Scrollable areas use `flex-1 overflow-auto` to fill remaining space

### When to Use ScrollArea vs Native Overflow

**Use native `overflow-auto` (recommended):**
- Full-height scrolling areas (sidebars, main content)
- Simpler implementation, more reliable
- Better browser support and performance
- Mobile-friendly (respects system scroll behavior)
- Works consistently with flexbox layouts

**Use shadcn `ScrollArea` (advanced):**
- Small contained regions with custom scrollbar styling
- Modals/dialogs with fixed max-height
- When you need precise scrollbar customization
- Note: Can have edge cases with flex-1, prefer native overflow for full-height

```tsx
{/* Full-height areas - use native overflow (recommended) */}
<div className="flex-1 overflow-auto">
  <div className="p-4">Sidebar or main content</div>
</div>

{/* Small contained areas - ScrollArea acceptable */}
<ScrollArea className="h-[400px]">
  <div className="p-4">Fixed height content</div>
</ScrollArea>
```

### Common Mistakes to Avoid

❌ **Don't use calc() for scroll heights:**
```tsx
// BAD: Brittle, breaks on content changes
<ScrollArea className="h-[calc(100vh-100px)]">
```

✅ **Do use flexbox:**
```tsx
// GOOD: Flexible, adapts to any layout
<div className="flex-1 overflow-auto">
```

❌ **Don't forget parent constraints:**
```tsx
// BAD: flex-1 without parent height does nothing
<div className="flex-1 overflow-auto">
```

✅ **Do establish height on parent:**
```tsx
// GOOD: Parent has h-screen
<div className="flex flex-col h-screen">
  <div className="flex-1 overflow-auto">
```

❌ **Don't skip overflow-hidden on parent:**
```tsx
// BAD: Can cause layout issues
<div className="flex-1 flex flex-col">
  <div className="flex-1 overflow-auto">
```

✅ **Do add overflow-hidden to parent:**
```tsx
// GOOD: Prevents flex-1 from growing beyond bounds
<div className="flex-1 flex flex-col overflow-hidden">
  <div className="flex-1 overflow-auto">
```

### Modal with Scrollable Content

```tsx
<DialogContent className="max-h-[90vh] flex flex-col">
  <DialogHeader className="flex-shrink-0">
    <DialogTitle>Modal Title</DialogTitle>
  </DialogHeader>
  <ScrollArea className="flex-1 pr-4">
    <div className="space-y-4">
      {/* Long scrollable content */}
    </div>
  </ScrollArea>
  <DialogFooter className="flex-shrink-0">
    <Button>Close</Button>
  </DialogFooter>
</DialogContent>
```

### Debugging Scrolling Issues

If scrolling doesn't work:

1. **Check parent height:** Use browser devtools to verify the scrollable element's parent has a constrained height
2. **Verify flex setup:** Ensure `flex flex-col` on parent, `flex-1` on scrollable child
3. **Confirm overflow:** Check if `overflow-auto` or ScrollArea is applied
4. **Look for overflow-hidden:** Parent of scrollable might need `overflow-hidden` to constrain growth

**Quick diagnostic:**
```tsx
// Add temporary red border to see element bounds
<div className="flex-1 overflow-auto border-2 border-red-500">
```

If the red border doesn't have the height you expect, the problem is in the parent flex setup, not the scrolling itself.

### Protected Routes

```tsx
// src/routes/_authenticated.tsx
import { createFileRoute, redirect } from '@tanstack/react-router';
import { useAuthStore } from '@/stores/useAuthStore';

export const Route = createFileRoute('/_authenticated')({
  beforeLoad: async () => {
    const token = useAuthStore.getState().token;
    if (!token) {
      throw redirect({ to: '/login' });
    }
  },
  component: AppLayout,
});
```

```tsx
// src/routes/_authenticated/dashboard.tsx
export const Route = createFileRoute('/_authenticated/dashboard')({
  component: Dashboard,
});
```

## Navigation Patterns

### Sidebar Navigation

```tsx
import { Link } from '@tanstack/react-router';
import { Home, Users, Settings, FileText } from 'lucide-react';
import { cn } from '@/lib/utils';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: Home },
  { name: 'Users', href: '/users', icon: Users },
  { name: 'Documents', href: '/documents', icon: FileText },
  { name: 'Settings', href: '/settings', icon: Settings },
];

export function Sidebar() {
  return (
    <nav className="flex h-full flex-col p-4">
      <div className="mb-8">
        <h1 className="text-xl font-bold">App Name</h1>
      </div>

      <div className="space-y-1">
        {navigation.map((item) => (
          <Link
            key={item.name}
            to={item.href}
            className={({ isActive }) =>
              cn(
                'flex items-center gap-3 rounded-lg px-3 py-2 text-sm transition-colors',
                isActive
                  ? 'bg-primary text-primary-foreground'
                  : 'text-muted-foreground hover:bg-accent hover:text-accent-foreground'
              )
            }
          >
            <item.icon className="h-4 w-4" />
            {item.name}
          </Link>
        ))}
      </div>

      {/* User section at bottom */}
      <div className="mt-auto border-t pt-4">
        <UserDropdown />
      </div>
    </nav>
  );
}
```

### Hierarchical Sidebar Items

When displaying hierarchical data (org charts, nested navigation, file trees) in sidebars, use padding-based indentation to prevent text clipping.

**✅ Correct Pattern:**
```tsx
interface HierarchyItemProps {
  person: { name: string; title: string; initials: string };
  level: number; // 0, 1, 2 for depth
  isSelected: boolean;
}

function HierarchyItem({ person, level, isSelected }: HierarchyItemProps) {
  const paddingLeft = level === 0 ? 'pl-3' : level === 1 ? 'pl-5' : 'pl-7';

  return (
    <button
      className={cn(
        'w-full flex items-center gap-2 py-3 pr-3 rounded-lg text-left',
        paddingLeft, // Use padding, not margin
        isSelected ? 'bg-primary text-primary-foreground' : 'hover:bg-accent'
      )}
    >
      <Avatar className="h-9 w-9 flex-shrink-0">
        <AvatarFallback>{person.initials}</AvatarFallback>
      </Avatar>

      {/* min-w-0 enables truncation to work */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium truncate">{person.name}</p>
        <p className="text-xs text-muted-foreground truncate">{person.title}</p>
      </div>

      {isSelected && <ChevronRight className="h-4 w-4 flex-shrink-0" />}
    </button>
  );
}
```

**Key Rules:**

❌ **Don't use margin for indentation:**
```tsx
<button className="ml-8 p-3">  {/* Reduces internal width, causes clipping */}
```

✅ **Do use padding for indentation:**
```tsx
<button className="p-3 pl-7">  {/* Indentation stays inside button bounds */}
```

❌ **Don't forget min-w-0 on text containers:**
```tsx
<div className="flex-1">  {/* truncate won't work */}
```

✅ **Do use min-w-0 for proper truncation:**
```tsx
<div className="flex-1 min-w-0">  {/* Enables truncate */}
```

**Sidebar Width Recommendations:**
- `w-64` (256px) - Basic flat navigation
- `w-80` (320px) - Standard sidebar with short labels
- `w-96` (384px) - Hierarchical items with 2+ levels (recommended)

**Quick test for clipping:** Add `border-2 border-red-500` to text container. If text overflows the red border, you're missing `min-w-0` or using margin-based indentation.

### Breadcrumbs

```tsx
import {
  Breadcrumb,
  BreadcrumbItem,
  BreadcrumbLink,
  BreadcrumbList,
  BreadcrumbPage,
  BreadcrumbSeparator,
} from '@/components/ui/breadcrumb';
import { useMatches } from '@tanstack/react-router';

export function DynamicBreadcrumbs() {
  const matches = useMatches();

  return (
    <Breadcrumb>
      <BreadcrumbList>
        {matches.map((match, index) => {
          const isLast = index === matches.length - 1;
          return (
            <BreadcrumbItem key={match.pathname}>
              {isLast ? (
                <BreadcrumbPage>{match.pathname}</BreadcrumbPage>
              ) : (
                <>
                  <BreadcrumbLink href={match.pathname}>
                    {match.pathname}
                  </BreadcrumbLink>
                  <BreadcrumbSeparator />
                </>
              )}
            </BreadcrumbItem>
          );
        })}
      </BreadcrumbList>
    </Breadcrumb>
  );
}
```

### Command Palette (⌘K)

```tsx
import { useEffect, useState } from 'react';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
} from '@/components/ui/command';
import { useNavigate } from '@tanstack/react-router';

export function CommandPalette() {
  const [open, setOpen] = useState(false);
  const navigate = useNavigate();

  useEffect(() => {
    const down = (e: KeyboardEvent) => {
      if (e.key === 'k' && (e.metaKey || e.ctrlKey)) {
        e.preventDefault();
        setOpen((open) => !open);
      }
    };

    document.addEventListener('keydown', down);
    return () => document.removeEventListener('keydown', down);
  }, []);

  return (
    <CommandDialog open={open} onOpenChange={setOpen}>
      <CommandInput placeholder="Type a command or search..." />
      <CommandList>
        <CommandEmpty>No results found.</CommandEmpty>
        <CommandGroup heading="Navigation">
          <CommandItem
            onSelect={() => {
              navigate({ to: '/dashboard' });
              setOpen(false);
            }}
          >
            Dashboard
          </CommandItem>
          <CommandItem
            onSelect={() => {
              navigate({ to: '/users' });
              setOpen(false);
            }}
          >
            Users
          </CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
```

## Data Management Patterns

### Optimistic Updates

```tsx
import { useMutation, useQueryClient } from '@tanstack/react-query';

interface Task {
  id: string;
  title: string;
  completed: boolean;
}

export function useToggleTask() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, completed }: { id: string; completed: boolean }) => {
      return api.updateTask(id, { completed });
    },
    onMutate: async ({ id, completed }) => {
      // Cancel outgoing refetches
      await queryClient.cancelQueries({ queryKey: ['tasks'] });

      // Snapshot previous value
      const previous = queryClient.getQueryData(['tasks']);

      // Optimistically update
      queryClient.setQueryData(['tasks'], (old: Task[]) =>
        old.map((task) =>
          task.id === id ? { ...task, completed } : task
        )
      );

      return { previous };
    },
    onError: (_err, _variables, context) => {
      // Rollback on error
      queryClient.setQueryData(['tasks'], context?.previous);
    },
    onSettled: () => {
      // Refetch after mutation
      queryClient.invalidateQueries({ queryKey: ['tasks'] });
    },
  });
}
```

### Pagination

```tsx
import { useQuery } from '@tanstack/react-query';
import { useState } from 'react';
import { Button } from '@/components/ui/button';

export function UserList() {
  const [page, setPage] = useState(1);

  const { data, isLoading } = useQuery({
    queryKey: ['users', page],
    queryFn: () => fetchUsers(page),
    keepPreviousData: true,
  });

  return (
    <div>
      {isLoading ? (
        <LoadingSkeleton />
      ) : (
        <UserTable users={data.users} />
      )}

      <div className="mt-4 flex items-center justify-between">
        <Button
          disabled={page === 1}
          onClick={() => setPage((p) => p - 1)}
        >
          Previous
        </Button>
        <span>Page {page}</span>
        <Button
          disabled={!data.hasMore}
          onClick={() => setPage((p) => p + 1)}
        >
          Next
        </Button>
      </div>
    </div>
  );
}
```

## Complex Forms

### Multi-Step Form

```tsx
import { useState } from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';

const step1Schema = z.object({
  name: z.string().min(2),
  email: z.string().email(),
});

const step2Schema = z.object({
  company: z.string().min(2),
  role: z.string(),
});

export function MultiStepForm() {
  const [step, setStep] = useState(1);
  const [formData, setFormData] = useState({});

  const schema = step === 1 ? step1Schema : step2Schema;
  const form = useForm({
    resolver: zodResolver(schema),
  });

  const onSubmit = (data: any) => {
    if (step === 1) {
      setFormData({ ...formData, ...data });
      setStep(2);
    } else {
      // Final submission
      const finalData = { ...formData, ...data };
      console.log(finalData);
    }
  };

  const progress = (step / 2) * 100;

  return (
    <div className="max-w-md">
      <Progress value={progress} className="mb-8" />

      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-4">
        {step === 1 && (
          <>
            {/* Step 1 fields */}
            <Input {...form.register('name')} placeholder="Name" />
            <Input {...form.register('email')} placeholder="Email" />
          </>
        )}

        {step === 2 && (
          <>
            {/* Step 2 fields */}
            <Input {...form.register('company')} placeholder="Company" />
            <Input {...form.register('role')} placeholder="Role" />
          </>
        )}

        <div className="flex justify-between">
          {step > 1 && (
            <Button type="button" variant="outline" onClick={() => setStep(step - 1)}>
              Back
            </Button>
          )}
          <Button type="submit">
            {step === 2 ? 'Submit' : 'Next'}
          </Button>
        </div>
      </form>
    </div>
  );
}
```

## Performance Optimization

### Code Splitting by Route

TanStack Router handles this automatically. Each route is lazy-loaded.

### Virtual Scrolling for Large Lists

```tsx
import { useVirtualizer } from '@tanstack/react-virtual';
import { useRef } from 'react';

export function VirtualList({ items }: { items: any[] }) {
  const parentRef = useRef<HTMLDivElement>(null);

  const virtualizer = useVirtualizer({
    count: items.length,
    getScrollElement: () => parentRef.current,
    estimateSize: () => 50,
  });

  return (
    <div ref={parentRef} className="h-[600px] overflow-auto">
      <div
        style={{
          height: `${virtualizer.getTotalSize()}px`,
          position: 'relative',
        }}
      >
        {virtualizer.getVirtualItems().map((virtualItem) => (
          <div
            key={virtualItem.key}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              width: '100%',
              height: `${virtualItem.size}px`,
              transform: `translateY(${virtualItem.start}px)`,
            }}
          >
            {items[virtualItem.index].name}
          </div>
        ))}
      </div>
    </div>
  );
}
```

### React Compiler

Enable for automatic memoization:

```bash
pnpm add -D babel-plugin-react-compiler
```

Configure in Vite:
```typescript
// vite.config.ts
export default defineConfig({
  plugins: [
    react({
      babel: {
        plugins: [
          ['babel-plugin-react-compiler', {}],
        ],
      },
    }),
  ],
});
```

## Testing Strategy

### Component Testing

```tsx
import { render, screen } from '@testing-library/react';
import { Button } from './button';

test('renders button with text', () => {
  render(<Button>Click me</Button>);
  expect(screen.getByText('Click me')).toBeInTheDocument();
});
```

### E2E Testing (Playwright)

```bash
pnpm add -D @playwright/test
```

```typescript
// tests/login.spec.ts
import { test, expect } from '@playwright/test';

test('user can log in', async ({ page }) => {
  await page.goto('/login');
  await page.fill('[name="email"]', 'user@example.com');
  await page.fill('[name="password"]', 'password');
  await page.click('button[type="submit"]');
  await expect(page).toHaveURL('/dashboard');
});
```

## Security Considerations

- Validate all inputs with Zod
- Sanitize user-generated content
- Use HTTPS in production
- Implement CSRF protection
- Set secure cookie flags
- Use environment variables for secrets
- Implement rate limiting
- Regular dependency updates

## Deployment

### Environment Variables

```bash
# .env.production
VITE_API_URL=https://api.production.com
VITE_APP_URL=https://app.production.com
```

Access in code:
```typescript
const API_URL = import.meta.env.VITE_API_URL;
```

### Build Optimization

```bash
# Production build
pnpm build

# Analyze bundle size
pnpm add -D rollup-plugin-visualizer
```

## Next Steps

1. Define application architecture and feature domains
2. Set up Zustand stores for global state
3. Create protected route structure
4. Implement authentication flow
5. Build core navigation (sidebar, command palette)
6. Develop feature modules
7. Add comprehensive error handling
8. Optimize performance (code splitting, caching)
9. Implement testing strategy
10. Deploy to production
