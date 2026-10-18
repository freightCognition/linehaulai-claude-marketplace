# Dark mode and theming

## The contract (`dark-mode.ts`)

```ts
export interface DarkModeProps {
	isDark?: boolean;                          // default false
	onIsDarkChange?: (isDark: boolean) => void;
}
export const DEFAULT_IS_DARK = false;
export function resolveIsDark(isDark?: boolean): boolean;             // isDark ?? false
export function toggleIsDark(isDark: boolean | undefined, onIsDarkChange?: (v: boolean) => void): boolean;
```

All four helpers and the type are exported from the package root (`import { toggleIsDark, type DarkModeProps } from 'extend-ui-svelte'`) and from the copied `dark-mode.ts`.

Rules:

- The parent owns the theme. Components never flip it themselves; they add a `dark` class to their own root element when `isDark` is true.
- `onIsDarkChange` is only called by components that render their own theme switch: `DocxViewer`, `XlsxViewer`, `DocxEditor`, `XlsxEditor`. In those four, both `isDark` and `onIsDarkChange` are **required** props. Everywhere else they are optional and `onIsDarkChange` is accepted but never called.
- Every component accepts `isDark` (all 20 component folders).

```svelte
<script lang="ts">
	import { XlsxViewer } from 'extend-ui-svelte/components/xlsx-viewer';
	import { PdfViewer } from 'extend-ui-svelte/components/pdf-viewer';

	let isDark = $state(false);
	const setDark = (value: boolean) => (isDark = value);
</script>

<button onclick={() => (isDark = !isDark)}>Theme</button>
<XlsxViewer src="/files/q3.xlsx" {isDark} onIsDarkChange={setDark} />
<PdfViewer src="/files/q3.pdf" {isDark} onIsDarkChange={setDark} />
```

Syncing with an app-wide theme (for example mode-watcher or a `data-theme` attribute): derive `isDark` from that source and write back to it in `onIsDarkChange`. Do not try to make the components read `prefers-color-scheme`; they will not.

## Scoped-CSS components

Viewers, editors, file components and extraction components style themselves with scoped `<style>` blocks and component-prefixed custom properties (for example `--pdf-border`, `--pdf-fg`, `--xlsx-border`, `--csv-border`, `--docx-border`, `--hr-bg`, `--splits-bg`, `--lb-border`, `--fu-border`, `--es-border`, `--pptx-border`, `--pdf-editor-accent`). They need no Tailwind. Their dark palette switches on the root `.dark` class. To re-skin one, read its `<style>` block for the variable names; there is no shared theme object.

## Tailwind primitives: `group`, `toggle`, `color-picker`

These three use Tailwind v4 utility classes and shadcn-style semantic tokens (`bg-background`, `text-muted-foreground`, `border-input`, `ring-ring`, ...). They need:

1. Tailwind v4 with `@tailwindcss/vite`.
2. The class-based dark variant matching the component root's `dark` class:
   ```css
   @custom-variant dark (&:where(.dark, .dark *));
   ```
3. The theme tokens. A shadcn-svelte app already has compatible ones. Otherwise use the block the library's docs site uses (ported from extend-hq/ui `apps/v4/app/globals.css`):
   ```css
   @theme inline {
   	--radius-sm: calc(var(--radius) * 0.6);
   	--radius-md: calc(var(--radius) * 0.8);
   	--radius-lg: var(--radius);
   	--radius-xl: calc(var(--radius) * 1.4);
   	--color-background: var(--background);
   	--color-foreground: var(--foreground);
   	--color-card: var(--card);
   	--color-card-foreground: var(--card-foreground);
   	--color-popover: var(--popover);
   	--color-popover-foreground: var(--popover-foreground);
   	--color-primary: var(--primary);
   	--color-primary-foreground: var(--primary-foreground);
   	--color-secondary: var(--secondary);
   	--color-secondary-foreground: var(--secondary-foreground);
   	--color-muted: var(--muted);
   	--color-muted-foreground: var(--muted-foreground);
   	--color-accent: var(--accent);
   	--color-accent-foreground: var(--accent-foreground);
   	--color-destructive: var(--destructive);
   	--color-destructive-foreground: var(--destructive-foreground);
   	--color-border: var(--border);
   	--color-input: var(--input);
   	--color-ring: var(--ring);
   }
   :root {
   	--radius: 0.625rem;
   	--background: oklch(1 0 0);
   	--foreground: var(--color-neutral-800);
   	--card: var(--color-white);
   	--card-foreground: var(--color-neutral-800);
   	--popover: var(--color-white);
   	--popover-foreground: var(--color-neutral-800);
   	--primary: var(--color-neutral-800);
   	--primary-foreground: var(--color-neutral-50);
   	--secondary: --alpha(var(--color-black) / 4%);
   	--secondary-foreground: var(--color-neutral-800);
   	--muted: --alpha(var(--color-black) / 4%);
   	--muted-foreground: color-mix(in srgb, var(--color-neutral-500) 90%, var(--color-black));
   	--accent: --alpha(var(--color-black) / 4%);
   	--accent-foreground: var(--color-neutral-800);
   	--destructive: var(--color-red-500);
   	--destructive-foreground: var(--color-red-700);
   	--border: --alpha(var(--color-black) / 8%);
   	--input: --alpha(var(--color-black) / 10%);
   	--ring: var(--color-neutral-400);
   }
   .dark {
   	--background: oklch(0.145 0 0);
   	--foreground: var(--color-neutral-100);
   	--card: color-mix(in srgb, var(--background) 98%, var(--color-white));
   	--card-foreground: var(--color-neutral-100);
   	--popover: color-mix(in srgb, var(--background) 98%, var(--color-white));
   	--popover-foreground: var(--color-neutral-100);
   	--primary: var(--color-neutral-100);
   	--primary-foreground: var(--color-neutral-800);
   	--secondary: --alpha(var(--color-white) / 4%);
   	--secondary-foreground: var(--color-neutral-100);
   	--muted: --alpha(var(--color-white) / 4%);
   	--muted-foreground: color-mix(in srgb, var(--color-neutral-500) 90%, var(--color-white));
   	--accent: --alpha(var(--color-white) / 4%);
   	--accent-foreground: var(--color-neutral-100);
   	--destructive: color-mix(in srgb, var(--color-red-500) 90%, var(--color-white));
   	--destructive-foreground: var(--color-red-400);
   	--border: --alpha(var(--color-white) / 6%);
   	--input: --alpha(var(--color-white) / 8%);
   	--ring: var(--color-neutral-500);
   }
   ```
4. Tailwind must scan the component files. Copy-in files under `src/` are scanned automatically. For the npm package, add a source path relative to the CSS file, for example in `src/app.css`:
   ```css
   @source "../node_modules/extend-ui-svelte/dist";
   ```

The library's docs site imports `tailwindcss/theme.css` and `tailwindcss/utilities.css` but deliberately leaves out Preflight so the scoped-CSS viewers keep their own look. If the app uses full `@import "tailwindcss"` (with Preflight), check that the viewers still look right.

## `cn` (`utils.ts`, registry item `utils`)

```ts
export function cn(...parts: Array<string | false | null | undefined>): string;
```

It filters falsy values and joins with spaces. Unlike shadcn's `cn`, it does **not** use `clsx` objects or `tailwind-merge`, so `cn('px-2', 'px-4')` keeps both classes. When overriding primitive styles through `class`, avoid conflicting utilities or wrap with your own `twMerge`. `cn` is not exported by the npm package; copy the `utils` item if you need it.
