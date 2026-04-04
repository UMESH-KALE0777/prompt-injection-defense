"""
Core OpenEnv-compliant environment.
Manages episode state, delegates grading, handles adaptive injections.
"""
from __future__ import annotations
from typing import Any

from .models import AgentObservation, AgentAction, AgentReward
from .tasks import build_tasks, get_hard_doc_for_turn, Task
from .grader import grade


class PromptInjectionEnv:

    def __init__(self, task_name: str = "obvious_injection"):
        self._tasks = build_tasks()
        if task_name not in self._tasks:
            raise ValueError(
                f"Unknown task: {task_name}. "
                f"Choose from {list(self._tasks.keys())}"
            )
        self._task_name = task_name
        self._task: Task = self._tasks[task_name]
        self._step: int = 0
        self._done: bool = False
        self._history: list[dict] = []
        self._last_obs: AgentObservation | None = None

    # ── OpenEnv API ──────────────────────────────────────────────────────────

    def reset(self) -> AgentObservation:
        # Rebuild tasks so injections are freshly randomised each episode
        self._tasks = build_tasks()
        self._task = self._tasks[self._task_name]
        self._step = 0
        self._done = False
        self._history = []

        obs = AgentObservation(
            task_instruction=self._task.instruction,
            document=self._task.base_document,
            step_number=0,
            history=[],
            warning_hint=self._task.warning_hint,
            task_name=self._task_name,
        )
        self._last_obs = obs
        return obs

    def step(
        self, action: AgentAction
    ) -> tuple[AgentObservation, AgentReward, bool, dict[str, Any]]:

        if self._done:
            raise RuntimeError("Episode is finished — call reset() first.")

        self._step += 1

        # Record history
        self._history.append({
            "step": self._step,
            "output": action.task_output,
            "detected": action.injection_detected,
        })

        # Grade the action
        reward = grade(
            action=action,
            correct_keywords=self._task.correct_keywords,
            forbidden_keywords=self._task.forbidden_keywords,
            injection_actually_present=True,  # always True in our env
            difficulty=self._task.difficulty,
        )

        # Check if episode is done
        done = (
            reward.value >= 0.9
            or self._step >= self._task.max_steps
        )
        self._done = done

        # For hard task — update document with next adaptive injection
        if self._task_name == "adaptive_injection" and not done:
            next_doc = get_hard_doc_for_turn(self._step)
        else:
            next_doc = self._task.base_document

        obs = AgentObservation(
            task_instruction=self._task.instruction,
            document=next_doc,
            step_number=self._step,
            history=list(self._history),
            warning_hint=self._task.warning_hint,
            task_name=self._task_name,
        )
        self._last_obs = obs

        info = {
            "task": self._task_name,
            "difficulty": self._task.difficulty,
            "step": self._step,
            "reward_breakdown": reward.breakdown,
        }

        return obs, reward, done, info

    def state(self) -> dict[str, Any]:
        return {
            "task": self._task_name,
            "difficulty": self._task.difficulty,
            "step_number": self._step,
            "done": self._done,
            "history_length": len(self._history),
            "max_steps": self._task.max_steps,
        }

    def close(self):
        pass