# Component Patterns - Spark App Template

## shadcn/ui Component Usage Guide

This guide covers common patterns and best practices for using shadcn/ui components in Spark App Template applications.

## Core Principles

1. **Copy, Don't Import**: shadcn components are copied into your project, giving you full ownership
2. **Customize Freely**: Edit components in `src/components/ui/` to match your needs
3. **Compose, Don't Duplicate**: Build complex components by composing primitives
4. **Maintain Consistency**: Follow established patterns across your app

## Common Patterns

### Forms with Validation

The canonical pattern for forms combines Form + react-hook-form + Zod:

```tsx
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Button } from '@/components/ui/button';
import {
  Form,
  FormControl,
  FormDescription,
  FormField,
  FormItem,
  FormLabel,
  FormMessage,
} from '@/components/ui/form';
import { Input } from '@/components/ui/input';

const formSchema = z.object({
  username: z.string().min(2, 'Username must be at least 2 characters'),
  email: z.string().email('Invalid email address'),
});

export function ProfileForm() {
  const form = useForm<z.infer<typeof formSchema>>({
    resolver: zodResolver(formSchema),
    defaultValues: {
      username: '',
      email: '',
    },
  });

  function onSubmit(values: z.infer<typeof formSchema>) {
    console.log(values);
  }

  return (
    <Form {...form}>
      <form onSubmit={form.handleSubmit(onSubmit)} className="space-y-6">
        <FormField
          control={form.control}
          name="username"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Username</FormLabel>
              <FormControl>
                <Input placeholder="johndoe" {...field} />
              </FormControl>
              <FormDescription>
                This is your public display name.
              </FormDescription>
              <FormMessage />
            </FormItem>
          )}
        />

        <FormField
          control={form.control}
          name="email"
          render={({ field }) => (
            <FormItem>
              <FormLabel>Email</FormLabel>
              <FormControl>
                <Input type="email" placeholder="john@example.com" {...field} />
              </FormControl>
              <FormMessage />
            </FormItem>
          )}
        />

        <Button type="submit">Submit</Button>
      </form>
    </Form>
  );
}
```

### Dialogs & Modals

Standard pattern for modal dialogs:

```tsx
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';

export function DeleteConfirmDialog() {
  return (
    <Dialog>
      <DialogTrigger asChild>
        <Button variant="destructive">Delete</Button>
      </DialogTrigger>
      <DialogContent>
        <DialogHeader>
          <DialogTitle>Are you sure?</DialogTitle>
          <DialogDescription>
            This action cannot be undone. This will permanently delete your
            account and remove your data from our servers.
          </DialogDescription>
        </DialogHeader>
        <DialogFooter>
          <Button variant="outline">Cancel</Button>
          <Button variant="destructive">Delete</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
```

### Cards with Actions

Pattern for content cards with interactive elements:

```tsx
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';

interface ProjectCardProps {
  title: string;
  description: string;
  status: 'active' | 'archived';
  onEdit: () => void;
  onDelete: () => void;
}

export function ProjectCard({
  title,
  description,
  status,
  onEdit,
  onDelete,
}: ProjectCardProps) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-start justify-between">
          <CardTitle>{title}</CardTitle>
          <Badge variant={status === 'active' ? 'default' : 'secondary'}>
            {status}
          </Badge>
        </div>
        <CardDescription>{description}</CardDescription>
      </CardHeader>
      <CardFooter className="flex justify-between">
        <Button variant="outline" onClick={onEdit}>
          Edit
        </Button>
        <Button variant="ghost" onClick={onDelete}>
          Delete
        </Button>
      </CardFooter>
    </Card>
  );
}
```

### Data Tables

Pattern for displaying tabular data:

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
import { Button } from '@/components/ui/button';
import { MoreHorizontal } from 'lucide-react';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

interface User {
  id: string;
  name: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
}

export function UserTable({ users }: { users: User[] }) {
  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>Name</TableHead>
          <TableHead>Email</TableHead>
          <TableHead>Role</TableHead>
          <TableHead>Status</TableHead>
          <TableHead className="w-[50px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {users.map((user) => (
          <TableRow key={user.id}>
            <TableCell className="font-medium">{user.name}</TableCell>
            <TableCell>{user.email}</TableCell>
            <TableCell>{user.role}</TableCell>
            <TableCell>
              <Badge variant={user.status === 'active' ? 'default' : 'secondary'}>
                {user.status}
              </Badge>
            </TableCell>
            <TableCell>
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" size="icon">
                    <MoreHorizontal className="h-4 w-4" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end">
                  <DropdownMenuItem>Edit</DropdownMenuItem>
                  <DropdownMenuItem>Delete</DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
```

### Select Dropdowns

Pattern for select/dropdown inputs:

```tsx
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';

export function StatusSelect() {
  return (
    <Select>
      <SelectTrigger className="w-[180px]">
        <SelectValue placeholder="Select status" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="active">Active</SelectItem>
        <SelectItem value="pending">Pending</SelectItem>
        <SelectItem value="archived">Archived</SelectItem>
      </SelectContent>
    </Select>
  );
}
```

With react-hook-form:

```tsx
<FormField
  control={form.control}
  name="status"
  render={({ field }) => (
    <FormItem>
      <FormLabel>Status</FormLabel>
      <Select onValueChange={field.onChange} defaultValue={field.value}>
        <FormControl>
          <SelectTrigger>
            <SelectValue placeholder="Select a status" />
          </SelectTrigger>
        </FormControl>
        <SelectContent>
          <SelectItem value="active">Active</SelectItem>
          <SelectItem value="pending">Pending</SelectItem>
        </SelectContent>
      </Select>
      <FormMessage />
    </FormItem>
  )}
/>
```

### Toast Notifications

Using Sonner for toast notifications:

```tsx
import { toast } from 'sonner';
import { Button } from '@/components/ui/button';

export function ToastExample() {
  return (
    <div className="space-x-2">
      <Button onClick={() => toast('Event has been created')}>
        Default
      </Button>
      <Button onClick={() => toast.success('Settings saved successfully')}>
        Success
      </Button>
      <Button onClick={() => toast.error('Something went wrong')}>
        Error
      </Button>
      <Button onClick={() => toast.promise(
        saveSettings(),
        {
          loading: 'Saving...',
          success: 'Settings saved!',
          error: 'Failed to save',
        }
      )}>
        Promise
      </Button>
    </div>
  );
}
```

### Tabs for Content Organization

```tsx
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Card, CardContent } from '@/components/ui/card';

export function SettingsTabs() {
  return (
    <Tabs defaultValue="general" className="w-full">
      <TabsList>
        <TabsTrigger value="general">General</TabsTrigger>
        <TabsTrigger value="security">Security</TabsTrigger>
        <TabsTrigger value="notifications">Notifications</TabsTrigger>
      </TabsList>
      <TabsContent value="general">
        <Card>
          <CardContent className="pt-6">
            General settings content
          </CardContent>
        </Card>
      </TabsContent>
      <TabsContent value="security">
        <Card>
          <CardContent className="pt-6">
            Security settings content
          </CardContent>
        </Card>
      </TabsContent>
    </Tabs>
  );
}
```

### Accordion for FAQ / Expandable Content

```tsx
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from '@/components/ui/accordion';

export function FAQ() {
  return (
    <Accordion type="single" collapsible className="w-full">
      <AccordionItem value="item-1">
        <AccordionTrigger>How do I get started?</AccordionTrigger>
        <AccordionContent>
          Getting started is easy! Simply sign up for an account and follow
          our onboarding guide.
        </AccordionContent>
      </AccordionItem>
      <AccordionItem value="item-2">
        <AccordionTrigger>What payment methods do you accept?</AccordionTrigger>
        <AccordionContent>
          We accept all major credit cards, PayPal, and bank transfers.
        </AccordionContent>
      </AccordionItem>
    </Accordion>
  );
}
```

### Command Palette (⌘K)

```tsx
import { useEffect, useState } from 'react';
import { useNavigate } from '@tanstack/react-router';
import {
  CommandDialog,
  CommandEmpty,
  CommandGroup,
  CommandInput,
  CommandItem,
  CommandList,
  CommandSeparator,
} from '@/components/ui/command';

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
          <CommandItem onSelect={() => navigate({ to: '/dashboard' })}>
            Dashboard
          </CommandItem>
          <CommandItem onSelect={() => navigate({ to: '/settings' })}>
            Settings
          </CommandItem>
        </CommandGroup>
        <CommandSeparator />
        <CommandGroup heading="Actions">
          <CommandItem>Create New Project</CommandItem>
          <CommandItem>Invite Team Member</CommandItem>
        </CommandGroup>
      </CommandList>
    </CommandDialog>
  );
}
```

### Sheet (Drawer) for Mobile Navigation

```tsx
import { Menu } from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from '@/components/ui/sheet';

export function MobileNav() {
  return (
    <Sheet>
      <SheetTrigger asChild>
        <Button variant="outline" size="icon" className="md:hidden">
          <Menu className="h-5 w-5" />
        </Button>
      </SheetTrigger>
      <SheetContent side="left">
        <SheetHeader>
          <SheetTitle>Navigation</SheetTitle>
          <SheetDescription>
            Navigate to different sections of the app
          </SheetDescription>
        </SheetHeader>
        <nav className="mt-6 flex flex-col space-y-2">
          <Button variant="ghost" className="justify-start">
            Dashboard
          </Button>
          <Button variant="ghost" className="justify-start">
            Projects
          </Button>
          <Button variant="ghost" className="justify-start">
            Settings
          </Button>
        </nav>
      </SheetContent>
    </Sheet>
  );
}
```

### Popovers for Contextual Content

```tsx
import { Button } from '@/components/ui/button';
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from '@/components/ui/popover';
import { Calendar } from '@/components/ui/calendar';

export function DatePickerPopover() {
  const [date, setDate] = useState<Date>();

  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline">
          {date ? format(date, 'PPP') : 'Pick a date'}
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

### Alert / Alert Dialog for Important Messages

**Alert** (non-blocking):
```tsx
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert';
import { InfoIcon } from 'lucide-react';

export function InfoAlert() {
  return (
    <Alert>
      <InfoIcon className="h-4 w-4" />
      <AlertTitle>Heads up!</AlertTitle>
      <AlertDescription>
        You can add components to your app using the CLI.
      </AlertDescription>
    </Alert>
  );
}
```

**AlertDialog** (blocking confirmation):
```tsx
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog';
import { Button } from '@/components/ui/button';

export function DeleteAlert() {
  return (
    <AlertDialog>
      <AlertDialogTrigger asChild>
        <Button variant="destructive">Delete Account</Button>
      </AlertDialogTrigger>
      <AlertDialogContent>
        <AlertDialogHeader>
          <AlertDialogTitle>Are you absolutely sure?</AlertDialogTitle>
          <AlertDialogDescription>
            This action cannot be undone. This will permanently delete your
            account and remove your data from our servers.
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter>
          <AlertDialogCancel>Cancel</AlertDialogCancel>
          <AlertDialogAction>Continue</AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
```

## Composition Patterns

### Combining Components

Build complex UIs by composing primitives:

```tsx
// Filter panel combining multiple components
export function FilterPanel() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Filters</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div>
          <Label>Status</Label>
          <Select>
            <SelectTrigger>
              <SelectValue placeholder="All statuses" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">All</SelectItem>
              <SelectItem value="active">Active</SelectItem>
              <SelectItem value="archived">Archived</SelectItem>
            </SelectContent>
          </Select>
        </div>

        <div>
          <Label>Date Range</Label>
          <Popover>
            <PopoverTrigger asChild>
              <Button variant="outline" className="w-full justify-start">
                Select date range
              </Button>
            </PopoverTrigger>
            <PopoverContent className="w-auto p-0">
              <Calendar mode="range" />
            </PopoverContent>
          </Popover>
        </div>

        <Separator />

        <div className="flex gap-2">
          <Button className="flex-1">Apply</Button>
          <Button variant="outline" className="flex-1">
            Reset
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
```

## Card Layout Patterns

### Understanding Card Spacing

shadcn Card components come with default spacing optimized for content cards but may need adjustment when used as structural containers.

**Default Card structure:**
- `CardHeader`: Uses `p-6` padding (1.5rem/24px on all sides)
- `CardContent`: Uses `p-6 pt-0` padding (removes top padding to prevent double spacing with CardHeader)
- Card wrapper: May include `py-6` and `gap-6` in some versions

**Key principle:** "Keep card content focused - cards work best when covering one topic" ([source](https://medium.com/@rivainasution/shadcn-ui-react-series-part-6-card-the-container-i-use-everywhere-without-thinking-a6f9dd711d18))

### When to Override Card Defaults

shadcn explicitly supports overriding defaults via className props ([Card docs](https://ui.shadcn.com/docs/components/card)). Here's when to use each pattern:

**Content Cards (Keep defaults):**
Use default spacing when Card represents discrete content:

```tsx
// ✅ Good - Content card benefits from default spacing
<Card>
  <CardHeader>
    <CardTitle>Project Updates</CardTitle>
    <CardDescription>Latest changes to your project</CardDescription>
  </CardHeader>
  <CardContent>
    <p>Each card should cover one focused topic</p>
  </CardContent>
</Card>
```

**Layout Cards (Override with p-0):**
Remove spacing when Card serves as a structural container:

```tsx
// ✅ Good - Layout card with full control over spacing
<Card className="p-0 gap-0 overflow-hidden flex flex-col">
  <div className="p-4 border-b bg-muted/30">
    <h2 className="font-semibold">Panel Header</h2>
  </div>
  <div className="flex-1 overflow-auto">
    {/* Panel content with independent spacing */}
  </div>
</Card>
```

**Partial Overrides:**
When you need asymmetric spacing control:

```tsx
// ✅ Good - Remove top padding only, preserve bottom
<Card className="pt-0">
  <CardContent className="pt-6">
    {/* Controlled top spacing, natural bottom spacing */}
  </CardContent>
</Card>
```

### Full-Height Card Layouts

For Cards that need to fill available vertical space:

```tsx
// Pattern: flex-col on Card, flex-1 on content area
<Card className="p-0 gap-0 overflow-hidden flex flex-col h-full">
  <div className="p-4 border-b">
    <h2>Fixed Header</h2>
  </div>
  <div className="flex-1 overflow-auto p-6">
    {/* Scrollable content fills remaining space */}
  </div>
  <div className="p-4 border-t">
    <Button>Fixed Footer</Button>
  </div>
</Card>
```

**Why this works:** Setting `flex: 1` on the content area allows it to "grow and take all available space" while pushing footers to the bottom ([CSS-Tricks](https://css-tricks.com/boxes-fill-height-dont-squish/)).

### Cards with ScrollArea

ScrollArea requires careful padding coordination:

```tsx
// ✅ Correct pattern - padding inside ScrollArea
<Card className="p-0">
  <CardHeader className="px-6 pt-6 pb-4">
    <CardTitle>Scrollable Content</CardTitle>
  </CardHeader>
  <CardContent className="p-0">
    <ScrollArea className="h-[400px] px-6">
      {/* Padding applied here, not on CardContent */}
      <div className="space-y-4">
        {items.map(item => <div key={item.id}>{item.content}</div>)}
      </div>
    </ScrollArea>
  </CardContent>
</Card>
```

**Key points:**
- Always set explicit height on ScrollArea (e.g., `h-[400px]`)
- Place padding inside ScrollArea, not on parent CardContent
- This prevents double scrollbars and layout issues ([Medium - ScrollArea](https://medium.com/@rivainasution/shadcn-ui-react-series-part-9-scroll-area-controlled-scrolling-without-layout-hacks-4263c6f899f4))

### Overflow-Hidden Considerations

The `overflow-hidden` class is commonly needed for layout cards but intentionally not default:

```tsx
// When to use overflow-hidden:
<Card className="overflow-hidden"> {/* Clips content to rounded corners */}
  <img src="hero.jpg" className="w-full" /> {/* Image respects border-radius */}
  <CardContent>...</CardContent>
</Card>
```

There's ongoing discussion about making this default, but it remains optional to support both `overflow: hidden` and `overflow: scroll` use cases ([GitHub #2885](https://github.com/shadcn-ui/ui/issues/2885)).

### Split Panel Pattern

Common pattern for side-by-side cards in dashboard layouts:

```tsx
<div className="grid lg:grid-cols-2 gap-6 h-[600px]">
  <Card className="p-0 gap-0 overflow-hidden flex flex-col">
    <div className="p-4 border-b bg-muted/30">
      <h2>Left Panel</h2>
    </div>
    <div className="flex-1 overflow-auto p-6">
      {/* Scrollable left content */}
    </div>
  </Card>

  <Card className="p-0 gap-0 overflow-hidden flex flex-col">
    <div className="p-4 border-b bg-muted/30">
      <h2>Right Panel</h2>
    </div>
    <div className="flex-1 overflow-auto p-6">
      {/* Scrollable right content */}
    </div>
  </Card>
</div>
```

### Nested Cards Pattern

Outer layout card with inner content cards:

```tsx
<Card className="p-0 gap-0 h-full overflow-hidden flex flex-col">
  {/* Outer: Layout card with no default spacing */}
  <div className="p-4 border-b bg-muted/30">
    <h1>Main Panel</h1>
  </div>

  <div className="flex-1 overflow-auto">
    <div className="p-6 space-y-6">
      {/* Inner: Content cards keep default spacing */}
      <Card>
        <CardHeader>
          <CardTitle>Section A</CardTitle>
        </CardHeader>
        <CardContent>
          Content benefits from Card's natural padding
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>Section B</CardTitle>
        </CardHeader>
        <CardContent>
          Another content card with default spacing
        </CardContent>
      </Card>
    </div>
  </div>
</Card>
```

### Card Spacing Decision Tree

Ask yourself these questions when using Cards:

1. **Is this a content card or layout card?**
   - Content: Represents discrete information → Keep defaults
   - Layout: Structural container → Override with `p-0 gap-0`

2. **Does the Card need to fill available height?**
   - Yes → Use `flex flex-col` on Card, `flex-1` on content area
   - Add `overflow-auto` on content area if scrolling needed

3. **Are there nested Cards?**
   - Outer Card: Override spacing (`p-0 gap-0`) for layout control
   - Inner Cards: Keep defaults for proper content spacing

4. **Using ScrollArea inside Card?**
   - CardContent needs `p-0`
   - Move padding into ScrollArea
   - Set explicit height on ScrollArea

5. **Need clipped corners for images?**
   - Add `overflow-hidden` to Card wrapper

## Best Practices

### 1. Use Variants

```tsx
<Button variant="default">Primary</Button>
<Button variant="outline">Secondary</Button>
<Button variant="ghost">Tertiary</Button>
<Button variant="destructive">Delete</Button>
```

### 2. Consistent Sizing

```tsx
<Button size="sm">Small</Button>
<Button size="default">Default</Button>
<Button size="lg">Large</Button>
<Button size="icon">
  <Plus className="h-4 w-4" />
</Button>
```

### 3. Accessible Labels

```tsx
<Label htmlFor="email">Email</Label>
<Input id="email" type="email" />
```

### 4. Loading States

```tsx
<Button disabled>
  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
  Please wait
</Button>
```

### 5. Empty States

```tsx
{items.length === 0 ? (
  <div className="flex flex-col items-center justify-center py-12 text-center">
    <FileQuestion className="h-12 w-12 text-muted-foreground" />
    <h3 className="mt-4 text-lg font-semibold">No projects found</h3>
    <p className="mt-2 text-sm text-muted-foreground">
      Get started by creating a new project.
    </p>
    <Button className="mt-4">
      <Plus className="mr-2 h-4 w-4" />
      New Project
    </Button>
  </div>
) : (
  <ProjectList items={items} />
)}
```

## Common Mistakes to Avoid

❌ **Don't** nest interactive elements:
```tsx
<Button>
  <Link to="/profile">Profile</Link> {/* Wrong */}
</Button>
```

✅ **Do** use asChild:
```tsx
<Button asChild>
  <Link to="/profile">Profile</Link> {/* Correct */}
</Button>
```

❌ **Don't** ignore form validation feedback:
```tsx
<Input {...field} /> {/* Missing FormMessage */}
```

✅ **Do** show validation errors:
```tsx
<FormItem>
  <FormControl>
    <Input {...field} />
  </FormControl>
  <FormMessage /> {/* Shows errors */}
</FormItem>
```

❌ **Don't** use inline styles for theming:
```tsx
<Button style={{ background: 'blue' }}> {/* Wrong */}
```

✅ **Do** use CSS variables:
```tsx
<Button className="bg-primary"> {/* Correct */}
```

---

**Remember**: shadcn components are starting points. Customize them to match your design system, maintain consistency across your app, and always prioritize accessibility and user experience.
