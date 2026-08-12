from enum import Enum


class ArticleType(str, Enum):
    NEWS = "News"
    ADVISORY = "Advisory"
    RESEARCH = "Research"
    TUTORIAL = "Tutorial"
    OPINION = "Opinion"
    RELEASE = "Release"
    BLOG = "Blog"
    DOCUMENTATION = "Documentation"
    OTHER = "Other"


class Severity(str, Enum):
    NONE = "None"
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


class Actionability(str, Enum):
    INFORMATIONAL = "Informational"
    MONITOR = "Monitor"
    ACTION_RECOMMENDED = "Action Recommended"
    IMMEDIATE_ACTION = "Immediate Action"


class Audience(str, Enum):
    ENGINEERING = "Engineering"
    SECURITY = "Security"
    LEADERSHIP = "Leadership"
    AI = "AI"
    GENERAL = "General"

