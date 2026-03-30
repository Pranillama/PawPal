# PawPal+ 🐾

**PawPal+** is a smart pet care scheduling app built with Python and Streamlit. It helps busy pet owners stay consistent with their pet's daily care by generating a prioritised, conflict-aware daily plan from a list of tasks.

## Features

| Feature | Description |
|---|---|
| **Owner + multi-pet setup** | Create an owner profile with a daily time budget, then add any number of pets with health notes. |
| **Task management** | Add tasks with type, duration, priority (1–5), optional preferred time, and optional recurrence days. Filter tasks by type or completion status. |
| **Priority-first scheduling** | The daily plan is built greedily — highest priority tasks are scheduled first until the time budget is exhausted. Skipped tasks are displayed with an explanation. |
| **Time-based sorting** | The schedule can be viewed in priority order or chronological order. Untimed tasks are always placed last. |
| **Recurring task rescheduling** | Completing a recurring task does not permanently close it. The next due date is automatically calculated using `timedelta` — daily tasks reschedule to tomorrow, weekly-pattern tasks find the next matching weekday. |
| **Conflict detection** | Overlapping time windows (`[start, start + duration)`) are detected and shown as prominent error banners before the plan, with specific overlap details. |
| **Scheduling reasoning** | An expandable "How was this schedule built?" section explains the algorithm's decisions in plain English. |

## 📸 Demo

> Add a screenshot here after launching the app. Use `streamlit run app.py` to start it.

## Scenario

A busy pet owner needs help staying consistent with pet care. PawPal+ helps them:

- Track pet care tasks (walks, feeding, meds, enrichment, grooming, etc.)
- Consider constraints (time available, priority, owner preferences)
- Produce a daily plan and explain why it chose that plan

## Testing PawPal+

Run the full test suite with:

```bash
python -m pytest
```

The suite covers 27 tests across five areas:

| Area | What is tested |
|---|---|
| **Task** | `mark_complete()` changes status; recurring tasks are NOT permanently completed; `is_due_today()` respects weekday recurrence and `next_due_date` |
| **Pet** | Task count increases on `add_task()`; completed tasks are excluded from `get_tasks_due_today()` |
| **Owner** | Pet back-reference is set on `add_pet()`; `set_available_time()` updates the budget |
| **Scheduler — scheduling** | Time budget is never exceeded; high-priority tasks are chosen over low; skipped tasks are recorded; empty-pet and all-tasks-exceed-budget edge cases |
| **Scheduler — algorithms** | `sort_by_time()` returns chronological order with untimed tasks last; `filter_tasks()` by type and status; recurring daily tasks reschedule to tomorrow via `timedelta`; conflict detection catches overlapping windows but not non-overlapping ones; untimed tasks never trigger conflicts |

**Confidence level: ★★★★☆ (4/5)**
The scheduler's core logic — priority ordering, time budget enforcement, recurring rescheduling, and conflict detection — is fully covered. The main untested area is the Streamlit UI layer (`app.py`) and integration between multiple pets sharing a single owner's time budget simultaneously.

## Getting started

### Setup

```bash
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Smarter Scheduling

PawPal+ goes beyond a simple task list with four algorithmic features:

| Feature | How it works |
|---|---|
| **Priority-first scheduling** | Tasks are sorted by priority (1–5). The scheduler greedily fills the owner's daily time budget, highest priority first. Skipped tasks are surfaced explicitly. |
| **Time-based sorting** | `Scheduler.sort_by_time()` sorts tasks by `preferred_time` (HH:MM) using a lambda key. Tasks without a preferred time are placed last. |
| **Filtering** | `Scheduler.filter_tasks()` accepts optional `completed` and `task_type` filters so the UI or CLI can show relevant subsets (e.g., only walks, only incomplete tasks). |
| **Recurring task rescheduling** | When `task.mark_complete()` is called on a recurring task, the task is not permanently completed. Instead, `next_due_date` is advanced using `timedelta` — daily tasks reschedule to tomorrow, weekly-pattern tasks find the next matching weekday. |
| **Conflict detection** | `Scheduler.detect_conflicts()` compares `[start, start + duration)` intervals for all timed tasks. Overlapping windows produce a warning rather than an error, so the plan is still returned. |

### Suggested workflow

1. Read the scenario carefully and identify requirements and edge cases.
2. Draft a UML diagram (classes, attributes, methods, relationships).
3. Convert UML into Python class stubs (no logic yet).
4. Implement scheduling logic in small increments.
5. Add tests to verify key behaviors.
6. Connect your logic to the Streamlit UI in `app.py`.
7. Refine UML so it matches what you actually built.
