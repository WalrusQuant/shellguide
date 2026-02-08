# ShellGuide Feature Roadmap

Six features to transform ShellGuide from a basic shell tutorial into a teaching tool that builds real understanding. Each feature is independent and buildable one at a time.

---

## Build Order

```
Phase 1 (Foundation):     Feature 6 — Better Mistake Handling
Phase 2 (Content):        Feature 2 — Explain the "Why"  ←→  Feature 3 — Real-World Scenarios
Phase 3 (Capabilities):   Feature 4 — Finder Equivalents ←→  Feature 5 — Cheat Sheet
Phase 4 (Complex):        Feature 1 — Progressive Difficulty
```

Features within the same phase can be built in either order. Later phases benefit from earlier ones but don't strictly require them.

---

## Feature 6: Better Mistake Handling

**Build first — enriches the feedback system everything else uses.**

### What Changes

**`src/shellguide/core/challenges.py`** — Extend `Feedback` dataclass:
```python
@dataclass(frozen=True)
class Feedback:
    kind: FeedbackKind
    message: str
    explanation: str = ""
    attempted_effect: str = ""   # NEW: what the user's command would have done
    suggestion: str = ""         # NEW: what they should try instead
```

New validator factory `_common_mistakes` that maps recognized wrong commands to explanations of what they'd do and what to try instead. Extends the existing `_command_with_warnings` pattern.

**`src/shellguide/screens/teach_screen.py`** — Update the INCORRECT feedback branch (~line 197) to display `attempted_effect` and `suggestion` when present.

### Steps
1. Add `attempted_effect` and `suggestion` fields to `Feedback` (defaults to `""`, backward compatible)
2. Create `_common_mistakes` validator factory
3. Migrate Lesson 6 (Deleting) validators to use `_common_mistakes` with mistake dictionaries
4. Add mistake dictionaries to Lesson 5 (Copying) — e.g., forgetting `-r` for directory copy
5. Update INCORRECT display in `teach_screen.py` to show the new fields
6. Test each lesson to verify existing CORRECT/ACCEPTABLE paths still work

### Example
User types `rm -rf temp.log` when asked to delete a file:
> **What your command does:** This would delete temp.log, but -rf is overkill. '-r' is for directories (recursive), '-f' suppresses prompts. Neither is needed for a single file.
> **Try this:** rm temp.log

---

## Feature 2: Explain the "Why" Not Just the "What"

**Content rewrite — no structural changes needed.**

### What Changes

**`src/shellguide/core/challenges.py`** — Rewrite `teaching` and `explanation` strings across all 8 lessons (~40 challenges). Shift from terse descriptions to motivation-driven explanations.

**`src/shellguide/core/command_explainer.py`** — Rewrite `COMMAND_REFERENCE` flag descriptions (~30 entries).

**`src/shellguide/core/command_builder.py`** — Optionally enrich `explanation` strings in all 13 `build_*` functions (these appear in learn-mode file browser).

### Example Transformation
**Before:** `"'-r' (recursive) is needed to copy directories."`

**After:** `"Without -r, cp refuses to copy directories because it doesn't know how deep the contents go. -r tells it to keep going into every subfolder until there's nothing left to copy. This is a safety feature — cp makes you explicitly say 'yes, copy everything inside.'"`

### Steps
1. Define a writing style guide: explain WHY, mention what happens without the flag, use analogies to physical world
2. Rewrite Lesson 1 as a template, review the tone
3. Apply the pattern to Lessons 2–8
4. Rewrite `COMMAND_REFERENCE` flag descriptions
5. Optionally update `command_builder.py` explanation strings

---

## Feature 3: Real-World Scenarios

**Content rewrite — changes prompts, teaching text, and sandbox layouts.**

### What Changes

**`src/shellguide/core/challenges.py`** — Rewrite all 8 `_LN_LAYOUT` dicts, challenge `prompt`/`teaching` strings, and update validators when filenames change.

### Lesson Themes
| Lesson | Current | New Theme |
|--------|---------|-----------|
| 1. Looking Around | Generic files | "You just cloned a project from GitHub. Explore what's in it." |
| 2. Navigation | Generic dirs | "Your team's monorepo has several services. Navigate between them." |
| 3. Creating | Abstract files | "Setting up a new web project from scratch." |
| 4. Renaming/Moving | Generic rename | "Reorganizing — the project structure needs cleanup." |
| 5. Copying | Abstract copy | "Making backups before a big refactor." |
| 6. Deleting | Generic delete | "Sprint cleanup — remove old build artifacts and temp files." |
| 7. Reading Files | Generic text | "Debugging — read config files and logs to find the problem." |
| 8. Finding Things | Generic search | "You inherited a large codebase. Find the files you need." |

### Critical Constraint
When filenames change in sandbox layouts, validators MUST be updated to match. E.g., if `todo.txt` becomes `index.html`, then `_check_effect(lambda b, a: "todo.txt" in a.files ...)` must change too.

### Steps
1. Define thematic context for each lesson
2. Design realistic sandbox layouts (project-like file names, directory structures, file contents)
3. Rewrite Lesson 1 prompts + layout, update validators
4. Repeat for Lessons 2–8
5. Test each lesson end-to-end to verify all validators pass

---

## Feature 4: Show the Finder Equivalent

**New field on data models + display updates.**

### What Changes

**`src/shellguide/core/command_builder.py`** — Add `gui_equivalent: str = ""` to `ShellCommand`. Update all 13 `build_*` functions:

| Command | Finder Equivalent |
|---------|-------------------|
| `ls` | Opening a Finder window to see folder contents |
| `cd` | Double-clicking a folder to open it |
| `mkdir` | Right-click → New Folder |
| `touch` | File → New Document (but empty) |
| `rm` | Move to Trash → Empty Trash (rm skips the Trash) |
| `mv` | Dragging to a new folder, or right-click → Rename |
| `cp` | Option+drag to duplicate |
| `cat` | Opening a file in Quick Look (Spacebar) |
| `open` | Double-clicking a file |
| `du` | Right-click → Get Info (file size) |
| `find` | Cmd+F in Finder, or Spotlight |
| `stat` | Right-click → Get Info |

**`src/shellguide/widgets/command_log.py`** — Add a third line to `log_command` showing the GUI equivalent (dimmed, with desktop icon prefix).

**`src/shellguide/core/challenges.py`** — Add `gui_equivalent: str = ""` to `Challenge`. Populate for all 40 challenges.

**`src/shellguide/screens/teach_screen.py`** — Show `gui_equivalent` after CORRECT/ACCEPTABLE feedback.

### Steps
1. Add `gui_equivalent` field to `ShellCommand` dataclass
2. Write gui_equivalent strings for all 13 `build_*` functions
3. Update `CommandLog.log_command` to display it
4. Test in file browser learn mode
5. Add `gui_equivalent` field to `Challenge` dataclass
6. Populate for all 40 challenges
7. Update `teach_screen.py` feedback display
8. Test in teach mode

---

## Feature 5: Cheat Sheet That Builds As You Learn

**New data model, new widget, integration with TeachScreen.**

### New Files

**`src/shellguide/core/cheat_sheet.py`** — `CheatSheet` class with `CheatSheetEntry(command, description, lesson_id, category)`. In-memory dict keyed by command string. Methods: `add()`, `entries`, `entries_by_category()`, `count`.

**`src/shellguide/widgets/cheat_sheet_panel.py`** — `CheatSheetPanel(Vertical)` widget showing mastered commands grouped by lesson/category. Hidden by default, toggled with Tab key.

### What Changes

**`src/shellguide/core/challenges.py`** — Add to `Challenge`:
```python
mastered_command: str = ""        # e.g., "ls -l"
mastered_description: str = ""    # e.g., "List files with details"
```
Populate for all 40 challenges.

**`src/shellguide/screens/teach_screen.py`** — Add `CheatSheet` instance. On CORRECT/ACCEPTABLE feedback, add the challenge's `mastered_command` to the sheet and update the panel. Add Tab keybinding to toggle panel visibility.

**`src/shellguide/styles/app.tcss`** — Add `#cheat-sheet-panel` styles (hidden by default, `display: block` when `.visible` class applied).

### Steps
1. Create `cheat_sheet.py` data model
2. Create `cheat_sheet_panel.py` widget
3. Add `mastered_command`/`mastered_description` fields to `Challenge`
4. Populate for all 40 challenges
5. Add `CheatSheet` instance + `CheatSheetPanel` to `TeachScreen`
6. Wire up feedback → cheat sheet updates
7. Add Tab toggle keybinding + CSS
8. Test: complete several challenges, verify cheat sheet populates

### Optional Enhancement
Persist to `~/.shellguide/cheat_sheet.json` so it survives restarts. Defer this unless requested.

---

## Feature 1: Progressive Difficulty

**Build last — most complex, touches executor, data model, and UI.**

### What Changes

**`src/shellguide/core/challenges.py`** — Add to `Challenge`:
```python
difficulty: int = 1                              # 1–3
allowed_operators: frozenset[str] = frozenset()  # e.g., frozenset({"&&"})
```

Add to `Lesson`:
```python
requires_lesson: str | None = None   # id of prerequisite lesson
```

Add 2–3 new advanced lessons (Lessons 9–10) with chained commands:
- **Lesson 9: Combining Commands** — `mkdir project && cd project`, `touch file && cat file`, etc.
- **Lesson 10: Real Workflows** — Multi-step tasks that mirror actual development workflows

**`src/shellguide/core/executor.py`** — Three changes:
1. `_check_blocked_operators` accepts an `allowed: frozenset[str]` parameter to exempt operators per-challenge
2. New `_run_chained` function that splits on `&&` and executes each part sequentially (stops on first failure, mimicking real `&&` behavior)
3. `run_in_sandbox` gains an `allowed_operators` parameter, routes to `_run_chained` when `&&` is both allowed and present

**`src/shellguide/screens/teach_screen.py`** — Three changes:
1. Pass `self._challenge.allowed_operators` to `run_in_sandbox`
2. Track `_completed_lessons: set[str]` — add lesson ID on completion
3. Lesson gating: check `requires_lesson` before starting next lesson

### Steps
1. Add `allowed_operators` and `difficulty` fields to `Challenge`
2. Add `requires_lesson` field to `Lesson`
3. Update `_check_blocked_operators` to accept allowed set
4. Add `_run_chained` function to executor
5. Update `run_in_sandbox` signature and routing logic
6. Update `TeachScreen.on_input_submitted` to pass `allowed_operators`
7. Add `_completed_lessons` tracking and gating logic
8. Write Lesson 9 (Combining Commands) with `allowed_operators=frozenset({"&&"})`
9. Write Lesson 10 (Real Workflows) with multi-step challenges
10. Update `ALL_LESSONS` tuple
11. Set `requires_lesson` on existing lessons for sequential gating (lesson 2 requires lesson 1, etc.)
12. Test: verify single-command lessons unaffected; verify chained commands work; verify gating prevents skipping

---

## Key Files Reference

| File | Modified By Features |
|------|---------------------|
| `src/shellguide/core/challenges.py` | All 6 |
| `src/shellguide/screens/teach_screen.py` | 1, 4, 5, 6 |
| `src/shellguide/core/executor.py` | 1 |
| `src/shellguide/core/command_builder.py` | 2, 4 |
| `src/shellguide/core/command_explainer.py` | 2 |
| `src/shellguide/widgets/command_log.py` | 4 |
| `src/shellguide/styles/app.tcss` | 5 |
| `src/shellguide/core/cheat_sheet.py` | 5 (new) |
| `src/shellguide/widgets/cheat_sheet_panel.py` | 5 (new) |
