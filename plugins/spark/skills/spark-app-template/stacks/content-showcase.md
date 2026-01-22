# Content Showcase Stack

## Overview

The content showcase stack is optimized for content-focused applications including marketing sites, portfolios, blogs, documentation sites, and landing pages where typography and reading experience are paramount.

## When to Use

- Marketing websites and landing pages
- Portfolio sites
- Blog platforms
- Documentation sites
- Content-heavy applications
- Informational websites

## Extends Default Stack

This stack includes ALL packages from `default-webapp.md` PLUS the following additive packages.

## Additional Packages

### Content Processing
```bash
pnpm add marked  # Markdown to HTML
pnpm add dompurify  # Sanitize HTML (security)
```

### Additional shadcn Components
```bash
# Content components
pnpm dlx shadcn@latest add separator
pnpm dlx shadcn@latest add breadcrumb
pnpm dlx shadcn@latest add navigation-menu
pnpm dlx shadcn@latest add accordion
```

## Design Guidance

### Typography-First Design

Content showcases live or die by their typography. The reading experience must be exceptional.

**Type Scale** (larger than default):
```css
/* Add to index.css */
h1: 3.5rem (56px), line-height: 1.1, font-weight: 700
h2: 2.5rem (40px), line-height: 1.2, font-weight: 600
h3: 2rem (32px), line-height: 1.3, font-weight: 600
h4: 1.5rem (24px), line-height: 1.4, font-weight: 600
body: 1.125rem (18px), line-height: 1.7, font-weight: 400
lead: 1.25rem (20px), line-height: 1.6, font-weight: 400
```

**Line Length**: Optimal reading is 60-75 characters per line
```css
.prose {
  max-width: 65ch;
}
```

**Vertical Rhythm**: Consistent spacing between elements
```css
/* Spacing scale */
h1: mb-6
h2: mt-12 mb-4
h3: mt-8 mb-3
p: mb-4
```

### Distinctive Font Pairings

**Recommended for Content**:

**Option 1: Editorial**
- Headings: **Playfair Display** (serif, elegant)
- Body: **Source Sans 3** (sans-serif, readable)
- Use: Magazine-style, luxury brands, editorial content

**Option 2: Modern Technical**
- Headings: **Space Grotesk** (geometric, modern)
- Body: **IBM Plex Sans** (clean, professional)
- Use: Tech companies, startups, modern brands

**Option 3: Classic**
- Headings: **Newsreader** (serif, traditional)
- Body: **Source Sans 3** (sans-serif)
- Use: Publications, journalism, classic brands

Update `index.html`:
```html
<!-- Example: Editorial pairing -->
<link
  href="https://fonts.googleapis.com/css2?family=Playfair+Display:wght@600;700;800&family=Source+Sans+3:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

Update `index.css`:
```css
body {
  font-family: 'Source Sans 3', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  font-family: 'Playfair Display', serif;
}
```

### Color for Content

**Muted, Sophisticated Palette**:
```css
:root {
  /* Warm, readable background */
  --background: oklch(0.98 0.005 85);
  --foreground: oklch(0.22 0.01 75);

  /* Subtle, elegant primary */
  --primary: oklch(0.40 0.08 240);
  --primary-foreground: oklch(0.99 0 0);

  /* Warm accent for links */
  --accent: oklch(0.55 0.12 35);
  --accent-foreground: oklch(0.22 0.01 75);

  /* Larger radius for softer feel */
  --radius: 0.75rem;
}
```

### Whitespace & Breathing Room

Content needs generous spacing:
- **Section padding**: py-16 to py-24 (mobile), py-24 to py-32 (desktop)
- **Content width**: max-w-4xl or max-w-5xl centered
- **Grid gaps**: gap-8 to gap-12
- **Margins**: Generous margins around content blocks

## Layout Patterns

### Hero Section

```tsx
export function Hero() {
  return (
    <section className="relative py-20 md:py-32">
      <div className="container max-w-6xl">
        <div className="mx-auto max-w-3xl text-center">
          <h1 className="text-5xl font-bold tracking-tight md:text-6xl lg:text-7xl">
            Build Beautiful Web Experiences
          </h1>
          <p className="mt-6 text-xl leading-relaxed text-muted-foreground">
            A comprehensive toolkit for creating production-ready applications
            with exceptional design and performance.
          </p>
          <div className="mt-10 flex items-center justify-center gap-4">
            <Button size="lg">Get Started</Button>
            <Button size="lg" variant="outline">Learn More</Button>
          </div>
        </div>
      </div>
    </section>
  );
}
```

### Content Grid (Features, Services, etc.)

```tsx
import { Card, CardContent } from '@/components/ui/card';

const features = [
  {
    title: 'Fast Performance',
    description: 'Built with modern tools for lightning-fast load times.',
    icon: Zap
  },
  // ...
];

export function Features() {
  return (
    <section className="py-24">
      <div className="container max-w-6xl">
        <div className="text-center">
          <h2 className="text-4xl font-bold">Why Choose Us</h2>
          <p className="mt-4 text-xl text-muted-foreground">
            Everything you need to build exceptional web applications
          </p>
        </div>

        <div className="mt-16 grid gap-8 md:grid-cols-2 lg:grid-cols-3">
          {features.map((feature) => (
            <Card key={feature.title} className="border-2">
              <CardContent className="p-6">
                <feature.icon className="h-10 w-10 text-primary" />
                <h3 className="mt-4 text-xl font-semibold">{feature.title}</h3>
                <p className="mt-2 leading-relaxed text-muted-foreground">
                  {feature.description}
                </p>
              </CardContent>
            </Card>
          ))}
        </div>
      </div>
    </section>
  );
}
```

### Long-Form Content (Blog Post, Article)

```tsx
import { Separator } from '@/components/ui/separator';

export function Article({ content }: { content: string }) {
  return (
    <article className="py-12">
      <div className="container max-w-4xl">
        {/* Article header */}
        <header className="mb-12">
          <h1 className="text-5xl font-bold">Article Title</h1>
          <div className="mt-4 flex items-center gap-4 text-muted-foreground">
            <time>January 20, 2026</time>
            <Separator orientation="vertical" className="h-4" />
            <span>5 min read</span>
          </div>
        </header>

        {/* Article content */}
        <div
          className="prose prose-lg max-w-none"
          dangerouslySetInnerHTML={{ __html: content }}
        />
      </div>
    </article>
  );
}
```

## Markdown Processing

### Convert Markdown to HTML

```tsx
import { marked } from 'marked';
import DOMPurify from 'dompurify';

// Configure marked for better output
marked.setOptions({
  gfm: true, // GitHub Flavored Markdown
  breaks: true, // Convert \n to <br>
});

export function renderMarkdown(markdown: string): string {
  const html = marked(markdown);
  return DOMPurify.sanitize(html);
}
```

### Markdown Component

```tsx
interface MarkdownProps {
  content: string;
}

export function Markdown({ content }: MarkdownProps) {
  const html = renderMarkdown(content);

  return (
    <div
      className="prose prose-lg max-w-none prose-headings:font-bold prose-h1:text-4xl prose-h2:text-3xl prose-h3:text-2xl prose-p:leading-relaxed prose-a:text-primary prose-a:no-underline hover:prose-a:underline prose-img:rounded-lg"
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}
```

## Navigation Patterns

### Header Navigation

```tsx
import { NavigationMenu, NavigationMenuItem, NavigationMenuLink, NavigationMenuList } from '@/components/ui/navigation-menu';
import { Button } from '@/components/ui/button';

export function Header() {
  return (
    <header className="sticky top-0 z-50 border-b bg-background/95 backdrop-blur">
      <div className="container flex h-16 items-center justify-between">
        <div className="flex items-center gap-8">
          <a href="/" className="text-xl font-bold">Brand</a>

          <NavigationMenu className="hidden md:flex">
            <NavigationMenuList>
              <NavigationMenuItem>
                <NavigationMenuLink href="/features">Features</NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink href="/pricing">Pricing</NavigationMenuLink>
              </NavigationMenuItem>
              <NavigationMenuItem>
                <NavigationMenuLink href="/blog">Blog</NavigationMenuLink>
              </NavigationMenuItem>
            </NavigationMenuList>
          </NavigationMenu>
        </div>

        <div className="flex items-center gap-4">
          <Button variant="ghost">Sign In</Button>
          <Button>Get Started</Button>
        </div>
      </div>
    </header>
  );
}
```

### Footer

```tsx
export function Footer() {
  return (
    <footer className="border-t">
      <div className="container py-12">
        <div className="grid gap-8 md:grid-cols-4">
          <div>
            <h3 className="font-bold">Product</h3>
            <ul className="mt-4 space-y-2 text-muted-foreground">
              <li><a href="/features">Features</a></li>
              <li><a href="/pricing">Pricing</a></li>
              <li><a href="/changelog">Changelog</a></li>
            </ul>
          </div>
          {/* More columns */}
        </div>

        <div className="mt-12 border-t pt-8 text-center text-sm text-muted-foreground">
          <p>&copy; 2026 Your Company. All rights reserved.</p>
        </div>
      </div>
    </footer>
  );
}
```

## SEO Optimization

### Meta Tags (in route components)

```tsx
// src/routes/index.tsx
import { createFileRoute } from '@tanstack/react-router';
import { Helmet } from 'react-helmet-async'; // Install if needed

export const Route = createFileRoute('/')({
  component: HomePage,
});

function HomePage() {
  return (
    <>
      <Helmet>
        <title>Your App - Tagline</title>
        <meta name="description" content="Compelling description under 160 characters" />
        <meta property="og:title" content="Your App" />
        <meta property="og:description" content="Description for social sharing" />
        <meta property="og:image" content="/og-image.jpg" />
        <meta name="twitter:card" content="summary_large_image" />
      </Helmet>

      {/* Page content */}
    </>
  );
}
```

## Performance for Content Sites

### Image Optimization

```tsx
// Use WebP with fallbacks
<picture>
  <source srcSet="/image.webp" type="image/webp" />
  <source srcSet="/image.jpg" type="image/jpeg" />
  <img src="/image.jpg" alt="Description" loading="lazy" />
</picture>
```

### Font Loading Strategy

Already using `display=swap` for optimal font loading. Consider:
```html
<!-- Preload critical fonts -->
<link
  rel="preload"
  href="/fonts/display-font.woff2"
  as="font"
  type="font/woff2"
  crossorigin
/>
```

### Code Splitting

Content pages should load instantly:
```tsx
// Lazy load heavy components
const HeavyComponent = lazy(() => import('./HeavyComponent'));

<Suspense fallback={<LoadingSpinner />}>
  <HeavyComponent />
</Suspense>
```

## Accessibility

- Use semantic HTML (`<article>`, `<section>`, `<nav>`, `<header>`, `<footer>`)
- Proper heading hierarchy (don't skip levels)
- Alt text for all images
- Keyboard navigation for interactive elements
- Focus states visible on all links/buttons
- Color contrast meets WCAG AA

## Responsive Typography

```css
/* Fluid typography scale */
h1 {
  font-size: clamp(2.5rem, 5vw, 3.5rem);
}

h2 {
  font-size: clamp(2rem, 4vw, 2.5rem);
}

body {
  font-size: clamp(1rem, 2vw, 1.125rem);
}
```

## Next Steps

1. Define your content structure and pages
2. Choose typography pairing that matches brand
3. Create reusable layout components
4. Set up markdown processing if needed
5. Optimize images and fonts
6. Add SEO meta tags to all pages
7. Test reading experience on multiple devices
