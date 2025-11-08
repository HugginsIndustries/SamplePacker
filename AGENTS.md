## Agent Operating Instructions

These rules apply to any automated assistant working in this repository. Follow them for every task unless explicitly overruled by the maintainer.

1. **Keep documentation current.** Whenever you change behavior, configuration, or user-facing flow, update both `README.md` and `docs/GUI_GUIDE.md` in the same change set. Cross-check acceptance criteria and examples so the docs match the new behaviour.
2. **Maintain code quality.** Use the project's established formatting tools and idioms. Prefer clear structure, descriptive naming, defensive programming, and add tests when behavior could regress.
3. **Review and maintain `TODO.md`.** Before starting work, read the entire `TODO.md`. When tasks touch roadmap items, update the relevant entries using the maintainer guide at the top of that file (imperative phrasing, priority tags, acceptance bullets, summary counts, etc.).
4. **Ask when unsure.** If any requirement, scope, or detail is ambiguous, stop and request clarification before proceeding. Never make assumptions about desired behaviour or acceptance criteria.
5. **Run relevant checks.** Before handing back changes, run these commands in order: `pytest -q`, `ruff check spectrosampler tests scripts`, `mypy spectrosampler --ignore-missing-imports`, `black spectrosampler tests scripts`. If any command reports issues, resolve them and re-run until they pass; use `--fix` when a tool supports it.

Compliance with these rules is mandatory for every contribution.

