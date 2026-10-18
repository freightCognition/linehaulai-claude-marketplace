# Group, GroupText, GroupSeparator

Source: `src/lib/components/group/`. A segmented container that joins adjacent children: inner corners are squared and the double borders are removed. Upstream aliases are `ButtonGroup`, `ButtonGroupText`, and `ButtonGroupSeparator` (the same components).

Styling is Tailwind utility classes only (`border-input`, `bg-muted`, `text-muted-foreground`, `bg-input`). The app needs Tailwind v4 with shadcn-style tokens.

## Imports

```ts
import { Group, GroupText, GroupSeparator, groupVariants, ButtonGroup, ButtonGroupText, ButtonGroupSeparator } from 'extend-ui-svelte';
import type { GroupProps, GroupTextProps, GroupSeparatorProps, GroupOrientation, GroupSeparatorOrientation } from 'extend-ui-svelte';
// subpath: 'extend-ui-svelte/components/group'
// registry copy-in: '$lib/components/group/index.js' (needs $lib/dark-mode, $lib/utils)
```

## Group props

No prop is `$bindable`. Any other attribute is spread onto the root `<div role="group" data-slot="group">`, so pass `aria-label` there.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `children` | `Snippet` | required | Group content. |
| `orientation` | `'horizontal' \| 'vertical'` | horizontal styling (`data-orientation` unset) | Joins along the x or y axis. Vertical adds `flex-col`. |
| `class` / `className` | `string` | `''` | Merged. |
| `isDark` | `boolean` | `false` | Adds the `dark` class. |
| `onIsDarkChange` | `(isDark: boolean) => void` | none | Never called. |

## GroupText props

Renders `<div data-slot="group-text">`, a muted, bordered label cell (for example a unit, prefix, or icon). Accepts `children: Snippet` (required), `class`/`className`, `isDark`, `onIsDarkChange`, and spreads the rest. There is no `render` prop (an upstream parity gap). It always renders a `div`.

## GroupSeparator props

Renders `<div role="separator" data-slot="separator">` with `aria-orientation`.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `orientation` | `'horizontal' \| 'vertical'` | `'vertical'` | Use `vertical` inside a horizontal group. |
| `class` / `className`, `isDark`, `onIsDarkChange` | | | As above. Other attributes are spread. |

## groupVariants

`groupVariants({ orientation?, class? }): string` returns the class string for a plain element that should behave like a `Group`. `ToggleGroup` with `spacing="none"` uses it internally.

## How the joining works (important)

The edge-joining selectors only target **direct children that have a `data-slot` attribute**. Plain `<button>` or `<input>` elements without `data-slot` keep their own rounded borders. Give each child `data-slot` (any value, for example `data-slot="button"` or `data-slot="input"`), or use library parts that already set one (`GroupText`, `GroupSeparator`, `Toggle`). Children must also share the same border styling for the seam to look clean. Nested groups get `gap-2` between them.

## Keyboard and accessibility

The root has `role="group"`. Give it an `aria-label`. There is no keyboard handling, because focus moves with Tab across the children. A focused child is raised (`z-1`) so its ring is not clipped.

## Full example: search field and pager

```svelte
<script lang="ts">
	import { Group, GroupText, GroupSeparator } from 'extend-ui-svelte';
	let page = $state(1);
	let query = $state('');
	const btn = 'h-8 rounded-lg border border-input bg-background px-3 text-sm hover:bg-accent';
</script>

<Group aria-label="Search">
	<GroupText>https://</GroupText>
	<input data-slot="input" class="h-8 rounded-lg border border-input px-2 text-sm" bind:value={query} placeholder="example.com" />
	<button data-slot="button" class={btn}>Go</button>
</Group>

<Group aria-label="Pagination">
	<button data-slot="button" class={btn} disabled={page === 1} onclick={() => page--}>Prev</button>
	<GroupSeparator />
	<GroupText>Page {page}</GroupText>
	<GroupSeparator />
	<button data-slot="button" class={btn} onclick={() => page++}>Next</button>
</Group>

<Group orientation="vertical" aria-label="Zoom">
	<button data-slot="button" class={btn}>+</button>
	<button data-slot="button" class={btn}>-</button>
</Group>
```

## Gotchas

- No `data-slot` on a child means no joined edges.
- `cn` has no tailwind-merge. A conflicting class you pass is appended, not swapped.
- Not ported: upstream's dark-mode hover and pressed separator tints, and focus-ring separator shifts.
