# -*- coding: utf-8 -*-
from __future__ import annotations

from collections import Counter
import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid



class UserInfo(TypedDict):
    _id: str
    name: str
    fitness_goal: str

class WorkoutPlanInfo(TypedDict):
    plan_id: str
    user_id: str
    name: str
    schedule: str

class ExerciseInfo(TypedDict):
    exercise_id: str
    name: str
    type: str

class WorkoutPlanExerciseInfo(TypedDict):
    plan_id: str
    exercise_id: str
    sets: int
    repetitions: int
    order: int
    scheduled_day: str

class _GeneratedEnvImpl:
    def __init__(self):
        # Users: {user_id: UserInfo}
        self.users: Dict[str, UserInfo] = {}
        # WorkoutPlans: {plan_id: WorkoutPlanInfo}
        self.workout_plans: Dict[str, WorkoutPlanInfo] = {}
        # Exercises: {exercise_id: ExerciseInfo}
        self.exercises: Dict[str, ExerciseInfo] = {}
        # WorkoutPlanExercises: {plan_id: List[WorkoutPlanExerciseInfo]}
        self.workout_plan_exercises: Dict[str, List[WorkoutPlanExerciseInfo]] = {}

        # Constraints:
        # - Each WorkoutPlan must be associated with an existing User.
        # - Exercises added to a WorkoutPlan must specify at least sets and repetitions.
        # - An Exercise may only be added to a WorkoutPlan once per scheduled_day unless explicitly allowed.
        # - Schedule information must comply with the plan’s overall schedule constraints.

    def get_user_by_name(self, name: str) -> dict:
        """
        Retrieve user information by their name.

        Args:
            name (str): The name of the user to query.

        Returns:
            dict: {
                "success": True,
                "data": UserInfo  # The user info if found
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - If multiple users have the same name, the first match is returned.
        """
        for user_info in self.users.values():
            if user_info["name"] == name:
                return {"success": True, "data": user_info}
        return {"success": False, "error": "User not found"}

    def get_user_by_id(self, user_id: str) -> dict:
        """
        Retrieve user information by user ID.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict:
                - If found: {"success": True, "data": UserInfo}
                - If not found: {"success": False, "error": "User not found"}
        Constraints:
            - user_id must exist in self.users.
        """
        user_info = self.users.get(user_id)
        if user_info is None:
            return { "success": False, "error": "User not found" }
        return { "success": True, "data": user_info }

    def list_all_users(self) -> dict:
        """
        Return a list of all users in the system.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[UserInfo], # May be empty if no users exist
            }
        """
        return {
            "success": True,
            "data": list(self.users.values())
        }

    def get_workout_plans_by_user(self, user_id: str) -> dict:
        """
        Retrieve all workout plans associated with a specific user.

        Args:
            user_id (str): The unique identifier for the user.

        Returns:
            dict: {
                "success": True,
                "data": List[WorkoutPlanInfo]
            }
            or
            {
                "success": False,
                "error": "User not found"
            }

        Constraints:
            - The user_id must correspond to an existing User in the system.
        """
        if user_id not in self.users:
            return { "success": False, "error": "User not found" }

        plans = [
            plan_info for plan_info in self.workout_plans.values()
            if plan_info["user_id"] == user_id
        ]
        return { "success": True, "data": plans }

    def get_workout_plan_by_id(self, plan_id: str) -> dict:
        """
        Retrieve the details of a specific workout plan given its unique plan ID.

        Args:
            plan_id (str): The unique identifier of the workout plan.

        Returns:
            dict: 
                On success: { "success": True, "data": WorkoutPlanInfo }
                On failure: { "success": False, "error": "Workout plan not found" }
        Constraints:
            - The workout plan with the given ID must exist.
        """
        if plan_id not in self.workout_plans:
            return { "success": False, "error": "Workout plan not found" }

        return { "success": True, "data": self.workout_plans[plan_id] }

    def get_exercise_by_name(self, name: str) -> dict:
        """
        Locate a single exercise in the system by its exact name.

        Args:
            name (str): The name of the exercise to search for.

        Returns:
            dict: {
                "success": True,
                "data": ExerciseInfo
            }
            or
            {
                "success": False,
                "error": "Exercise with name '<name>' not found"
            }
        Constraints:
            - Name matching is case-sensitive.
            - Returns the first match if multiple exercises have the same name.
        """
        for exercise in self.exercises.values():
            if exercise["name"] == name:
                return {"success": True, "data": exercise}
        return {"success": False, "error": f"Exercise with name '{name}' not found"}

    def get_exercise_by_id(self, exercise_id: str) -> dict:
        """
        Retrieve the complete information of a specific exercise by its ID.

        Args:
            exercise_id (str): The unique identifier for the exercise.

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "data": ExerciseInfo  # Full info for the requested exercise
                    }
                On failure:
                    {
                        "success": False,
                        "error": "Exercise not found"
                    }

        Constraints:
            - exercise_id must exist in self.exercises
        """
        exercise = self.exercises.get(exercise_id)
        if not exercise:
            return { "success": False, "error": "Exercise not found" }
        return { "success": True, "data": exercise }

    def list_all_exercises(self) -> dict:
        """
        Return a list of all available (predefined or custom) exercises.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ExerciseInfo]  # List of all exercises (may be empty)
            }
        """
        result = list(self.exercises.values())
        return {"success": True, "data": result}

    def get_plan_exercises(self, plan_id: str) -> dict:
        """
        List all exercises (with configuration) associated with a given workout plan.

        Args:
            plan_id (str): The workout plan's unique identifier.

        Returns:
            dict: {
                "success": True,
                "data": List[dict]  # Each item combines WorkoutPlanExerciseInfo and ExerciseInfo.
            }
            or
            {
                "success": False,
                "error": str
            }
        Constraints:
            - The specified plan_id must exist.
        """
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "Workout plan does not exist."}

        wpe_list = self.workout_plan_exercises.get(plan_id, [])

        result = []
        for wpe in wpe_list:
            exercise_info = self.exercises.get(wpe["exercise_id"])
            if exercise_info:
                # Combine plan-specific info with exercise basic info
                combined = {
                    **wpe,
                    "exercise_info": exercise_info
                }
                result.append(combined)
            else:
                # If the exercise is missing (shouldn't happen), omit or provide warning in future.

                continue

        return {"success": True, "data": result}

    def get_plan_exercise_by_exercise_and_day(self, plan_id: str, exercise_id: str, scheduled_day: str) -> dict:
        """
        Check and retrieve the association of a specific exercise with a given workout plan on a particular scheduled day.

        Args:
            plan_id (str): The ID of the workout plan.
            exercise_id (str): The exercise ID to search for.
            scheduled_day (str): The day (e.g., 'Monday') the exercise is scheduled for.

        Returns:
            dict:
                - If the plan does not exist:
                    { "success": False, "error": "Workout plan does not exist" }
                - If found:
                    { "success": True, "data": WorkoutPlanExerciseInfo }
                - If not found:
                    { "success": True, "data": None }
        Constraints:
            - The workout plan must exist.
            - Will return only the first matching (plan_id, exercise_id, scheduled_day) association if it exists.
        """
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "Workout plan does not exist"}

        plan_exercises = self.workout_plan_exercises.get(plan_id, [])
        for exercise_info in plan_exercises:
            if (exercise_info["exercise_id"] == exercise_id and
                exercise_info["scheduled_day"] == scheduled_day):
                return {"success": True, "data": exercise_info}

        return {"success": True, "data": None}

    def get_plan_schedule(self, plan_id: str) -> dict:
        """
        Retrieve the schedule rules or configured schedule for a workout plan.
    
        Args:
            plan_id (str): The unique identifier of the workout plan.
    
        Returns:
            dict: {
                "success": True,
                "data": str  # The configured schedule/rules of the plan
            }
            or
            {
                "success": False,
                "error": str  # Error message if the plan_id does not exist
            }
    
        Constraints:
            - plan_id must exist in the system.
        """
        plan = self.workout_plans.get(plan_id)
        if not plan:
            return { "success": False, "error": "Workout plan does not exist" }
        return { "success": True, "data": plan["schedule"] }

    def add_exercise_to_plan(
        self,
        plan_id: str,
        exercise_id: str,
        sets: int,
        repetitions: int,
        order: int,
        scheduled_day: str
    ) -> dict:
        """
        Add a specified exercise to a workout plan for a given day, specifying sets, repetitions, and order.

        Args:
            plan_id (str): Workout plan identifier.
            exercise_id (str): Exercise identifier to add.
            sets (int): Number of sets (>0).
            repetitions (int): Number of repetitions per set (>0).
            order (int): The order of the exercise in the day's plan.
            scheduled_day (str): Day for scheduling the exercise (e.g., "Monday").

        Returns:
            dict: {
                "success": True,
                "message": "Exercise added to workout plan for the specified day."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - plan_id must exist.
            - exercise_id must exist.
            - sets and repetitions must both be >0.
            - Exercise cannot be added to the same plan on the same scheduled_day more than once.
        """
        # Check plan exists
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "Workout plan does not exist."}
        # Check exercise exists
        if exercise_id not in self.exercises:
            return {"success": False, "error": "Exercise does not exist."}
        # Check sets and repetitions
        if not (isinstance(sets, int) and sets > 0):
            return {"success": False, "error": "Sets must be a positive integer."}
        if not (isinstance(repetitions, int) and repetitions > 0):
            return {"success": False, "error": "Repetitions must be a positive integer."}
        # Get plan exercises for the plan (empty list if none yet)
        plan_exercises = self.workout_plan_exercises.get(plan_id, [])
        # Check duplicate (exercise already scheduled on the same day)
        for ex in plan_exercises:
            if ex["exercise_id"] == exercise_id and ex["scheduled_day"] == scheduled_day:
                return {"success": False, "error": "Exercise already added to the plan for this day."}
        # Add to plan
        new_entry = {
            "plan_id": plan_id,
            "exercise_id": exercise_id,
            "sets": sets,
            "repetitions": repetitions,
            "order": order,
            "scheduled_day": scheduled_day
        }
        plan_exercises.append(new_entry)
        self.workout_plan_exercises[plan_id] = plan_exercises
        return {"success": True, "message": "Exercise added to workout plan for the specified day."}

    def create_exercise(self, name: str, type: str) -> dict:
        """
        Create a new exercise in the system if it doesn't already exist.

        Args:
            name (str): The name of the exercise.
            type (str): The type/category of the exercise.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Exercise created successfully.",
                    "exercise": ExerciseInfo  # (only if successful)
                }
            or 
                {
                    "success": False,
                    "error": "Reason for failure (e.g., already exists or invalid input)."
                }
        Constraints:
            - No duplicate exercise (same name and type) may be created.
            - Input fields must be non-empty.
        """
        if not name or not type:
            return { "success": False, "error": "Exercise name and type are required." }

        # Check for duplicate (case-insensitive name/type)
        for exercise in self.exercises.values():
            if exercise['name'].strip().lower() == name.strip().lower() and \
               exercise['type'].strip().lower() == type.strip().lower():
                return { "success": False, "error": "Exercise with this name and type already exists." }

        # Generate unique exercise_id
        exercise_id = str(uuid.uuid4())

        new_exercise = {
            "exercise_id": exercise_id,
            "name": name.strip(),
            "type": type.strip(),
        }

        self.exercises[exercise_id] = new_exercise

        return {
            "success": True,
            "message": "Exercise created successfully.",
            "exercise": new_exercise
        }

    def create_workout_plan(self, plan_id: str, user_id: str, name: str, schedule: str) -> dict:
        """
        Create a new workout plan for a user with the specified name and schedule.

        Args:
            plan_id (str): Unique identifier for the workout plan.
            user_id (str): ID of the user for whom the plan is created.
            name (str): Name of the workout plan.
            schedule (str): Schedule of the plan (e.g., "Mon/Wed/Fri" or similar).

        Returns:
            dict: {
                "success": True,
                "message": "Workout plan created for user <user_id>"
            }
            or
            {
                "success": False,
                "error": <Reason>
            }

        Constraints:
            - The user_id must correspond to an existing user.
            - The plan_id must be unique (not already in use).
        """
        if not plan_id or not user_id or not name or not schedule:
            return { "success": False, "error": "All parameters (plan_id, user_id, name, schedule) must be provided and non-empty." }

        if plan_id in self.workout_plans:
            return { "success": False, "error": f"Workout plan with id {plan_id} already exists." }

        if user_id not in self.users:
            return { "success": False, "error": f"User with id {user_id} does not exist." }

        self.workout_plans[plan_id] = {
            "plan_id": plan_id,
            "user_id": user_id,
            "name": name,
            "schedule": schedule
        }
        # Initialize the plan's exercise list as empty
        self.workout_plan_exercises[plan_id] = []

        return { "success": True, "message": f"Workout plan created for user {user_id}" }

    def remove_exercise_from_plan(
        self,
        plan_id: str,
        exercise_id: str,
        scheduled_day: str,
        order: int = None,
    ) -> dict:
        """
        Remove a specific exercise from a workout plan for a given day.

        Args:
            plan_id (str): The identifier of the workout plan.
            exercise_id (str): The identifier of the exercise to remove.
            scheduled_day (str): The day for which the exercise should be removed.
            order (int, optional): The exact order slot to remove when the same exercise
                appears multiple times on the same day. If omitted, only the lowest-order
                matching entry is removed.

        Returns:
            dict: {
                "success": True,
                "message": "Exercise removed from plan for day."
            }
            or
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - The workout plan must exist.
            - The exercise association must exist for the given day in the plan.
            - If order is provided, the exercise association must also match that order.
        """
        if plan_id not in self.workout_plans:
            return { "success": False, "error": "Workout plan does not exist." }
        if plan_id not in self.workout_plan_exercises:
            return { "success": False, "error": "No exercises found for the workout plan." }

        exercises = self.workout_plan_exercises[plan_id]
        matching_entries = []
        for idx, ex in enumerate(exercises):
            if ex["exercise_id"] != exercise_id or ex["scheduled_day"] != scheduled_day:
                continue
            if order is not None and ex["order"] != order:
                continue
            matching_entries.append((idx, ex))

        if not matching_entries:
            if order is not None:
                return {
                    "success": False,
                    "error": "Exercise with given ID, day, and order not found in plan.",
                }
            return { "success": False, "error": "Exercise with given ID and day not found in plan." }

        target_idx, _removed_exercise = min(
            matching_entries,
            key=lambda item: (item[1]["order"], item[0]),
        )
        updated_exercises = exercises[:target_idx] + exercises[target_idx + 1 :]

        self.workout_plan_exercises[plan_id] = updated_exercises
        return {"success": True, "message": "Exercise removed from plan for day."}

    def update_plan_exercise(
        self,
        plan_id: str,
        exercise_id: str,
        scheduled_day: str,
        new_sets: int = None,
        new_repetitions: int = None,
        new_order: int = None,
        new_scheduled_day: str = None,
    ) -> dict:
        """
        Change the sets, repetitions, order, or scheduled day for an exercise in a workout plan.

        Args:
            plan_id (str): The ID of the workout plan.
            exercise_id (str): The ID of the exercise to modify.
            scheduled_day (str): The current scheduled day for the exercise.
            new_sets (int, optional): New number of sets (must be ≥1 if provided).
            new_repetitions (int, optional): New number of repetitions (must be ≥1 if provided).
            new_order (int, optional): New order value (must be ≥1 if provided).
            new_scheduled_day (str, optional): The new scheduled day (must be non-blank if provided).

        Returns:
            dict: {
                "success": True,
                "message": "Exercise in plan updated."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - Plan and exercise must exist.
            - The exercise must be attached to the plan on the given scheduled_day.
            - No duplicate exercise for (plan_id, exercise_id, scheduled_day).
            - sets/repetitions/order must be valid if provided.
            - scheduled_day must be valid if changed.
        """
        # Check plan exists
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "WorkoutPlan not found"}
        # Check exercise exists
        if exercise_id not in self.exercises:
            return {"success": False, "error": "Exercise not found"}
        # Find the exercise entry in the plan/exercise list for this plan and day
        ex_list = self.workout_plan_exercises.get(plan_id, [])
        found = None
        for ex in ex_list:
            if ex["exercise_id"] == exercise_id and ex["scheduled_day"] == scheduled_day:
                found = ex
                break
        if not found:
            return {"success": False, "error": "Exercise not scheduled in plan on specified day"}

        # Checks for new parameters
        if new_sets is not None and new_sets < 1:
            return {"success": False, "error": "Invalid sets: must be ≥1"}
        if new_repetitions is not None and new_repetitions < 1:
            return {"success": False, "error": "Invalid repetitions: must be ≥1"}
        if new_order is not None and new_order < 1:
            return {"success": False, "error": "Invalid order: must be ≥1"}

        # Changing day? Must ensure no duplicate for (plan_id, exercise_id, new_scheduled_day)
        if new_scheduled_day is not None:
            if new_scheduled_day.strip() == "":
                return {"success": False, "error": "scheduled_day cannot be blank"}
            for ex in ex_list:
                # Only fail if the new day/plan/exercise combo exists for a _different_ record
                if (
                    ex["exercise_id"] == exercise_id
                    and ex["scheduled_day"] == new_scheduled_day
                    and ex is not found
                ):
                    return {"success": False, "error": "Exercise already scheduled for this plan and day"}

        # Changing order? Must avoid duplicate order in plan+day
        if new_order is not None:
            for ex in ex_list:
                if (
                    ex["scheduled_day"] == (new_scheduled_day if new_scheduled_day else scheduled_day)
                    and ex["order"] == new_order
                    and ex is not found
                ):
                    return {"success": False, "error": "Another exercise already has that order for this day"}

        # Apply updates
        if new_sets is not None:
            found["sets"] = new_sets
        if new_repetitions is not None:
            found["repetitions"] = new_repetitions
        if new_order is not None:
            found["order"] = new_order
        if new_scheduled_day is not None:
            found["scheduled_day"] = new_scheduled_day

        return {"success": True, "message": "Exercise in plan updated."}

    def reorder_plan_exercises(
        self,
        plan_id: str,
        new_exercise_order: list[str],
        scheduled_day: str = None,
    ) -> dict:
        """
        Change the order of exercises in a workout plan.

        Args:
            plan_id (str): The workout plan identifier.
            new_exercise_order (list of str): Desired exercise_id sequence. Duplicate IDs are
                allowed as long as they match the targeted entries exactly.
            scheduled_day (str, optional): If provided, reorder only that day's exercises.
                If omitted, reorder the entire plan and recompute each day's local order
                values from the supplied flat sequence.

        Returns:
            dict:
                On success:
                    {"success": True, "message": "Exercises reordered in plan <plan_id>."}
                On failure:
                    {"success": False, "error": "reason"}
    
        Constraints:
            - plan_id must exist.
            - The supplied exercise_id sequence must match the targeted entries exactly,
              including duplicates.
        """
        # Check plan existence
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "Workout plan does not exist."}

        if plan_id not in self.workout_plan_exercises or len(self.workout_plan_exercises[plan_id]) == 0:
            return {"success": False, "error": "No exercises found for this workout plan."}

        current_exercises = self.workout_plan_exercises[plan_id]
        if scheduled_day is None:
            target_entries = list(current_exercises)
        else:
            target_entries = [
                ex for ex in current_exercises if ex["scheduled_day"] == scheduled_day
            ]
            if not target_entries:
                return {
                    "success": False,
                    "error": f"No exercises found for workout plan {plan_id} on {scheduled_day}.",
                }

        current_ids = [ex["exercise_id"] for ex in target_entries]
        if Counter(new_exercise_order) != Counter(current_ids):
            return {"success": False, "error": "New order does not match targeted exercises."}

        entries_by_id: Dict[str, List[dict]] = {}
        for ex in target_entries:
            entries_by_id.setdefault(ex["exercise_id"], []).append(ex)

        reordered_entries: List[dict] = []
        for exercise_id in new_exercise_order:
            reordered_entries.append(entries_by_id[exercise_id].pop(0))

        if scheduled_day is None:
            day_order_counters: Dict[str, int] = {}
            for ex in reordered_entries:
                day = ex["scheduled_day"]
                day_order_counters[day] = day_order_counters.get(day, 0) + 1
                ex["order"] = day_order_counters[day]
            self.workout_plan_exercises[plan_id] = reordered_entries
            return {"success": True, "message": f"Exercises reordered in plan {plan_id}."}

        for new_order_idx, ex in enumerate(reordered_entries, 1):
            ex["order"] = new_order_idx

        first_target_idx = next(
            idx for idx, ex in enumerate(current_exercises) if ex["scheduled_day"] == scheduled_day
        )
        before_entries = current_exercises[:first_target_idx]
        after_entries = [
            ex for ex in current_exercises[first_target_idx:] if ex["scheduled_day"] != scheduled_day
        ]
        updated_plan_entries = before_entries + reordered_entries + after_entries

        self.workout_plan_exercises[plan_id] = updated_plan_entries
        return {
            "success": True,
            "message": f"Exercises reordered in plan {plan_id} for {scheduled_day}.",
        }

    def update_plan_schedule(self, plan_id: str, new_schedule: str) -> dict:
        """
        Modify the schedule for an entire workout plan, ensuring all scheduled exercises comply.

        Args:
            plan_id (str): The workout plan to update.
            new_schedule (str): The new schedule string (e.g., comma-separated days).

        Returns:
            dict: {
                "success": True,
                "message": str  # Operation result
            }
            or
            {
                "success": False,
                "error": str  # Description of the error
            }

        Constraints:
            - The plan must exist.
            - All WorkoutPlanExercises scheduled_day must be within the new schedule.
        """
        if plan_id not in self.workout_plans:
            return {"success": False, "error": "Workout plan does not exist."}
    
        # Assume schedule format: comma-separated days, e.g. "Mon,Wed,Fri"
        new_schedule_days = [day.strip() for day in new_schedule.split(",") if day.strip()]

        # Check compliance for all exercises in plan
        exercises = self.workout_plan_exercises.get(plan_id, [])
        for wpe in exercises:
            if wpe["scheduled_day"] not in new_schedule_days:
                return {
                    "success": False,
                    "error": (
                        f"Exercise scheduled on '{wpe['scheduled_day']}' not allowed by new plan schedule."
                    )
                }
    
        # Update the plan's schedule
        self.workout_plans[plan_id]["schedule"] = new_schedule

        return {
            "success": True,
            "message": f"Schedule updated for plan {plan_id}"
        }

    def delete_workout_plan(self, plan_id: str) -> dict:
        """
        Remove a workout plan and all its associated exercises from the system.

        Args:
            plan_id (str): The unique identifier of the workout plan to be deleted.

        Returns:
            dict: 
              - On success:
                  {"success": True, "message": "Workout plan <plan_id> and its associated exercises deleted."}
              - On error (plan not found):
                  {"success": False, "error": "Workout plan does not exist."}

        Constraints:
            - If the plan does not exist, the operation fails.
            - Associated exercises (WorkoutPlanExercise) for that plan are also deleted (if any).
        """
        if plan_id not in self.workout_plans:
            return { "success": False, "error": "Workout plan does not exist." }

        # Delete the plan
        del self.workout_plans[plan_id]

        # Delete all associated exercises for this plan
        if plan_id in self.workout_plan_exercises:
            del self.workout_plan_exercises[plan_id]

        return { 
            "success": True, 
            "message": f"Workout plan {plan_id} and its associated exercises deleted."
        }

    def update_exercise_info(self, exercise_id: str, name: str = None, type: str = None) -> dict:
        """
        Update the attributes (name, type) of an existing Exercise.

        Args:
            exercise_id (str): ID of the exercise to update.
            name (str, optional): New name for the exercise.
            type (str, optional): New type/category for the exercise.

        Returns:
            dict: 
                {
                    "success": True,
                    "message": "Exercise info updated successfully."
                }
            or
                {
                    "success": False,
                    "error": "Reason for failure"
                }

        Constraints:
            - Exercise must exist in the system.
            - Only 'name' and 'type' may be updated.
            - At least one attribute must be provided for update.
        """
        if exercise_id not in self.exercises:
            return { "success": False, "error": "Exercise does not exist." }

        if name is None and type is None:
            return { "success": False, "error": "No attributes provided for update." }

        update_fields = {}
        if name is not None:
            update_fields["name"] = name
        if type is not None:
            update_fields["type"] = type

        # Only update allowed keys
        for key in update_fields:
            if key not in ["name", "type"]:
                return { "success": False, "error": f"Invalid attribute '{key}' for exercise update." }

        self.exercises[exercise_id].update(update_fields)
        return { "success": True, "message": "Exercise info updated successfully." }


class PersonalFitnessApp(BaseEnv):
    def __init__(self, *, parameters=None):
        super().__init__()
        self.parameters = copy.deepcopy(parameters or {})
        self._mirrored_state_keys = set()
        self._inner = self._build_inner_env()
        self._apply_init_config(self._inner, self.parameters if isinstance(self.parameters, dict) else {})
        self._sync_from_inner()

    @staticmethod
    def _build_inner_env():
        try:
            return _GeneratedEnvImpl({})
        except Exception:
            return _GeneratedEnvImpl()

    @staticmethod
    def _apply_init_config(env, init_config):
        if not isinstance(init_config, dict):
            return
        for key, value in init_config.items():
            setattr(env, key, copy.deepcopy(value))

    def _sync_from_inner(self):
        reserved = {
            "parameters",
            "_inner",
            "_mirrored_state_keys",
            "tool_list",
            "env_description",
            "initial_parameter_schema",
            "default_initial_parameters",
            "tool_descs",
        }
        current = set()
        for key, value in vars(self._inner).items():
            if key.startswith("__") and key.endswith("__"):
                continue
            if key in reserved:
                continue
            setattr(self, key, copy.deepcopy(value))
            current.add(key)
        stale = getattr(self, "_mirrored_state_keys", set()) - current
        for key in stale:
            if hasattr(self, key):
                delattr(self, key)
        self._mirrored_state_keys = current

    def _call_inner_tool(self, tool_name: str, kwargs: Dict[str, Any]):
        func = getattr(self._inner, tool_name)
        result = func(**copy.deepcopy(kwargs or {}))
        self._sync_from_inner()
        return result

    def get_user_by_name(self, **kwargs):
        return self._call_inner_tool('get_user_by_name', kwargs)

    def get_user_by_id(self, **kwargs):
        return self._call_inner_tool('get_user_by_id', kwargs)

    def list_all_users(self, **kwargs):
        return self._call_inner_tool('list_all_users', kwargs)

    def get_workout_plans_by_user(self, **kwargs):
        return self._call_inner_tool('get_workout_plans_by_user', kwargs)

    def get_workout_plan_by_id(self, **kwargs):
        return self._call_inner_tool('get_workout_plan_by_id', kwargs)

    def get_exercise_by_name(self, **kwargs):
        return self._call_inner_tool('get_exercise_by_name', kwargs)

    def get_exercise_by_id(self, **kwargs):
        return self._call_inner_tool('get_exercise_by_id', kwargs)

    def list_all_exercises(self, **kwargs):
        return self._call_inner_tool('list_all_exercises', kwargs)

    def get_plan_exercises(self, **kwargs):
        return self._call_inner_tool('get_plan_exercises', kwargs)

    def get_plan_exercise_by_exercise_and_day(self, **kwargs):
        return self._call_inner_tool('get_plan_exercise_by_exercise_and_day', kwargs)

    def get_plan_schedule(self, **kwargs):
        return self._call_inner_tool('get_plan_schedule', kwargs)

    def add_exercise_to_plan(self, **kwargs):
        return self._call_inner_tool('add_exercise_to_plan', kwargs)

    def create_exercise(self, **kwargs):
        return self._call_inner_tool('create_exercise', kwargs)

    def create_workout_plan(self, **kwargs):
        return self._call_inner_tool('create_workout_plan', kwargs)

    def remove_exercise_from_plan(self, **kwargs):
        return self._call_inner_tool('remove_exercise_from_plan', kwargs)

    def update_plan_exercise(self, **kwargs):
        return self._call_inner_tool('update_plan_exercise', kwargs)

    def reorder_plan_exercises(self, **kwargs):
        return self._call_inner_tool('reorder_plan_exercises', kwargs)

    def update_plan_schedule(self, **kwargs):
        return self._call_inner_tool('update_plan_schedule', kwargs)

    def delete_workout_plan(self, **kwargs):
        return self._call_inner_tool('delete_workout_plan', kwargs)

    def update_exercise_info(self, **kwargs):
        return self._call_inner_tool('update_exercise_info', kwargs)
