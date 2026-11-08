# PRD Template - Spark App Template

## Purpose

A Product Requirements Document (PRD) helps structure thinking before implementation. Use this simplified template to plan features, design direction, and success criteria.

## When to Use

- Planning new applications
- Adding major features
- Clarifying requirements
- Aligning design decisions
- Documenting design system choices

## Template

---

# [Application Name]

## Purpose Statement

*(One sentence describing what this web app does and why it exists)*

Example: "A weekly meal planning application that helps users organize their meals and automatically generates consolidated grocery shopping lists."

---

## Experience Qualities

*(Three adjectives with one-sentence elaborations defining the user experience)*

1. **[Adjective]** - [One-sentence elaboration]
2. **[Adjective]** - [One-sentence elaboration]
3. **[Adjective]** - [One-sentence elaboration]

Example:
1. **Effortless** - Planning meals should feel intuitive and quick, not like a chore
2. **Organized** - Clear visual structure makes the week's meals easy to scan and manage
3. **Satisfying** - Generating a shopping list from planned meals should feel like magic

---

## Complexity Level

*(Select ONE and explain why)*

- [ ] **Micro Tool** (single-purpose application)
  - *Why*: [One-sentence justification]
  - *Example*: Calculator app, color picker, unit converter

- [ ] **Content Showcase** (information-focused)
  - *Why*: [One-sentence justification]
  - *Example*: Marketing landing page, portfolio, blog

- [ ] **Light Application** (multiple features with basic state)
  - *Why*: [One-sentence justification]
  - *Example*: Todo list, meal planner, expense tracker

- [ ] **Complex Application** (advanced functionality, multiple views)
  - *Why*: [One-sentence justification]
  - *Example*: CRM, analytics dashboard, project management tool

---

## Essential Features

*(For each core feature, document:)*

### Feature 1: [Feature Name]

- **Functionality**: What it does
- **Purpose**: Why it matters to users
- **Trigger**: How the user initiates it
- **Progression**: Terse UX flow (use → to separate steps)
  - Example: `Click slot → Enter meal name + ingredients → Save → Meal saved to slot`
- **Success Criteria**: How we'll know it works

### Feature 2: [Feature Name]

*(Repeat structure above)*

---

## Edge Case Handling

*(How will the app handle unexpected situations?)*

- **[Edge Case Name]**: [Short one-line solution]
- **[Edge Case Name]**: [Short one-line solution]

Example:
- **Empty week**: Show friendly empty state with prompt to add first meal
- **No ingredients**: Allow meals without ingredients (eating out, leftovers)
- **Duplicate ingredients**: Combine same ingredients across meals in grocery list

---

## Design Direction

*(What specific feelings should the design evoke in users?)*

Example: "The design should feel like a well-organized kitchen bulletin board - warm, practical, and inviting. It should reduce the cognitive load of meal planning by presenting information clearly and making actions obvious."

---

## Color Selection

*(Describe the color scheme approach and specific colors. Use OKLCH format.)*

### Color Palette

- **Primary Color**: `oklch(L C H)` - [What it communicates]
- **Secondary Colors**: `oklch(L C H)` - [Their purposes]
- **Accent Color**: `oklch(L C H)` - [For CTAs and important elements]

### Foreground/Background Pairings

*(Document text colors on backgrounds with WCAG AA validation)*

- `Background (name oklch(L C H))`: `Text color (oklch(L C H))` - Ratio [X.X:1] [✓ or ✗]

Example:
- `Background (Warm Cream oklch(0.96 0.02 85))`: `Dark brown text (oklch(0.25 0.02 55))` - Ratio 8.5:1 ✓
- `Primary (Herb Green oklch(0.55 0.15 145))`: `White text (oklch(0.99 0 0))` - Ratio 4.8:1 ✓

---

## Font Selection

*(What characteristics should the typefaces convey, and which fonts should be used?)*

**Chosen Fonts**:
- **Headings**: [Font Name] - [Character description]
- **Body**: [Font Name] - [Character description]
- **Code** *(if applicable)*: [Font Name]

### Typographic Hierarchy

- **H1 (Page Title)**: [Font] [Weight]/[Size]px/[Tracking]
- **H2 (Section Headers)**: [Font] [Weight]/[Size]px/[Tracking]
- **H3 (Subsections)**: [Font] [Weight]/[Size]px/[Tracking]
- **Body (Main Text)**: [Font] [Weight]/[Size]px
- **Caption (Supporting)**: [Font] [Weight]/[Size]px

Example:
- **H1 (App Title)**: Space Grotesk Bold/32px/tight letter spacing
- **Body (Meal Names)**: Source Sans 3 Regular/16px
- **Caption (Ingredients)**: Source Sans 3 Regular/14px/muted color

---

## Animations

*(How should animations be used? Balance subtle functionality with moments of delight.)*

Example: "Subtle animations reinforce actions without slowing down the experience - meals should 'pop' into place when added, and the grocery list should build item by item when generated, creating a satisfying moment of accomplishment."

---

## Component Selection

### UI Components

*(Which shadcn components will be used?)*

- **[Component Name]**: [Use case]
- **[Component Name]**: [Use case]

Example:
- **Card**: For each day's meal container and the grocery list panel
- **Dialog**: For adding/editing meals with ingredient entry
- **Button**: Primary for generate list, secondary for add meal actions
- **Checkbox**: For checking off grocery items

### Customizations

*(Any custom components needed beyond shadcn?)*

- **[Custom Component]**: [Why needed, what it does]

Example:
- **Meal Slot Component**: Custom component showing empty state vs filled state with hover interactions
- **Ingredient Chip**: Removable tags for ingredients during entry

### Component States

*(How should interactive elements behave in different states?)*

- **[Element] - [State]**: [Behavior/appearance]

Example:
- **Empty meal slot**: Dashed border, muted plus icon, hover brightens
- **Filled meal slot**: Solid background, meal name visible, hover shows edit option
- **Grocery item checked**: Reduced opacity, strikethrough, checkbox filled

### Icon Selection

*(Which Lucide icons represent each action?)*

- **[Action]**: [Icon name]

Example:
- **Add meal**: Plus
- **Remove meal**: Trash
- **Generate grocery list**: ShoppingCart
- **Edit meal**: Pencil

### Spacing System

*(Consistent padding and margin values using Tailwind scale)*

- **Gap between [elements]**: gap-[X]
- **Padding inside [containers]**: p-[X]

Example:
- **Gap between days**: gap-4
- **Gap between meal slots**: gap-2
- **Padding inside cards**: p-4
- **Padding for main container**: p-6

### Mobile Responsive Strategy

*(How components adapt on smaller screens)*

Example:
- Stack days vertically on mobile
- Grocery list becomes full-screen overlay
- Larger touch targets for meal slots

---

## Success Metrics

*(How will we measure if the application succeeds?)*

**User Experience Metrics**:
- [ ] [Metric name and target]
- [ ] [Metric name and target]

**Technical Metrics**:
- [ ] INP < 200ms
- [ ] LCP < 2.5s
- [ ] CLS < 0.1

**Feature Adoption**:
- [ ] [Specific feature usage target]

---

## Out of Scope

*(What will NOT be included in the initial version?)*

- [ ] [Feature or capability]
- [ ] [Feature or capability]

Example:
- Recipe database integration
- Social sharing features
- Advanced meal planning algorithms

---

## Implementation Notes

*(Technical considerations, dependencies, or constraints)*

- **Stack**: See Spark App Template default-webapp.md / data-dashboard.md / etc.
- **Data Persistence**: [Where/how data is stored]
- **Third-party Services**: [Any external APIs or services]

---

## Next Steps

1. [ ] Review PRD with stakeholders
2. [ ] Create color palette and validate contrast
3. [ ] Set up typography in `index.css`
4. [ ] Scaffold project structure
5. [ ] Implement features in priority order
6. [ ] Test with real users
7. [ ] Iterate based on feedback

---

## Example: Complete PRD

See the spark-fullstack-template PRD.md for a complete example following this structure.

---

**Tips**:
- Be specific, not vague
- Use concrete examples
- Validate color contrast ratios
- Think through edge cases early
- Keep it concise but complete
- Update PRD as requirements evolve
- Use this as a living document, not a one-time exercise

**Remember**: A good PRD prevents wasted development time. Spend 1 hour planning to save 10 hours of rework.
