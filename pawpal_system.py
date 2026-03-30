"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Module-level helper
# ---------------------------------------------------------------------------

def _time_to_minutes(time_str: str) -> int:
    """Convert an 'HH:MM' string to minutes since midnight."""
    h, m = map(int, time_str.split(":"))
    return h * 60 + m


# ---------------------------------------------------------------------------
# Task
# ---------------------------------------------------------------------------

@dataclass
class Task:
    """A single pet-care task (walk, feeding, medication, etc.)."""

    title: str
    task_type: str                          # "walk" | "feeding" | "medication" | "grooming" | "enrichment"
    duration_minutes: int
    priority: int                           # 1 (low) – 5 (high)
    preferred_time: Optional[str] = None   # e.g. "08:00"
    is_recurring: bool = False
    recurrence_days: list[str] = field(default_factory=list)  # e.g. ["Mon", "Wed", "Fri"]
    is_completed: bool = False
    next_due_date: Optional[datetime.date] = None  # set after completing a recurring task

    def mark_complete(self) -> None:
        """Mark task done; recurring tasks auto-reschedule to their next occurrence."""
        if self.is_recurring:
            # Advance the next due date instead of permanently completing
            self.next_due_date = self._next_occurrence()
            # is_completed stays False — the task recurs
        else:
            self.is_completed = True

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        today = datetime.date.today()

        if self.is_completed:
            # Non-recurring tasks permanently done
            return False

        if self.is_recurring:
            if self.next_due_date is not None:
                # Recurring task was completed — check if next occurrence has arrived
                return today >= self.next_due_date
            # Never completed yet — check by weekday
            return today.strftime("%a") in self.recurrence_days

        # One-off task that hasn't been completed
        return True

    def _next_occurrence(self) -> datetime.date:
        """Calculate the next date this recurring task falls due."""
        today = datetime.date.today()
        all_days = {"Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"}

        # Daily (every day of the week) → tomorrow
        if set(self.recurrence_days) >= all_days:
            return today + datetime.timedelta(days=1)

        # Weekly-ish — find nearest future weekday in recurrence_days
        weekday_map = {"Mon": 0, "Tue": 1, "Wed": 2, "Thu": 3,
                       "Fri": 4, "Sat": 5, "Sun": 6}
        today_num = today.weekday()
        deltas = []
        for day in self.recurrence_days:
            delta = (weekday_map[day] - today_num) % 7
            deltas.append(delta if delta > 0 else 7)  # 0 means today → next week
        return today + datetime.timedelta(days=min(deltas))

    def __lt__(self, other: Task) -> bool:
        """Higher priority value sorts first (descending order)."""
        return self.priority > other.priority


# ---------------------------------------------------------------------------
# Pet
# ---------------------------------------------------------------------------

@dataclass
class Pet:
    """Represents a pet owned by an Owner."""

    name: str
    species: str
    age: int
    health_notes: str = ""
    owner: Optional[Owner] = field(default=None, repr=False)
    _tasks: list[Task] = field(default_factory=list, repr=False)

    def add_task(self, task: Task) -> None:
        """Append a task to this pet's task list."""
        self._tasks.append(task)

    def get_tasks(self) -> list[Task]:
        """Return all tasks registered for this pet."""
        return list(self._tasks)

    def get_tasks_due_today(self) -> list[Task]:
        """Return tasks that are due today and not permanently completed."""
        return [t for t in self._tasks if t.is_due_today()]


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their daily time availability."""

    def __init__(self, name: str, available_minutes_per_day: int = 120, preferences: dict = None):
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences: dict = preferences or {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner and set the back-reference."""
        pet.owner = self
        self._pets.append(pet)

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        return list(self._pets)

    def set_available_time(self, minutes: int) -> None:
        """Update the owner's daily time budget in minutes."""
        self.available_minutes_per_day = minutes


# ---------------------------------------------------------------------------
# Schedule
# ---------------------------------------------------------------------------

class Schedule:
    """An ordered daily plan of tasks for one pet."""

    def __init__(self, owner: Owner, pet: Pet, date: datetime.date = None):
        self.owner = owner
        self.pet = pet
        self.date: datetime.date = date or datetime.date.today()
        self.planned_tasks: list[Task] = []
        self.skipped_tasks: list[Task] = []   # tasks excluded due to time/conflict

    def add_task(self, task: Task) -> None:
        """Append a task to the planned schedule."""
        self.planned_tasks.append(task)

    def remove_task(self, task: Task) -> None:
        """Remove a task from the planned schedule."""
        self.planned_tasks.remove(task)

    def get_total_duration(self) -> int:
        """Return the total minutes consumed by all planned tasks."""
        return sum(t.duration_minutes for t in self.planned_tasks)

    def display(self) -> str:
        """Return a formatted, human-readable string of the daily plan."""
        lines = [
            f"{'=' * 50}",
            f"  Daily Schedule for {self.pet.name} — {self.date}",
            f"  Owner: {self.owner.name}  |  Budget: {self.owner.available_minutes_per_day} min",
            f"{'=' * 50}",
        ]

        if not self.planned_tasks:
            lines.append("  (no tasks scheduled today)")
        else:
            for i, task in enumerate(self.planned_tasks, 1):
                time_str = f"  @ {task.preferred_time}" if task.preferred_time else ""
                recurring = " [recurring]" if task.is_recurring else ""
                lines.append(
                    f"  {i}. [P{task.priority}] {task.title}"
                    f" ({task.duration_minutes} min){time_str}{recurring}"
                )

        lines.append(f"\n  Used: {self.get_total_duration()} / {self.owner.available_minutes_per_day} min")

        if self.skipped_tasks:
            lines.append("\n  Skipped (time budget exceeded):")
            for task in self.skipped_tasks:
                lines.append(f"    - {task.title} ({task.duration_minutes} min, priority {task.priority})")

        lines.append("=" * 50)
        return "\n".join(lines)


# ---------------------------------------------------------------------------
# Scheduler
# ---------------------------------------------------------------------------

class Scheduler:
    """Algorithm layer — reads Owner + Pet data and produces a Schedule."""

    def __init__(self, owner: Owner, pet: Pet):
        self.owner = owner
        self.pet = pet

    def sort_by_priority(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by priority (highest first)."""
        return sorted(tasks)

    def sort_by_time(self, tasks: list[Task]) -> list[Task]:
        """Return tasks sorted by preferred_time (earliest first); untimed tasks go last."""
        return sorted(
            tasks,
            key=lambda t: _time_to_minutes(t.preferred_time) if t.preferred_time else float("inf"),
        )

    def filter_tasks(
        self,
        tasks: list[Task],
        completed: Optional[bool] = None,
        task_type: Optional[str] = None,
    ) -> list[Task]:
        """
        Filter a task list by completion status and/or task type.

        Args:
            tasks:      Source list to filter.
            completed:  True → completed only, False → incomplete only, None → no filter.
            task_type:  E.g. 'walk', 'feeding'; None means no filter.
        """
        result = tasks
        if completed is not None:
            result = [t for t in result if t.is_completed == completed]
        if task_type is not None:
            result = [t for t in result if t.task_type == task_type]
        return result

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """
        Return pairs of tasks whose scheduled time windows overlap.

        Two tasks conflict when their [start, start + duration) intervals intersect.
        Only tasks with a preferred_time are evaluated.
        """
        conflicts = []
        timed = [t for t in tasks if t.preferred_time]
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                a, b = timed[i], timed[j]
                a_start = _time_to_minutes(a.preferred_time)
                a_end   = a_start + a.duration_minutes
                b_start = _time_to_minutes(b.preferred_time)
                b_end   = b_start + b.duration_minutes
                # Intervals overlap when neither ends before the other starts
                if a_start < b_end and b_start < a_end:
                    conflicts.append((a, b))
        return conflicts

    def generate_plan(self) -> Schedule:
        """
        Build and return a Schedule for today.

        Algorithm:
        1. Collect incomplete tasks due today from the pet.
        2. Sort by priority (highest first); break ties by preferred_time (earliest first).
        3. Greedily add tasks until the owner's time budget is exhausted.
        4. Record leftover tasks in skipped_tasks.
        """
        schedule = Schedule(owner=self.owner, pet=self.pet)

        # Primary: priority (highest first); secondary: time (earliest first)
        tasks = self.pet.get_tasks_due_today()
        tasks = sorted(
            tasks,
            key=lambda t: (
                -t.priority,
                _time_to_minutes(t.preferred_time) if t.preferred_time else float("inf"),
            ),
        )

        budget = self.owner.available_minutes_per_day
        used = 0
        for task in tasks:
            if used + task.duration_minutes <= budget:
                schedule.add_task(task)
                used += task.duration_minutes
            else:
                schedule.skipped_tasks.append(task)

        return schedule

    def explain_reasoning(self) -> str:
        """Return a plain-English explanation of how the plan was constructed."""
        schedule = self.generate_plan()
        total_considered = len(schedule.planned_tasks) + len(schedule.skipped_tasks)
        lines = [
            f"Scheduling reasoning for {self.pet.name}:",
            f"  Available time  : {self.owner.available_minutes_per_day} min",
            f"  Tasks considered: {total_considered}",
            f"  Tasks scheduled : {len(schedule.planned_tasks)} ({schedule.get_total_duration()} min used)",
            f"  Tasks skipped   : {len(schedule.skipped_tasks)}",
            "",
            "  Tasks were sorted by priority (highest first), with ties broken by",
            "  preferred time (earliest first). The scheduler added each task",
            "  greedily until the daily time budget was exhausted.",
        ]

        conflicts = self.detect_conflicts(schedule.planned_tasks)
        if conflicts:
            lines.append(f"\n  Warning — {len(conflicts)} time conflict(s) detected:")
            for a, b in conflicts:
                lines.append(
                    f"    '{a.title}' ({a.preferred_time}–{_time_to_minutes(a.preferred_time) + a.duration_minutes} min) "
                    f"overlaps '{b.title}' ({b.preferred_time})"
                )

        return "\n".join(lines)
