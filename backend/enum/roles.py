from enum import Enum
class Role(str, Enum):
    ADMIN = "admin"
    WRITER = "writer"
    USER = "user"
