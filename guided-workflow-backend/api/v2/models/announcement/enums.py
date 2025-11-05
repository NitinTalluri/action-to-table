from enum import Enum, IntEnum


class AnnouncementCategory(str, Enum):
    """
    Enum for representing different categories of announcements.

    Attributes:
        Bugs: Represents announcements related to bugs.
        Campaigns: Represents announcements related to campaigns.
        TrainingRequirements: Represents announcements related to training requirements.
        Releases: Represents announcements related to releases.
        General: Represents general announcements.
        Alerts: Represents alerts such as scheduled downtime.
        ProcessSDPChanges: Represents announcements related to process or SDP changes.
    """

    Bugs = "Bugs"
    Campaigns = "Campaigns"
    TrainingRequirements = "Training Requirements"
    Releases = "Releases"
    General = "General"
    Alerts = "Alerts"
    ProcessSDPChanges = "Process / SDP Changes"

    def __str__(self):
        """
        Returns a string representation of the enum member.

        Returns:
            str: The value of the enum member.
        """
        return self.value


class AnnouncementPriority(IntEnum):
    """
    Enum for representing different priority levels of announcements.

    Attributes:
        Low: Represents low priority announcements.
        Medium: Represents medium priority announcements.
        High: Represents high priority announcements.
    """

    Low = 10
    Medium = 20
    High = 30
