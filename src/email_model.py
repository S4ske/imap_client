class Email:
    def __init__(self, email_id: int, sender: str = "", description: str = "", body: list[str] | None = None) -> None:
        self.id = email_id
        self.sender = sender
        self.description = description
        self.body = body if body else []

    def add_body_component(self, component: str) -> None:
        self.body.append(component)
