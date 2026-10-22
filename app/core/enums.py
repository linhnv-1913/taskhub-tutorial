from enum import StrEnum


class TaskStatus(StrEnum):
    TODO = "TODO"


class TaskPriority(StrEnum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class UserRole(StrEnum):
    USER = "USER"
    ADMIN = "ADMIN"
