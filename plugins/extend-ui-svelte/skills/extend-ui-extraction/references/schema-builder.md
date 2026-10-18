# SchemaBuilder reference

Visual editor for an extraction schema. Source: `src/lib/components/schema-builder/SchemaBuilder.svelte`, `SchemaJsonView.svelte`.

```ts
import { SchemaBuilder, SchemaBuilderPanel, SchemaJsonView } from 'extend-ui-svelte';
import {
	serializeSchema, SAMPLE_SCHEMA, createSchemaBuilderProperty, createSchemaBuilderEnumValue,
	createSchemaBuilderId, normalizePropertyForType, SCHEMA_BUILDER_FIELD_TYPES,
	SCHEMA_BUILDER_ARRAY_ITEM_TYPES,
	type SchemaBuilderSchema, type SchemaBuilderProperty, type SerializedSchema, type SchemaBuilderProps
} from 'extend-ui-svelte/components/schema-builder';
// Registry copy-in: '$lib/components/schema-builder/index.js'
```

`SchemaBuilderPanel` is the same component under the upstream name. The subpath also has a default export.

## Props (`SchemaBuilder`)

| Prop | Type | Default | Bindable | Description |
|---|---|---|---|---|
| `defaultSchema` | `SchemaBuilderSchema` | `SAMPLE_SCHEMA` | no | Uncontrolled starting schema. Read once at mount. |
| `schema` | `SchemaBuilderSchema` | `undefined` | no | Controlled schema. When set, the builder renders only this and reports edits through `onSchemaChange`. |
| `onSchemaChange` | `(schema: SchemaBuilderSchema) => void` | - | - | Called with a plain (snapshotted) schema after every edit, in both modes. |
| `onSerializedSchemaChange` | `(schema: SerializedSchema) => void` | - | - | Port addition. Called with `serializeSchema(current)` on mount and whenever the current schema object changes. |
| `isDark` | `boolean` | `false` | no | Parent-controlled dark mode. |
| `onIsDarkChange` | `(isDark: boolean) => void` | - | - | Accepted for parity; never called (no theme switch rendered). |
| `theme` | `'light' \| 'dark'` | `undefined` | no | Upstream prop; wins over `isDark` when given. |
| `class` / `className` | `string` | `''` | no | Merged onto the root. |

No snippets. Not `$bindable`: use `schema` + `onSchemaChange`.

## SchemaJsonView props

| Prop | Type | Default | Description |
|---|---|---|---|
| `schema` | `SchemaBuilderSchema` | required | Editor model; serialized internally. |
| `theme` | `'light' \| 'dark'` | `'light'` | Adds a `dark` class. |
| `scrollResetKey` | `string \| number` | `0` | Changing it scrolls back to top. |
| `class` | `string` | `''` | Root class. |

Renders plain preformatted JSON (`max-height: 32rem`, keyboard-scrollable). The builder already renders one beside the form, so use `SchemaJsonView` alone only for a read-only preview.

## Types

```ts
type SchemaBuilderScalarType = 'string' | 'number' | 'integer' | 'boolean' | 'null';
type SchemaBuilderFieldType = SchemaBuilderScalarType | 'object' | 'array' | 'enum';
type SchemaBuilderArrayScalarType = Exclude<SchemaBuilderScalarType, 'null'>;
type SchemaBuilderArrayItemType = SchemaBuilderArrayScalarType | 'object' | 'enum';
type SchemaBuilderTheme = 'light' | 'dark';

interface SchemaBuilderEnumValue { id: string; value: string; description: string; }

interface SchemaBuilderProperty {
	id: string;              // stable, unique; used for keyed rendering and drag
	key: string;             // JSON property name; blank keys are omitted from output
	type: SchemaBuilderFieldType;
	description: string;     // required string, use '' for none
	required?: boolean;      // port addition
	enumValues?: SchemaBuilderEnumValue[];   // type 'enum'
	properties?: SchemaBuilderProperty[];    // type 'object'
	items?: {                                // type 'array'
		type: SchemaBuilderArrayItemType;
		properties?: SchemaBuilderProperty[];  // items.type 'object'
		enumValues?: SchemaBuilderEnumValue[]; // items.type 'enum'
	};
}

interface SchemaBuilderSchema { properties: SchemaBuilderProperty[]; }

interface SerializedSchemaProperty {
	type: string;
	description?: string;
	enum?: string[];
	enumDescriptions?: Record<string, string>;
	properties?: Record<string, SerializedSchemaProperty>;
	required?: string[];
	items?: SerializedSchemaProperty;
}

interface SerializedSchema {
	type: 'object';
	properties: Record<string, SerializedSchemaProperty>;
	required?: string[];
}
```

## Helpers

| Export | Signature | Notes |
|---|---|---|
| `serializeSchema` | `(schema: SchemaBuilderSchema) => SerializedSchema` | Pure; use server-side too. |
| `createSchemaBuilderProperty` | `(type?: SchemaBuilderFieldType) => SchemaBuilderProperty` | Blank key, normalized for the type. Default `'string'`. |
| `createSchemaBuilderEnumValue` | `() => SchemaBuilderEnumValue` | Blank value. |
| `createSchemaBuilderId` | `(prefix?: string) => string` | `prefix-<uuid>`; default prefix `'field'`. |
| `normalizePropertyForType` | `(property, type) => SchemaBuilderProperty` | Clears fields that do not apply. New `object` gets one blank child; new `array` gets `items: { type: 'object', properties: [one blank string] }`; new `enum` gets one blank value. |
| `SAMPLE_SCHEMA` | `SchemaBuilderSchema` | Upstream bank-statement sample. |
| `SCHEMA_BUILDER_FIELD_TYPES` | `SchemaBuilderFieldType[]` | Options for the type select. |
| `SCHEMA_BUILDER_ARRAY_ITEM_TYPES` | `SchemaBuilderArrayItemType[]` | Array item type options (no `null`, no nested `array`). |

## Serialization rules

- Keys are trimmed; properties with empty keys disappear (with their `required` flag).
- Empty descriptions are omitted.
- `enum` becomes `{ type: 'string', enum: [...values], enumDescriptions: {value: description} }` (only values with a description appear in `enumDescriptions`).
- `required` is emitted as an array on the parent object at every level, only when non-empty.
- Arrays of scalars become `{ type: 'array', items: { type } }`.

## Interaction and keyboard

- Each row: Field key input, Field type select, Required checkbox, Description input, "Remove field" button. Objects get "Add nested field"; arrays get an "Array item type" select and "Add nested field" for object items; enums get value/description inputs, "Remove enum value", and "Add enum value".
- "Add field" appends a blank string field at the top level.
- Reorder: native HTML5 drag on top-level rows only (drag handle). There is no keyboard reorder; all other controls are standard focusable inputs and buttons.
- Controlled mode: if the parent ignores an edit, inputs snap back to the controlled value after the next tick (like a React controlled input).

## Full example: schema editor that saves to an API

```svelte
<script lang="ts">
	import { SchemaBuilder } from 'extend-ui-svelte';
	import {
		serializeSchema,
		type SchemaBuilderSchema
	} from 'extend-ui-svelte/components/schema-builder';

	let { initial, isDark = false }: { initial: SchemaBuilderSchema; isDark?: boolean } = $props();

	// svelte-ignore state_referenced_locally
	let schema = $state<SchemaBuilderSchema>(initial);
	let saving = $state(false);

	const invalid = $derived(
		schema.properties.some((p) => !p.key.trim()) ||
			new Set(schema.properties.map((p) => p.key.trim())).size !== schema.properties.length
	);

	async function save() {
		saving = true;
		try {
			await fetch('/api/processors/invoice/schema', {
				method: 'PUT',
				headers: { 'content-type': 'application/json' },
				body: JSON.stringify(serializeSchema(schema))
			});
		} finally {
			saving = false;
		}
	}
</script>

<SchemaBuilder {schema} {isDark} onSchemaChange={(next) => (schema = next)} />
<button type="button" disabled={invalid || saving} onclick={save}>Save schema</button>
{#if invalid}<p role="alert">Every top-level field needs a unique, non-empty key.</p>{/if}
```

Sample model for an invoice:

```ts
const initial: SchemaBuilderSchema = {
	properties: [
		{ id: 'inv-no', key: 'invoice_number', type: 'string', description: 'Invoice identifier', required: true },
		{ id: 'inv-date', key: 'invoice_date', type: 'string', description: 'ISO date' },
		{ id: 'inv-total', key: 'total', type: 'number', description: 'Grand total', required: true },
		{ id: 'inv-cur', key: 'currency', type: 'enum', description: '',
		  enumValues: [ { id: 'usd', value: 'USD', description: '' }, { id: 'eur', value: 'EUR', description: '' } ] },
		{ id: 'inv-lines', key: 'line_items', type: 'array', description: 'Billed lines',
		  items: { type: 'object', properties: [
			{ id: 'li-desc', key: 'description', type: 'string', description: '' },
			{ id: 'li-amt', key: 'amount', type: 'number', description: '', required: true }
		  ] } }
	]
};
```

## Gotchas

- Omitting both `schema` and `defaultSchema` shows the bank-statement `SAMPLE_SCHEMA`. Pass `defaultSchema={{ properties: [] }}` for an empty builder (it shows "No fields yet").
- `defaultSchema` is read once; changing it later does nothing. Switch to `schema` for external updates.
- Every property and enum value needs a unique `id`. Build them with `createSchemaBuilderId()` when importing a JSON Schema.
- There is no JSON-Schema-to-model parser. Converting an existing JSON Schema back into `SchemaBuilderSchema` is your code.
- The component does not validate duplicate or empty keys; duplicates overwrite each other in the serialized object.
- `onSerializedSchemaChange` fires on mount too, not only on edits.

## Differences from upstream (deliberate, recorded in the source header)

Form and JSON render side by side instead of tabs; JSON is plain text; drag reorders top-level fields only (no nested moves, enum reordering, or collapsible nested editors); "Add field" replaces "Add property"; added `required`, `onSerializedSchemaChange`, and remove buttons; dark mode via `isDark` (upstream `theme` still accepted); no app-theme lookup.
