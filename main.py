"""
main.py — CLI demo script for PawPal+.
Demonstrates: priority scheduling, time-based sorting, filtering,
              recurring-task rescheduling, and conflict detection.
Run: python main.py
"""

import datetime
from pawpal_system import Owner, Pet, Task, Scheduler


def section(title: str) -> None:
    print(f"\n{'─' * 50}")
    print(f"  {title}")
    print(f"{'─' * 50}")


def main():
    # ------------------------------------------------------------------ #
    # Setup: owner + two pets
    # ------------------------------------------------------------------ #
    owner = Owner(name="Alex", available_minutes_per_day=90)

    buddy = Pet(name="Buddy", species="Dog", age=3, health_notes="Needs joint supplement")
    luna  = Pet(name="Luna",  species="Cat", age=5, health_notes="Indoor only")

    owner.add_pet(buddy)
    owner.add_pet(luna)

    # ------------------------------------------------------------------ #
    # Tasks for Buddy — added OUT OF ORDER intentionally
    # ------------------------------------------------------------------ #
    buddy.add_task(Task(
        title="Evening walk",
        task_type="walk",
        duration_minutes=30,
        priority=3,
        preferred_time="18:00",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    buddy.add_task(Task(
        title="Morning walk",
        task_type="walk",
        duration_minutes=30,
        priority=5,
        preferred_time="07:00",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    buddy.add_task(Task(
        title="Breakfast feeding",
        task_type="feeding",
        duration_minutes=10,
        priority=5,
        preferred_time="07:30",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    buddy.add_task(Task(
        title="Joint supplement",
        task_type="medication",
        duration_minutes=5,
        priority=4,
        preferred_time="07:35",   # overlaps breakfast (07:30–07:40) → conflict demo
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    buddy.add_task(Task(
        title="Grooming brush",
        task_type="grooming",
        duration_minutes=15,
        priority=2,
        preferred_time="19:00",
    ))

    # Tasks for Luna
    luna.add_task(Task(
        title="Morning feeding",
        task_type="feeding",
        duration_minutes=10,
        priority=5,
        preferred_time="07:30",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    luna.add_task(Task(
        title="Litter box cleaning",
        task_type="grooming",
        duration_minutes=10,
        priority=4,
        preferred_time="09:00",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    luna.add_task(Task(
        title="Interactive play",
        task_type="enrichment",
        duration_minutes=15,
        priority=3,
        preferred_time="19:00",
    ))

    scheduler_buddy = Scheduler(owner=owner, pet=buddy)
    scheduler_luna  = Scheduler(owner=owner, pet=luna)

    # ------------------------------------------------------------------ #
    # 1. Daily schedule (priority-first, time as tiebreaker)
    # ------------------------------------------------------------------ #
    section("1. DAILY SCHEDULE")
    for scheduler in [scheduler_buddy, scheduler_luna]:
        print(scheduler.generate_plan().display())

    # ------------------------------------------------------------------ #
    # 2. Sort by time (earliest first)
    # ------------------------------------------------------------------ #
    section("2. BUDDY'S TASKS SORTED BY TIME")
    by_time = scheduler_buddy.sort_by_time(buddy.get_tasks_due_today())
    for task in by_time:
        time = task.preferred_time or "no time"
        print(f"  {time}  [{task.task_type}] {task.title} ({task.duration_minutes} min)")

    # ------------------------------------------------------------------ #
    # 3. Filter tasks
    # ------------------------------------------------------------------ #
    section("3. FILTERING — walks only")
    walks = scheduler_buddy.filter_tasks(buddy.get_tasks(), task_type="walk")
    for t in walks:
        print(f"  {t.title}")

    section("3. FILTERING — incomplete tasks only")
    incomplete = scheduler_buddy.filter_tasks(buddy.get_tasks(), completed=False)
    print(f"  {len(incomplete)} incomplete task(s) for Buddy")

    # ------------------------------------------------------------------ #
    # 4. Recurring task auto-reschedule
    # ------------------------------------------------------------------ #
    section("4. RECURRING TASK AUTO-RESCHEDULE")
    morning_walk = next(t for t in buddy.get_tasks() if t.title == "Morning walk")
    print(f"  Before: is_completed={morning_walk.is_completed}, next_due_date={morning_walk.next_due_date}")
    morning_walk.mark_complete()
    print(f"  After:  is_completed={morning_walk.is_completed}, next_due_date={morning_walk.next_due_date}")
    expected_next = datetime.date.today() + datetime.timedelta(days=1)
    print(f"  Expected next due: {expected_next}  ✓" if morning_walk.next_due_date == expected_next
          else f"  Next due: {morning_walk.next_due_date}")

    # ------------------------------------------------------------------ #
    # 5. Conflict detection (duration-overlap based)
    # ------------------------------------------------------------------ #
    section("5. CONFLICT DETECTION")
    plan = scheduler_buddy.generate_plan()
    conflicts = scheduler_buddy.detect_conflicts(plan.planned_tasks)
    if conflicts:
        print(f"  {len(conflicts)} conflict(s) found:")
        for a, b in conflicts:
            print(f"    ⚠  '{a.title}' ({a.preferred_time}, {a.duration_minutes} min) "
                  f"overlaps '{b.title}' ({b.preferred_time}, {b.duration_minutes} min)")
    else:
        print("  No conflicts detected.")

    # ------------------------------------------------------------------ #
    # 6. Reasoning
    # ------------------------------------------------------------------ #
    section("6. SCHEDULER REASONING — Luna")
    print(scheduler_luna.explain_reasoning())


if __name__ == "__main__":
    main()
