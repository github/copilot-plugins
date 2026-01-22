# Radix UI Migration Guide - Spark App Template

## Context

Radix UI, the foundation of shadcn/ui, has received fewer updates since its acquisition by WorkOS. While Radix remains stable and battle-tested, the ecosystem is evolving with new alternatives.

## Current Status (January 2026)

**Radix UI**:
- ✅ Mature, stable, production-ready
- ✅ Powers shadcn/ui (45+ components)
- ✅ Used by millions of production apps
- ⚠️ Slower update cadence
- ⚠️ Uncertainty about long-term roadmap

**Recommendation for New Projects**: Use Radix with confidence, but be aware of migration paths.

## Migration Options

### Option 1: Stay with Radix (Recommended for Most)

**When to choose**:
- Building production apps today
- Need stability over cutting-edge features
- Want proven components with wide adoption
- Using shadcn/ui ecosystem

**Action**: No changes needed. Continue using Radix-based shadcn components.

**Monitoring**: Watch for shadcn/ui announcements about alternative foundations.

---

### Option 2: Migrate to Base UI

**What is Base UI?**
- Built by original Radix team (now at Vercel/MUI)
- Currently in beta, but "looking really good" per shadcn
- Designed for easy migration from Radix
- Similar API and component structure

**Status**: Beta (as of January 2026)

**Migration Path**:

1. **Wait for shadcn/ui Support**
   shadcn/ui now supports Base UI components. You can choose Radix or Base UI when installing:

   ```bash
   pnpm dlx shadcn@latest init
   # Choose Base UI when prompted
   ```

2. **Gradual Component Migration**
   shadcn components are framework-agnostic. When Base UI components are added to shadcn, you can:

   ```bash
   # Install Base UI version of component
   pnpm dlx shadcn@latest add button --base-ui
   ```

3. **Auto-Detection**
   The shadcn CLI auto-detects your library and applies the right transformations.

**Trade-offs**:
- ✅ Future-proof choice
- ✅ Active development
- ✅ Backed by Vercel/MUI
- ⚠️ Still in beta
- ⚠️ Smaller ecosystem currently

---

### Option 3: Migrate to React Aria

**What is React Aria?**
- Built by Adobe
- Powers React Spectrum (Adobe's design system)
- Superior accessibility implementation
- Behavior-first hooks implementing WAI-ARIA spec
- Production-ready and actively maintained

**When to choose**:
- Accessibility is top priority
- Need advanced customization
- Want long-term Adobe backing
- Building design systems

**Migration Effort**: Moderate to High
- React Aria has different API patterns
- Requires rewriting component wrappers
- More control, but more work

**Example Migration**:

Before (Radix via shadcn):
```tsx
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';

<Dialog>
  <DialogTrigger>Open</DialogTrigger>
  <DialogContent>
    <DialogHeader>
      <DialogTitle>Title</DialogTitle>
    </DialogHeader>
  </DialogContent>
</Dialog>
```

After (React Aria):
```tsx
import { DialogTrigger, Modal, Dialog, Heading } from 'react-aria-components';

<DialogTrigger>
  <Button>Open</Button>
  <Modal>
    <Dialog>
      <Heading slot="title">Title</Heading>
      {/* Content */}
    </Dialog>
  </Modal>
</DialogTrigger>
```

**Resources**:
- [React Aria Documentation](https://react-spectrum.adobe.com/react-aria/)
- [React Aria Components](https://react-spectrum.adobe.com/react-aria/components.html)

---

## Practical Migration Strategy

### Phase 1: Assessment (Now)

1. **Inventory your Radix usage**
   ```bash
   grep -r "@radix-ui" src/
   ```

2. **Identify critical components**
   - Dialog/Modal
   - Dropdown Menu
   - Select
   - Popover
   - Tooltip
   - etc.

3. **Evaluate impact**
   - How many components use Radix?
   - Are they heavily customized?
   - What's the migration cost vs. benefit?

### Phase 2: Monitoring (Ongoing)

**Watch for**:
- shadcn/ui announcements about Base UI support
- Radix UI update frequency
- Community migration patterns
- Base UI stable release

**Action Items**:
- Subscribe to shadcn/ui GitHub releases
- Follow @shadcn on Twitter/X
- Monitor Radix UI GitHub activity

### Phase 3: Migration (When Ready)

**Trigger Migration When**:
- Base UI reaches stable v1.0
- shadcn/ui fully supports Base UI
- Radix UI shows signs of abandonment
- Security vulnerabilities go unpatched

**Migration Approach**:

1. **Test Environment First**
   - Set up new branch
   - Migrate one component at a time
   - Test thoroughly before production

2. **Gradual Rollout**
   ```bash
   # Migrate component by component
   pnpm dlx shadcn@latest add button --base-ui
   pnpm dlx shadcn@latest add dialog --base-ui
   ```

3. **Coexistence**
   - Both Radix and Base UI can coexist temporarily
   - Migrate high-traffic components first
   - Monitor for issues

### Phase 4: Complete Migration (Future)

**Timeline**: Likely 2026-2027

**Steps**:
1. All new components use Base UI
2. Gradual migration of existing components
3. Remove Radix dependencies when complete
4. Update documentation

---

## For Spark App Template Users

### Current Recommendation

**Default**: Use Radix-based shadcn/ui
- Production-ready today
- Extensive component library (45+)
- Proven track record
- Wide community support

**Exception**: If building from scratch in Q3 2026+, consider Base UI if stable.

### Staying Updated

Spark App Template will be updated when:
- Base UI reaches stable v1.0
- shadcn/ui completes Base UI integration
- Migration path is proven and low-risk

**Check for updates**:
- Spark App Template GitHub releases
- shadcn/ui changelog
- This migration guide (will be updated)

---

## FAQ

**Q: Should I worry about Radix today?**
A: No. Radix is stable and production-ready. Use it with confidence.

**Q: When should I migrate?**
A: When Base UI is stable (v1.0+) and shadcn/ui fully supports it, likely mid-to-late 2026.

**Q: Can I use Radix for new projects now?**
A: Yes. The migration path will be straightforward when Base UI is ready.

**Q: What about React Aria?**
A: Excellent choice for accessibility-first projects, but requires more custom work.

**Q: Will shadcn/ui abandon Radix?**
A: No indication of abandonment. shadcn is adding Base UI as an option, not replacing Radix.

**Q: How much work is the migration?**
A: Minimal if using shadcn/ui. Components can be swapped one at a time with CLI.

---

## Resources

**Radix UI**:
- Documentation: [radix-ui.com](https://www.radix-ui.com/)
- GitHub: [github.com/radix-ui/primitives](https://github.com/radix-ui/primitives)

**Base UI**:
- Documentation: [mui.com/base-ui](https://mui.com/base-ui/)
- GitHub: [github.com/mui/base-ui](https://github.com/mui/base-ui)

**React Aria**:
- Documentation: [react-spectrum.adobe.com/react-aria](https://react-spectrum.adobe.com/react-aria/)
- GitHub: [github.com/adobe/react-spectrum](https://github.com/adobe/react-spectrum)

**shadcn/ui**:
- Documentation: [ui.shadcn.com](https://ui.shadcn.com/)
- GitHub: [github.com/shadcn-ui/ui](https://github.com/shadcn-ui/ui)

---

**Last Updated**: January 2026

**Next Review**: Q2 2026 (when Base UI v1.0 expected)

---

**Remember**: Don't let uncertainty paralyze you. Radix is production-ready today. When Base UI reaches stability, migration will be straightforward. Build now, migrate later if needed.
