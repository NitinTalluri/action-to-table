import pytest

from api.v2.models.links import (
    V2GenericLinkRead,
    V2AcatLinkRead,
    V2MceLinkRead,
    V2PartyLinkRead,
    V2SmartLinkRead,
)


@pytest.mark.parametrize(
    "link_type, link_model",
    [
        ("acat_links", V2AcatLinkRead),
        ("mce_links", V2MceLinkRead),
        ("party_links", V2PartyLinkRead),
        ("smart_links", V2SmartLinkRead),
    ],
)
def test_generic_model_parsing(link_type, link_model):
    """
    Given a link model that has a __root__ field with a Union
    Check that we can parse an dictionary of form {"link_type": "acat_links", "dc_engagement_id": 1, "id": 1}
    """
    data = {
        "link_type": link_type,
        "dc_engagement_id": 1,
        "id": 1,
    }
    link = V2GenericLinkRead.parse_obj(data)
    assert isinstance(link.__root__, link_model)
