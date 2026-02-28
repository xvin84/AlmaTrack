from aiogram.fsm.state import State, StatesGroup


class OnboardingFSM(StatesGroup):
    """
    Onboarding flow:
      role → faculty_browse → enrollment_year [→ graduation_year if alumni]
      → employment_status
      → [company_name → work_city → work_format → position_title → position_level]
      → confirm
      → [editing_field → <back to any field state> → confirm]
    """

    # Step 1
    role = State()

    # Step 2 — FSM data: fac_path: list[int], fac_page: int
    faculty_browse = State()

    # Step 3 — FSM data: year_page: int
    enrollment_year = State()
    graduation_year = State()  # alumni only

    # Step 4
    employment_status = State()

    # Step 5 — only when working
    company_name = State()
    work_city = State()
    work_format = State()
    position_title = State()
    position_level = State()

    # Step 6 — summary + confirm
    confirm = State()

    # Edit mode — show list of fields to edit
    # FSM data: is_editing=True, current_edit_field: str
    editing_field = State()
