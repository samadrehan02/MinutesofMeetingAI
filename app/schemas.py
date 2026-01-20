from pydantic import BaseModel
from typing import List

class TopicDetail(BaseModel):
    topic: str
    details: str

class DecisionDetail(BaseModel):
    decision: str
    rationale: str

class Task(BaseModel):
    description: str
    owner: str
    deadline: str

class MinutesOfMeeting(BaseModel):
    meeting_summary: str
    key_topics: List[TopicDetail]
    decisions: List[DecisionDetail]
    tasks: List[Task]