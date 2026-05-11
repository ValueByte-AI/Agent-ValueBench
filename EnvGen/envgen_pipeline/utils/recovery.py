"""Shared recovery primitives for fault-tolerant env generation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class RecoverableAPIError(RuntimeError):
    """API/network/quota errors that can be resumed after human intervention."""

    provider: str
    model: str
    profile_name: str
    base_url: str
    kind: str
    message: str
    original_type: str = ""

    def __post_init__(self) -> None:
        RuntimeError.__init__(
            self,
            f"[{self.kind}] profile={self.profile_name or 'default'} "
            f"provider={self.provider} model={self.model}: {self.message}",
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provider": self.provider,
            "model": self.model,
            "profile_name": self.profile_name,
            "base_url": self.base_url,
            "kind": self.kind,
            "message": self.message,
            "original_type": self.original_type,
        }


class RecoverableStepError(RuntimeError):
    """A step paused because an API failure happened mid-item."""

    def __init__(
        self,
        *,
        step_label: str,
        error: RecoverableAPIError,
        partial_item: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(f"{step_label} paused: {format_api_error(error)}")
        self.step_label = step_label
        self.error = error
        self.partial_item = partial_item


class StageBlockedError(RuntimeError):
    """A stage cannot merge/finalize because some shards are still blocked."""

    def __init__(self, stage_label: str, blocked_shards: List[Dict[str, Any]]) -> None:
        message_lines = [f"[{stage_label}] blocked shards detected:"]
        for shard in blocked_shards:
            error = shard.get("error") or {}
            message_lines.append(
                "  - "
                f"shard={shard.get('shard_id')} profile={shard.get('profile_name')} "
                f"state={shard.get('state')} step={shard.get('current_step')} "
                f"kind={error.get('kind', 'unknown')} msg={error.get('message', '')}"
            )
        super().__init__("\n".join(message_lines))
        self.stage_label = stage_label
        self.blocked_shards = blocked_shards


class StageCoordinatorActiveError(RuntimeError):
    """Another coordinator already owns the stage-level runtime lock."""

    def __init__(
        self,
        stage_label: str,
        *,
        leader_pid: int | None = None,
    ) -> None:
        message = f"[{stage_label}] active coordinator is already running"
        if leader_pid:
            message += f" (pid={leader_pid})"
        message += ". Wait for it to finish, or rerun with --resume to signal blocked shards."
        super().__init__(message)
        self.stage_label = stage_label
        self.leader_pid = leader_pid


class StageResumeSignalHandled(RuntimeError):
    """A resume command only signaled the active coordinator, then exited."""

    def __init__(
        self,
        stage_label: str,
        *,
        signaled_shards: List[Dict[str, Any]],
        leader_pid: int | None = None,
    ) -> None:
        if signaled_shards:
            details = ", ".join(
                f"shard={item.get('shard_id')} profile={item.get('profile_name')}"
                for item in signaled_shards
            )
            message = (
                f"[{stage_label}] active coordinator is already running"
                + (f" (pid={leader_pid})" if leader_pid else "")
                + f". Sent resume signal for blocked shards: {details}"
            )
        else:
            message = (
                f"[{stage_label}] active coordinator is already running"
                + (f" (pid={leader_pid})" if leader_pid else "")
                + ". No blocked shards needed a resume signal."
            )
        super().__init__(message)
        self.stage_label = stage_label
        self.signaled_shards = signaled_shards
        self.leader_pid = leader_pid


def is_recoverable_api_error(exc: BaseException) -> bool:
    return isinstance(exc, RecoverableAPIError)


def is_recoverable_step_error(exc: BaseException) -> bool:
    return isinstance(exc, RecoverableStepError)


def format_api_error(error: RecoverableAPIError) -> str:
    return (
        f"profile={error.profile_name or 'default'} kind={error.kind} "
        f"model={error.model} message={error.message}"
    )
