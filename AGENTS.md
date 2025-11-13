## Agent Operating Instructions

These rules apply to any automated assistant working in this repository. Follow them for every task unless explicitly overruled by the maintainer.

Compliance with these rules is mandatory for every contribution.

1. **Keep documentation current.** When you change behavior, configuration, or any user-facing flow, update both `README.md` and `docs/GUI_GUIDE.md` together. Make sure the acceptance criteria and examples still match reality, keep the content focused on current behaviour (no legacy callouts or “now/previously” phrasing), add clear plain-language comments explaining any new or changed code, and highlight the documentation updates in your final summary.

2. **Maintain code quality.** Follow the project's established formatting tools and idioms (naming, typing, docstrings, etc.). Prefer clear structure, descriptive naming, defensive programming, integrate new code with all relevant systems (project files, settings, tests, undo/redo, etc.), and add tests when behavior could regress.

3. **Maintain `TODO.md`.** Before starting work, read the entire `TODO.md`. When tasks touch roadmap items, update the relevant entries using the maintainer guide at the top (imperative phrasing, priority tags, acceptance bullets, summary counts). Do not mark items complete—remove them once finished—and confirm the summary counts still reflect reality before handing off.

4. **Ask when unsure.** If any requirement, scope, or detail is ambiguous, stop and request clarification before proceeding. Never assume desired behaviour or acceptance criteria, and never make changes outside the user’s requested scope. If a deviation seems necessary, pause, explain why, and get confirmation before continuing; suggestions are fine, but confirm before expanding the edit scope. If the maintainer is unavailable, pause work and summarize open questions instead of guessing.

5. **Install dev tooling.** Before running project checks, install development dependencies. Locally, run `pip install -e ".[dev]"`. In cloud shells (e.g., Cursor sandbox), run `cd /workspace && sudo apt-get update && sudo apt-get install -y ffmpeg`, then `cd /workspace && pip install -e ".[dev]"`; rerun these `sudo` steps if the container resets.

6. **Run relevant checks.** Before handing back changes, run these commands in order. Locally: `pytest -q`, `ruff check spectrosampler tests scripts --fix`, `mypy spectrosampler --ignore-missing-imports`, `black spectrosampler tests scripts`. In cloud shells, run `cd /workspace && python3 -m pytest -q`, `cd /workspace && python3 -m ruff check spectrosampler tests scripts --fix`, `cd /workspace && python3 -m mypy spectrosampler --ignore-missing-imports`, `cd /workspace && python3 -m black spectrosampler tests scripts`. Always run the full sequence; if any command fails, fix the issue, restart the sequence from the top, and include the command output in your summary so reviewers see what ran.

7. **Prioritize current release.** The program is unreleased; skip backward compatibility. Optimize functionality and efficiency first, document only the current behaviour (no legacy callouts or comparisons), and when you make performance-oriented changes, provide a brief rationale or metric so the benefit is clear.

8. **Preserve user edits.** Leave any existing uncommitted changes untouched unless the maintainer explicitly instructs you to revert them. If you encounter unexpected workspace changes mid-task, pause and ask how to proceed instead of reverting or overwriting; when they touch the same files you’re editing, review and reconcile them carefully before continuing.

9. **Document in lockstep.** When behavior changes, update `README.md` and `docs/GUI_GUIDE.md` in the same commit, keep both focused on current behaviour (no legacy callouts or “now it…” wording), and mention the cross-check in your summary.

10. **Explain changes.** In your final summary, provide a detailed account of what you changed, how you changed it, and why the change was necessary so reviewers fully understand the reasoning.

11. **Commit message format.** When asked to write or rewrite a commit message, first check the staged changes using `git diff --cached --stat` and `git diff --cached` to understand what will be committed. Format the message as a code block (triple backticks) for easy copy/paste. The message must start with a concise title line (imperative mood, ~50-70 characters), followed by a blank line, then a bulleted list of key changes based on the staged diff. Each bullet should describe what was changed, where it was changed, and why if non-obvious. Group related changes together and be specific about file paths and function names. Include documentation updates, test additions, and TODO.md updates as separate bullets (see example below).

12. **Confirm rules before starting.** Before starting any work, confirm you have read all the rules in AGENTS.md by starting your response with "I HAVE READ ALL THE FOLLOWING RULES", then listing all the rules (numbered 1-12), then ending with "I WILL FOLLOW ALL THESE RULES", then wait for the user to type "GO" before proceeding with any work.

Commit Message Example:

```
Add overlap/duplicate removal/merge actions and peak normalization export option

- Added "Remove All Overlaps", "Remove All Duplicates", and "Merge All Overlaps" Edit menu actions in `spectrosampler/gui/main_window.py` for cleaning up detection results. Remove All Overlaps keeps the earliest-starting sample in each overlap group. Remove All Duplicates removes samples whose start/end times are within 5 ms of another sample, keeping one per set. Merge All Overlaps combines each overlap group into a single sample spanning from the earliest start time to the latest end time, preserving enabled state and preferring "manual" detector when present.

- Implemented `find_overlaps_within_segments()` and `find_duplicates_within_segments()` helper functions in `spectrosampler/gui/overlap_detector.py` using union-find algorithms to ensure all transitive overlaps and duplicates are correctly grouped together, fixing edge cases where chains of overlaps/duplicates weren't properly detected.

- Enhanced `is_duplicate()` with epsilon handling for floating point precision issues and rewrote `find_overlaps_within_segments()` to use union-find for transitive closure, ensuring robust detection even with floating point rounding errors.

- Updated `_update_sample_action_states()` to enable/disable overlap/duplicate removal/merge actions based on detection results, and added calls to `_update_sample_action_states()` in `_on_sample_moved()`, `_on_sample_resized()`, `_on_model_times_edited()`, `_on_model_duration_edited()`, and `_on_sample_created()` to ensure actions update immediately after segment edits.

- Added "Peak Normalization" toggle to Export menu and implemented two-pass peak normalization in `spectrosampler/audio_io.py` using FFmpeg's `volumedetect` to detect peak levels and `volume` filter to normalize samples to -0.1 dBFS without clipping. Fixed FFmpeg command construction to properly combine fade filters with volumedetect in a single `-af` option.

- Added "_norm" suffix to exported filenames when peak normalization is enabled by updating `build_sample_filename()` in `spectrosampler/export.py` to accept a `normalize` parameter and appending "norm" to filename parts when enabled.

- Wired normalization parameter through `PipelineWrapper.export_samples()` to `export_sample()` function and enhanced export settings persistence in `spectrosampler/gui/main_window.py` and project save/load to include normalization setting, ensuring it persists across sessions and project files.

- Added comprehensive test coverage in `tests/test_overlap_detector.py` with 16 tests covering edge cases including transitive overlaps/duplicates, nested overlaps, multiple groups, and custom tolerance scenarios.

- Updated `README.md` and `docs/GUI_GUIDE.md` to document the new Edit menu actions and peak normalization export option, including filename suffix behavior and persistence across sessions.

- Removed completed items from `TODO.md` and updated summary count from "P1: 22 items" to "P1: 20 items" to reflect completion of overlap/duplicate removal and peak normalization features.
```