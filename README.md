# linehaul.ai Claude Marketplace

A Claude Code plugin marketplace containing production-ready plugins for business system integrations and backend development orchestration.

## Overview

This repository hosts a collection of reusable Claude Code plugins designed to accelerate development workflows and integration patterns. It serves as a central registry for specialized skills, commands, and agents that can be added to your Claude Code environment.

## Available Plugins

### Full Stack & Orchestration

- **golang-orchestrator**: Subagent orchestration for production Golang backends with Echo framework. Features specialized agents for architecture and routing.

### UI & Visualization

- **shadcn-svelte-skill**: Svelte UI component management with shadcn-svelte, Skeleton UI, and Melt UI guidance (Tailwind CSS v4.1 + TypeScript).
- **svelte-flow**: Interactive node-based editors and flow diagrams with @xyflow/svelte (workflow editors, DAG editors, mindmaps).
- **layerchart**: Pre-built chart components for rapid data visualization (bar, line, pie, tree maps, geographic charts).
- **layercake**: Headless visualization framework for unlimited custom visualizations (maximum flexibility).
- **svelte5-runes**: Comprehensive guidance for Svelte 5 runes system, reactivity patterns, and Svelte 4→5 migration.

### Integration & Logic

- **quickbooks-api-integration**: QuickBooks Online API integration guidance for ERP/CRM/TMS systems.
- **sequential-thinking**: Systematic problem-solving through iterative reasoning with revision and branching.
- **sveltekit-spa**: SvelteKit SPA development patterns and configuration with comprehensive backend integration guidance.
- **supabase**: Supabase development plugin with SQL style guide, RLS policy guidance, and laneweaverTMS-specific database patterns.

## Usage

### Adding the Marketplace

To add this marketplace to Claude Code, use the `/plugin marketplace add` command with the path to this repository:

```bash
/plugin marketplace add freightCognition/linehaulai-claude-marketplace
```

For example:
```bash
/plugin marketplace add .
```

### Installing Plugins

Once the marketplace is added, you can install specific plugins by name:

```bash
/plugin install linehaulai-claude-marketplace
```

Examples:
```bash
/plugin install golang-orchestrator
/plugin install svelte-flow
/plugin install sequential-thinking
```

## Structure

All plugins are located in the `.claude-plugin/` directory.

- **Full Plugins** (e.g., `golang-orchestrator`): Contain `commands/`, `skills/`, and `agents/` directories, and a `plugin.json` manifest.
- **Skill Plugins** (e.g., `sequential-thinking`): Contain primarily `SKILL.md` and optional references.
- **Hybrid Plugins** (e.g., `shadcn-svelte-skill`): Combinations of skills and commands.

For detailed architecture, directory structure, and conventions, please refer to [CLAUDE.md](CLAUDE.md).

## Contributing

To develop or modify plugins in this marketplace:

1.  Navigate to the specific plugin directory under `.claude-plugin/`.
2.  Modify the relevant skills, commands, or documentation.
3.  For full plugins, ensure you update the version in `.claude-plugin/{plugin-name}/.claude-plugin/plugin.json`.
4.  If adding a new plugin, register it in `.claude-plugin/marketplace.json`.

## License

See [LICENSE](LICENSE) for details.
