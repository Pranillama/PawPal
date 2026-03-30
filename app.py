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
    st.session_state.owner = None

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
            st.session_state.owner = Owner(
                name=owner_name,
                available_minutes_per_day=int(available_time),
            )
        else:
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
st.caption("Smart pet care scheduling — priority-first, conflict-aware, recurring-task friendly.")

if st.session_state.owner is None:
    st.info("Enter your name in the sidebar and click **Save owner profile** to get started.")
    st.stop()

owner: Owner = st.session_state.owner

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------

tab_pets, tab_tasks, tab_schedule = st.tabs(["🐾 Pets", "📋 Tasks", "📅 Daily Schedule"])

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
        health_notes = st.text_input("Health notes (optional)", placeholder="e.g. needs joint supplement")
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
            due_count = len(pet.get_tasks_due_today())
            total_count = len(pet.get_tasks())
            with st.container(border=True):
                cols = st.columns([3, 1])
                with cols[0]:
                    st.markdown(f"**{pet.name}** · {pet.species} · {pet.age} yr")
                    if pet.health_notes:
                        st.caption(f"Health notes: {pet.health_notes}")
                with cols[1]:
                    st.metric("Due today", due_count, delta=f"{total_count} total", delta_color="off")
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

        # --- Add task form ---
        with st.form("add_task_form", clear_on_submit=True):
            st.markdown(f"**Add a task for {selected_pet.name}**")
            col1, col2 = st.columns(2)
            with col1:
                task_title = st.text_input("Task title", placeholder="Morning walk")
                task_type = st.selectbox(
                    "Type", ["walk", "feeding", "medication", "grooming", "enrichment"]
                )
                duration = st.number_input("Duration (minutes)", min_value=1, max_value=240, value=20)
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

        # --- Filter + task list ---
        all_tasks = selected_pet.get_tasks()
        if all_tasks:
            st.divider()

            # Filter controls using Scheduler.filter_tasks()
            scheduler = Scheduler(owner=owner, pet=selected_pet)
            fc1, fc2 = st.columns(2)
            with fc1:
                type_filter = st.selectbox(
                    "Filter by type",
                    ["all", "walk", "feeding", "medication", "grooming", "enrichment"],
                    key="task_type_filter",
                )
            with fc2:
                status_filter = st.selectbox(
                    "Filter by status",
                    ["all", "incomplete", "completed"],
                    key="task_status_filter",
                )

            filtered = scheduler.filter_tasks(
                all_tasks,
                completed={"incomplete": False, "completed": True}.get(status_filter),
                task_type=None if type_filter == "all" else type_filter,
            )

            st.markdown(
                f"**{selected_pet.name}'s tasks** — showing {len(filtered)} of {len(all_tasks)}"
            )

            if not filtered:
                st.info("No tasks match the selected filters.")
            else:
                PRIORITY_COLOURS = {5: "🔴", 4: "🟠", 3: "🟡", 2: "🔵", 1: "⚪"}
                for task in filtered:
                    status_icon = "✅" if task.is_completed else "⬜"
                    p_icon = PRIORITY_COLOURS.get(task.priority, "")
                    time_str = f" · {task.preferred_time}" if task.preferred_time else ""
                    recur = f" · 🔁 {', '.join(task.recurrence_days)}" if task.is_recurring else ""
                    next_due = f" · next: {task.next_due_date}" if task.next_due_date else ""
                    st.markdown(
                        f"{status_icon} {p_icon} **{task.title}** "
                        f"({task.task_type} · {task.duration_minutes} min · P{task.priority})"
                        f"{time_str}{recur}{next_due}"
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
        col_sel, col_sort = st.columns([2, 1])
        with col_sel:
            selected_name = st.selectbox("Generate schedule for", pet_names, key="sched_pet")
        with col_sort:
            sort_mode = st.selectbox("Display order", ["By priority", "By time"], key="sort_mode")

        selected_pet = next(p for p in pets if p.name == selected_name)

        if st.button("Generate today's schedule", use_container_width=True, type="primary"):
            scheduler = Scheduler(owner=owner, pet=selected_pet)
            schedule  = scheduler.generate_plan()

            # --- Summary metrics ---
            budget_pct = int(schedule.get_total_duration() / owner.available_minutes_per_day * 100)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("Scheduled", len(schedule.planned_tasks))
            c2.metric("Minutes used", f"{schedule.get_total_duration()} / {owner.available_minutes_per_day}")
            c3.metric("Budget used", f"{budget_pct}%")
            c4.metric("Skipped", len(schedule.skipped_tasks))

            # --- Conflict warnings (prominent, before the plan) ---
            conflicts = scheduler.detect_conflicts(schedule.planned_tasks)
            if conflicts:
                st.divider()
                for a, b in conflicts:
                    st.error(
                        f"**Scheduling conflict:** '{a.title}' ({a.preferred_time}, "
                        f"{a.duration_minutes} min) overlaps with '{b.title}' "
                        f"({b.preferred_time}, {b.duration_minutes} min). "
                        f"Consider adjusting one of these times."
                    )

            st.divider()

            # --- Planned tasks ---
            if schedule.planned_tasks:
                display_tasks = (
                    scheduler.sort_by_time(schedule.planned_tasks)
                    if sort_mode == "By time"
                    else schedule.planned_tasks  # already priority-sorted by generate_plan()
                )

                sort_label = "chronological order" if sort_mode == "By time" else "priority order"
                st.markdown(f"**Planned tasks** *(sorted by {sort_label})*")

                PRIORITY_COLOURS = {5: "🔴", 4: "🟠", 3: "🟡", 2: "🔵", 1: "⚪"}
                for i, task in enumerate(display_tasks, 1):
                    p_icon    = PRIORITY_COLOURS.get(task.priority, "")
                    time_str  = f"@ {task.preferred_time}  " if task.preferred_time else ""
                    recur_str = " 🔁" if task.is_recurring else ""
                    with st.container(border=True):
                        st.markdown(
                            f"{i}. {p_icon} **{task.title}**{recur_str}  \n"
                            f"   {time_str}{task.duration_minutes} min · Priority {task.priority} · {task.task_type}"
                        )
            else:
                st.warning("No tasks due today, or all tasks are already completed.")

            # --- Skipped tasks ---
            if schedule.skipped_tasks:
                st.divider()
                with st.expander(f"Skipped tasks ({len(schedule.skipped_tasks)}) — time budget exceeded"):
                    for task in schedule.skipped_tasks:
                        st.markdown(
                            f"- **{task.title}** · {task.duration_minutes} min · P{task.priority}"
                        )
                    st.caption(
                        "These tasks were excluded because adding them would exceed your daily "
                        f"time budget of {owner.available_minutes_per_day} minutes. "
                        "Increase your budget or remove lower-priority tasks to fit them in."
                    )

            # --- Reasoning ---
            st.divider()
            with st.expander("How was this schedule built?"):
                st.markdown(
                    "Tasks were **sorted by priority** (highest first). Where priorities tied, "
                    "tasks with an earlier preferred time were scheduled first. "
                    "The scheduler then added tasks **greedily** until your daily time budget was exhausted."
                )
                st.code(scheduler.explain_reasoning(), language=None)
