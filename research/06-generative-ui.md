# LLM-driven UI: specs, patterns and practice (2025–2026)

Research pass, 2026-09-15. Status labels: shipped / stable spec / preview / proposal / paused.

## 1. Specs and protocols

- **OpenAI Apps SDK** (shipped, on MCP). A tool result carries `structuredContent` (model and
  component see it), `content`, and `_meta` (component only). The tool points at a UI template via
  `_meta.ui.resourceUri`. Inside the iframe `window.openai` exposes tool input/output, widget state,
  `callTool`, `sendFollowUpMessage`, display modes. The model emits a tool call; the server emits data
  plus a pointer to a pre-registered component ([reference](https://developers.openai.com/apps-sdk/reference),
  [ui-guidelines](https://developers.openai.com/apps-sdk/concepts/ui-guidelines)).
- **MCP Apps (SEP-1865)**, proposed 21 Nov 2025, stable 26 Jan 2026. UI templates are `ui://`
  resources, `text/html;profile=mcp-app`; iframe and host speak MCP JSON-RPC over postMessage
  (`ui/initialize`, `ui/notifications/tool-result`, `ui/message`, `ui/open-link`…). Hosts inject theme
  CSS variables. Shipped in Claude web/desktop, VS Code Insiders, ChatGPT
  ([Jan 2026 post](https://blog.modelcontextprotocol.io/posts/2026-01-26-mcp-apps/),
  [spec](https://github.com/modelcontextprotocol/ext-apps/blob/main/specification/2026-01-26/apps.mdx)).
- **MCP-UI** (shipped library): `rawHtml`, `externalUrl`, `remoteDom`, with adapters for both above
  ([mcpui.dev](https://mcpui.dev/guide/getting-started)).
- **Google A2UI** (v0.9.1 stable, v1.0 candidate, Jun 2026). The one where the model emits the layout
  tree: a flat adjacency list of components bound to a separate data model by JSON Pointer, so partial
  trees stream and degrade gracefully. Renderers: Flutter, Lit, Angular. No Svelte
  ([spec](https://a2ui.org/specification/v1.0-a2ui/)).
- **Vercel AI SDK**: `streamUI` / RSC path is paused. The recommended pattern is AI SDK UI: the model
  calls a tool, the client switches on `part.type === 'tool-<name>'` and renders a local component
  ([generative-user-interfaces](https://ai-sdk.dev/docs/ai-sdk-ui/generative-user-interfaces)).
- **json-render** (Vercel Labs, Jan 2026, Apache-2.0): Schema (Zod), Catalog (the components the model
  may use, with prop schemas and descriptions), Registry (binds to real components). Flat spec
  `{root, elements}`; `SpecStreamCompiler` renders progressively; `catalog.validate()`. Renderers for
  React, Vue, **Svelte**, Solid ([repo](https://github.com/vercel-labs/json-render),
  [Svelte API](https://json-render.dev/docs/api/svelte)). LangChain's docs recommend it.
- **CopilotKit / AG-UI**: event transport plus "tool rendering" (a component per tool name); adapters
  for A2UI and MCP Apps ([docs](https://docs.copilotkit.ai/ag2/generative-ui)).
- Others: assistant-ui, Thesys C1, Hashbrown.

## 2. What the model emits

| shape | examples | pros | cons |
|---|---|---|---|
| tool call, server picks a pre-built component | Apps SDK, MCP Apps, AI SDK UI, CopilotKit | model can't invent UI; typed; fastest | one component per tool |
| JSON layout tree, catalog-constrained | A2UI, json-render, Thesys | composable, streamable, validatable | model can mis-bind props; needs validation and repair |
| RSC streamed from the server | AI SDK `streamUI` | real components | React-only, paused |
| free HTML in a sandboxed iframe | MCP Apps `ui://`, Artifacts | expressive | security, style drift, unauditable |

CopilotKit's spectrum: static (pick from pre-built), declarative (JSON description), open-ended.
"Start constrained, expand with structure."

## 3. Practitioner guidance, ranked

1. Close the vocabulary. CloudThinker shipped 24 components in a hard whitelist: "the agent physically
   cannot emit a `<script>` tag" ([Apr 2026](https://cloudthinker.io/blogs/generative-ui-in-production-lessons-shipping-agent-dashboards));
   Puck: unconstrained generation is "AI slop" ([Feb 2026](https://puckeditor.com/blog/ai-slop-vs-constrained-ui)).
2. Only render a widget when it beats text: inspection, comparison, editing, confirmation, navigation
   ([OpenAI ux-principles](https://developers.openai.com/apps-sdk/concepts/ux-principles)).
3. Answer first, then the widget, and "avoid content that is redundant with the card" (ui-guidelines).
4. Card for one decision or small structured data, max two primary actions; carousel for 3–8 similar
   items; no nested scroll, no tabs inside a card (ui-guidelines).
5. Writes: propose, then commit. `needsApproval` / interrupt-and-resume, a confirmation card before
   side effects ([AI SDK](https://www.aisdkagents.com/patterns/ai-elements-confirmation),
   [OpenAI Agents SDK](https://openai.github.io/openai-agents-js/guides/human-in-the-loop/)).
6. Stream in render order: headline, then charts, then tables. "Perceived latency drops more than
   actual latency does" (CloudThinker).
7. Feed validation errors back as LLM-friendly hints, not stack traces (CloudThinker).
8. Separate structure from data (A2UI, Apps SDK `_meta`).
9. Provenance: keep the spec; diff and replay turns without re-running the agent (CloudThinker).
10. Instability erodes learnability; tight rails, never free generation.
11. Evaluation exists: generated interfaces +72% preference over chat baselines
    ([arXiv 2508.19227](https://arxiv.org/abs/2508.19227)); A2UI-Bench scores spec validity.

## 4. Svelte and local-agent options

`@json-render/svelte` is first-class: `defineRegistry(catalog)`, `<Renderer spec registry loading />`,
components as Svelte 5 snippets receiving `{props, children, emit, bindings, loading}`, streaming via
`createUIStream`. `@ai-sdk/svelte` v5 has parity with React for tool parts. A2UI has no Svelte
renderer.

Local agent channels: (a) stdio NDJSON, `claude -p --output-format stream-json --input-format
stream-json`, with `--permission-prompt-tool stdio` so the page is the approval UI
([CLI protocol notes](https://github.com/Roasbeef/claude-agent-sdk-go/blob/main/docs/cli-protocol.md));
(b) a WebSocket relay ([claude-agent-server](https://github.com/dzhng/claude-agent-server));
(c) a JSONL watcher on the agent's own session ([codex-watcher](https://github.com/xiaolai/codex-watcher));
(d) MCP over stdio with a local widget emulator ([MCPJam](https://www.mcpjam.com/blog/app-builder)).

## Recommendation, if an ask channel is built

- `@json-render/svelte`, not a hand-rolled renderer.
- One NDJSON event per turn over stdio→WebSocket: `{v, turn, op, surface, say, spec, data, meta}`;
  `say` is the prose answer, the widget never repeats it; `data` holds rows once, props bind by
  JSON Pointer; `meta` holds provenance (tool, filter, timestamp), component-visible only.
- Ten components, closed: Stack, Card, Table, Text, Badge, Chart, Thread, Message, Button, Confirm.
- Rows ≥ 8 or ≥ 4 columns → Table; 3–8 items with a thumbnail → cards; one fact → Text + Badge.
- A write is a `Confirm` node emitted before acting: `{summary, diff:[{field,from,to}], danger, token}`;
  the page emits `confirm` back and the CLI resumes. The same card can serve Claude Code's own tool
  approvals via `--permission-prompt-tool stdio`.
- Validate every spec with `catalog.validate()`; reply with a one-line repair hint on failure.
- Escape hatch later: wrap the same catalog as an MCP Apps `ui://` resource so the surfaces render
  inside Claude or ChatGPT.

Caveats: AI SDK RSC is paused; A2UI v1.0 is a candidate with no Svelte renderer.
