# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, List, TypedDict
import uuid
from typing import List, Dict, Optional



class SymptomInfo(TypedDict):
    symptom_id: str
    name: str
    description: str

class CauseInfo(TypedDict):
    cause_id: str
    name: str
    description: str

class TreatmentInfo(TypedDict):
    treatment_id: str
    name: str
    description: str

class MedicalConditionInfo(TypedDict):
    condition_id: str
    name: str
    description: str
    symptom_ids: List[str]
    cause_ids: List[str]
    treatment_ids: List[str]

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Medical Knowledge Base System environment state.
        """

        # MedicalConditions: {condition_id: MedicalConditionInfo}
        #   - Attributes: condition_id, name, description, symptom_ids, cause_ids, treatment_ids
        self.medical_conditions: Dict[str, MedicalConditionInfo] = {}

        # Symptoms: {symptom_id: SymptomInfo}
        #   - Attributes: symptom_id, name, description
        self.symptoms: Dict[str, SymptomInfo] = {}

        # Causes: {cause_id: CauseInfo}
        #   - Attributes: cause_id, name, description
        self.causes: Dict[str, CauseInfo] = {}

        # Treatments: {treatment_id: TreatmentInfo}
        #   - Attributes: treatment_id, name, description
        self.treatments: Dict[str, TreatmentInfo] = {}

        # Constraint annotations:
        # - Each medical condition must have at least a name before insertion.
        # - Symptom, cause, and treatment entities should be de-duplicated by name.
        # - Relationships (medical condition to symptoms, causes, treatments) are many-to-many.
        # - Referential integrity must be preserved on entity updates across linked conditions.

    def get_medical_condition_by_name(self, name: str) -> dict:
        """
        Retrieve a medical condition record by its name.

        Args:
            name (str): The exact name of the medical condition to fetch.

        Returns:
            dict: {
                "success": True,
                "data": MedicalConditionInfo,
            }
            or
            {
                "success": False,
                "error": str,  # Medical condition not found
            }
        Constraints:
            - Name must match exactly (case-sensitive).
        """
        for condition in self.medical_conditions.values():
            if condition["name"] == name:
                return { "success": True, "data": condition }
        return { "success": False, "error": "Medical condition not found" }

    def get_all_medical_conditions(self) -> dict:
        """
        Retrieve a list of all medical condition records in the knowledge base.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[MedicalConditionInfo]  # List of all condition records (may be empty)
                }
        """
        data = list(self.medical_conditions.values())
        return { "success": True, "data": data }

    def get_medical_condition_details(self, condition_id: str) -> dict:
        """
        Retrieve full details for a medical condition, including:
          - Core attributes: condition_id, name, description
          - Linked symptoms, causes, and treatments (with their information, not just IDs)

        Args:
            condition_id (str): The unique ID of the medical condition.

        Returns:
            dict
            {
                "success": True,
                "data": {
                    "condition": MedicalConditionInfo,
                    "symptoms": List[SymptomInfo],
                    "causes": List[CauseInfo],
                    "treatments": List[TreatmentInfo],
                }
            }
            or
            {
                "success": False,
                "error": "Condition not found"
            }

        Constraints:
            - Returns all available details for referenced symptom/cause/treatment IDs.
            - Skips dangling references if present (should not occur by design).

        """
        cond = self.medical_conditions.get(condition_id)
        if not cond:
            return {"success": False, "error": "Condition not found"}

        # Gather symptom, cause, and treatment info; skip missing references
        symptoms = [self.symptoms[sid]
                    for sid in cond.get("symptom_ids", [])
                    if sid in self.symptoms]
        causes = [self.causes[cid]
                  for cid in cond.get("cause_ids", [])
                  if cid in self.causes]
        treatments = [self.treatments[tid]
                      for tid in cond.get("treatment_ids", [])
                      if tid in self.treatments]

        return {
            "success": True,
            "data": {
                "condition": cond,
                "symptoms": symptoms,
                "causes": causes,
                "treatments": treatments
            }
        }

    def find_symptom_by_name(self, name: str) -> dict:
        """
        Retrieve an existing symptom record by name for de-duplication.

        Args:
            name (str): The symptom name to find.

        Returns:
            dict:
                - If found: { "success": True, "data": SymptomInfo }
                - If not found: { "success": True, "data": None }
                - If invalid input: { "success": False, "error": "Symptom name cannot be empty" }

        Constraints:
            - Symptom name must not be empty.
            - Symptom matching is exact, case-sensitive.
            - Only one symptom per name (de-duplication enforced elsewhere).
        """
        if not isinstance(name, str) or name.strip() == "":
            return { "success": False, "error": "Symptom name cannot be empty" }

        for symptom in self.symptoms.values():
            if symptom["name"] == name:
                return { "success": True, "data": symptom }

        return { "success": True, "data": None }

    def get_all_symptoms(self) -> dict:
        """
        Retrieve all symptom records in the database.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[SymptomInfo]  # List of symptom records, may be empty if no symptoms exist
            }

        Constraints:
            - None (read-only)
        """
        symptoms_list = list(self.symptoms.values())
        return { "success": True, "data": symptoms_list }

    def find_cause_by_name(self, name: str) -> dict:
        """
        Retrieve an existing cause record by name for de-duplication.

        Args:
            name (str): The name of the cause to find.

        Returns:
            dict: {
                "success": True,
                "data": CauseInfo | None  # Returns the cause info if found, else None.
            }

        Notes:
            - Searches for an exact (case-sensitive) match.
            - Returns None if not found.
        """
        for cause in self.causes.values():
            if cause["name"] == name:
                return {"success": True, "data": cause}
        return {"success": True, "data": None}

    def get_all_causes(self) -> dict:
        """
        List all causes in the database.

        Returns:
            dict: {
                "success": True,
                "data": List[CauseInfo]  # List of all cause info dicts. May be empty.
            }
            or
            {
                "success": False,
                "error": str  # Error message if operation failed.
            }
        """
        if not isinstance(self.causes, dict):
            return { "success": False, "error": "Internal causes database error." }
        all_causes = list(self.causes.values())
        return { "success": True, "data": all_causes }

    def find_treatment_by_name(self, name: str) -> dict:
        """
        Retrieve existing treatment(s) by exact (case-insensitive) name for de-duplication.

        Args:
            name (str): The treatment name to search for.

        Returns:
            dict: {
                "success": True,
                "data": List[TreatmentInfo]  # List of all matching treatments (may be empty if none)
            }
            or
            {
                "success": False,
                "error": str  # e.g., "Invalid treatment name"
            }

        Notes:
            - Matching is case-insensitive and exact on the name field.
            - Returns all matching treatments.
            - No error if no treatment found; returns empty list.
        """
        if not isinstance(name, str) or not name.strip():
            return { "success": False, "error": "Invalid treatment name" }
        name_lower = name.strip().lower()
        matches = [
            treatment for treatment in self.treatments.values()
            if treatment["name"].strip().lower() == name_lower
        ]
        return { "success": True, "data": matches }

    def get_all_treatments(self) -> dict:
        """
        List all treatment records in the medical knowledge base.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[TreatmentInfo]  # List of treatment records (may be empty if none)
            }

            If an internal error occurs (very unlikely in normal use), returns:
            {
                "success": False,
                "error": <reason>
            }

        Constraints:
            - No parameters are required.
            - Returns an empty list if no treatments are present.
        """
        if not hasattr(self, 'treatments') or not isinstance(self.treatments, dict):
            return { "success": False, "error": "Treatment registry unavailable" }

        all_treatments = list(self.treatments.values())
        return { "success": True, "data": all_treatments }

    def list_conditions_with_symptom(self, symptom_id: str) -> dict:
        """
        List all medical conditions associated with a specific symptom.

        Args:
            symptom_id (str): The ID of the symptom to query.

        Returns:
            dict: {
                "success": True,
                "data": List[MedicalConditionInfo]  # List of medical conditions (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. symptom does not exist
            }

        Constraints:
            - The symptom must exist in the system (referential integrity).
        """
        if symptom_id not in self.symptoms:
            return { "success": False, "error": "Symptom does not exist" }

        results = [
            cond_info for cond_info in self.medical_conditions.values()
            if symptom_id in cond_info["symptom_ids"]
        ]

        return { "success": True, "data": results }

    def list_conditions_with_cause(self, cause_id: str) -> dict:
        """
        List all medical conditions associated with a specific cause.

        Args:
            cause_id (str): The unique identifier of the cause.

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[MedicalConditionInfo],  # May be empty if none linked
                }
                or
                {
                    "success": False,
                    "error": str  # If cause does not exist
                }
        Constraints:
            - The cause must exist.
            - Results include all MedicalConditionInfo objects where cause_id is present in cause_ids.
        """
        if cause_id not in self.causes:
            return {"success": False, "error": "Cause not found"}
    
        conditions = [
            cond for cond in self.medical_conditions.values()
            if cause_id in cond.get("cause_ids", [])
        ]
        return {"success": True, "data": conditions}

    def list_conditions_with_treatment(self, treatment_id: str) -> dict:
        """
        List all medical conditions associated with a specific treatment.

        Args:
            treatment_id (str): The unique identifier of the treatment.

        Returns:
            dict: 
                - On success: {"success": True, "data": List[MedicalConditionInfo]}
                - On failure (invalid treatment): {"success": False, "error": str}

        Constraints:
            - treatment_id must exist in the system.
            - Only returns conditions where treatment_id is in their treatment_ids.
        """
        if treatment_id not in self.treatments:
            return { "success": False, "error": "Treatment not found" }

        results = [
            condition for condition in self.medical_conditions.values()
            if treatment_id in condition.get("treatment_ids", [])
        ]
        return { "success": True, "data": results }


    def add_medical_condition(self,
                              name: str,
                              description: Optional[str] = "",
                              symptoms: Optional[List[Dict[str, str]]] = None,
                              causes: Optional[List[Dict[str, str]]] = None,
                              treatments: Optional[List[Dict[str, str]]] = None) -> dict:
        """
        Add a new medical condition with name, description, and related symptoms, causes, and treatments.
        De-duplicates symptoms/causes/treatments by name across the KB. 
        Links to existing related records or adds them if missing.
        Preserves referential integrity.

        Args:
            name (str): Name of the medical condition (required).
            description (str): Optional description.
            symptoms (List[Dict[str, str]]): List of symptoms (dicts: {"name": ..., "description": ...}).
            causes (List[Dict[str, str]]): List of causes (dicts: {"name": ..., "description": ...}).
            treatments (List[Dict[str, str]]): List of treatments (dicts: {"name": ..., "description": ...}).

        Returns:
            dict: 
                On success: {"success": True, "message": "..."}
                On error:   {"success": False, "error": "..."}
        Constraints:
            - Condition "name" must be provided.
            - Symptoms, Causes, Treatments are de-duplicated by name.
            - All links must point to existing or just-created entities.
        """
        # Validate mandatory field
        if not name or not name.strip():
            return { "success": False, "error": "Medical condition name is required" }

        # Initialize lists if None
        symptoms = symptoms if symptoms is not None else []
        causes = causes if causes is not None else []
        treatments = treatments if treatments is not None else []

        # Helper to clean/normalize incoming dicts (support {"name": ..., "description": ...} or {"name": ...})
        def extract_name_desc(entity: Dict[str, str]) -> (str, str):
            n = entity.get("name") or ""
            d = entity.get("description") or ""
            return n.strip(), d.strip()

        # (1) De-duplicate/add symptoms
        symptom_ids = []
        for sympt in symptoms:
            s_name, s_desc = extract_name_desc(sympt)
            if not s_name:
                continue  # skip unnamed
            found = None
            for s_id, s in self.symptoms.items():
                if s["name"] == s_name:
                    found = s_id
                    break
            if found:
                symptom_ids.append(found)
            else:
                new_id = str(uuid.uuid4())
                self.symptoms[new_id] = {
                    "symptom_id": new_id,
                    "name": s_name,
                    "description": s_desc
                }
                symptom_ids.append(new_id)

        # (2) De-duplicate/add causes
        cause_ids = []
        for cause in causes:
            c_name, c_desc = extract_name_desc(cause)
            if not c_name:
                continue
            found = None
            for c_id, c in self.causes.items():
                if c["name"] == c_name:
                    found = c_id
                    break
            if found:
                cause_ids.append(found)
            else:
                new_id = str(uuid.uuid4())
                self.causes[new_id] = {
                    "cause_id": new_id,
                    "name": c_name,
                    "description": c_desc
                }
                cause_ids.append(new_id)

        # (3) De-duplicate/add treatments
        treatment_ids = []
        for treat in treatments:
            t_name, t_desc = extract_name_desc(treat)
            if not t_name:
                continue
            found = None
            for t_id, t in self.treatments.items():
                if t["name"] == t_name:
                    found = t_id
                    break
            if found:
                treatment_ids.append(found)
            else:
                new_id = str(uuid.uuid4())
                self.treatments[new_id] = {
                    "treatment_id": new_id,
                    "name": t_name,
                    "description": t_desc
                }
                treatment_ids.append(new_id)

        # Create new condition_id
        condition_id = str(uuid.uuid4())
        self.medical_conditions[condition_id] = {
            "condition_id": condition_id,
            "name": name.strip(),
            "description": description.strip() if description else "",
            "symptom_ids": symptom_ids,
            "cause_ids": cause_ids,
            "treatment_ids": treatment_ids,
        }

        return {
            "success": True,
            "message": f"Added medical condition '{name}' with id {condition_id}"
        }

    def update_medical_condition(
        self,
        condition_id: str,
        name: str = None,
        description: str = None,
        symptom_names: list = None,
        cause_names: list = None,
        treatment_names: list = None
    ) -> dict:
        """
        Update the information for a medical condition:
        - Name (must not be empty if provided),
        - Description,
        - Linked symptoms, causes, and treatments (linked by entity names; deduplication enforced).

        Args:
            condition_id (str): The ID of the medical condition to update.
            name (str, optional): New name for the medical condition.
            description (str, optional): New description.
            symptom_names (list of str, optional): Names of symptoms to link.
            cause_names (list of str, optional): Names of causes to link.
            treatment_names (list of str, optional): Names of treatments to link.

        Returns:
            dict: 
                - On success: { "success": True, "message": "Medical condition updated." }
                - On error: { "success": False, "error": <error message> }

        Constraints:
            - Condition must exist.
            - Must not set name to empty string.
            - Deduplication for symptoms, causes, treatments by name.
            - Links updated accordingly.
            - Referential integrity is preserved.
        """
        # Check condition exists
        cond = self.medical_conditions.get(condition_id)
        if cond is None:
            return { "success": False, "error": "condition not found" }

        # Update name if provided
        if name is not None:
            if not name.strip():
                return { "success": False, "error": "name cannot be empty" }
            cond["name"] = name.strip()

        # After name update, enforce non-empty name
        if not cond["name"]:
            return { "success": False, "error": "name cannot be empty" }

        # Update description if provided
        if description is not None:
            cond["description"] = description

        # Utilities for symptom/cause/treatment deduplication and linking
        def _get_or_create_symptom_id(symptom_name):
            for sid, info in self.symptoms.items():
                if info["name"].lower() == symptom_name.lower():
                    return sid
            # Not found, create new
            new_id = f"SYM{len(self.symptoms)+1:04d}"
            self.symptoms[new_id] = {"symptom_id": new_id, "name": symptom_name, "description": ""}
            return new_id

        def _get_or_create_cause_id(cause_name):
            for cid, info in self.causes.items():
                if info["name"].lower() == cause_name.lower():
                    return cid
            # Not found, create new
            new_id = f"CAU{len(self.causes)+1:04d}"
            self.causes[new_id] = {"cause_id": new_id, "name": cause_name, "description": ""}
            return new_id

        def _get_or_create_treatment_id(treatment_name):
            for tid, info in self.treatments.items():
                if info["name"].lower() == treatment_name.lower():
                    return tid
            # Not found, create new
            new_id = f"TRE{len(self.treatments)+1:04d}"
            self.treatments[new_id] = {"treatment_id": new_id, "name": treatment_name, "description": ""}
            return new_id

        # Update symptom links if provided
        if symptom_names is not None:
            ids = []
            for s_name in symptom_names:
                if s_name.strip():
                    sid = _get_or_create_symptom_id(s_name.strip())
                    ids.append(sid)
            cond["symptom_ids"] = ids

        # Update cause links if provided
        if cause_names is not None:
            ids = []
            for c_name in cause_names:
                if c_name.strip():
                    cid = _get_or_create_cause_id(c_name.strip())
                    ids.append(cid)
            cond["cause_ids"] = ids

        # Update treatment links if provided
        if treatment_names is not None:
            ids = []
            for t_name in treatment_names:
                if t_name.strip():
                    tid = _get_or_create_treatment_id(t_name.strip())
                    ids.append(tid)
            cond["treatment_ids"] = ids

        # Save back (dict is mutable, but explicit for clarity)
        self.medical_conditions[condition_id] = cond
        return { "success": True, "message": "Medical condition updated." }

    def add_or_link_symptom(
        self,
        name: str,
        description: str,
        condition_ids: list
    ) -> dict:
        """
        Add a new symptom if it doesn't already exist (by name, case-insensitive).
        If it exists, return existing. Link the symptom to all listed medical conditions
        (by condition_id, only if the condition exists).

        Args:
            name (str): Symptom name. (Must not be empty)
            description (str): Symptom description (optional).
            condition_ids (List[str]): List of medical condition IDs to link to.

        Returns:
            dict: 
              - success: True/False
              - data: If success, {symptom_id, linked_conditions, skipped_conditions}
              - error: If failure, reason string.

        Constraints:
          - Symptom name must not be empty.
          - De-duplicate on name (case-insensitive).
          - Only link to MedicalConditions that exist.
          - Maintain referential integrity (symptom must be in condition's symptom_ids).
        """
        if not isinstance(name, str) or not name.strip():
            return {"success": False, "error": "Symptom name is required and cannot be empty."}
        name_stripped = name.strip()

        # Try to find existing symptom (case-insensitive match)
        existing_symptom_id = None
        for sid, sinfo in self.symptoms.items():
            if sinfo["name"].strip().lower() == name_stripped.lower():
                existing_symptom_id = sid
                break

        if existing_symptom_id:
            symptom_id = existing_symptom_id
        else:
            # Generate a new unique symptom_id (e.g. "SYMPTOM_N")
            base_id = f"SYMPTOM_{len(self.symptoms)+1}"
            i = 1
            symptom_id = base_id
            # Guarantee uniqueness of symptom_id
            while symptom_id in self.symptoms:
                i += 1
                symptom_id = f"{base_id}_{i}"
            self.symptoms[symptom_id] = {
                "symptom_id": symptom_id,
                "name": name_stripped,
                "description": description or "",
            }

        linked_conditions = []
        skipped_conditions = []
        condition_ids = condition_ids or []
        for cid in condition_ids:
            if cid in self.medical_conditions:
                mc = self.medical_conditions[cid]
                # Add symptom_id if not already present
                if symptom_id not in mc["symptom_ids"]:
                    mc["symptom_ids"].append(symptom_id)
                linked_conditions.append(cid)
            else:
                skipped_conditions.append(cid)

        return {
            "success": True,
            "data": {
                "symptom_id": symptom_id,
                "linked_conditions": linked_conditions,
                "skipped_conditions": skipped_conditions
            }
        }

    def add_or_link_cause(self, cause_name: str, cause_description: str, condition_ids: list) -> dict:
        """
        Add a new Cause entity (if one with the same name does not exist, case-insensitive),
        or reuse the existing Cause. Link the Cause to one or more MedicalCondition records,
        adding the cause's ID to each condition's cause_ids set (ensuring no duplicates).
    
        Args:
            cause_name (str): Name of the cause (must not be empty).
            cause_description (str): Cause description (used only if a new cause is created).
            condition_ids (List[str]): List of medical condition IDs to link the cause to.

        Returns:
            dict: On success: {"success": True, "message": str, "cause_id": str}
                  On failure: {"success": False, "error": str}

        Constraints:
            - De-duplicate Cause by name (case-insensitive).
            - Only link to valid condition_ids (must exist).
            - No duplicate cause_ids per condition.
            - cause_name must not be empty.
        """
        if not cause_name or not cause_name.strip():
            return {"success": False, "error": "Cause name must not be empty."}
        # Search for existing cause by name (case-insensitive)
        cause_id = None
        for cid, cause in self.causes.items():
            if cause['name'].strip().lower() == cause_name.strip().lower():
                cause_id = cid
                break
        # If not found, create new cause
        if cause_id is None:
            # Generate a unique cause_id (UUID or increment)
            cause_id = str(uuid.uuid4())
            self.causes[cause_id] = {
                "cause_id": cause_id,
                "name": cause_name.strip(),
                "description": cause_description
            }
            created = True
        else:
            created = False
        # Validate condition_ids
        not_found = [cid for cid in condition_ids if cid not in self.medical_conditions]
        if not_found:
            return {"success": False, "error": f"Condition IDs do not exist: {not_found}"}
        # Link cause to conditions
        count_linked = 0
        for cond_id in condition_ids:
            cond = self.medical_conditions[cond_id]
            if cause_id not in cond["cause_ids"]:
                cond["cause_ids"].append(cause_id)
                count_linked += 1
        message = f"Cause {'created' if created else 'linked'} and associated with {count_linked} conditions."
        return {"success": True, "message": message, "cause_id": cause_id}

    def add_or_link_treatment(
        self,
        treatment_name: str,
        treatment_description: str,
        condition_ids: list
    ) -> dict:
        """
        Add a new treatment to the knowledge base if one with the same name does not already exist,
        or return the existing treatment. Then, link the treatment to each specified medical condition.

        Args:
            treatment_name (str): Name for the treatment (must not be empty).
            treatment_description (str): Description of the treatment.
            condition_ids (list of str): List of medical condition IDs to link this treatment to.

        Returns:
            dict: On success:
               {
                 "success": True,
                 "message": "...",
                 "treatment_id": "<treatment_id>"
               }
               On failure:
               { "success": False, "error": "reason" }

        Constraints:
            - Treatment entities are de-duplicated by name (case-sensitive).
            - All condition IDs must exist; partial linking will be performed if only some are valid.
            - No duplicate treatment ID in a condition's treatment_ids.
        """
        # Validate name
        if not treatment_name or not isinstance(treatment_name, str):
            return { "success": False, "error": "Treatment name must be provided." }
        if not condition_ids or not isinstance(condition_ids, list):
            return { "success": False, "error": "A non-empty list of condition_ids must be provided." }

        # 1. De-duplicate Treatment by name
        existing_treatment_id = None
        for tid, tinfo in self.treatments.items():
            if tinfo["name"] == treatment_name:
                existing_treatment_id = tid
                break

        if existing_treatment_id:
            treatment_id = existing_treatment_id
            # Optionally, update the description if it's different (not strictly required here)
            if treatment_description != self.treatments[treatment_id]["description"]:
                self.treatments[treatment_id]["description"] = treatment_description
        else:
            # Create new unique treatment_id
            treatment_id = "TREATMENT_" + uuid.uuid4().hex[:8]
            self.treatments[treatment_id] = {
                "treatment_id": treatment_id,
                "name": treatment_name,
                "description": treatment_description
            }

        # 2. Link to each provided condition
        linked = []
        missing = []
        for cid in condition_ids:
            cond = self.medical_conditions.get(cid)
            if cond:
                if treatment_id not in cond["treatment_ids"]:
                    cond["treatment_ids"].append(treatment_id)
                linked.append(cid)
            else:
                missing.append(cid)

        if not linked:
            return {
                "success": False,
                "error": "None of the provided condition_ids exist in the knowledge base."
            }

        msg = f"Linked treatment '{treatment_id}' to conditions: {linked}."
        if missing:
            msg += f" The following condition_ids do not exist and were skipped: {missing}"

        return {
            "success": True,
            "message": msg,
            "treatment_id": treatment_id
        }

    def update_symptom(self, symptom_id: str, name: str = None, description: str = None) -> dict:
        """
        Update details of a symptom, ensuring all linked medical conditions remain consistent.

        Args:
            symptom_id (str): The unique ID of the symptom to update.
            name (str, optional): The new name for the symptom. If provided, will check/merge with others of same name.
            description (str, optional): The new description for the symptom.
    
        Returns:
            dict: On success:
                { "success": True, "message": "<updated or merged information>" }
            On failure:
                { "success": False, "error": "<description>" }

        Constraints:
            - De-duplicated by symptom name. If `name` is given and a symptom with that name exists (and different id),
              all references to this symptom in conditions are updated to the existing one, then this is deleted.
            - All medical conditions referencing this symptom remain consistent.
            - At least one of name or description must be provided.
        """
        if symptom_id not in self.symptoms:
            return { "success": False, "error": "Symptom not found" }
        if name is None and description is None:
            return { "success": False, "error": "No update data provided; specify name and/or description" }

        cur_symptom = self.symptoms[symptom_id]
        merge_needed = False
        target_symptom_id = symptom_id

        # De-duplication/merge by name if the new name matches another symptom (with different id)
        if name is not None:
            for other_id, other_symptom in self.symptoms.items():
                if other_id != symptom_id and other_symptom["name"].strip().lower() == name.strip().lower():
                    # Found duplicate name; need to merge
                    merge_needed = True
                    target_symptom_id = other_id
                    break

        if not merge_needed:
            # Standard update
            updated = False
            if name is not None and cur_symptom["name"] != name:
                cur_symptom["name"] = name
                updated = True
            if description is not None and cur_symptom["description"] != description:
                cur_symptom["description"] = description
                updated = True
            if updated:
                self.symptoms[symptom_id] = cur_symptom
                return { "success": True, "message": f"Symptom '{symptom_id}' updated." }
            else:
                return { "success": True, "message": "No changes made; data was identical." }
        else:
            # Merge: update all medical conditions to point to target_symptom_id, then delete this one
            for cond in self.medical_conditions.values():
                if symptom_id in cond["symptom_ids"]:
                    # Replace with target only if not already present
                    if target_symptom_id not in cond["symptom_ids"]:
                        cond["symptom_ids"].append(target_symptom_id)
                    cond["symptom_ids"] = [sid for sid in cond["symptom_ids"] if sid != symptom_id]
            # Optionally update description if provided and different (and retains info)
            if description is not None:
                target_symptom = self.symptoms[target_symptom_id]
                if target_symptom["description"] != description:
                    target_symptom["description"] = description
                    self.symptoms[target_symptom_id] = target_symptom
            # Delete the old (now-merged) symptom
            del self.symptoms[symptom_id]
            return { "success": True, "message": f"Symptom merged with existing symptom '{target_symptom_id}' due to duplicate name. All references updated." }

    def update_cause(self, cause_id: str, name: str = None, description: str = None) -> dict:
        """
        Update the name and/or description of a Cause entity.
        Ensures cause name uniqueness and preserves referential integrity for all linked medical conditions.

        Args:
            cause_id (str): Unique ID of the cause to update.
            name (str, optional): New name for the cause. Must be unique across causes.
            description (str, optional): New description for the cause.

        Returns:
            dict: {
                "success": True,
                "message": "Cause updated successfully"
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
        - Cause with cause_id must exist.
        - If updating name, it must not duplicate another cause's name.
        - Linked medical conditions retain cause_id reference (referential integrity preserved).
        """

        # Validate cause existence
        cause = self.causes.get(cause_id)
        if not cause:
            return { "success": False, "error": "Cause not found." }

        # Must update at least one field
        if name is None and description is None:
            return { "success": False, "error": "No update fields provided." }

        # Check for name duplication if updating name
        if name is not None:
            for cid, cinfo in self.causes.items():
                if cid != cause_id and cinfo["name"].lower() == name.lower():
                    return { "success": False, "error": "Duplicate cause name exists." }
            cause["name"] = name

        if description is not None:
            cause["description"] = description

        # Update in the database
        self.causes[cause_id] = cause   # (Not strictly necessary, but preserves consistency)

        # No changes to medical_conditions needed; IDs remain valid
        return { "success": True, "message": "Cause updated successfully" }

    def update_treatment(self, treatment_id: str, name: str = None, description: str = None) -> dict:
        """
        Update details of the treatment with the given treatment_id.
        Only 'name' and/or 'description' can be updated.
        Treatment remains linked to all previously associated conditions (referential integrity preserved).

        Args:
            treatment_id (str): The ID of the treatment to update.
            name (str, optional): New name for the treatment.
            description (str, optional): New description for the treatment.

        Returns:
            dict: {
                "success": True,
                "message": "Treatment updated successfully."
            }
            or
            {
                "success": False,
                "error": "Reason for failure."
            }
    
        Constraints:
            - treatment_id must exist in the system.
            - At least one of 'name' or 'description' must be provided.
            - Only updates allowed are to 'name' and 'description' (not treatment_id).
            - Referential integrity (condition-treatment links) must not be broken.
        """
        if treatment_id not in self.treatments:
            return { "success": False, "error": "Treatment ID does not exist." }
        if name is None and description is None:
            return { "success": False, "error": "At least one of name or description must be provided." }

        treatment = self.treatments[treatment_id]
        if name is not None:
            treatment["name"] = name
        if description is not None:
            treatment["description"] = description

        # Treatment remains referenced by all existing conditions (nothing else to do)
        return { "success": True, "message": "Treatment updated successfully." }

    def remove_symptom_from_condition(self, condition_id: str, symptom_id: str) -> dict:
        """
        Unlink a symptom from a medical condition, preserving referential integrity.

        Args:
            condition_id (str): The unique identifier of the medical condition.
            symptom_id (str): The unique identifier of the symptom to remove.

        Returns:
            dict: {
                "success": True,
                "message": "Symptom unlinked from condition."
            }
            or
            {
                "success": False,
                "error": "..."
            }

        Constraints:
            - Both medical condition and symptom must exist.
            - Only removes the reference; does not delete the symptom or condition entity.
            - Operation is idempotent: if the link doesn't exist, returns appropriate error.
        """
        # Check condition exists
        condition = self.medical_conditions.get(condition_id)
        if condition is None:
            return { "success": False, "error": "Medical condition not found." }
        # Check symptom exists
        if symptom_id not in self.symptoms:
            return { "success": False, "error": "Symptom not found." }
        # Check if the symptom is linked to the condition
        if symptom_id not in condition["symptom_ids"]:
            return { "success": False, "error": "Symptom not linked to condition." }
        # Unlink the symptom
        condition["symptom_ids"].remove(symptom_id)
        return { "success": True, "message": "Symptom unlinked from condition." }

    def remove_cause_from_condition(self, condition_id: str, cause_id: str) -> dict:
        """
        Unlink a cause from a medical condition, preserving referential integrity.

        Args:
            condition_id (str): The ID of the medical condition.
            cause_id (str): The ID of the cause to be removed from the condition.

        Returns:
            dict:
                - success: True and message if link removed.
                - success: False and error if condition or cause doesn't exist, or if cause not linked.

        Constraints:
            - Both condition and cause must exist.
            - Cause must currently be linked to the condition (in cause_ids).
            - Many-to-many relationship: Only the link is removed, entities are preserved.
            - Referential integrity is preserved.
        """
        if condition_id not in self.medical_conditions:
            return { "success": False, "error": f"Medical condition with ID '{condition_id}' does not exist." }
        if cause_id not in self.causes:
            return { "success": False, "error": f"Cause with ID '{cause_id}' does not exist." }

        condition = self.medical_conditions[condition_id]
        if cause_id not in condition["cause_ids"]:
            return { "success": False, "error": f"Cause '{cause_id}' is not linked to medical condition '{condition_id}'." }

        # Remove the cause_id from the condition's cause_ids
        condition["cause_ids"].remove(cause_id)

        # Update preserved in-place due to dict reference
        return {
            "success": True,
            "message": f"Cause '{cause_id}' unlinked from medical condition '{condition_id}'."
        }

    def remove_treatment_from_condition(self, condition_id: str, treatment_id: str) -> dict:
        """
        Unlink (remove) a treatment from the list of treatments of a medical condition.
        Preserves referential integrity (does not delete either entity).

        Args:
            condition_id (str): The ID of the medical condition.
            treatment_id (str): The ID of the treatment to remove.

        Returns:
            dict: Success or error message.

            Success: {
                "success": True,
                "message": "Treatment <treatment_id> unlinked from condition <condition_id>."
            }
            Failure:
            {
                "success": False,
                "error": str (Describes which ID does not exist, or if treatment not linked)
            }
        """
        if condition_id not in self.medical_conditions:
            return {"success": False, "error": f"Condition '{condition_id}' does not exist."}

        if treatment_id not in self.treatments:
            return {"success": False, "error": f"Treatment '{treatment_id}' does not exist."}

        condition_info = self.medical_conditions[condition_id]
        if treatment_id not in condition_info["treatment_ids"]:
            return {"success": False, "error": f"Treatment '{treatment_id}' is not linked to condition '{condition_id}'."}

        condition_info["treatment_ids"].remove(treatment_id)

        return {
            "success": True,
            "message": f"Treatment '{treatment_id}' unlinked from condition '{condition_id}'."
        }

    def delete_medical_condition(self, condition_id: str) -> dict:
        """
        Delete a medical condition by its ID.
        Also ensures referential integrity: all links from the condition to symptoms,
        causes, and treatments are removed by deleting the MedicalCondition entry.
        (Other entities like symptoms/causes/treatments are not deleted, even if now unreferenced.)

        Args:
            condition_id (str): The unique ID of the medical condition to delete.

        Returns:
            dict: {
                "success": True,
                "message": str   # Description of deletion
            }
            or
            {
                "success": False,
                "error": str     # Error description
            }
        """
        if not isinstance(condition_id, str) or not condition_id:
            return { "success": False, "error": "Invalid condition_id parameter." }

        if condition_id not in self.medical_conditions:
            return { "success": False, "error": "Medical condition does not exist." }
    
        deleted_name = self.medical_conditions[condition_id]["name"]
        del self.medical_conditions[condition_id]

        return {
            "success": True,
            "message": f"Medical condition '{deleted_name}' (ID: {condition_id}) was deleted."
        }

    def delete_symptom(self, symptom_id: str) -> dict:
        """
        Delete a symptom from the knowledge base and remove all references to it in medical conditions.

        Args:
            symptom_id (str): The unique identifier for the symptom to delete.

        Returns:
            dict:
                {
                    "success": True,
                    "message": "Symptom deleted and references updated."
                }
                OR
                {
                    "success": False,
                    "error": "<reason>"
                }

        Constraints:
            - Symptom must exist.
            - All medical conditions referencing this symptom must have that reference removed for referential integrity.
        """
        if symptom_id not in self.symptoms:
            return {
                "success": False,
                "error": f"Symptom with id '{symptom_id}' does not exist."
            }

        # Remove references from all medical conditions
        for condition in self.medical_conditions.values():
            if symptom_id in condition["symptom_ids"]:
                condition["symptom_ids"].remove(symptom_id)

        # Remove the symptom itself
        del self.symptoms[symptom_id]

        return {
            "success": True,
            "message": "Symptom deleted and references updated."
        }

    def delete_cause(self, cause_id: str) -> dict:
        """
        Delete the cause with the given cause_id and remove its references from all associated medical conditions.

        Args:
            cause_id (str): The unique identifier for the cause to delete.

        Returns:
            dict:
              Success: {"success": True, "message": "Cause deleted and references removed from medical conditions."}
              Failure: {"success": False, "error": "Cause not found."}

        Constraints:
            - If the cause does not exist, operation fails.
            - All references to the cause in any medical condition's 'cause_ids' must be removed (referential integrity).
        """
        # If cause_id doesn't exist, fail
        if cause_id not in self.causes:
            return {"success": False, "error": "Cause not found."}

        # Remove reference from all medical conditions
        for cond in self.medical_conditions.values():
            if cause_id in cond["cause_ids"]:
                cond["cause_ids"] = [cid for cid in cond["cause_ids"] if cid != cause_id]

        # Delete the cause itself
        del self.causes[cause_id]

        return {
            "success": True,
            "message": "Cause deleted and references removed from medical conditions."
        }

    def delete_treatment(self, treatment_id: str) -> dict:
        """
        Delete a treatment and update related medical conditions accordingly.

        Args:
            treatment_id (str): The unique ID of the treatment to be deleted.

        Returns:
            dict: {
                "success": True,
                "message": "Treatment deleted and relationships updated successfully."
            }
            or
            {
                "success": False,
                "error": "Treatment not found."
            }

        Constraints:
            - If the treatment does not exist, return an error.
            - All medical conditions referencing this treatment must have it removed from their treatment_ids list.
            - Referential integrity must always be maintained.
        """
        if treatment_id not in self.treatments:
            return {"success": False, "error": "Treatment not found."}

        # Remove treatment from the treatments dict
        del self.treatments[treatment_id]

        # Remove the reference from all medical conditions
        for condition in self.medical_conditions.values():
            if treatment_id in condition.get("treatment_ids", []):
                condition["treatment_ids"] = [
                    t_id for t_id in condition["treatment_ids"] if t_id != treatment_id
                ]

        return {
            "success": True,
            "message": "Treatment deleted and relationships updated successfully."
        }


class MedicalKnowledgeBaseSystem(BaseEnv):
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

    def get_medical_condition_by_name(self, **kwargs):
        return self._call_inner_tool('get_medical_condition_by_name', kwargs)

    def get_all_medical_conditions(self, **kwargs):
        return self._call_inner_tool('get_all_medical_conditions', kwargs)

    def get_medical_condition_details(self, **kwargs):
        return self._call_inner_tool('get_medical_condition_details', kwargs)

    def find_symptom_by_name(self, **kwargs):
        return self._call_inner_tool('find_symptom_by_name', kwargs)

    def get_all_symptoms(self, **kwargs):
        return self._call_inner_tool('get_all_symptoms', kwargs)

    def find_cause_by_name(self, **kwargs):
        return self._call_inner_tool('find_cause_by_name', kwargs)

    def get_all_causes(self, **kwargs):
        return self._call_inner_tool('get_all_causes', kwargs)

    def find_treatment_by_name(self, **kwargs):
        return self._call_inner_tool('find_treatment_by_name', kwargs)

    def get_all_treatments(self, **kwargs):
        return self._call_inner_tool('get_all_treatments', kwargs)

    def list_conditions_with_symptom(self, **kwargs):
        return self._call_inner_tool('list_conditions_with_symptom', kwargs)

    def list_conditions_with_cause(self, **kwargs):
        return self._call_inner_tool('list_conditions_with_cause', kwargs)

    def list_conditions_with_treatment(self, **kwargs):
        return self._call_inner_tool('list_conditions_with_treatment', kwargs)

    def add_medical_condition(self, **kwargs):
        return self._call_inner_tool('add_medical_condition', kwargs)

    def update_medical_condition(self, **kwargs):
        return self._call_inner_tool('update_medical_condition', kwargs)

    def add_or_link_symptom(self, **kwargs):
        return self._call_inner_tool('add_or_link_symptom', kwargs)

    def add_or_link_cause(self, **kwargs):
        return self._call_inner_tool('add_or_link_cause', kwargs)

    def add_or_link_treatment(self, **kwargs):
        return self._call_inner_tool('add_or_link_treatment', kwargs)

    def update_symptom(self, **kwargs):
        return self._call_inner_tool('update_symptom', kwargs)

    def update_cause(self, **kwargs):
        return self._call_inner_tool('update_cause', kwargs)

    def update_treatment(self, **kwargs):
        return self._call_inner_tool('update_treatment', kwargs)

    def remove_symptom_from_condition(self, **kwargs):
        return self._call_inner_tool('remove_symptom_from_condition', kwargs)

    def remove_cause_from_condition(self, **kwargs):
        return self._call_inner_tool('remove_cause_from_condition', kwargs)

    def remove_treatment_from_condition(self, **kwargs):
        return self._call_inner_tool('remove_treatment_from_condition', kwargs)

    def delete_medical_condition(self, **kwargs):
        return self._call_inner_tool('delete_medical_condition', kwargs)

    def delete_symptom(self, **kwargs):
        return self._call_inner_tool('delete_symptom', kwargs)

    def delete_cause(self, **kwargs):
        return self._call_inner_tool('delete_cause', kwargs)

    def delete_treatment(self, **kwargs):
        return self._call_inner_tool('delete_treatment', kwargs)

