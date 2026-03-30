"""
PawPal+ — backend logic layer.
All core classes live here; app.py imports from this module.
"""

from __future__ import annotations

import datetime
from dataclasses import dataclass, field
from typing import Optional


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

    def mark_complete(self) -> None:
        """Set this task's completion status to True."""
        self.is_completed = True

    def is_due_today(self) -> bool:
        """Return True if the task should appear in today's schedule."""
        if not self.is_recurring:
            return True
        today_abbr = datetime.date.today().strftime("%a")  # "Mon", "Tue", …
        return today_abbr in self.recurrence_days

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
        """Return incomplete tasks that are due today."""
        return [t for t in self._tasks if t.is_due_today() and not t.is_completed]


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
        """Return a new list of tasks sorted by priority, highest first."""
        return sorted(tasks)

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple[Task, Task]]:
        """Return pairs of tasks that share the same preferred time slot."""
        conflicts = []
        timed = [t for t in tasks if t.preferred_time]
        for i in range(len(timed)):
            for j in range(i + 1, len(timed)):
                if timed[i].preferred_time == timed[j].preferred_time:
                    conflicts.append((timed[i], timed[j]))
        return conflicts

    def generate_plan(self) -> Schedule:
        """
        Build and return a Schedule for today.

        Algorithm:
        1. Collect incomplete tasks due today from the pet.
        2. Sort by priority (highest first).
        3. Greedily add tasks until the owner's time budget is exhausted.
        4. Record leftover tasks in skipped_tasks.
        """
        schedule = Schedule(owner=self.owner, pet=self.pet)
        tasks = self.sort_by_priority(self.pet.get_tasks_due_today())
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
            "  Tasks were sorted by priority (highest first). The scheduler added each",
            "  task greedily until the daily time budget was exhausted.",
        ]

        conflicts = self.detect_conflicts(schedule.planned_tasks)
        if conflicts:
            lines.append(f"\n  Warning — {len(conflicts)} time conflict(s) detected:")
            for a, b in conflicts:
                lines.append(f"    '{a.title}' and '{b.title}' both prefer {a.preferred_time}")

        return "\n".join(lines)
