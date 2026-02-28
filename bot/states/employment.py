from aiogram.fsm.state import State, StatesGroup


class UpdateEmploymentFSM(StatesGroup):
    """
    /update flow:
    confirm_end_current → company_name → work_city → work_format
    → position_title → position_level → confirm
    """

    # Ask whether to close the current job record
    confirm_end_current = State()

    # New job details
    company_name = State()
    work_city = State()
    work_format = State()
    position_title = State()
    position_level = State()

    # Final confirmation before saving
    confirm = State()
