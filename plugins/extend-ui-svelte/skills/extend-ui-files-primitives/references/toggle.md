# Toggle, ToggleGroup, ToggleGroupItem

Source: `src/lib/components/toggle/`. Plain-button ports of the Base UI Toggle and ToggleGroup primitives, with upstream variants and sizes. Styling is Tailwind utility classes. The app needs Tailwind v4 with shadcn-style tokens.

## Imports

```ts
import { Toggle, ToggleGroup, ToggleGroupItem, toggleVariants, toggleGroupVariants } from 'extend-ui-svelte';
import type { ToggleProps, ToggleGroupProps, ToggleGroupItemProps, ToggleSize, ToggleVariant, ToggleGroupOrientation, ToggleGroupSpacing } from 'extend-ui-svelte';
import type { ToggleChangeEventDetails } from 'extend-ui-svelte/components/toggle'; // not in the root entry
// registry copy-in: '$lib/components/toggle/index.js' (needs group, $lib/dark-mode, $lib/utils)
```

## Toggle props

No prop is `$bindable`. Other attributes (for example `aria-label`, `title`, `data-*`) are spread onto the `<button>`. `type` and `form` are dropped, so it is always `type="button"`.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `pressed` | `boolean` | none | Controlled state. Leave it out for uncontrolled. |
| `defaultPressed` | `boolean` | `false` | Uncontrolled initial state. Read once. |
| `onPressedChange` | `(pressed: boolean, details: ToggleChangeEventDetails) => void` | none | Fires on click with the next state. `details.cancel()` skips the uncontrolled update (standalone only). |
| `disabled` | `boolean` | `false` | Also inherited from an enclosing `ToggleGroup`. |
| `variant` | `'default' \| 'outline'` | `'default'` | `outline` adds a border and background. |
| `size` | `'default' \| 'lg' \| 'sm'` | `'default'` | Heights 9/10/8 (or 8/9/7 at `sm:` and up). |
| `value` | `string` | generated id | Item value inside a `ToggleGroup`. |
| `onclick` | `(e: MouseEvent) => void` | none | Runs **before** the built-in toggle. `e.preventDefault()` skips the toggle. |
| `onfocus` | `(e: FocusEvent) => void` | none | Runs after the group focus tracking. |
| `children` | `Snippet` | none | Content. |
| `class` / `className` | `string` | `''` | Merged. |
| `isDark` / `onIsDarkChange` | | `false` / none | `dark` class. The callback is never called. |

Rendered state: `aria-pressed`, `data-pressed` (present when pressed), `data-disabled`, `data-slot="toggle"`.

## ToggleGroup props

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `value` | `string[]` | none | Controlled selection (always an array, even for single-select). |
| `defaultValue` | `string[]` | `[]` | Uncontrolled initial selection. |
| `onValueChange` | `(value: string[], details: ToggleChangeEventDetails) => void` | none | Next selection. `details.cancel()` keeps the current one. |
| `multiple` | `boolean` | `false` | Single-select clicks the active item to clear it (result `[]`). |
| `loopFocus` | `boolean` | `true` | Arrow focus wraps from the last item to the first. |
| `disabled` | `boolean` | `false` | Disables every item. |
| `orientation` | `'horizontal' \| 'vertical'` | `'horizontal'` | Axis for arrow keys and layout. |
| `spacing` | `'default' \| 'none'` | `'default'` | `default`: `gap-1`. `none`: joined edges like `Group`. |
| `onkeydown` | `(e: KeyboardEvent) => void` | none | Runs before built-in navigation. `preventDefault()` skips it. |
| `children`, `class`/`className`, `isDark`, `onIsDarkChange` | | | As above. The rest is spread onto the root `div[role=group]`. |

## ToggleGroupItem props

A `Toggle` with `data-slot="toggle-group-item"`. Typed props: `value?: string` (default generated id), `children?: Snippet`, `onPressedChange`, `disabled`, `variant`, `size`, `class`, `className`, `isDark`, `onIsDarkChange`. Other attributes are forwarded. Inside a group the item's pressed state comes from the group's selection, so `pressed` and `defaultPressed` on an item are ignored.

## ToggleChangeEventDetails

```ts
interface ToggleChangeEventDetails {
	reason: 'none';
	event: Event;
	cancel: () => void;           // skip the built-in state change
	allowPropagation: () => void; // parity only
	isCanceled: boolean;
	isPropagationAllowed: boolean;
	trigger: Element | undefined;
}
```

In a group the order is: the group's `onValueChange` runs first (and can cancel), then the item's `onPressedChange` runs with the same details. An item's `cancel()` cannot block the group.

## Keyboard and accessibility

- Toggle: a native button, so Space and Enter work. `aria-pressed` reflects the state. Icon-only toggles need an `aria-label`.
- ToggleGroup: one Tab stop (the last focused item, else the first enabled item). Arrow keys along the orientation, plus Home and End, move focus without selecting. Space or Enter selects. Keys held with Shift, Ctrl, Alt, or Meta are ignored. The group uses `role="group"` with `data-orientation` (no `aria-orientation`). Give it an `aria-label`.

## Full example: editor toolbar

```svelte
<script lang="ts">
	import { Toggle, ToggleGroup, ToggleGroupItem, Group, GroupSeparator } from 'extend-ui-svelte';

	let marks = $state<string[]>([]);
	let align = $state<string[]>(['left']);
	let preview = $state(false);
	let locked = $state(true);
</script>

<Group aria-label="Formatting">
	<ToggleGroup multiple spacing="none" aria-label="Text style" value={marks} onValueChange={(v) => (marks = v)}>
		<ToggleGroupItem value="bold" variant="outline" aria-label="Bold"><b>B</b></ToggleGroupItem>
		<ToggleGroupItem value="italic" variant="outline" aria-label="Italic"><i>I</i></ToggleGroupItem>
	</ToggleGroup>
</Group>

<!-- single-select that cannot be cleared: cancel when the result would be empty -->
<ToggleGroup
	aria-label="Alignment"
	value={align}
	onValueChange={(next, details) => (next.length ? (align = next) : details.cancel())}
>
	<ToggleGroupItem value="left">Left</ToggleGroupItem>
	<ToggleGroupItem value="center">Center</ToggleGroupItem>
	<ToggleGroupItem value="right">Right</ToggleGroupItem>
</ToggleGroup>

<Toggle pressed={preview} onPressedChange={(p) => (preview = p)} size="sm">Preview</Toggle>

<!-- uncontrolled with a confirm veto -->
<Toggle
	defaultPressed
	onPressedChange={(next, details) => {
		if (!next && !confirm('Unlock editing?')) details.cancel();
		else locked = next;
	}}
>Locked: {locked}</Toggle>
```

## Gotchas

- `bind:pressed` and `bind:value` do not work. Use the callbacks with `$state`.
- In a controlled group, `cancel()` only matters for the uncontrolled path. With `value` set, simply not updating your state keeps the selection.
- A `ToggleGroup` value is a `string[]` even when `multiple={false}`.
- A toggle never submits a form. Mirror its state in a hidden input.
- Parity ledger: `ToggleGroupItem`'s `className`, `variant`, and `size` are listed as unrecorded gaps because they reach `Toggle` through the rest spread rather than named destructuring. They are typed and forwarded.
- Not ported from upstream's class list: the before-pseudo shadow, the touch hit-area, and the icon sizing utilities.
