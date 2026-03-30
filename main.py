"""
main.py — CLI demo script for PawPal+.
Run: python main.py
"""

from pawpal_system import Owner, Pet, Task, Scheduler


def main():
    # --- Owner ---
    owner = Owner(name="Alex", available_minutes_per_day=90)

    # --- Pets ---
    buddy = Pet(name="Buddy", species="Dog", age=3, health_notes="Needs joint supplement")
    luna  = Pet(name="Luna",  species="Cat", age=5, health_notes="Indoor only")

    owner.add_pet(buddy)
    owner.add_pet(luna)

    # --- Tasks for Buddy (dog) ---
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
        preferred_time="08:00",
        is_recurring=True,
        recurrence_days=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
    ))
    buddy.add_task(Task(
        title="Fetch / enrichment play",
        task_type="enrichment",
        duration_minutes=20,
        priority=3,
        preferred_time="17:00",
    ))
    buddy.add_task(Task(
        title="Grooming brush",
        task_type="grooming",
        duration_minutes=15,
        priority=2,
        preferred_time="18:00",
    ))

    # --- Tasks for Luna (cat) ---
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
        title="Interactive play session",
        task_type="enrichment",
        duration_minutes=15,
        priority=3,
        preferred_time="19:00",
    ))

    # --- Generate and display schedules ---
    for pet in owner.get_pets():
        scheduler = Scheduler(owner=owner, pet=pet)
        schedule  = scheduler.generate_plan()

        print()
        print(schedule.display())
        print()
        print(scheduler.explain_reasoning())
        print()


if __name__ == "__main__":
    main()
