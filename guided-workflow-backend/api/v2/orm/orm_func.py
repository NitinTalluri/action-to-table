from sqlalchemy.sql.functions import GenericFunction
from sqlalchemy.types import DateTime


class utc_time(GenericFunction):
    type = DateTime
    inherit_cache = True
    identifier = "utc_time"
    name = "sysdate"
