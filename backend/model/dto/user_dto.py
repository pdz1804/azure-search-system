class user_dto:
    def __init__(self, id: str, full_name: str, email: str, role: str, avatar_url: str):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.role = role
        self.avatar_url = avatar_url
