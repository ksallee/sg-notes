# sg-notes

A notes workbench for Flow Production Tracking: every note in a project, under the record it is
about, threaded, searched and acted on in bulk. It is built on
[sg-widgets](https://github.com/ksallee/sg-widgets) and is the first app to run on that library.

![The lead view: a project's notes grouped under the records they are about, with one thread open](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/lead-view.png)

## Try it

<https://sg-notes.vercel.app>

Name your own Flow PT site and approve the session in the tab that opens. The App Session Launcher
signs you in as yourself, the token stays in your browser, and this app's server holds nothing: no
site, no key, no note.

## The themes

| Default | Supabase | Claude |
| --- | --- | --- |
| ![Default, light](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-default-light.png) | ![Supabase, light](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-supabase-light.png) | ![Claude, light](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-claude-light.png) |
| ![Default, dark](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-default-dark.png) | ![Supabase, dark](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-supabase-dark.png) | ![Claude, dark](https://raw.githubusercontent.com/ksallee/sg-notes/main/docs/screenshots/theme-claude-dark.png) |

Three themes, light and dark, from the palette menu in the bar. All three are the sg-widgets docs
site's own, so the widgets are seen wearing a palette they were not drawn on.

## What it does

- Replies to one note or to every ticked note, and closes them in the same pass.
- Closes notes, and marks them read or unread.
- Changes who a note is addressed to, and forwards a copy to new people.
- Groups the list on the record, the task, the version, the author, the addressee, the status or
  the note type.
- Searches the whole project on the site rather than the page that is loaded.
- Says who owes the next word on every thread.

## Run it locally

    pnpm install
    pnpm dev

Open the URL Vite prints, name the site, sign in when the tab opens, and pick a project. With
`.env.local` holding `FPT_API_SITE_URL`, `FPT_API_SCRIPT_NAME` and `FPT_API_API_KEY` (see
`.env.example`), `pnpm dev` reads through the script key and no sign-in is needed; a production build
ignores those and always signs in.

`docs/development.md` is the rest of the working notes: the headless QA tool, the drives and the
deploy. `docs/fixtures.md` is the seeded sandbox the screenshots were taken on.

## Built on

[sg-widgets](https://github.com/ksallee/sg-widgets), documented at
<https://sg-widgets.vercel.app>. The client, the pickers, the filter bar, the entity cards and the
tables all come from there, installed as registry copies.

## Licence

MIT. See `LICENSE`.
