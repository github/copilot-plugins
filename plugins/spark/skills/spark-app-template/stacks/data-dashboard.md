# Data Dashboard Stack

## Overview

The data dashboard stack is optimized for applications that display and visualize data, including analytics dashboards, admin panels, reporting tools, and data-heavy interfaces.

## When to Use

- Analytics dashboards
- Admin panels
- Business intelligence tools
- Data visualization applications
- Monitoring and reporting interfaces
- CRM or ERP interfaces

## Extends Default Stack

This stack includes ALL packages from `default-webapp.md` PLUS the following additive packages.

## Additional Packages

### Data Visualization
```bash
pnpm add recharts
pnpm add d3  # For advanced custom visualizations
```

### Date Handling
```bash
pnpm add date-fns
pnpm add react-day-picker  # Often included with shadcn calendar
```

### Additional shadcn Components
```bash
# Data display components
pnpm dlx shadcn@latest add table
pnpm dlx shadcn@latest add calendar
pnpm dlx shadcn@latest add select
pnpm dlx shadcn@latest add badge
pnpm dlx shadcn@latest add separator
pnpm dlx shadcn@latest add scroll-area
pnpm dlx shadcn@latest add dropdown-menu
pnpm dlx shadcn@latest add popover

# For filtering/search
pnpm dlx shadcn@latest add command
pnpm dlx shadcn@latest add input
```

## Design Guidance

### Data Density Principles

Dashboards require higher information density than standard apps:

**Layout Strategy**:
- Grid-based layouts (12-column system)
- Cards for grouping related metrics
- Compact spacing (gap: 2-4 instead of 4-6)
- Responsive breakpoints: sm (640px), md (768px), lg (1024px), xl (1280px)

**Visual Hierarchy**:
1. **Primary metrics**: Large, prominent (KPIs, key numbers)
2. **Supporting data**: Medium size (trends, comparisons)
3. **Contextual info**: Small, muted (labels, timestamps)

### Color for Data

**Status Colors**:
```css
/* Add to index.css :root */
--success: oklch(0.65 0.15 145);  /* Green for positive/success */
--warning: oklch(0.75 0.14 85);   /* Yellow for warning */
--error: oklch(0.55 0.20 25);     /* Red for error/negative */
--info: oklch(0.60 0.12 240);     /* Blue for info */
```

**Chart Colors** (distinct, WCAG compliant):
```css
--chart-1: oklch(0.55 0.15 265);
--chart-2: oklch(0.68 0.16 30);
--chart-3: oklch(0.60 0.14 145);
--chart-4: oklch(0.70 0.12 85);
--chart-5: oklch(0.50 0.18 340);
```

### Typography for Data

**Number Formatting**:
- Use tabular figures (monospace numbers) for alignment
- Large size for primary metrics (text-4xl or text-5xl)
- Medium for supporting metrics (text-2xl)
- Include units/labels in muted color

```tsx
<div className="space-y-1">
  <p className="text-5xl font-bold tabular-nums">1,234</p>
  <p className="text-sm text-muted-foreground">Total Users</p>
</div>
```

## Dashboard Layout Patterns

### Main Dashboard Layout

```tsx
// src/routes/dashboard.tsx
export default function Dashboard() {
  return (
    <div className="flex min-h-screen">
      {/* Sidebar */}
      <aside className="w-64 border-r bg-card">
        <nav className="p-4">
          {/* Navigation items */}
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1">
        {/* Header */}
        <header className="border-b bg-card px-6 py-4">
          <h1 className="text-2xl font-bold">Dashboard</h1>
        </header>

        {/* Content area */}
        <div className="p-6">
          {/* Stats grid */}
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            <MetricCard />
            <MetricCard />
            <MetricCard />
            <MetricCard />
          </div>

          {/* Charts */}
          <div className="mt-6 grid gap-4 md:grid-cols-2">
            <Card>
              <CardHeader>
                <CardTitle>Revenue Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <LineChart data={data} />
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>User Growth</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart data={data} />
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
```

### Metric Card Component

```tsx
import { Card, CardContent } from '@/components/ui/card';
import { TrendingUp, TrendingDown } from 'lucide-react';

interface MetricCardProps {
  title: string;
  value: string;
  change: number;
  changeLabel: string;
}

export function MetricCard({ title, value, change, changeLabel }: MetricCardProps) {
  const isPositive = change >= 0;

  return (
    <Card>
      <CardContent className="p-6">
        <div className="flex items-center justify-between">
          <p className="text-sm font-medium text-muted-foreground">{title}</p>
          {isPositive ? (
            <TrendingUp className="h-4 w-4 text-success" />
          ) : (
            <TrendingDown className="h-4 w-4 text-error" />
          )}
        </div>
        <div className="mt-2">
          <p className="text-3xl font-bold tabular-nums">{value}</p>
          <p className="mt-1 text-sm text-muted-foreground">
            <span className={isPositive ? 'text-success' : 'text-error'}>
              {isPositive ? '+' : ''}{change}%
            </span>{' '}
            {changeLabel}
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Chart Examples with Recharts

### Line Chart

```tsx
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

const data = [
  { month: 'Jan', revenue: 4000 },
  { month: 'Feb', revenue: 3000 },
  { month: 'Mar', revenue: 5000 },
  // ...
];

export function RevenueChart() {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <LineChart data={data}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
        <XAxis
          dataKey="month"
          tick={{ fontSize: 12 }}
          tickLine={false}
        />
        <YAxis
          tick={{ fontSize: 12 }}
          tickLine={false}
          axisLine={false}
        />
        <Tooltip
          contentStyle={{
            backgroundColor: 'hsl(var(--card))',
            border: '1px solid hsl(var(--border))',
            borderRadius: '0.5rem'
          }}
        />
        <Line
          type="monotone"
          dataKey="revenue"
          stroke="hsl(var(--primary))"
          strokeWidth={2}
          dot={false}
        />
      </LineChart>
    </ResponsiveContainer>
  );
}
```

### Bar Chart

```tsx
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer
} from 'recharts';

export function UserGrowthChart({ data }: { data: any[] }) {
  return (
    <ResponsiveContainer width="100%" height={300}>
      <BarChart data={data}>
        <CartesianGrid strokeDasharray="3 3" opacity={0.1} />
        <XAxis dataKey="month" tick={{ fontSize: 12 }} tickLine={false} />
        <YAxis tick={{ fontSize: 12 }} tickLine={false} axisLine={false} />
        <Tooltip />
        <Bar
          dataKey="users"
          fill="hsl(var(--primary))"
          radius={[4, 4, 0, 0]}
        />
      </BarChart>
    </ResponsiveContainer>
  );
}
```

## Data Table Pattern

```tsx
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';

interface User {
  id: string;
  name: string;
  email: string;
  status: 'active' | 'inactive';
  createdAt: Date;
}

export function UserTable({ users }: { users: User[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Status</TableHead>
          <TableHead>Created</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id}>
            <TableCell className="font-medium">{user.name}</TableCell>
            <TableCell>{user.email}</TableCell>
            <TableCell>
              <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                {user.status}
              </Badge>
            </TableCell>
            <TableCell className="text-muted-foreground">
              {format(user.createdAt, 'MMM d, yyyy')}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

## Date Filtering Pattern

```tsx
import { useState } from 'react';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { Button } from '@/components/ui/button';
import { CalendarIcon } from 'lucide-react';
import { format } from 'date-fns';

export function DateRangePicker() {
  const [date, setDate] = useState<Date>();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" className="justify-start text-left font-normal">
          <CalendarIcon className="mr-2 h-4 w-4" />
          {date ? format(date, 'PPP') : <span>Pick a date</span>}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-auto p-0">
        <Calendar
          mode="single"
          selected={date}
          onSelect={setDate}
          initialFocus
        />
      </PopoverContent>
    </Popover>
  );
}
```

## Performance Considerations

### Large Datasets

For tables with 1000+ rows:
```tsx
import { useVirtualizer } from '@tanstack/react-virtual';

// Implement virtual scrolling for performance
```

### Real-time Updates

```tsx
import { useQuery } from '@tanstack/react-query';

// Poll for updates
const { data } = useQuery({
  queryKey: ['metrics'],
  queryFn: fetchMetrics,
  refetchInterval: 30000, // 30 seconds
});
```

### Optimize Charts

- Limit data points (aggregate if > 100 points)
- Debounce resize events
- Use memo for expensive calculations

## Responsive Design

**Mobile Dashboard** (< 768px):
- Stack cards vertically
- Hide sidebar, use hamburger menu
- Simplify charts (fewer data points)
- Prioritize key metrics above fold

**Tablet** (768px - 1024px):
- 2-column grid for metrics
- Sidebar can collapse/expand
- Full chart functionality

**Desktop** (> 1024px):
- 4-column grid for metrics
- Permanent sidebar
- Full feature set

## Accessibility

- Use semantic HTML (`<table>`, `<th>`, `<td>`)
- Provide chart descriptions with `aria-label`
- Ensure color contrast meets WCAG AA
- Keyboard navigation for all interactive elements
- Screen reader announcements for data updates

## Next Steps

1. Define your metrics and data sources
2. Set up data fetching with TanStack Query
3. Build reusable chart components
4. Implement filtering and date range selection
5. Add real-time updates if needed
6. Test with realistic data volumes
7. Optimize for performance
