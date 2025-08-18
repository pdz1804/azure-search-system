from enum import Enum
class Status(str, Enum):
    LIKE = "like"
    DISLIKE = "dislike"
    BOOKMARK = "bookmark"

    def __str__(self):
        return self.value
