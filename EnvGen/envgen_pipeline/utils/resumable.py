"""Helpers for resumable list-based step execution."""

from __future__ import annotations

from collections import deque
from concurrent.futures import FIRST_COMPLETED, Future, wait
from copy import deepcopy
from typing import Any, Callable, Deque, Dict, Iterable, List, Tuple

from tqdm import tqdm

from utils.call_llm import get_current_api_profile
from utils.context_executor import ContextThreadPoolExecutor
from utils.process_file import path_exists, read_file, save_file
from utils.recovery import RecoverableAPIError, RecoverableStepError


ItemKeyFn = Callable[[Dict[str, Any]], Any]
ItemCompleteFn = Callable[[Dict[str, Any]], bool]
ItemProcessFn = Callable[[Dict[str, Any]], Dict[str, Any]]


def _format_progress_desc(step_label: str, progress_desc: str | None = None) -> str:
    base_desc = str(progress_desc or step_label).strip() or step_label
    profile = get_current_api_profile()
    profile_name = profile.name if profile and str(profile.name).strip() else "default"
    return f"{base_desc} [{profile_name}]"


def count_completed_items(
    *,
    ordered_keys: List[Any],
    result_map: Dict[Any, Dict[str, Any]],
    is_complete_fn: ItemCompleteFn,
) -> int:
    return sum(
        1
        for key in ordered_keys
        if key in result_map and is_complete_fn(result_map[key])
    )


def build_resume_progress(
    *,
    ordered_keys: List[Any],
    result_map: Dict[Any, Dict[str, Any]],
    is_complete_fn: ItemCompleteFn,
    step_label: str,
    progress_desc: str | None = None,
    progress_position: int | None = None,
):
    completed = count_completed_items(
        ordered_keys=ordered_keys,
        result_map=result_map,
        is_complete_fn=is_complete_fn,
    )
    return tqdm(
        total=len(ordered_keys),
        initial=completed,
        desc=_format_progress_desc(step_label, progress_desc),
        unit="item",
        dynamic_ncols=True,
        leave=True,
        position=progress_position,
        bar_format="{desc}: {n_fmt}/{total_fmt} |{bar}| {elapsed}<{remaining}",
    )


def _completion_delta(
    *,
    previous_item: Dict[str, Any] | None,
    current_item: Dict[str, Any] | None,
    is_complete_fn: ItemCompleteFn,
) -> int:
    previous_complete = bool(previous_item is not None and is_complete_fn(previous_item))
    current_complete = bool(current_item is not None and is_complete_fn(current_item))
    return int(current_complete) - int(previous_complete)


def load_resume_state(
    input_items: Iterable[Dict[str, Any]],
    output_path: str,
    *,
    key_fn: ItemKeyFn,
) -> Tuple[List[Any], Dict[Any, Dict[str, Any]], List[Dict[str, Any]]]:
    """Return ordered keys, existing result map, and working items for this run."""
    input_list = list(input_items)
    ordered_keys = [key_fn(item) for item in input_list]
    existing_map: Dict[Any, Dict[str, Any]] = {}

    if path_exists(output_path):
        existing = read_file(output_path)
        if isinstance(existing, list):
            for item in existing:
                if isinstance(item, dict):
                    existing_map[key_fn(item)] = item

    working_items: List[Dict[str, Any]] = []
    for item in input_list:
        key = key_fn(item)
        if key in existing_map:
            working_items.append(deepcopy(existing_map[key]))
        else:
            working_items.append(deepcopy(item))
    return ordered_keys, existing_map, working_items


def save_resume_state(
    output_path: str,
    *,
    ordered_keys: List[Any],
    result_map: Dict[Any, Dict[str, Any]],
) -> None:
    save_file(
        output_path,
        [deepcopy(result_map[key]) for key in ordered_keys if key in result_map],
    )


def run_sequential_step(
    *,
    items: Iterable[Dict[str, Any]],
    output_path: str,
    key_fn: ItemKeyFn,
    is_complete_fn: ItemCompleteFn,
    process_fn: ItemProcessFn,
    save_every: int,
    step_label: str,
    progress_desc: str | None = None,
    progress_position: int | None = None,
) -> List[Dict[str, Any]]:
    ordered_keys, result_map, working_items = load_resume_state(items, output_path, key_fn=key_fn)
    save_every = max(1, int(save_every))
    since_save = 0
    progress = build_resume_progress(
        ordered_keys=ordered_keys,
        result_map=result_map,
        is_complete_fn=is_complete_fn,
        step_label=step_label,
        progress_desc=progress_desc,
        progress_position=progress_position,
    )

    try:
        for item in working_items:
            key = key_fn(item)
            existing = result_map.get(key)
            if existing is not None and is_complete_fn(existing):
                continue
            try:
                result_map[key] = process_fn(item)
            except RecoverableStepError as exc:
                if exc.partial_item is not None:
                    result_map[key] = deepcopy(exc.partial_item)
                delta = _completion_delta(
                    previous_item=existing,
                    current_item=result_map.get(key),
                    is_complete_fn=is_complete_fn,
                )
                if delta > 0:
                    progress.update(delta)
                save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
                raise
            except RecoverableAPIError as exc:
                save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
                raise RecoverableStepError(
                    step_label=step_label,
                    error=exc,
                    partial_item=deepcopy(item),
                ) from exc
            delta = _completion_delta(
                previous_item=existing,
                current_item=result_map.get(key),
                is_complete_fn=is_complete_fn,
            )
            if delta > 0:
                progress.update(delta)
            since_save += 1
            if since_save >= save_every:
                save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
                since_save = 0
    except KeyboardInterrupt:
        save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
        raise
    finally:
        progress.close()

    save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
    return [result_map[key] for key in ordered_keys if key in result_map]


def run_parallel_step(
    *,
    items: Iterable[Dict[str, Any]],
    output_path: str,
    key_fn: ItemKeyFn,
    is_complete_fn: ItemCompleteFn,
    process_fn: ItemProcessFn,
    save_every: int,
    max_workers: int,
    step_label: str,
    progress_desc: str | None = None,
    progress_position: int | None = None,
) -> List[Dict[str, Any]]:
    ordered_keys, result_map, working_items = load_resume_state(items, output_path, key_fn=key_fn)
    pending: Deque[Dict[str, Any]] = deque(
        item
        for item in working_items
        if not (key_fn(item) in result_map and is_complete_fn(result_map[key_fn(item)]))
    )

    if not pending:
        save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
        return [result_map[key] for key in ordered_keys if key in result_map]

    save_every = max(1, int(save_every))
    max_workers = max(1, int(max_workers))
    in_flight: Dict[Future, Tuple[Any, Dict[str, Any]]] = {}
    since_save = 0
    recoverable_exc: RecoverableStepError | None = None
    progress = build_resume_progress(
        ordered_keys=ordered_keys,
        result_map=result_map,
        is_complete_fn=is_complete_fn,
        step_label=step_label,
        progress_desc=progress_desc,
        progress_position=progress_position,
    )

    executor = ContextThreadPoolExecutor(max_workers=max_workers)
    try:
        while pending and len(in_flight) < max_workers:
            item = pending.popleft()
            future = executor.submit(process_fn, deepcopy(item))
            in_flight[future] = (key_fn(item), deepcopy(item))

        while in_flight:
            done, _ = wait(in_flight.keys(), return_when=FIRST_COMPLETED)
            for future in done:
                key, original_item = in_flight.pop(future)
                existing = result_map.get(key)
                try:
                    result = future.result()
                except RecoverableStepError as exc:
                    if exc.partial_item is not None:
                        result_map[key] = deepcopy(exc.partial_item)
                    recoverable_exc = exc
                except RecoverableAPIError as exc:
                    recoverable_exc = RecoverableStepError(
                        step_label=step_label,
                        error=exc,
                        partial_item=deepcopy(original_item),
                    )
                    result_map[key] = deepcopy(original_item)
                else:
                    result_map[key] = result
                    since_save += 1
                delta = _completion_delta(
                    previous_item=existing,
                    current_item=result_map.get(key),
                    is_complete_fn=is_complete_fn,
                )
                if delta > 0:
                    progress.update(delta)

                if since_save >= save_every or recoverable_exc is not None:
                    save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
                    since_save = 0

            if recoverable_exc is not None:
                for other in list(in_flight.keys()):
                    other.cancel()
                in_flight.clear()
                pending.clear()
                raise recoverable_exc

            while pending and len(in_flight) < max_workers:
                item = pending.popleft()
                future = executor.submit(process_fn, deepcopy(item))
                in_flight[future] = (key_fn(item), deepcopy(item))
    except KeyboardInterrupt:
        save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
        raise
    finally:
        executor.shutdown(wait=True, cancel_futures=True)
        progress.close()

    save_resume_state(output_path, ordered_keys=ordered_keys, result_map=result_map)
    return [result_map[key] for key in ordered_keys if key in result_map]
