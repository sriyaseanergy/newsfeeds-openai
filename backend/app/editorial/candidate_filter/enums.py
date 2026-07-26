from enum import Enum


class CandidateDecision(str, Enum):
    CLASSIFY = "CLASSIFY"
    SKIP = "SKIP"

