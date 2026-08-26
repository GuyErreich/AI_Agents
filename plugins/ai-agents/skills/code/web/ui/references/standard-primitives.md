# Standard Primitives

Shared building blocks in a project's common UI folder. Extend these before creating one-off variants.

## Catalog

| Primitive | Responsibility |
|---|---|
| **Button** | Primary/secondary/ghost variants; loading and disabled; icon slot |
| **Stack / FormStack** | Vertical rhythm, gap tokens, optional dividers |
| **FormPage / FormShell** | Page padding, title area, scroll boundary |
| **FormActionBar** | Sticky footer actions on forms |
| **SegmentedControl** | Mutually exclusive short options (2–5) |
| **MemberChipPicker / ChipPicker** | Multi-select chips with toggle state |
| **Sheet / BottomSheet** | Portal shell, header, body, optional action bar — behavior in UX skill |
| **SheetCloseButton** | Consistent close/cancel with press + dismiss lifecycle |
| **TabBarNav** | Tab list + sliding indicator slot |
| **WheelPicker** | Column snap picker shell |

Not every project has every primitive yet — **add to this catalog** when a pattern repeats twice, do not clone ad hoc.

## Headless behavior layer

Style wrappers sit on top of accessible primitives:

| Behavior | Libraries |
|---|---|
| Dialog focus trap, escape | Radix Dialog, React Aria Modal |
| Disclosure, tabs roving focus | Radix Tabs, React Aria Tabs |
| Select/combobox | Radix Select, React Aria ComboBox |
| Toast | Radix Toast, Sonner |

Pattern:

```
StyledButton → wraps <button> or Radix Slot
BottomSheet → portal + Radix Dialog or Vaul + project CSS
```

**UI owns structure and composition.** Motion, dismiss timing, and library choice: `code/web/ux`.

## Reuse rules

1. Search `components/ui/common/` (or project equivalent) before new component
2. Extend variant props on existing primitive — do not fork `ButtonPrimary`, `ButtonSecondary` as separate files unless size warrants split
3. Extract when same JSX appears twice with same layout responsibility — see `reuse-extraction.md`
4. Feature-specific widgets compose primitives; they do not reimplement button chrome

## Wrapper discipline

Each wrapper must justify itself:

- Layout boundary (stack, grid region)
- Semantic boundary (form, nav landmark)
- State boundary (controlled open/close for sheet)
- Scroll boundary (overflow container)

Avoid pass-through wrappers that only rename a div.

## Checklist for new interactive UI

```
- [ ] Uses Button / Sheet / SegmentedControl from common/ when applicable
- [ ] Headless lib provides focus trap and ARIA where required
- [ ] No duplicate primitive for same visual variant
- [ ] UX skill loaded for press, motion, dismiss on interactive surfaces
```
