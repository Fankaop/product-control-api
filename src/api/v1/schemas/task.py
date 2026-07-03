from pydantic import BaseModel


class TaskResponse(BaseModel):
    task_id: str
    status: str 
    message:  str | None = None

class TaskStatusResponse(BaseModel):
    task_id: str
    status: str
    result: dict | None = None
