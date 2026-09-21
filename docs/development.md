# Working on sg-notes

`BRIEF.md` is the plan. `research/` is what the community and the docs say the day looks like.
`docs/fixtures.md` is the seeded sandbox and the shapes captured off it. `docs/seams.md` is what
fought when the sg-widgets registry met its first host.

## Run it

    pnpm install
    pnpm dev

Open the URL Vite prints, name the site, sign in through the App Session Launcher when the tab
opens, and pick a project. The pick is remembered. With `.env.local` holding `FPT_API_SITE_URL`,
`FPT_API_SCRIPT_NAME` and `FPT_API_API_KEY` (see `.env.example`), `pnpm dev` reads through the
script key and no sign-in is needed; a production build ignores those and always signs in.

    pnpm check
    pnpm test
    pnpm build

The widgets under `src/lib/components` are registry copies of sg-widgets; `docs/seams.md` says how
they were installed and what to repair after an `add`. `sg-widgets-core` comes from npm.

## What the page does on its own

While the tab is visible it reads the project's Note and Reply events from the event log every
twenty seconds, and at once when the tab comes back: a note someone else changed or answered is read
again in place, and a note someone else wrote shows as a "new notes" pill beside the count rather
than moving the list under you. Sync from SG, in the palette and the row menu, reads everything
again.

Note bodies render as the site's markdown (GitHub Flavored, `marked`), from the token tree and never
from HTML: a raw tag shows as typed, an image is a link, and a link opens only over http, https or
mailto.

## Driving the page

    node tools/qa.mjs --project 1180 --drive tools/drives/lead-view.js
    node tools/qa.mjs --project 1180 --shot .playwright-mcp/lead.png
    node tools/qa.mjs --project 1180 --theme claude --mode light --shot .playwright-mcp/claude.png

The tool starts its own `vite dev` unless `--url` names a running server, so `/live/dev-token` signs
the page in from `.env.local` and nobody has to approve a request.

A drive is the body of an async function; it returns `{verdict, ...}` and the exit code follows.
`tools/drives/` holds one per behaviour: the lead view, search and grouping, a reply, bulk actions.
The reply and bulk drives write to the project they run on. `readme-shot.js` is the view the
README's screenshots show: it narrows the set to the seeded artist accounts and replaces the site's
host in the bar, so nothing in frame names the site or the person whose it is.

The page wears one of three themes, all the sg-widgets docs site's own (Default, Supabase, Claude),
in light, dark or the system's scheme, from the palette menu in the bar; `--theme` and `--mode` set
them for a drive. The app is where the widgets are seen wearing a palette they were not drawn on,
beside primitives that are not sg-widgets' own.

## Deploy

<https://sg-notes.vercel.app>, from `main` alone. `vercel.json` names SvelteKit as the framework,
enables `main` under `git.deploymentEnabled`, and skips every other ref in `ignoreCommand` off
`VERCEL_GIT_COMMIT_REF`, so a feature branch never builds a preview. The build is
`@sveltejs/adapter-vercel`: the page is a client-rendered shell (`ssr = false`) and the three routes
under `/live/` are serverless functions.

The app is live-only. There is no mock and no seeded copy of anything: the deployed page shows
nothing until a person names a Flow PT site and approves a session through the App Session Launcher,
and says why it cannot read otherwise.

Set in the Vercel project, values never in the repo:

| var | what it does deployed |
|---|---|
| `PUBLIC_FPT_SITE_URL` | the site the sign-in form offers by default. The only one the deployed page reads. |
| `FPT_API_SITE_URL`, `FPT_API_SCRIPT_NAME`, `FPT_API_API_KEY` | the script key `/live/dev-token` mints a bearer from. Read under `vite dev` only: the deployed build answers that route 404 before it looks at them, so a public deployment has no reason to carry the key. |

Every one of the four is read through `$env/dynamic/private` or `$env/dynamic/public`, which is the
platform's environment at request time; nothing reads `.env.local` off a disk.
