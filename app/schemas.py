from pydantic import BaseModel
from typing import List, Optional

class Task(BaseModel):
    description: str
    owner: Optional[str]
    deadline: Optional[str]

class MinutesOfMeeting(BaseModel):
    meeting_summary: str
    key_topics: List[str]
    decisions: List[str]
    tasks: List[Task]