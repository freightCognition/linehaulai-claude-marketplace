# ColorPicker, ColorPickerPanel

Source: `src/lib/components/color-picker/`. An OKLCH chroma and lightness plane with a vertical hue slider, an optional opacity slider, an EyeDropper button (where the browser supports it), a value field, channel fields, and a format select (OKLCH, HSL, RGB, Hex).

Styling is Tailwind utility classes (`bg-popover`, `border-input`, `ring-ring`, `bg-accent`). The app needs Tailwind v4 with shadcn-style tokens.

## Imports

```ts
import { ColorPicker, ColorPickerPanel } from 'extend-ui-svelte';
import type { ColorPickerProps, ColorPickerPanelProps, ColorFormat, ColorPickerVariant } from 'extend-ui-svelte';
// subpath: 'extend-ui-svelte/components/color-picker'
// registry copy-in: '$lib/components/color-picker/index.js' (needs $lib/dark-mode, $lib/utils)
```

`ColorFormat = 'oklch' | 'hsl' | 'rgb' | 'hex'` and `ColorPickerVariant = 'input' | 'swatch' | 'panel'`.

## ColorPicker props

No prop is `$bindable`. Any other attribute (`id`, `data-*`, `aria-*`) is spread onto the root wrapper.

| Prop | Type | Default | Description |
| --- | --- | --- | --- |
| `value` | `string` | none | Current color (any parseable CSS color: hex, `rgb()`, `hsl()`, `oklch()`). Takes priority over `color`. If neither is set, `#111827`. |
| `color` | `string` | none | Upstream alias of `value`. Passing it makes the default variant `swatch`. |
| `onChange` | `(value: string) => void` | none | Fires on every change (dragging fires continuously). Always a hex string: `#rrggbb`, or `#rrggbbaa` when alpha is below 1. |
| `label` | `string` | `'Choose color'` | `aria-label` of the trigger. The value field becomes `"{label} value"` and the popup `"{label} panel"`. |
| `disabled` | `boolean` | `false` | Disables the trigger, value field, and channel and opacity fields. Like upstream, the plane, sliders, eyedropper, and format select stay interactive once open. |
| `showAlpha` | `boolean` | `false` | Adds the opacity slider and field. When off, alpha is forced to 1. |
| `defaultFormat` | `ColorFormat` | `'hex'` | Initial format of the text fields. Read once. Typing another format switches it. |
| `variant` | `ColorPickerVariant` | `'swatch'` if `color` is set, else `'input'` | `input`: field with a swatch button, value text input, and optional opacity percentage. `swatch`: a small square button only. `panel`: the picker rendered inline, always open. |
| `icon` | `Snippet` | none | Swatch variant: render this icon in the trigger (ghost style) with a color bar under it. |
| `rainbowTrigger` | `boolean` | `false` | Swatch variant: rainbow trigger instead of the color fill. |
| `onTriggerMouseDown` | `(event: MouseEvent) => void` | none | Swatch trigger only (for example to keep editor selection: call `event.preventDefault()`). |
| `onTriggerPointerDown` | `(event: PointerEvent) => void` | none | Swatch trigger only. |
| `class` / `className` | `string` | `''` | Swatch: on the trigger button. Input: on the field box. Panel: on the root. |
| `isDark` | `boolean` | `false` | Adds `dark`. |
| `onIsDarkChange` | `(isDark: boolean) => void` | none | Never called. |

## ColorPickerPanel props

A `ColorPicker` pinned to `variant="panel"`. Props: `color: string` (required), `label: string` (required), `onChange: (color: string) => void` (required), `showAlpha?: boolean = false`, `class`/`className`, `isDark`, `onIsDarkChange`. No rest spread.

## Controlled behavior

The internal state starts from the mount value and then follows `value` or `color` when the parent changes it. Echoes of the component's own `onChange` are ignored, so the standard loop `value={c} onChange={(v) => (c = v)}` is safe. If you pass `value` without `onChange`, the picker still moves internally (it does not snap back).

## Keyboard and accessibility

- Trigger: `aria-expanded`, `aria-haspopup="dialog"`, and `aria-controls` when open. Opening moves focus into the popup (`role="dialog"`). Escape, a click outside, or tabbing out closes it and returns focus to the trigger.
- Plane (`aria-label="Chroma and lightness"`): the arrow keys move by 1, or by 10 with Shift.
- Hue and Opacity sliders: `role="slider"` with `aria-orientation="vertical"` and value attributes. ArrowUp or ArrowRight increases, ArrowDown or ArrowLeft decreases, and Shift takes a bigger step.
- Text fields: commit on Enter or blur. Escape reverts the draft. Channel and opacity fields step with ArrowUp and ArrowDown (Shift for a bigger step).
- Copying a fully selected value field copies the full CSS color in the current format.

## Full example: theme settings

```svelte
<script lang="ts">
	import { ColorPicker, ColorPickerPanel } from 'extend-ui-svelte';

	let brand = $state('#2563eb');
	let overlay = $state('#00000080');
	let highlight = $state('#facc15');
</script>

<form method="POST" class="grid gap-4">
	<label class="grid gap-1">
		<span>Brand</span>
		<ColorPicker value={brand} onChange={(v) => (brand = v)} label="Brand color" defaultFormat="oklch" />
		<input type="hidden" name="brand" value={brand} />
	</label>

	<div class="flex items-center gap-2">
		<span>Overlay</span>
		<ColorPicker variant="swatch" value={overlay} onChange={(v) => (overlay = v)} label="Overlay color" showAlpha />
		<input type="hidden" name="overlay" value={overlay} />
	</div>

	<ColorPickerPanel color={highlight} label="Highlight color" onChange={(v) => (highlight = v)} />
	<input type="hidden" name="highlight" value={highlight} />
</form>

<div style:background={brand} class="h-8 rounded"></div>
```

## Gotchas

- `bind:value` does not work, because `value` is not `$bindable`. Use `value` plus `onChange`.
- The output is always hex, even when the user typed `oklch(...)`. Convert it yourself if you store another format.
- The popup renders inline below the trigger, not in a portal. Inside an `overflow: hidden` container it can be clipped. Give it room or use the `panel` variant.
- The EyeDropper button only appears where `window.EyeDropper` exists (Chromium).
- Not ported from upstream: the per-channel copy buttons, focus-reselect, and alpha scrub-dragging. The format picker is a native `<select>`.
