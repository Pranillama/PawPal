"""
Tests for PawPal+ core logic.
Run with: python -m pytest
"""

import pytest
from pawpal_system import Owner, Pet, Task, Schedule, Scheduler


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def sample_task():
    return Task(title="Morning walk", task_type="walk", duration_minutes=30, priority=5)


@pytest.fixture
def sample_pet():
    return Pet(name="Buddy", species="Dog", age=3)


@pytest.fixture
def sample_owner():
    return Owner(name="Alex", available_minutes_per_day=90)


# ---------------------------------------------------------------------------
# Task tests
# ---------------------------------------------------------------------------

def test_mark_complete_changes_status(sample_task):
    """mark_complete() should set is_completed to True."""
    assert sample_task.is_completed is False
    sample_task.mark_complete()
    assert sample_task.is_completed is True


def test_mark_complete_idempotent(sample_task):
    """Calling mark_complete() twice should leave task completed."""
    sample_task.mark_complete()
    sample_task.mark_complete()
    assert sample_task.is_completed is True


def test_non_recurring_task_is_always_due(sample_task):
    """A non-recurring task should always be due today."""
    assert sample_task.is_due_today() is True


def test_recurring_task_due_on_correct_day():
    """A recurring task is only due on its scheduled days."""
    import datetime
    today_abbr = datetime.date.today().strftime("%a")
    other_days = [d for d in ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"] if d != today_abbr]

    due_today = Task("Med", "medication", 5, 4, is_recurring=True, recurrence_days=[today_abbr])
    not_due = Task("Med", "medication", 5, 4, is_recurring=True, recurrence_days=other_days[:1])

    assert due_today.is_due_today() is True
    assert not_due.is_due_today() is False


def test_task_priority_ordering():
    """Higher priority tasks should sort before lower priority tasks."""
    low  = Task("Low",  "enrichment", 10, priority=1)
    high = Task("High", "walk",       30, priority=5)
    mid  = Task("Mid",  "feeding",    10, priority=3)

    sorted_tasks = sorted([low, mid, high])
    assert sorted_tasks[0].title == "High"
    assert sorted_tasks[-1].title == "Low"


# ---------------------------------------------------------------------------
# Pet tests
# ---------------------------------------------------------------------------

def test_add_task_increases_count(sample_pet, sample_task):
    """Adding a task to a Pet should increase the task count by one."""
    before = len(sample_pet.get_tasks())
    sample_pet.add_task(sample_task)
    assert len(sample_pet.get_tasks()) == before + 1


def test_add_multiple_tasks(sample_pet):
    """Adding three tasks should result in three tasks on the pet."""
    for i in range(3):
        sample_pet.add_task(Task(f"Task {i}", "walk", 10, priority=3))
    assert len(sample_pet.get_tasks()) == 3


def test_completed_task_excluded_from_due_today(sample_pet, sample_task):
    """A completed task should not appear in get_tasks_due_today()."""
    sample_task.mark_complete()
    sample_pet.add_task(sample_task)
    assert sample_task not in sample_pet.get_tasks_due_today()


# ---------------------------------------------------------------------------
# Owner tests
# ---------------------------------------------------------------------------

def test_add_pet_sets_back_reference(sample_owner, sample_pet):
    """add_pet() should set the pet's owner reference."""
    sample_owner.add_pet(sample_pet)
    assert sample_pet.owner is sample_owner


def test_owner_tracks_multiple_pets(sample_owner):
    """Owner should track all added pets."""
    p1 = Pet("Buddy", "Dog", 3)
    p2 = Pet("Luna",  "Cat", 5)
    sample_owner.add_pet(p1)
    sample_owner.add_pet(p2)
    assert len(sample_owner.get_pets()) == 2


def test_set_available_time(sample_owner):
    """set_available_time() should update the owner's time budget."""
    sample_owner.set_available_time(60)
    assert sample_owner.available_minutes_per_day == 60


# ---------------------------------------------------------------------------
# Scheduler tests
# ---------------------------------------------------------------------------

def test_generate_plan_respects_time_budget(sample_owner, sample_pet):
    """Scheduler should not exceed the owner's available time budget."""
    for i in range(5):
        sample_pet.add_task(Task(f"Task {i}", "walk", 30, priority=3))
    sample_owner.add_pet(sample_pet)
    sample_owner.set_available_time(60)

    scheduler = Scheduler(owner=sample_owner, pet=sample_pet)
    schedule = scheduler.generate_plan()

    assert schedule.get_total_duration() <= sample_owner.available_minutes_per_day


def test_generate_plan_prioritises_high_priority(sample_owner, sample_pet):
    """Scheduler should include high-priority tasks before low-priority ones."""
    sample_pet.add_task(Task("Low task",  "enrichment", 40, priority=1))
    sample_pet.add_task(Task("High task", "walk",       40, priority=5))
    sample_owner.add_pet(sample_pet)
    sample_owner.set_available_time(50)  # only room for one 40-min task

    scheduler = Scheduler(owner=sample_owner, pet=sample_pet)
    schedule = scheduler.generate_plan()

    titles = [t.title for t in schedule.planned_tasks]
    assert "High task" in titles
    assert "Low task" not in titles


def test_skipped_tasks_recorded(sample_owner, sample_pet):
    """Tasks that don't fit the budget should appear in skipped_tasks."""
    sample_pet.add_task(Task("Task A", "walk",    60, priority=5))
    sample_pet.add_task(Task("Task B", "feeding", 60, priority=3))
    sample_owner.add_pet(sample_pet)
    sample_owner.set_available_time(60)

    scheduler = Scheduler(owner=sample_owner, pet=sample_pet)
    schedule = scheduler.generate_plan()

    assert len(schedule.skipped_tasks) == 1
    assert schedule.skipped_tasks[0].title == "Task B"


def test_detect_conflicts_finds_same_time_tasks(sample_owner, sample_pet):
    """detect_conflicts() should flag tasks sharing the same preferred time."""
    t1 = Task("Walk",    "walk",    30, priority=5, preferred_time="08:00")
    t2 = Task("Feeding", "feeding", 10, priority=4, preferred_time="08:00")
    sample_owner.add_pet(sample_pet)

    scheduler = Scheduler(owner=sample_owner, pet=sample_pet)
    conflicts = scheduler.detect_conflicts([t1, t2])

    assert len(conflicts) == 1
    conflict_titles = {conflicts[0][0].title, conflicts[0][1].title}
    assert conflict_titles == {"Walk", "Feeding"}
