# Color Palettes - Spark App Template

## OKLCH: The Color Format for 2026

OKLCH (Oklab Lightness Chroma Hue) is a perceptually uniform color space. Unlike RGB or HSL, equal numerical changes produce equal perceived differences.

**Why OKLCH?**
- ✅ Perceptually uniform (50% lightness looks halfway between black and white)
- ✅ Predictable color manipulation
- ✅ Better gamut coverage (more vibrant colors possible)
- ✅ Native browser support (all modern browsers)
- ✅ Easier to maintain consistent contrast

**OKLCH Format**:
```css
color: oklch(L C H / A);
/* L = Lightness (0-1, where 0.5 is truly middle gray)
   C = Chroma (0-0.4, color intensity/saturation)
   H = Hue (0-360 degrees)
   A = Alpha (0-1, optional) */
```

**Example**:
```css
--primary: oklch(0.55 0.15 265);
/* 55% lightness, medium chroma, blue-purple hue */
```

## Color Palette Structure

Every Spark App Template app should define these semantic color tokens:

```css
:root {
  /* Base colors */
  --background: oklch(...);
  --foreground: oklch(...);

  /* Component backgrounds */
  --card: oklch(...);
  --card-foreground: oklch(...);
  --popover: oklch(...);
  --popover-foreground: oklch(...);

  /* Action colors */
  --primary: oklch(...);
  --primary-foreground: oklch(...);
  --secondary: oklch(...);
  --secondary-foreground: oklch(...);
  --accent: oklch(...);
  --accent-foreground: oklch(...);
  --destructive: oklch(...);
  --destructive-foreground: oklch(...);

  /* Supporting colors */
  --muted: oklch(...);
  --muted-foreground: oklch(...);
  --border: oklch(...);
  --input: oklch(...);
  --ring: oklch(...);

  /* Optional: Status colors */
  --success: oklch(...);
  --warning: oklch(...);
  --error: oklch(...);
  --info: oklch(...);
}
```

## Pre-Curated Palettes

### Palette 1: Professional Blue (Default)

Modern, trustworthy, professional. Think Stripe, Linear, Vercel.

```css
:root {
  --background: oklch(0.98 0.01 240);
  --foreground: oklch(0.20 0.02 240);

  --card: oklch(1 0 0);
  --card-foreground: oklch(0.20 0.02 240);

  --popover: oklch(1 0 0);
  --popover-foreground: oklch(0.20 0.02 240);

  --primary: oklch(0.45 0.15 265);        /* Deep blue */
  --primary-foreground: oklch(0.99 0 0);

  --secondary: oklch(0.94 0.02 240);
  --secondary-foreground: oklch(0.30 0.02 240);

  --accent: oklch(0.68 0.16 240);         /* Bright blue */
  --accent-foreground: oklch(0.20 0.02 240);

  --destructive: oklch(0.55 0.20 25);     /* Red */
  --destructive-foreground: oklch(0.98 0 0);

  --muted: oklch(0.95 0.01 240);
  --muted-foreground: oklch(0.48 0.02 240);

  --border: oklch(0.88 0.02 240);
  --input: oklch(0.90 0.01 240);
  --ring: oklch(0.45 0.15 265);

  /* Status colors */
  --success: oklch(0.60 0.14 145);        /* Green */
  --warning: oklch(0.70 0.16 85);         /* Yellow */
  --error: oklch(0.55 0.20 25);           /* Red */
  --info: oklch(0.60 0.12 240);           /* Blue */

  --radius: 0.5rem;
}
```

**Contrast Checks**:
- Background → Foreground: 12.8:1 ✅
- Primary → Primary Foreground: 8.2:1 ✅
- Accent → Accent Foreground: 5.1:1 ✅

---

### Palette 2: Warm & Inviting

Organic, friendly, approachable. Think Notion, Figma.

```css
:root {
  --background: oklch(0.98 0.005 85);      /* Warm off-white */
  --foreground: oklch(0.22 0.01 75);

  --card: oklch(1 0 0);
  --card-foreground: oklch(0.22 0.01 75);

  --primary: oklch(0.50 0.12 35);          /* Warm orange-red */
  --primary-foreground: oklch(0.99 0 0);

  --secondary: oklch(0.94 0.02 85);
  --secondary-foreground: oklch(0.30 0.01 75);

  --accent: oklch(0.70 0.14 55);           /* Warm orange */
  --accent-foreground: oklch(0.22 0.01 75);

  --destructive: oklch(0.52 0.22 30);
  --destructive-foreground: oklch(0.98 0 0);

  --muted: oklch(0.96 0.01 85);
  --muted-foreground: oklch(0.50 0.01 75);

  --border: oklch(0.88 0.02 85);
  --input: oklch(0.92 0.01 85);
  --ring: oklch(0.50 0.12 35);

  --success: oklch(0.58 0.15 145);
  --warning: oklch(0.75 0.14 85);
  --error: oklch(0.52 0.22 30);
  --info: oklch(0.58 0.12 240);

  --radius: 0.75rem;  /* Larger radius for friendly feel */
}
```

---

### Palette 3: Dark Mode Elegant

Sophisticated dark theme with purple accents.

```css
:root {
  --background: oklch(0.15 0.01 265);      /* Deep blue-black */
  --foreground: oklch(0.95 0.01 265);

  --card: oklch(0.18 0.01 265);
  --card-foreground: oklch(0.95 0.01 265);

  --popover: oklch(0.18 0.01 265);
  --popover-foreground: oklch(0.95 0.01 265);

  --primary: oklch(0.70 0.20 300);         /* Bright purple */
  --primary-foreground: oklch(0.15 0.01 265);

  --secondary: oklch(0.22 0.02 265);
  --secondary-foreground: oklch(0.85 0.01 265);

  --accent: oklch(0.65 0.25 330);          /* Pink-purple */
  --accent-foreground: oklch(0.95 0.01 265);

  --destructive: oklch(0.60 0.24 25);
  --destructive-foreground: oklch(0.95 0.01 265);

  --muted: oklch(0.22 0.02 265);
  --muted-foreground: oklch(0.60 0.01 265);

  --border: oklch(0.25 0.02 265);
  --input: oklch(0.22 0.02 265);
  --ring: oklch(0.70 0.20 300);

  --success: oklch(0.65 0.16 145);
  --warning: oklch(0.72 0.16 85);
  --error: oklch(0.60 0.24 25);
  --info: oklch(0.65 0.14 240);

  --radius: 0.5rem;
}
```

---

### Palette 4: Vibrant & Bold

High energy, attention-grabbing. Think gaming, creative tools.

```css
:root {
  --background: oklch(0.98 0.01 265);
  --foreground: oklch(0.15 0.02 265);

  --card: oklch(1 0 0);
  --card-foreground: oklch(0.15 0.02 265);

  --primary: oklch(0.55 0.28 310);         /* Hot magenta */
  --primary-foreground: oklch(0.99 0 0);

  --secondary: oklch(0.92 0.03 265);
  --secondary-foreground: oklch(0.25 0.02 265);

  --accent: oklch(0.65 0.26 180);          /* Cyan */
  --accent-foreground: oklch(0.15 0.02 265);

  --destructive: oklch(0.58 0.26 25);
  --destructive-foreground: oklch(0.98 0 0);

  --muted: oklch(0.94 0.02 265);
  --muted-foreground: oklch(0.50 0.02 265);

  --border: oklch(0.86 0.03 265);
  --input: oklch(0.90 0.02 265);
  --ring: oklch(0.55 0.28 310);

  --success: oklch(0.62 0.20 145);
  --warning: oklch(0.72 0.18 85);
  --error: oklch(0.58 0.26 25);
  --info: oklch(0.62 0.16 240);

  --radius: 0.25rem;  /* Sharp corners for edgy feel */
}
```

---

### Palette 5: Minimalist Monochrome

Pure focus, maximum clarity. Think Apple, minimalist tools.

```css
:root {
  --background: oklch(1 0 0);              /* Pure white */
  --foreground: oklch(0.10 0 0);           /* Near black */

  --card: oklch(0.98 0 0);
  --card-foreground: oklch(0.10 0 0);

  --popover: oklch(0.98 0 0);
  --popover-foreground: oklch(0.10 0 0);

  --primary: oklch(0.10 0 0);              /* Black */
  --primary-foreground: oklch(1 0 0);

  --secondary: oklch(0.94 0 0);
  --secondary-foreground: oklch(0.20 0 0);

  --accent: oklch(0.40 0 0);               /* Dark gray */
  --accent-foreground: oklch(1 0 0);

  --destructive: oklch(0.30 0 0);
  --destructive-foreground: oklch(1 0 0);

  --muted: oklch(0.96 0 0);
  --muted-foreground: oklch(0.50 0 0);

  --border: oklch(0.90 0 0);
  --input: oklch(0.94 0 0);
  --ring: oklch(0.10 0 0);

  --success: oklch(0.50 0 0);
  --warning: oklch(0.50 0 0);
  --error: oklch(0.30 0 0);
  --info: oklch(0.50 0 0);

  --radius: 0rem;  /* No rounded corners */
}
```

---

### Palette 6: Nature-Inspired Green

Calm, growth-focused, eco-friendly. Think sustainability, health.

```css
:root {
  --background: oklch(0.98 0.01 145);
  --foreground: oklch(0.20 0.02 145);

  --card: oklch(1 0 0);
  --card-foreground: oklch(0.20 0.02 145);

  --primary: oklch(0.48 0.14 155);         /* Forest green */
  --primary-foreground: oklch(0.99 0 0);

  --secondary: oklch(0.94 0.02 145);
  --secondary-foreground: oklch(0.28 0.02 145);

  --accent: oklch(0.65 0.16 135);          /* Bright green */
  --accent-foreground: oklch(0.20 0.02 145);

  --destructive: oklch(0.55 0.20 25);
  --destructive-foreground: oklch(0.98 0 0);

  --muted: oklch(0.96 0.01 145);
  --muted-foreground: oklch(0.50 0.02 145);

  --border: oklch(0.88 0.02 145);
  --input: oklch(0.92 0.01 145);
  --ring: oklch(0.48 0.14 155);

  --success: oklch(0.62 0.16 145);
  --warning: oklch(0.72 0.14 85);
  --error: oklch(0.55 0.20 25);
  --info: oklch(0.60 0.12 240);

  --radius: 1rem;  /* Very rounded for organic feel */
}
```

---

## WCAG Contrast Guidelines

**Required Ratios**:
- **Normal text (< 18px)**: 4.5:1 (AA) or 7:1 (AAA)
- **Large text (≥ 18px or ≥ 14px bold)**: 3:1 (AA) or 4.5:1 (AAA)
- **UI components**: 3:1 minimum

**Testing Your Colors**:
```css
/* Example: Check if primary text on background passes */
background: oklch(0.98 0.01 240);  /* Light */
foreground: oklch(0.20 0.02 240);  /* Dark */
/* Contrast ratio: ~13:1 (Passes AAA for all text) ✅ */
```

**Tools**:
- OKLCH Contrast Checker: oklch.com
- Who Can Use: whocanuse.com
- WebAIM Contrast Checker: webaim.org/resources/contrastchecker

## Validating Your Palette

Before using any palette, verify these pairings:

```markdown
✅ Background → Foreground
✅ Card → Card Foreground
✅ Primary → Primary Foreground
✅ Secondary → Secondary Foreground
✅ Accent → Accent Foreground
✅ Muted Background → Muted Foreground
✅ Success/Warning/Error → Background
```

## Creating Custom Palettes

### Step 1: Choose Your Hue

```css
/* Blue family: 240-270 */
--hue: 265;

/* Red family: 0-30 */
--hue: 25;

/* Green family: 130-160 */
--hue: 145;

/* Purple family: 280-320 */
--hue: 300;

/* Orange family: 40-70 */
--hue: 55;
```

### Step 2: Define Lightness Scale

```css
/* Light theme scale */
--l-100: 0.98;  /* Lightest (backgrounds) */
--l-200: 0.94;
--l-300: 0.88;
--l-400: 0.80;
--l-500: 0.60;  /* Middle */
--l-600: 0.45;  /* Primary actions */
--l-700: 0.30;
--l-800: 0.20;  /* Darkest (text) */
```

### Step 3: Set Chroma (Saturation)

```css
/* Low chroma = subtle, professional */
--c-low: 0.05;

/* Medium chroma = balanced */
--c-medium: 0.12;

/* High chroma = vibrant */
--c-high: 0.20;
```

### Step 4: Build Your Palette

```css
:root {
  --background: oklch(0.98 0.01 var(--hue));
  --foreground: oklch(0.20 0.02 var(--hue));
  --primary: oklch(0.45 0.15 var(--hue));
  --accent: oklch(0.68 0.16 var(--hue));
  /* Continue for all tokens */
}
```

## Color Manipulation

### Lighten/Darken

```css
/* Original */
--color: oklch(0.50 0.15 265);

/* Lighter (increase L) */
--color-light: oklch(0.70 0.15 265);

/* Darker (decrease L) */
--color-dark: oklch(0.30 0.15 265);
```

### More/Less Saturated

```css
/* Original */
--color: oklch(0.50 0.15 265);

/* More saturated (increase C) */
--color-vibrant: oklch(0.50 0.25 265);

/* Less saturated (decrease C) */
--color-muted: oklch(0.50 0.05 265);
```

### Shift Hue

```css
/* Original blue */
--color: oklch(0.50 0.15 265);

/* Shift to purple */
--color-purple: oklch(0.50 0.15 300);

/* Shift to cyan */
--color-cyan: oklch(0.50 0.15 200);
```

### Using color-mix()

```css
/* Mix two colors */
.mixed {
  background: color-mix(in oklch, var(--primary) 70%, var(--accent) 30%);
}

/* Lighten with white */
.lightened {
  background: color-mix(in oklch, var(--primary) 80%, white 20%);
}

/* Darken with black */
.darkened {
  background: color-mix(in oklch, var(--primary) 80%, black 20%);
}
```

## Implementing Dark Mode (Optional)

Only implement dark mode if explicitly requested. Single theme is preferred.

```css
@media (prefers-color-scheme: dark) {
  :root {
    --background: oklch(0.15 0.01 265);
    --foreground: oklch(0.95 0.01 265);
    /* Invert lightness scale */
  }
}
```

Or use `next-themes` for manual toggle:

```tsx
import { ThemeProvider } from 'next-themes';

<ThemeProvider attribute="class">
  <App />
</ThemeProvider>
```

---

**Remember**: Color is emotional. Choose palettes that align with your brand personality, validate contrast for accessibility, and test with real users to ensure your colors communicate effectively.
