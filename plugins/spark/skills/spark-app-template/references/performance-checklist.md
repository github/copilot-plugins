# Performance Checklist - Spark App Template

## Core Web Vitals 2026

Google's Core Web Vitals are essential metrics for user experience and SEO ranking.

### Current Metrics

**INP (Interaction to Next Paint)** - Replaced FID in March 2024
- **Target**: < 200ms (Good)
- **What it measures**: Full interaction responsiveness (input delay + processing + paint)
- **Why it matters**: Captures complete user interaction experience, not just first click

**LCP (Largest Contentful Paint)**
- **Target**: < 2.5s (Good)
- **What it measures**: Time for largest content element to render
- **Why it matters**: Perceived loading performance

**CLS (Cumulative Layout Shift)**
- **Target**: < 0.1 (Good)
- **What it measures**: Visual stability (unexpected layout shifts)
- **Why it matters**: User frustration from elements moving during interaction

### Measuring Core Web Vitals

**In Development:**
```bash
# Chrome DevTools
1. Open DevTools (F12)
2. Lighthouse tab
3. Generate report
4. Check Performance score + Web Vitals
```

**In Production:**
```tsx
// Install web-vitals
pnpm add web-vitals

// src/main.tsx
import { onCLS, onINP, onLCP } from 'web-vitals';

onCLS(console.log);
onINP(console.log);
onLCP(console.log);

// Or send to analytics
function sendToAnalytics(metric) {
  fetch('/analytics', {
    method: 'POST',
    body: JSON.stringify(metric),
  });
}

onINP(sendToAnalytics);
```

## React 19 Compiler

### What It Does

The React Compiler automatically memoizes components and values, eliminating manual `useMemo`, `useCallback`, and `React.memo` in most cases.

**Performance Gains**:
- 12% faster initial loads
- 2.5x faster interactions
- Reduces unnecessary re-renders automatically

### Enabling React Compiler

```bash
pnpm add -D babel-plugin-react-compiler
```

```typescript
// vite.config.ts
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

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

### Verification

Check that components are compiled:

```tsx
// You'll still write normal React
function MyComponent() {
  const [count, setCount] = useState(0);

  // Compiler automatically memoizes this
  const expensiveValue = count * 2;

  return <div>{expensiveValue}</div>;
}

// Compiler output (internal):
// - Tracks dependencies automatically
// - Memoizes render when dependencies don't change
// - No manual optimization needed
```

## Image Optimization

### Use Modern Formats

```tsx
// WebP with fallback
<picture>
  <source srcSet="/image.webp" type="image/webp" />
  <source srcSet="/image.avif" type="image/avif" />
  <img src="/image.jpg" alt="Description" loading="lazy" />
</picture>
```

### Responsive Images

```tsx
<img
  srcSet="
    /image-400.jpg 400w,
    /image-800.jpg 800w,
    /image-1200.jpg 1200w
  "
  sizes="(max-width: 640px) 400px, (max-width: 1024px) 800px, 1200px"
  src="/image-800.jpg"
  alt="Description"
  loading="lazy"
/>
```

### Lazy Loading

```tsx
// Native lazy loading (built-in)
<img src="/image.jpg" loading="lazy" alt="Description" />

// Eager load above-the-fold images
<img src="/hero.jpg" loading="eager" alt="Hero" />

// Or priority loading
<img src="/hero.jpg" fetchpriority="high" alt="Hero" />
```

### Image CDN

Use image CDNs for automatic optimization:

```tsx
// Example: Cloudinary
<img
  src="https://res.cloudinary.com/demo/image/upload/w_400,f_auto,q_auto/sample.jpg"
  alt="Optimized"
/>

// w_400 = width 400px
// f_auto = automatic format (WebP/AVIF)
// q_auto = automatic quality
```

## Font Optimization

### Variable Fonts

```html
<!-- One file, all weights -->
<link
  href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400..700&display=swap"
  rel="stylesheet"
/>
```

**Benefits**:
- Single HTTP request
- Smaller total file size
- Smooth weight interpolation

### Font Display Strategy

```css
@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/font.woff2') format('woff2');
  font-display: swap; /* Show fallback immediately */
}
```

**Options**:
- `swap`: Best for most cases (show fallback, swap when loaded)
- `optional`: Only use if cached (best for performance)
- `fallback`: Brief invisible period, then fallback

### Preload Critical Fonts

```html
<head>
  <link
    rel="preload"
    href="/fonts/heading-font.woff2"
    as="font"
    type="font/woff2"
    crossorigin
  />
</head>
```

**Only preload**:
- Hero/heading font
- Above-the-fold text
- Max 1-2 fonts

### Font Subsetting

If self-hosting, subset fonts to include only needed characters:

```bash
# Install pyftsubset
pip install fonttools

# Subset to Latin characters only
pyftsubset font.ttf \
  --output-file=font-subset.woff2 \
  --flavor=woff2 \
  --layout-features=* \
  --unicodes=U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,U+2000-206F,U+2074,U+20AC,U+2122,U+2191,U+2193,U+2212,U+2215,U+FEFF,U+FFFD
```

## Code Splitting

### Route-Based Splitting

TanStack Router handles this automatically:

```tsx
// Each route is automatically code-split
export const Route = createFileRoute('/dashboard')({
  component: Dashboard, // Only loaded when route is accessed
});
```

### Component Lazy Loading

```tsx
import { lazy, Suspense } from 'react';

const HeavyChart = lazy(() => import('./HeavyChart'));

export function Dashboard() {
  return (
    <Suspense fallback={<ChartSkeleton />}>
      <HeavyChart data={data} />
    </Suspense>
  );
}
```

### Dynamic Imports

```tsx
// Load on demand
async function handleExport() {
  const { exportToPDF } = await import('./export-utils');
  exportToPDF(data);
}
```

## Bundle Size Optimization

### Analyze Bundle

```bash
pnpm add -D rollup-plugin-visualizer
```

```typescript
// vite.config.ts
import { visualizer } from 'rollup-plugin-visualizer';

export default defineConfig({
  plugins: [
    visualizer({
      open: true,
      gzipSize: true,
      brotliSize: true,
    }),
  ],
});
```

### Tree-Shaking Tips

```tsx
// ❌ Bad: Imports entire library
import _ from 'lodash';

// ✅ Good: Import only what you need
import debounce from 'lodash/debounce';

// ❌ Bad: Imports all icons
import * as Icons from 'lucide-react';

// ✅ Good: Import specific icons
import { Home, Settings } from 'lucide-react';
```

### Remove Unused Code

```bash
# Check unused dependencies
pnpm exec depcheck

# Remove unused exports
pnpm add -D ts-prune
pnpm exec ts-prune
```

## TanStack Query Optimization

### Caching Strategy

```tsx
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60 * 1000, // 1 minute
      gcTime: 5 * 60 * 1000, // 5 minutes (was cacheTime)
      refetchOnWindowFocus: false, // Disable aggressive refetching
    },
  },
});
```

### Prefetching

```tsx
import { queryOptions, useSuspenseQuery } from '@tanstack/react-query';

const userQueryOptions = queryOptions({
  queryKey: ['user', userId],
  queryFn: () => fetchUser(userId),
});

// Prefetch on hover
<Link
  to="/user/$userId"
  params={{ userId }}
  onMouseEnter={() => {
    queryClient.prefetchQuery(userQueryOptions);
  }}
>
  View Profile
</Link>
```

### Suspense for Data Loading

```tsx
export function UserProfile({ userId }: { userId: string }) {
  // useSuspenseQuery throws promise, letting Suspense handle loading
  const { data } = useSuspenseQuery({
    queryKey: ['user', userId],
    queryFn: () => fetchUser(userId),
  });

  return <div>{data.name}</div>;
}

// Parent component
<Suspense fallback={<ProfileSkeleton />}>
  <UserProfile userId={userId} />
</Suspense>
```

## Animation Performance

### Use GPU-Accelerated Properties

```css
/* ✅ GPU-accelerated (fast) */
.animated {
  transform: translateX(100px);
  opacity: 0.5;
}

/* ❌ CPU-bound (slow) */
.animated {
  margin-left: 100px;
  width: 200px;
}
```

### Debounce Expensive Operations

```tsx
import { debounce } from 'lodash';
import { useEffect, useMemo } from 'react';

export function SearchInput() {
  const [query, setQuery] = useState('');

  const debouncedSearch = useMemo(
    () => debounce((value: string) => {
      // Expensive search operation
      performSearch(value);
    }, 300),
    []
  );

  useEffect(() => {
    return () => debouncedSearch.cancel();
  }, [debouncedSearch]);

  return (
    <input
      value={query}
      onChange={(e) => {
        setQuery(e.target.value);
        debouncedSearch(e.target.value);
      }}
    />
  );
}
```

### Use will-change Sparingly

```css
/* Only during animation */
.animating {
  will-change: transform;
}

/* Remove after animation */
.animated {
  will-change: auto;
}
```

## Rendering Optimization

### Virtual Scrolling (Large Lists)

```bash
pnpm add @tanstack/react-virtual
```

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

### Avoid Inline Functions in Render

```tsx
// ❌ Bad: Creates new function every render
<Button onClick={() => handleClick(item.id)}>Click</Button>

// ✅ Good: Memoized function (if React Compiler not enabled)
const handleClickItem = useCallback(() => {
  handleClick(item.id);
}, [item.id]);

<Button onClick={handleClickItem}>Click</Button>

// ✅ Best: With React Compiler, write naturally
<Button onClick={() => handleClick(item.id)}>Click</Button>
// Compiler auto-memoizes this
```

## Network Optimization

### API Request Batching

```tsx
// Batch multiple queries
const results = useQueries({
  queries: [
    { queryKey: ['user', userId], queryFn: fetchUser },
    { queryKey: ['posts', userId], queryFn: fetchPosts },
    { queryKey: ['comments', userId], queryFn: fetchComments },
  ],
});
```

### Request Deduplication

TanStack Query automatically deduplicates identical concurrent requests.

### Compression

Ensure server sends compressed responses:

```http
Content-Encoding: gzip
Content-Encoding: br (Brotli, even better)
```

## Production Build Optimization

### Vite Build Settings

```typescript
// vite.config.ts
export default defineConfig({
  build: {
    target: 'es2020',
    minify: 'terser',
    rollupOptions: {
      output: {
        manualChunks: {
          vendor: ['react', 'react-dom'],
          router: ['@tanstack/react-router'],
          ui: ['lucide-react', 'motion'],
        },
      },
    },
  },
});
```

### Environment-Specific Code

```tsx
if (import.meta.env.DEV) {
  // Development-only code (stripped in production)
  console.log('Debug info');
}

if (import.meta.env.PROD) {
  // Production-only code
  initAnalytics();
}
```

## Performance Checklist

Use this checklist before deploying:

- [ ] **Core Web Vitals**: INP < 200ms, LCP < 2.5s, CLS < 0.1
- [ ] **React Compiler**: Enabled and verified working
- [ ] **Images**: Using WebP/AVIF, lazy loaded, responsive
- [ ] **Fonts**: Variable fonts, font-display: swap, preload critical
- [ ] **Bundle Size**: Analyzed, < 200KB initial bundle gzipped
- [ ] **Code Splitting**: Routes split, heavy components lazy loaded
- [ ] **Caching**: TanStack Query configured, stale times set
- [ ] **Animations**: GPU-accelerated properties only
- [ ] **Virtual Scrolling**: Implemented for lists > 100 items
- [ ] **Network**: Requests batched, compression enabled
- [ ] **Production Build**: Minified, tree-shaken, optimized chunks

## Monitoring

Set up continuous monitoring:

```tsx
// Track Core Web Vitals
import { onCLS, onINP, onLCP } from 'web-vitals';

const sendToAnalytics = (metric) => {
  // Send to your analytics service
  fetch('/api/analytics', {
    method: 'POST',
    body: JSON.stringify(metric),
  });
};

onCLS(sendToAnalytics);
onINP(sendToAnalytics);
onLCP(sendToAnalytics);
```

**Tools**:
- Google Search Console (real user metrics)
- Chrome DevTools (Lighthouse)
- WebPageTest (comprehensive testing)
- Vercel Analytics (if deploying on Vercel)

---

**Remember**: Performance is a feature, not an afterthought. Budget your performance from the start, measure continuously, and optimize based on real-world data, not assumptions.
