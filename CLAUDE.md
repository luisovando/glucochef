Claude-specific behavior on top of `AGENTS.md`. Read `AGENTS.md` first for the universal repo context: project description, language rule, repository structure, scope boundary, and commit conventions.

## Reading order at the start of any task

1. `AGENTS.md` — universal repo context
2. `skills/glucochef-conventions/SKILL.md` — product domain, stack, principles, anti-patterns
3. Any task-specific skill under `skills/glucochef-<artifact>/SKILL.md`
4. Relevant context from `memory-bank/` when cross-cutting decisions are involved

Do not produce an artifact without having read `glucochef-conventions` for the current task at least once in the session.

## Use skills before improvising

When a skill exists for the artifact being produced, apply it. Skills encode conventions that have already been decided; inventing alternative conventions on the fly creates drift and undermines the layer.

If a needed skill does not exist yet, propose creating it as a separate step before producing the artifact. Do not silently bake conventions into the artifact itself.

## prompts.md tracking

After each response that touches GlucoChef in any of these categories — architecture, code, user stories, data model, API, tests, CI/CD — signal whether the prompt that produced the response merits being saved to `prompts.md`, and identify the section under which it should be registered.

Format for entries in `prompts.md`:

- **Context**: what state preceded the prompt; what decisions or assumptions were already in place
- **Prompt**: the reconstructed reusable form of the prompt (not the verbatim casual ask), wrapped in a blockquote
- **Output**: which artifact or decision the prompt produced
- **Design notes** (optional): non-obvious decisions worth preserving for future readers

The reconstructed form matters: prompts captured for `prompts.md` should be usable in a fresh session to produce the same output, not a transcript of the casual conversation.

## OpenSpec discipline

For non-trivial features, scaffold a change folder under `openspec/changes/` before writing code. Each change folder contains `proposal.md`, `specs/`, `design.md`, and `tasks.md`. The `tasks.md` is the executable plan and the contract for the change. Small fixes, copy tweaks, and one-line corrections do not require this ceremony.

## Posture

- Treat MVP scope as fixed. If a request would expand it, surface the conflict and propose the in-scope alternative before proceeding.
- Treat the ~30h work budget as a constraint, not a guideline. Prefer recommendations that protect the budget over recommendations that maximize technical sophistication.
- Prefer recommending what already exists in the repo over inventing parallel conventions. If two patterns collide, resolve the collision before producing the artifact.
- When in doubt, ask before generating. Generating speculative content that has to be discarded is more expensive than a clarifying question.