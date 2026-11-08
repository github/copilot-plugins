# Typography Pairings - Spark App Template

## Typography as Identity

Typography is voice made visible. Your font choices communicate personality, professionalism, and brand identity before users read a single word.

## Fonts to Avoid (Overused)

These fonts have become clichés in modern web design:

❌ **Inter** - The default choice for everything. Overused to the point of invisibility.
❌ **Roboto** - Google's everywhere font. Safe but soulless.
❌ **Arial / Helvetica** - Corporate boredom incarnate.
❌ **Space Grotesk** - Was trendy in 2023-2024, now cliché.
❌ **Poppins** - Every Figma tutorial uses this.

**Why avoid them?** They're not bad fonts, they're just everywhere. Your brand deserves distinction.

## Font Personality Guide

Choose fonts based on the character you want to project:

### Serious & Professional
- IBM Plex Sans, Source Sans 3, Work Sans
- Clean, readable, trustworthy
- Use for: B2B SaaS, enterprise tools, financial services

### Creative & Distinctive
- Bricolage Grotesque, Cabinet Grotesk, General Sans
- Unique character, memorable
- Use for: Agencies, design tools, creative platforms

### Technical & Precise
- JetBrains Mono, IBM Plex Mono, Fira Code
- Monospace aesthetic, developer-friendly
- Use for: Developer tools, code editors, technical products

### Editorial & Elegant
- Newsreader, Playfair Display, Spectral
- Timeless serif styling
- Use for: Publications, content platforms, luxury brands

### Modern & Friendly
- DM Sans, Plus Jakarta Sans, Outfit
- Approachable, warm, contemporary
- Use for: Consumer apps, community platforms, social products

### Bold & Expressive
- Darker Grotesque, Lexend, Syne
- Strong personality, attention-grabbing
- Use for: Marketing sites, landing pages, bold brands

## Recommended Pairings

### Pairing 1: Technical & Clean
**Headings**: IBM Plex Sans (600, 700)
**Body**: Source Sans 3 (400, 500, 600)

```html
<link
  href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@600;700&family=Source+Sans+3:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'IBM Plex Sans', sans-serif;
  --font-body: 'Source Sans 3', sans-serif;
}
```

**Character**: Professional, technical, trustworthy
**Best for**: SaaS platforms, B2B tools, developer products
**Why it works**: Both fonts share geometric structure but distinct enough for hierarchy

---

### Pairing 2: Editorial & Sophisticated
**Headings**: Newsreader (600, 700)
**Body**: Source Sans 3 (400, 500, 600)

```html
<link
  href="https://fonts.googleapis.com/css2?family=Newsreader:wght@600;700&family=Source+Sans+3:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'Newsreader', serif;
  --font-body: 'Source Sans 3', sans-serif;
}
```

**Character**: Editorial, classic, authoritative
**Best for**: Publications, content platforms, journalism, blogs
**Why it works**: Serif + sans-serif contrast creates clear hierarchy

---

### Pairing 3: Modern & Distinctive
**Headings**: Bricolage Grotesque (600, 700, 800)
**Body**: DM Sans (400, 500, 600)

```html
<link
  href="https://fonts.googleapis.com/css2?family=Bricolage+Grotesque:wght@600;700;800&family=DM+Sans:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'Bricolage Grotesque', sans-serif;
  --font-body: 'DM Sans', sans-serif;
}
```

**Character**: Modern, distinctive, creative
**Best for**: Design agencies, creative tools, innovative products
**Why it works**: Bricolage's unique character balanced by DM Sans' neutrality

---

### Pairing 4: Developer-Focused
**Headings**: IBM Plex Sans (600, 700)
**Body**: IBM Plex Sans (400, 500)
**Code**: IBM Plex Mono (400, 500)

```html
<link
  href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600;700&family=IBM+Plex+Mono:wght@400;500&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'IBM Plex Sans', sans-serif;
  --font-body: 'IBM Plex Sans', sans-serif;
  --font-mono: 'IBM Plex Mono', monospace;
}

code, pre {
  font-family: var(--font-mono);
}
```

**Character**: Technical, precise, developer-friendly
**Best for**: Code editors, dev tools, technical documentation
**Why it works**: Unified family creates cohesion; mono variant for code

---

### Pairing 5: Warm & Approachable
**Headings**: Outfit (600, 700, 800)
**Body**: Plus Jakarta Sans (400, 500, 600)

```html
<link
  href="https://fonts.googleapis.com/css2?family=Outfit:wght@600;700;800&family=Plus+Jakarta+Sans:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'Outfit', sans-serif;
  --font-body: 'Plus Jakarta Sans', sans-serif;
}
```

**Character**: Friendly, modern, accessible
**Best for**: Consumer apps, community platforms, social products
**Why it works**: Both fonts have rounded, friendly forms

---

### Pairing 6: Bold & Impactful
**Headings**: Syne (700, 800)
**Body**: Work Sans (400, 500, 600)

```html
<link
  href="https://fonts.googleapis.com/css2?family=Syne:wght@700;800&family=Work+Sans:wght@400;500;600&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'Syne', sans-serif;
  --font-body: 'Work Sans', sans-serif;
}
```

**Character**: Bold, attention-grabbing, confident
**Best for**: Marketing sites, landing pages, bold brands
**Why it works**: Syne's distinctive style balanced by Work Sans' neutrality

---

### Pairing 7: Minimalist & Refined
**Headings**: DM Sans (500, 600, 700)
**Body**: DM Sans (400, 500)

```html
<link
  href="https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700&display=swap"
  rel="stylesheet"
/>
```

```css
:root {
  --font-heading: 'DM Sans', sans-serif;
  --font-body: 'DM Sans', sans-serif;
}

h1, h2, h3, h4, h5, h6 {
  font-family: var(--font-heading);
  letter-spacing: -0.02em; /* Tighter tracking for headings */
}
```

**Character**: Clean, minimalist, modern
**Best for**: Minimalist designs, tools, utilities
**Why it works**: Single-font system with weight differentiation

---

## Typography Scale

Use these scales with your chosen pairing:

### Standard Scale (Default)
```css
:root {
  --text-xs: 0.75rem;     /* 12px */
  --text-sm: 0.875rem;    /* 14px */
  --text-base: 1rem;      /* 16px */
  --text-lg: 1.125rem;    /* 18px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 1.875rem;   /* 30px */
  --text-4xl: 2.25rem;    /* 36px */
  --text-5xl: 3rem;       /* 48px */
  --text-6xl: 3.75rem;    /* 60px */
}
```

### Large Scale (Content-Focused)
```css
:root {
  --text-base: 1.125rem;  /* 18px body text */
  --text-lg: 1.25rem;     /* 20px lead text */
  --text-xl: 1.5rem;      /* 24px */
  --text-2xl: 2rem;       /* 32px */
  --text-3xl: 2.5rem;     /* 40px */
  --text-4xl: 3rem;       /* 48px */
  --text-5xl: 3.5rem;     /* 56px */
  --text-6xl: 4rem;       /* 64px */
}
```

### Compact Scale (Data-Dense)
```css
:root {
  --text-xs: 0.6875rem;   /* 11px */
  --text-sm: 0.8125rem;   /* 13px */
  --text-base: 0.9375rem; /* 15px */
  --text-lg: 1.0625rem;   /* 17px */
  --text-xl: 1.25rem;     /* 20px */
  --text-2xl: 1.5rem;     /* 24px */
  --text-3xl: 2rem;       /* 32px */
  --text-4xl: 2.5rem;     /* 40px */
}
```

## Line Height Guidelines

```css
/* Tight - for headings */
.line-height-tight {
  line-height: 1.2;
}

/* Normal - for UI text */
.line-height-normal {
  line-height: 1.5;
}

/* Relaxed - for body content */
.line-height-relaxed {
  line-height: 1.7;
}

/* Loose - for large body text */
.line-height-loose {
  line-height: 1.8;
}
```

**Rule of thumb**:
- Larger text → tighter line-height (headings: 1.1-1.3)
- Smaller text → looser line-height (body: 1.5-1.7)
- Narrow columns → looser line-height
- Wide columns → tighter line-height

## Letter Spacing (Tracking)

```css
/* Tight - for headings, large text */
.tracking-tight {
  letter-spacing: -0.02em;
}

/* Normal - default */
.tracking-normal {
  letter-spacing: 0;
}

/* Wide - for small caps, labels */
.tracking-wide {
  letter-spacing: 0.05em;
}

/* Wider - for uppercase labels */
.tracking-wider {
  letter-spacing: 0.1em;
}
```

**When to use**:
- Large headings (48px+): `-0.02em` to `-0.04em`
- Body text: `0` (default)
- Small uppercase labels: `0.05em` to `0.1em`
- Never positive tracking on lowercase text

## Font Loading Best Practices

### Use Variable Fonts When Available

Variable fonts = one file, multiple weights.

```html
<!-- Traditional (multiple files) -->
<link href="...wght@400;500;600;700" rel="stylesheet" />
<!-- Downloads: 4 files ~400KB total -->

<!-- Variable font (single file) -->
<link href="...wght@400..700" rel="stylesheet" />
<!-- Downloads: 1 file ~150KB -->
```

**Performance win**: Fewer HTTP requests, smaller total size, smooth weight interpolation.

### Font Display Strategy

```css
@font-face {
  font-family: 'Custom Font';
  src: url('/fonts/font.woff2') format('woff2');
  font-display: swap; /* Show fallback immediately, swap when loaded */
  font-weight: 400 700; /* Variable font weight range */
}
```

**Options**:
- `swap` (recommended): Show fallback, swap when loaded
- `optional`: Use custom font only if cached
- `fallback`: Brief invisible period, then show fallback

### Preload Critical Fonts

```html
<head>
  <!-- Preload only the most critical font -->
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
- Heading font (if custom-hosted)
- Above-the-fold text
- Max 1-2 fonts

## Fallback Font Stacks

Define system fallbacks that match your custom font's metrics:

```css
:root {
  /* Sans-serif stacks */
  --font-sans: 'IBM Plex Sans', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;

  /* Serif stacks */
  --font-serif: 'Newsreader', 'Iowan Old Style', 'Apple Garamond', 'Palatino Linotype', 'Times New Roman', serif;

  /* Monospace stacks */
  --font-mono: 'IBM Plex Mono', 'SF Mono', Monaco, 'Cascadia Code', 'Courier New', monospace;
}
```

## Responsive Typography

### Fluid Type Scale

```css
h1 {
  font-size: clamp(2.5rem, 5vw + 1rem, 4rem);
  /* Min: 40px, Scales with viewport, Max: 64px */
}

h2 {
  font-size: clamp(2rem, 4vw + 0.5rem, 3rem);
}

body {
  font-size: clamp(1rem, 2vw, 1.125rem);
}
```

### Breakpoint-Based (Tailwind)

```tsx
<h1 className="text-4xl md:text-5xl lg:text-6xl font-bold">
  Responsive Heading
</h1>
```

## Accessibility Considerations

**Minimum Sizes**:
- Body text: 16px minimum (1rem)
- Small text (captions): 14px minimum (0.875rem)
- Never go below 12px for any text

**Contrast**:
- Body text: 4.5:1 contrast ratio (WCAG AA)
- Large text (18px+ or 14px bold): 3:1 contrast ratio

**Line Length**:
- Optimal: 60-75 characters per line
- Max: 90 characters per line
- Use `max-width: 65ch` for readable content blocks

## Testing Your Typography

**Checklist**:
- [ ] Readable at all sizes (mobile to desktop)
- [ ] Clear hierarchy (can distinguish h1 from h2 from h3)
- [ ] Sufficient contrast (pass WCAG AA)
- [ ] Line length appropriate (not too wide)
- [ ] Loads quickly (< 100ms font load)
- [ ] Fallback fonts match proportions
- [ ] Accessible (zoom to 200% still readable)

**Tools**:
- Google Fonts: fonts.google.com
- Type Scale Calculator: type-scale.com
- Font Pairing: fontpair.co
- Contrast Checker: whocanuse.com

---

**Remember**: Typography is not just decoration—it's the primary interface between your content and your users. Choose wisely, test thoroughly, and iterate based on feedback.
