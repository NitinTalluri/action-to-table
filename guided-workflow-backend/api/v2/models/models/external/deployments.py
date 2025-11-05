from . import Model


class DeploymentItem(Model):
    id: str
    name: str
    flow_id: str
    tags: set[str]
