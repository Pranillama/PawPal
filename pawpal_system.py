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
        """Mark this task as completed."""
        pass

    def is_due_today(self) -> bool:
        """Return True if this task should appear in today's schedule."""
        pass

    def __lt__(self, other: Task) -> bool:
        """Higher priority value sorts first (descending)."""
        pass


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
        """Add a care task to this pet's task list."""
        pass

    def get_tasks(self) -> list[Task]:
        """Return all tasks for this pet."""
        pass

    def get_tasks_due_today(self) -> list[Task]:
        """Return only the tasks that are due today."""
        pass


# ---------------------------------------------------------------------------
# Owner
# ---------------------------------------------------------------------------

class Owner:
    """Represents the pet owner and their availability."""

    def __init__(self, name: str, available_minutes_per_day: int = 120, preferences: dict = None):
        self.name = name
        self.available_minutes_per_day = available_minutes_per_day
        self.preferences: dict = preferences or {}
        self._pets: list[Pet] = []

    def add_pet(self, pet: Pet) -> None:
        """Register a pet under this owner."""
        pass

    def get_pets(self) -> list[Pet]:
        """Return all pets belonging to this owner."""
        pass

    def set_available_time(self, minutes: int) -> None:
        """Update how many minutes per day the owner has for pet care."""
        pass


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
        """Append a task to the plan."""
        pass

    def remove_task(self, task: Task) -> None:
        """Remove a task from the plan."""
        pass

    def get_total_duration(self) -> int:
        """Return the sum of all planned task durations in minutes."""
        pass

    def display(self) -> str:
        """Return a human-readable string of the daily plan."""
        pass


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
        pass

    def detect_conflicts(self, tasks: list[Task]) -> list[tuple]:
        """Return pairs of tasks whose preferred times overlap."""
        pass

    def generate_plan(self) -> Schedule:
        """
        Build and return a Schedule for today.

        Algorithm outline:
        1. Collect tasks due today from the pet.
        2. Sort by priority (highest first).
        3. Greedily add tasks until available time is exhausted.
        4. Detect and flag any time conflicts.
        """
        pass

    def explain_reasoning(self) -> str:
        """Return a plain-English explanation of how the plan was constructed."""
        pass
