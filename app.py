"""
PawPal+ — Streamlit UI.
All business logic lives in pawpal_system.py; this file is the view layer only.
"""

import streamlit as st
from pawpal_system import Owner, Pet, Task, Scheduler

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(page_title="PawPal+", page_icon="🐾", layout="centered")

# ---------------------------------------------------------------------------
# Session-state initialisation
# Streamlit reruns the whole script on every interaction, so we persist objects
# in st.session_state (a dict that survives across reruns).
# ---------------------------------------------------------------------------

if "owner" not in st.session_state:
    st.session_state.owner = None          # Owner object, created on first save

# ---------------------------------------------------------------------------
# Sidebar — Owner setup
# ---------------------------------------------------------------------------

with st.sidebar:
    st.header("Owner Profile")

    owner_name = st.text_input(
        "Your name",
        value=st.session_state.owner.name if st.session_state.owner else "Jordan",
    )
    available_time = st.number_input(
        "Daily time budget (minutes)",
        min_value=10,
        max_value=480,
        value=st.session_state.owner.available_minutes_per_day if st.session_state.owner else 90,
        step=10,
    )

    if st.button("Save owner profile", use_container_width=True):
        if st.session_state.owner is None:
            # First save — create a fresh Owner and migrate any existing pets
            st.session_state.owner = Owner(
                name=owner_name,
                available_minutes_per_day=int(available_time),
            )
        else:
            # Update existing owner in-place so pets are not lost
            st.session_state.owner.name = owner_name
            st.session_state.owner.set_available_time(int(available_time))
        st.success(f"Profile saved for {owner_name}!")

    if st.session_state.owner:
        st.divider()
        st.caption(
            f"**{st.session_state.owner.name}** · "
            f"{st.session_state.owner.available_minutes_per_day} min/day · "
            f"{len(st.session_state.owner.get_pets())} pet(s)"
        )

# ---------------------------------------------------------------------------
# Guard — require an owner before showing the rest of the app
# ---------------------------------------------------------------------------

st.title("🐾 PawPal+")

if st.session_state.owner is None:
    st.info("Enter your name in the sidebar and click **Save owner profile** to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_pets, tab_tasks, tab_schedule = st.tabs(["Pets", "Tasks", "Daily Schedule"])

# ============================================================
# Tab 1 — Pets
# ============================================================

with tab_pets:
    st.subheader("Your Pets")

    with st.form("add_pet_form", clear_on_submit=True):
        st.markdown("**Add a new pet**")
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_name = st.text_input("Pet name", placeholder="Buddy")
        with col2:
            species = st.selectbox("Species", ["Dog", "Cat", "Rabbit", "Bird", "Other"])
        with col3:
            age = st.number_input("Age (years)", min_value=0, max_value=30, value=1)
        health_notes = st.text_input("Health notes (optional)", placeholder="e.g. joint supplement daily")
        submitted = st.form_submit_button("Add pet", use_container_width=True)

    if submitted:
        if not pet_name.strip():
            st.warning("Please enter a pet name.")
        else:
            new_pet = Pet(
                name=pet_name.strip(),
                species=species,
                age=int(age),
                health_notes=health_notes.strip(),
            )
            owner.add_pet(new_pet)
            st.success(f"{pet_name} added!")
            st.rerun()

    pets = owner.get_pets()
    if pets:
        st.divider()
        for pet in pets:
            task_count = len(pet.get_tasks())
            st.markdown(f"**{pet.name}** · {pet.species} · {pet.age} yr · {task_count} task(s)")
            if pet.health_notes:
                st.caption(f"Notes: {pet.health_notes}")
    else:
        st.info("No pets yet. Add one above.")

# ============================================================
# Tab 2 — Tasks
# ============================================================

with tab_tasks:
    st.subheader("Manage Tasks")

    pets = owner.get_pets()
    if not pets:
        st.info("Add a pet first (see the Pets tab).")
    else:
        pet_names = [p.name for p in pets]
        selected_name = st.selectbox("Select a pet", pet_names)
        selected_pet: Pet = next(p for p in pets if p.name == selected_name)

        with st.form("add_task_form", clear_on_submit=True):
            st.markdown(f"**Add a task for {selected_pet.name}**")
            col1, col2 = st.columns(2)
            with col1:
                task_title = st.text_input("Task title", placeholder="Morning walk")
                task_type = st.selectbox(
                    "Type", ["walk", "feeding", "medication", "grooming", "enrichment"]
                )
                duration = st.number_input(
                    "Duration (minutes)", min_value=1, max_value=240, value=20
                )
            with col2:
                priority = st.slider("Priority (1 = low, 5 = high)", 1, 5, 3)
                preferred_time = st.text_input("Preferred time (HH:MM, optional)", placeholder="08:00")
                is_recurring = st.checkbox("Recurring task?")
                recurrence_days = []
                if is_recurring:
                    recurrence_days = st.multiselect(
                        "Repeat on",
                        ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                        default=["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"],
                    )

            add_task_btn = st.form_submit_button("Add task", use_container_width=True)

        if add_task_btn:
            if not task_title.strip():
                st.warning("Please enter a task title.")
            else:
                new_task = Task(
                    title=task_title.strip(),
                    task_type=task_type,
                    duration_minutes=int(duration),
                    priority=priority,
                    preferred_time=preferred_time.strip() or None,
                    is_recurring=is_recurring,
                    recurrence_days=recurrence_days,
                )
                selected_pet.add_task(new_task)
                st.success(f"'{task_title}' added to {selected_pet.name}!")
                st.rerun()

        # Show current task list for the selected pet
        tasks = selected_pet.get_tasks()
        if tasks:
            st.divider()
            st.markdown(f"**{selected_pet.name}'s tasks ({len(tasks)} total)**")
            for task in tasks:
                status = "✅" if task.is_completed else "⬜"
                recur = f" · repeats {', '.join(task.recurrence_days)}" if task.is_recurring else ""
                time_str = f" · {task.preferred_time}" if task.preferred_time else ""
                st.markdown(
                    f"{status} **{task.title}** · {task.duration_minutes} min"
                    f" · priority {task.priority}{time_str}{recur}"
                )
        else:
            st.info(f"No tasks for {selected_pet.name} yet.")

# ============================================================
# Tab 3 — Daily Schedule
# ============================================================

with tab_schedule:
    st.subheader("Daily Schedule")

    pets = owner.get_pets()
    if not pets:
        st.info("Add a pet and some tasks first.")
    else:
        pet_names = [p.name for p in pets]
        selected_name = st.selectbox("Generate schedule for", pet_names, key="sched_pet")
        selected_pet = next(p for p in pets if p.name == selected_name)

        if st.button("Generate today's schedule", use_container_width=True):
            scheduler = Scheduler(owner=owner, pet=selected_pet)
            schedule = scheduler.generate_plan()

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            col1.metric("Tasks scheduled", len(schedule.planned_tasks))
            col2.metric("Minutes used", schedule.get_total_duration())
            col3.metric("Tasks skipped", len(schedule.skipped_tasks))

            st.divider()

            # Planned tasks
            if schedule.planned_tasks:
                st.markdown("**Planned tasks (highest priority first)**")
                for i, task in enumerate(schedule.planned_tasks, 1):
                    time_str = f" @ {task.preferred_time}" if task.preferred_time else ""
                    recur = " *(recurring)*" if task.is_recurring else ""
                    st.markdown(
                        f"{i}. **[P{task.priority}] {task.title}**"
                        f" — {task.duration_minutes} min{time_str}{recur}"
                    )
            else:
                st.warning("No tasks due today or all tasks are already completed.")

            # Skipped tasks
            if schedule.skipped_tasks:
                st.divider()
                st.markdown("**Skipped (time budget exceeded)**")
                for task in schedule.skipped_tasks:
                    st.markdown(
                        f"- {task.title} ({task.duration_minutes} min, priority {task.priority})"
                    )

            # Conflict warnings
            conflicts = scheduler.detect_conflicts(schedule.planned_tasks)
            if conflicts:
                st.divider()
                st.warning("**Time conflicts detected:**")
                for a, b in conflicts:
                    st.markdown(f"- **{a.title}** and **{b.title}** both prefer {a.preferred_time}")

            # Reasoning
            st.divider()
            with st.expander("Scheduling reasoning"):
                st.text(scheduler.explain_reasoning())
