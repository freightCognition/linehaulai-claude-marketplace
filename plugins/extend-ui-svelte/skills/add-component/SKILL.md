---
name: add-component
description: Install one extend-ui-svelte component into the current Svelte 5 project, with its engine dependencies, SSR-safe setup, and a minimal usage example. Invoked as /extend-ui-svelte:add-component <component-name>.
argument-hint: <component-name>
allowed-tools: Read, Bash, Edit, Write, Glob, Grep
---

# Add an extend-ui-svelte component

Install the component named in `$ARGUMENTS` into the user's project. Load the `extend-ui-svelte` hub skill's `references/installation.md` if any step below is unclear.

## Valid names

`pdf-viewer`, `docx-viewer`, `xlsx-viewer`, `pptx-viewer`, `csv-tsv-viewer`, `document-viewer-sidebar`, `pdf-editor`, `docx-editor`, `xlsx-editor`, `e-signature`, `file-upload`, `file-thumbnail`, `file-system`, `group`, `color-picker`, `toggle`, `schema-builder`, `document-splits`, `layout-blocks`, `bounding-box-citations`.

Shared items (install only as dependencies, or on explicit request): `dark-mode`, `utils`, `virtual-list`, `engines`.

## Steps

### 1. Validate the name

Normalize `$ARGUMENTS` to kebab-case lowercase. Accept the obvious aliases: `PdfViewer`/`PDFViewer` means `pdf-viewer`, `CsvViewer` means `csv-tsv-viewer`, `ButtonGroup` means `group`, `ESignatureBlock` means `e-signature`, `HumanReviewPanel` means `bounding-box-citations`, `OcrBlocksPanel` means `layout-blocks`, `SchemaBuilderPanel` means `schema-builder`. If the name is empty or still not in the list, print the valid names and stop.

### 2. Detect the project

Run these checks and keep the results:

- **Svelte 5**: `package.json` has `svelte` at `^5` or higher. If not, stop and say the library needs Svelte 5.
- **SvelteKit**: `@sveltejs/kit` in `package.json` and a `svelte.config.*` file. This decides whether `$lib` imports work.
- **Vite**: `vite` in devDependencies. Without Vite, warn that the PDF engine's `pdfjs-dist/build/pdf.worker.mjs?url` import needs a Vite-style `?url` loader (affects any component that uses the engines).
- **Tailwind v4**: `tailwindcss` at `^4` and `@tailwindcss/vite`. Find the main CSS file (usually `src/app.css`, the one imported in the root `+layout.svelte`).
- **Package manager** from the lockfile: `bun.lock`/`bun.lockb` is bun, `pnpm-lock.yaml` is pnpm, `yarn.lock` is yarn, `package-lock.json` is npm. Fall back to npm.
- **Existing install**: is `extend-ui-svelte` already in `dependencies`? Is there already a `src/lib/extend-ui/` (or another folder containing `components/<name>/index.ts` with the extend-hq/ui MIT header)? Reuse whichever path is already in use.

### 3. Choose the install path

- If the project already uses one path, use it.
- If the user said "npm" or "package", use the npm package. If they said "copy", "registry", or "source", use copy-in.
- Otherwise default to the **npm package**, and say in one line that copy-in is available for editable source.

### 4a. npm package path

1. Install: `<pm> add extend-ui-svelte` (or `npm i extend-ui-svelte`). All engines come with it as regular dependencies.
2. Import path for the example: `extend-ui-svelte/components/<name>`.

### 4b. Copy-in path

1. Check for a published registry first: `curl -sf https://extend-ui-svelte.linehaul.ai/r/<name>.json`. If it returns JSON, run `npx shadcn-svelte@latest add https://extend-ui-svelte.linehaul.ai/r/<name>.json` and check that the written files keep the `components/`, `engines/`, `virtual-list/` layout relative to each other. If it 404s (the state on 2026-10-18), copy manually:
2. Fetch `https://raw.githubusercontent.com/fakebizprez/extend-ui-svelte/main/registry.json`.
3. Resolve the closure: start from the item, add each `registryDependencies` entry recursively. Skip items already present in the target folder.
4. For each file in the closure, download `https://raw.githubusercontent.com/fakebizprez/extend-ui-svelte/main/<path>` with `curl -fsSL --create-dirs -o <dest> <url>`. `<dest>` is `src/lib/extend-ui/` plus the part of `<path>` after `src/lib/`. Never flatten or rename: components import `../../engines/...`, `../../virtual-list/...`, `../../dark-mode.js`, `../../utils.js`.
5. Collect the `dependencies` arrays across the closure and install them. Install SheetJS from its tarball URL exactly as written in the registry (`https://cdn.sheetjs.com/xlsx-0.20.3/xlsx-0.20.3.tgz`); for yarn use `xlsx@<url>`. Never `add xlsx` from the npm registry.
6. Check the copied files resolve: `grep -rhoE "from '\.\.?/[^']+'" src/lib/extend-ui | sort -u` and confirm every target exists.
7. Import path for the example: `$lib/extend-ui/components/<name>/index.js` (SvelteKit) or a relative path otherwise.

Engine npm closure for reference: any component that depends on `engines` (`pdf-viewer`, `docx-viewer`, `xlsx-viewer`, `pptx-viewer`, `pdf-editor`, `docx-editor`, `xlsx-editor`, `e-signature`, `file-upload`, `file-thumbnail`, `document-splits`, `bounding-box-citations`) needs `pdfjs-dist@^6.4.299`, `docx-preview@^0.4.1`, `pptx-browser@^4.1.5`, and SheetJS. Extras: `pdf-lib@^1.17.1` for pdf-viewer, pdf-editor, bounding-box-citations, e-signature; `signature_pad@^5.1.4` for e-signature; `jszip@^3.10.2` for docx-editor; `papaparse@^5.7.0` for csv-tsv-viewer; `marked@^18.1.0` plus `hast-util-sanitize@^5.0.2`, `hast-util-from-html@^2.0.3`, `hast-util-to-html@^9.0.5` for layout-blocks.

### 5. Worker and SSR setup

- **PDF worker**: do nothing by default. The engine imports the worker with `?url` and sets it before loading. Only if the user wants the worker from a custom URL (copy-in only), add a client-side call to `setPdfWorkerSrc(url)` from `$lib/extend-ui/engines/pdf/index.js` in the root `+layout.svelte` inside `onMount`.
- **SSR**: do not add `export const ssr = false`. Components load engines inside `onMount` or `$effect`. Only add a `browser` guard or an `onMount` dynamic import if the example code you write calls an engine directly.

### 6. Tailwind (only for `group`, `toggle`, `color-picker`)

If the component is one of these three:

- No Tailwind v4: tell the user these primitives need Tailwind v4 and offer the setup; still install the files.
- Tailwind v4 present: in the main CSS file, add the line `@custom-variant dark (&:where(.dark, .dark *));` if missing. Add the theme tokens from the hub skill's `references/dark-mode-and-theming.md` if `--background` and `--color-background` are not already defined (shadcn-svelte projects already have them). For the npm path, add `@source "<relative path>/node_modules/extend-ui-svelte/dist";` relative to that CSS file.

Every other component uses scoped CSS. Make no CSS changes for them.

### 7. Drop a minimal usage example

Read the installed component's `index.ts` and its main `.svelte` file `Props` interface (in `node_modules/extend-ui-svelte/dist/components/<name>/` or the copied folder) and use only props that exist there. Create `src/routes/extend-ui/<name>/+page.svelte` for SvelteKit (or `src/lib/examples/<Name>Example.svelte` otherwise) unless the user named a target file. Use `<script lang="ts">`, runes, and parent-owned dark mode:

```svelte
<script lang="ts">
	import { PdfViewer } from 'extend-ui-svelte/components/pdf-viewer';
	let isDark = $state(false);
</script>

<PdfViewer src="/sample.pdf" fileName="sample" defaultZoom="fit-width" height={720} {isDark} onIsDarkChange={(v) => (isDark = v)} />
```

Required props to remember:

- `docx-viewer`, `xlsx-viewer`, `docx-editor`, `xlsx-editor`: `isDark` and `onIsDarkChange` are required.
- `file-thumbnail`: `file` (a `File` or `ThumbnailFile`).
- `file-system`: `items: FileSystemItem[]`.
- `document-splits`: `splits`, `activePage`, `onSelectPage`, `onSplitsChange` (seed `splits` with `createInitialSplits(pageCount)` from the same import).
- `layout-blocks`: `blocks: OcrBlock[]`.
- `group`, `toggle` primitives: content via children snippets.

Point `src` at a file the user has, or tell them where to drop a sample in `static/`.

### 8. Verify

- Run the project's type check (`<pm> run check` if the script exists, else `npx svelte-check`). Fix errors in what you wrote.
- If a dev server is practical, start it, load the example route, and confirm it renders without console errors. Stop the server before finishing.

### 9. Report

State the install path used, the files added or changed, the packages installed, and the example route. For component-specific props and events, point to the sibling skill: extend-ui-viewers (pdf, docx, xlsx, pptx, csv-tsv viewers, document-viewer-sidebar), extend-ui-editors (pdf, docx, xlsx editors, e-signature), extend-ui-files-primitives (file-upload, file-thumbnail, file-system, group, color-picker, toggle), extend-ui-extraction (schema-builder, document-splits, layout-blocks, bounding-box-citations).
