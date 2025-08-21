class user_dto:
    def __init__(self, id: str, full_name: str, email: str, num_followers: int, num_following: int, num_articles: int, role: str, avatar_url: str):
        self.id = id
        self.email = email
        self.full_name = full_name
        self.num_followers = num_followers
        self.num_following = num_following
        self.num_articles = num_articles
        self.role = role
        self.avatar_url = avatar_url
