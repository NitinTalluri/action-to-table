from . import Model


class V2ReplaceResponsibleUser(Model):
    prev_user_id: int
    new_user_id: int
    booking_contract: int
