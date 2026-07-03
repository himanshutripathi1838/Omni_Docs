from pydantic import BaseModel


class CommandResult(BaseModel):
    task: str
    old_text: str | None = None
    new_text: str | None = None
