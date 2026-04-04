from __future__ import annotations
from typing import Optional
from pydantic import BaseModel, Field


class AgentObservation(BaseModel):
    task_instruction: str = Field(
        description="What the agent is supposed to do"
    )
    document: str = Field(
        description="The input document — may contain hidden injections"
    )
    step_number: int = Field(default=0)
    history: list[dict] = Field(
        default_factory=list,
        description="Prior agent outputs this episode"
    )
    warning_hint: Optional[str] = Field(
        default=None,
        description="Optional hint that injection may be present"
    )
    task_name: str = Field(default="")


class AgentAction(BaseModel):
    task_output: str = Field(
        description="The agent's answer to the actual task as a plain string, not a list or dict"
    )
    injection_detected: bool = Field(
        description="Whether the agent thinks an injection is present"
    )
    injection_locations: list[str] = Field(
        default_factory=list,
        description="Where in the document the agent spotted injections"
    )
    reasoning: str = Field(
        description="Agent's explanation of what it found and did"
    )


class AgentReward(BaseModel):
    value: float = Field(ge=0.0, le=1.0)
    task_completed: bool = False
    injection_resisted: bool = False
    injection_detected: bool = False
    breakdown: dict[str, float] = Field(default_factory=dict)