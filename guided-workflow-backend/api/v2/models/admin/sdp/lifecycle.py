from . import Model


class AdminSDPLifeCycle(Model):
    lifecycle_id: int
    lifecycle_desc: str
    lifecycle_doc_link: str


class AdminSDPLifeCycleCreate(Model):
    lifecycle_desc: str
    lifecycle_doc_link: str


class AdminSDPLifeCycleEdit(Model):
    lifecycle_id: int
    lifecycle_desc: str
    lifecycle_doc_link: str
