# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, TypedDict, Optional
from datetime import datetime



# Entity: Patient
class PatientInfo(TypedDict):
    patient_id: str
    name: str
    date_of_birth: str
    demographics: str  # For simplicity, assuming demographics is a serialized string or JSON
    contact_info: str

# Entity: Sample
class SampleInfo(TypedDict):
    sample_id: str
    patient_id: str
    collection_time: str
    sample_type: str
    status: str

# Entity: TestOrder
class TestOrderInfo(TypedDict):
    test_order_id: str
    patient_id: str
    sample_id: Optional[str]  # Some test orders may not have a sample yet
    test_type: str
    order_time: str
    status: str

# Entity: TestResult
class TestResultInfo(TypedDict):
    test_result_id: str
    test_order_id: str
    result_value: str  # Could be string or float, adjust type as needed
    units: str
    result_time: str
    reference_range: str
    interpretation: str
    status: str

class _GeneratedEnvImpl:
    def __init__(self):
        """
        Clinical Laboratory Information System (LIS) environment.
        Manages patients, samples, test orders, and test results.
        """
        # Patients: {patient_id: PatientInfo}
        self.patients: Dict[str, PatientInfo] = {}

        # Samples: {sample_id: SampleInfo}
        self.samples: Dict[str, SampleInfo] = {}

        # Test Orders: {test_order_id: TestOrderInfo}
        self.test_orders: Dict[str, TestOrderInfo] = {}

        # Test Results: {test_result_id: TestResultInfo}
        self.test_results: Dict[str, TestResultInfo] = {}

        # Constraints:
        # - Each test result must be associated with a valid test order.
        # - Each test order must be associated with a valid patient and (where applicable) a valid sample.
        # - Patients may have multiple test orders and results—querying the "latest" result requires result_time or order_time tracking.
        # - Access to test results must be secure and comply with patient confidentiality and regulatory requirements.

    def get_patient_by_id(self, patient_id: str) -> dict:
        """
        Retrieve a patient's full demographic information by their patient_id.

        Args:
            patient_id (str): The unique identifier of the patient.

        Returns:
            dict:
                - If found:
                    {"success": True, "data": PatientInfo}
                - If not found:
                    {"success": False, "error": "Patient not found"}

        Constraints:
            - The patient_id must exist in the system.
            - No state is modified.
        """
        patient = self.patients.get(patient_id)
        if patient is None:
            return { "success": False, "error": "Patient not found" }
        return { "success": True, "data": patient }

    def find_patient_by_demographics(
        self, 
        name: str = None, 
        date_of_birth: str = None, 
        demographics: str = None
    ) -> dict:
        """
        Retrieve patient(s) by matching one or more demographic criteria: name, date_of_birth, and/or demographics.

        Args:
            name (Optional[str]): Patient's name (full or partial, case-insensitive match).
            date_of_birth (Optional[str]): Patient's date of birth (exact match, e.g., 'YYYY-MM-DD').
            demographics (Optional[str]): Additional demographics info (case-insensitive substring match).

        Returns:
            dict:
                {
                    "success": True,
                    "data": List[PatientInfo],  # matching patient records (may be empty)
                }
                OR
                {
                    "success": False,
                    "error": str  # Error description for why the query couldn't be performed.
                }

        Constraints:
            - At least one of name, date_of_birth, or demographics must be provided.
            - Matching is loose substring for name/demographics (case-insensitive), exact for date_of_birth.
        """
        if not (name or date_of_birth or demographics):
            return {"success": False, "error": "At least one demographic field (name, date_of_birth, demographics) must be provided for patient search."}

        name_query = name.lower() if name else None
        demo_query = demographics.lower() if demographics else None

        matches = []
        for patient in self.patients.values():
            matched = True

            if name_query and name_query not in patient["name"].lower():
                matched = False
            if date_of_birth and date_of_birth != patient["date_of_birth"]:
                matched = False
            if demo_query and demo_query not in patient["demographics"].lower():
                matched = False

            if matched:
                matches.append(patient)

        return {"success": True, "data": matches}

    def list_samples_by_patient(self, patient_id: str) -> dict:
        """
        List all samples (SampleInfo) associated with a specified patient_id.

        Args:
            patient_id (str): The unique identifier for the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[SampleInfo]  # May be empty if patient has no samples
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "Patient does not exist"
            }

        Constraints:
            - patient_id must refer to a valid patient in the system.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        results = [
            sample for sample in self.samples.values() if sample["patient_id"] == patient_id
        ]

        return { "success": True, "data": results }

    def get_sample_by_id(self, sample_id: str) -> dict:
        """
        Retrieve details for a specific sample given its sample_id.

        Args:
            sample_id (str): The unique identifier of the sample.

        Returns:
            dict:
                - If found: {"success": True, "data": SampleInfo}
                - If not found: {"success": False, "error": "Sample not found"}
        """
        sample = self.samples.get(sample_id)
        if sample is None:
            return {"success": False, "error": "Sample not found"}
        return {"success": True, "data": sample}

    def list_test_orders_by_patient(self, patient_id: str) -> dict:
        """
        Retrieve all test orders associated with the given patient_id.

        Args:
            patient_id (str): The unique identifier for the patient.

        Returns:
            dict: {
                "success": True,
                "data": List[TestOrderInfo]  # All test orders for the patient (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Error description, e.g., patient does not exist
            }

        Constraints:
            - patient_id must exist in the system.
            - Returns empty list if patient exists but has no test orders.
        """
        if patient_id not in self.patients:
            return { "success": False, "error": "Patient does not exist" }

        orders = [
            test_order
            for test_order in self.test_orders.values()
            if test_order["patient_id"] == patient_id
        ]

        return { "success": True, "data": orders }

    def list_test_orders_by_sample(self, sample_id: str) -> dict:
        """
        Retrieve all test orders associated with a specific sample.

        Args:
            sample_id (str): The identifier of the sample.

        Returns:
            dict: {
                "success": True,
                "data": List[TestOrderInfo]  # List of all test orders for the sample (may be empty)
            }
            or
            {
                "success": False,
                "error": str  # Reason, e.g. "Sample not found"
            }

        Constraints:
            - The sample_id must exist in the samples table.
            - Returns all test orders where sample_id matches.
        """
        if sample_id not in self.samples:
            return {"success": False, "error": "Sample not found"}

        orders = [
            order for order in self.test_orders.values()
            if order.get("sample_id") == sample_id
        ]

        return {"success": True, "data": orders}

    def get_test_order_by_id(self, test_order_id: str) -> dict:
        """
        Retrieve details for a specific test order via test_order_id.

        Args:
            test_order_id (str): The unique identifier for the test order.

        Returns:
            dict: {
                "success": True,
                "data": TestOrderInfo
            }
            or
            {
                "success": False,
                "error": "Test order not found"
            }
        Constraints:
            - test_order_id must exist in the system.
        """
        test_order = self.test_orders.get(test_order_id)
        if test_order is None:
            return { "success": False, "error": "Test order not found" }
        return { "success": True, "data": test_order }

    def list_test_results_by_patient(self, patient_id: str) -> dict:
        """
        Retrieve all test results (via test orders) associated with a given patient.

        Args:
            patient_id (str): ID of the patient whose test results are to be retrieved.

        Returns:
            dict: {
                "success": True,
                "data": List[TestResultInfo]  # May be an empty list if no results found
            }
            OR
            {
                "success": False,
                "error": str  # "Patient not found"
            }

        Constraints:
            - The patient_id must exist in the patients registry.
            - Only retrieves results attached via test orders referencing the patient_id.
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}

        # Find all test_order_ids for this patient
        relevant_orders = [
            order["test_order_id"]
            for order in self.test_orders.values()
            if order["patient_id"] == patient_id
        ]

        # Fetch all test results attached to these orders
        results = [
            result
            for result in self.test_results.values()
            if result["test_order_id"] in relevant_orders
        ]

        return {
            "success": True,
            "data": results
        }

    def list_test_results_by_order(self, test_order_id: str) -> dict:
        """
        Retrieve all test results associated with a specified test order.

        Args:
            test_order_id (str): The unique ID of the test order to query.

        Returns:
            dict: {
                "success": True,
                "data": List[TestResultInfo],  # All test results for the order; may be empty if none
            }
            or
            {
                "success": False,
                "error": str  # Error message if test_order_id not found
            }

        Constraints:
            - test_order_id must exist in self.test_orders.
        """
        if test_order_id not in self.test_orders:
            return { "success": False, "error": "Test order does not exist" }
    
        result_list = [
            test_result for test_result in self.test_results.values()
            if test_result["test_order_id"] == test_order_id
        ]
        return { "success": True, "data": result_list }

    def get_test_result_by_id(self, test_result_id: str) -> dict:
        """
        Retrieve details for a specific test result by its unique test_result_id.

        Args:
            test_result_id (str): The unique identifier for the desired test result.

        Returns:
            dict: {
                "success": True,
                "data": TestResultInfo
            }
            or
            {
                "success": False,
                "error": "Test result not found"
            }

        Constraints:
            - The test result must exist in the LIS.
            - Does not enforce access control; assumes caller is authorized.
        """
        test_result = self.test_results.get(test_result_id)
        if not test_result:
            return {"success": False, "error": "Test result not found"}
        return {"success": True, "data": test_result}

    def get_latest_test_result_by_patient(self, patient_id: str) -> dict:
        """
        Retrieve the most recent test result(s) for the given patient, based on result_time.
    
        Args:
            patient_id (str): The identifier of the patient.
    
        Returns:
            dict: 
              On success:
                {
                    "success": True,
                    "data": List[TestResultInfo],  # May be empty if there are no results
                }
              On failure:
                {
                    "success": False,
                    "error": str
                }
        Constraints:
            - Patient must exist.
            - Returns all results with the latest result_time (if tie).
        """
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient not found"}
    
        # Get all test order IDs for the patient
        test_order_ids = [
            test_order_id for test_order_id, order in self.test_orders.items()
            if order["patient_id"] == patient_id
        ]
    
        if not test_order_ids:
            return {"success": True, "data": []}
    
        # Gather all test results for these orders
        patient_results = [
            result for result in self.test_results.values()
            if result["test_order_id"] in test_order_ids
        ]
    
        if not patient_results:
            return {"success": True, "data": []}
    
        # Find the latest result_time(s)
        # Assuming result_time is in ISO 8601 string format (or sortable)
        max_time = max(result["result_time"] for result in patient_results)
        latest_results = [
            result for result in patient_results
            if result["result_time"] == max_time
        ]
    
        return {"success": True, "data": latest_results}

    def list_test_results_by_time_range(
        self,
        start_time: str,
        end_time: str,
        patient_id: str = None,
        test_order_id: str = None
    ) -> dict:
        """
        Retrieve all test results within a specified time window filtered by patient or test order.

        Args:
            start_time (str): Start of the date/time window (ISO datetime string).
            end_time (str): End of the date/time window (ISO datetime string).
            patient_id (Optional[str]): (Optional) Patient ID to filter results by.
            test_order_id (Optional[str]): (Optional) Test order ID to filter results by.

        Returns:
            dict: {
                "success": True,
                "data": List[TestResultInfo]  # May be empty if none found
            }
            or
            {
                "success": False,
                "error": str  # Description of why the request failed
            }

        Constraints:
            - At least one of patient_id or test_order_id must be provided.
            - The provided IDs must exist in the corresponding records.
            - Only results where result_time >= start_time and result_time <= end_time are returned.
        """

        # Validate time window
        try:
            t_start = datetime.fromisoformat(start_time)
            t_end = datetime.fromisoformat(end_time)
            if t_start > t_end:
                return { "success": False, "error": "start_time must be less than or equal to end_time" }
        except Exception:
            return { "success": False, "error": "Invalid time format. Use ISO format (YYYY-MM-DDTHH:MM:SS)" }

        if not patient_id and not test_order_id:
            return { "success": False, "error": "Must provide at least patient_id or test_order_id" }

        # Gather candidate test_result_ids
        candidate_test_result_ids = set()

        # If test_order_id is provided, check existence, filter directly by it
        if test_order_id:
            if test_order_id not in self.test_orders:
                return { "success": False, "error": "test_order_id not found" }
            # Collect test results for this order
            for tr_id, tr_info in self.test_results.items():
                if tr_info['test_order_id'] == test_order_id:
                    candidate_test_result_ids.add(tr_id)
        elif patient_id:
            # test_order_id not provided; use all test orders for this patient
            if patient_id not in self.patients:
                return { "success": False, "error": "patient_id not found" }
            patient_test_orders = [
                to_id for to_id, to_info in self.test_orders.items()
                if to_info['patient_id'] == patient_id
            ]
            # Collect all test results for these orders
            for tr_id, tr_info in self.test_results.items():
                if tr_info['test_order_id'] in patient_test_orders:
                    candidate_test_result_ids.add(tr_id)
        else:
            # Should not reach here
            return { "success": False, "error": "Invalid query scope" }

        # Now, filter candidate results by result_time
        results_in_range = []
        for tr_id in candidate_test_result_ids:
            tr_info = self.test_results[tr_id]
            try:
                tr_time = datetime.fromisoformat(tr_info['result_time'])
            except Exception:
                continue  # Skip invalid date format entries
            if t_start <= tr_time <= t_end:
                results_in_range.append(tr_info)

        return { "success": True, "data": results_in_range }

    def add_patient(
        self,
        patient_id: str,
        name: str,
        date_of_birth: str,
        demographics: str,
        contact_info: str
    ) -> dict:
        """
        Add a new patient record to the system.

        Args:
            patient_id (str): Unique identifier for the patient (must not already exist).
            name (str): Patient's name.
            date_of_birth (str): Patient's date of birth.
            demographics (str): Patient's demographic information (serialized string).
            contact_info (str): Contact information for the patient.

        Returns:
            dict:
                Success: { "success": True, "message": "Patient record added." }
                Failure: { "success": False, "error": "Patient ID already exists." }

        Constraints:
            - The patient_id must be unique within the system.
        """
        if patient_id in self.patients:
            return { "success": False, "error": "Patient ID already exists." }

        self.patients[patient_id] = {
            "patient_id": patient_id,
            "name": name,
            "date_of_birth": date_of_birth,
            "demographics": demographics,
            "contact_info": contact_info
        }
        return { "success": True, "message": "Patient record added." }

    def update_patient_info(
        self,
        patient_id: str,
        demographics: str = None,
        contact_info: str = None
    ) -> dict:
        """
        Update demographic and/or contact information for an existing patient.

        Args:
            patient_id (str): Unique identifier of the patient.
            demographics (str, optional): New demographics information. If None, will not update.
            contact_info (str, optional): New contact information. If None, will not update.

        Returns:
            dict: 
                Success: {"success": True, "message": "Patient info updated for patient_id <id>."}
                Failure: {"success": False, "error": "reason"}

        Constraints:
            - The patient with patient_id must already exist.
            - At least one of demographics/contact_info must be provided (otherwise, no update is performed).
        """
        patient = self.patients.get(patient_id)
        if not patient:
            return {"success": False, "error": "Patient not found."}
    
        updated = False
        if demographics is not None:
            patient["demographics"] = demographics
            updated = True
        if contact_info is not None:
            patient["contact_info"] = contact_info
            updated = True
    
        if not updated:
            return {"success": False, "error": "No update fields provided."}
    
        self.patients[patient_id] = patient  # Optional, since dict is mutable, but ensures state sync.

        return {"success": True, "message": f"Patient info updated for patient_id {patient_id}."}

    def add_sample(
        self,
        sample_id: str,
        patient_id: str,
        collection_time: str,
        sample_type: str,
        status: str
    ) -> dict:
        """
        Add a new sample entry associated with a patient.

        Args:
            sample_id (str): Unique identifier for the new sample.
            patient_id (str): Existing patient ID to associate with this sample.
            collection_time (str): When the sample was collected.
            sample_type (str): The type of specimen (e.g., "blood", "urine").
            status (str): The workflow status of the sample.

        Returns:
            dict: {
                "success": True,
                "message": "Sample <sample_id> added for patient <patient_id>."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - sample_id must be unique.
            - patient_id must refer to an existing patient.
        """
        # Check for uniqueness of sample_id
        if sample_id in self.samples:
            return { "success": False, "error": f"Sample ID '{sample_id}' already exists." }
    
        # Check if the patient exists
        if patient_id not in self.patients:
            return { "success": False, "error": f"Patient ID '{patient_id}' does not exist." }
    
        # Basic check for required fields (optionally could add more validation)
        if not (sample_id and patient_id and collection_time and sample_type and status):
            return { "success": False, "error": "All sample fields must be provided and non-empty." }
    
        sample_info: SampleInfo = {
            "sample_id": sample_id,
            "patient_id": patient_id,
            "collection_time": collection_time,
            "sample_type": sample_type,
            "status": status
        }
    
        self.samples[sample_id] = sample_info

        return {
            "success": True,
            "message": f"Sample '{sample_id}' added for patient '{patient_id}'."
        }

    def update_sample_status(self, sample_id: str, status: str) -> dict:
        """
        Modify the status of an existing sample.

        Args:
            sample_id (str): The unique identifier of the sample to update.
            status (str): The new status to assign (e.g., 'collected', 'in process', 'completed').

        Returns:
            dict:
                On success: { "success": True, "message": "Sample status updated." }
                On failure: { "success": False, "error": "<reason>" }

        Constraints:
            - The sample with the given sample_id must exist in the system.
            - Any non-empty status string is accepted (no enforced valid status list).
        """
        if sample_id not in self.samples:
            return { "success": False, "error": "Sample not found." }
        if not isinstance(status, str) or not status.strip():
            return { "success": False, "error": "Invalid status." }
        self.samples[sample_id]['status'] = status.strip()
        return { "success": True, "message": "Sample status updated." }

    def add_test_order(
        self, 
        test_order_id: str, 
        patient_id: str, 
        test_type: str, 
        order_time: str, 
        status: str,
        sample_id: Optional[str] = None
    ) -> dict:
        """
        Create a new test order for a patient and, if available, associate it with a sample.

        Args:
            test_order_id (str): Unique identifier for this test order.
            patient_id (str): ID of the patient for whom this test is ordered.
            test_type (str): The type of laboratory test to perform.
            order_time (str): Time the order was placed (ISO string or similar).
            status (str): Initial status of the order.
            sample_id (Optional[str]): ID of the associated sample if available.

        Returns:
            dict: 
                On success: {
                    "success": True, 
                    "message": "Test order added for patient <patient_id>."
                }
                On failure: {
                    "success": False,
                    "error": <error_message>
                }

        Constraints:
            - The test_order_id must be unique (not already present).
            - The patient_id must reference an existing patient.
            - If sample_id is provided, it must exist in the samples registry.
            - Each test order must be associated with a valid patient and (if provided) valid sample.

        """
        if test_order_id in self.test_orders:
            return {"success": False, "error": "Test order ID already exists."}
        if patient_id not in self.patients:
            return {"success": False, "error": "Patient does not exist."}
        if sample_id is not None and sample_id not in self.samples:
            return {"success": False, "error": "Sample does not exist."}

        self.test_orders[test_order_id] = {
            "test_order_id": test_order_id,
            "patient_id": patient_id,
            "sample_id": sample_id,
            "test_type": test_type,
            "order_time": order_time,
            "status": status
        }

        return {
            "success": True,
            "message": f"Test order added for patient {patient_id}."
        }

    def update_test_order_status(self, test_order_id: str, new_status: str) -> dict:
        """
        Change the progress status of a test order.

        Args:
            test_order_id (str): The ID of the test order to update.
            new_status (str): The desired new status (e.g., "ordered", "in-process", "completed", "cancelled").

        Returns:
            dict:
                - On success: { "success": True, "message": "Test order status updated." }
                - On failure: { "success": False, "error": <reason> }

        Constraints:
            - The test order must exist in the system.
            - Optionally restrict status values to a known set: "ordered", "in-process", "completed", "cancelled".
        """
        if test_order_id not in self.test_orders:
            return { "success": False, "error": "Test order does not exist." }
        if not isinstance(new_status, str) or not new_status.strip():
            return { "success": False, "error": "Invalid status." }

        self.test_orders[test_order_id]["status"] = new_status.strip()

        return { "success": True, "message": "Test order status updated." }

    def add_test_result(
        self,
        test_result_id: str,
        test_order_id: str,
        result_value: str,
        units: str,
        result_time: str,
        reference_range: str,
        interpretation: str,
        status: str
    ) -> dict:
        """
        Add a new test result associated with an existing test order.

        Args:
            test_result_id (str): Unique identifier for the test result.
            test_order_id (str): ID of the associated test order. Must exist.
            result_value (str): Result value of the test.
            units (str): Units for the result value.
            result_time (str): Timestamp when the test result was generated.
            reference_range (str): Reference range for the result.
            interpretation (str): Interpretation of the result (e.g. 'Normal', 'High').
            status (str): Status of the result (e.g. 'final', 'preliminary').

        Returns:
            dict: {
                "success": True,
                "message": "Test result added successfully",
                "test_result_id": <test_result_id>
            }
            or
            {
                "success": False,
                "error": str
            }

        Constraints:
            - The referenced test_order_id must exist in the test_orders.
            - The test_result_id must be unique (not already in test_results).
        """
        # Check for required test order
        if test_order_id not in self.test_orders:
            return {"success": False, "error": "Associated test_order_id does not exist"}

        # Check uniqueness
        if test_result_id in self.test_results:
            return {"success": False, "error": "Test result ID already exists"}

        # Check for required fields (basic)
        if not all([
            test_result_id, test_order_id, result_value, units,
            result_time, reference_range, interpretation, status
        ]):
            return {"success": False, "error": "Missing required fields"}

        test_result_info: TestResultInfo = {
            "test_result_id": test_result_id,
            "test_order_id": test_order_id,
            "result_value": result_value,
            "units": units,
            "result_time": result_time,
            "reference_range": reference_range,
            "interpretation": interpretation,
            "status": status
        }
        self.test_results[test_result_id] = test_result_info
        return {
            "success": True,
            "message": "Test result added successfully",
            "test_result_id": test_result_id
        }

    def update_test_result_status(self, test_result_id: str, new_status: str) -> dict:
        """
        Modify the status of a test result (e.g., preliminary, final, corrected).

        Args:
            test_result_id (str): The unique ID of the test result to update.
            new_status (str): The new status value to set (e.g., "preliminary", "final", "corrected").

        Returns:
            dict: {
                "success": True,
                "message": "Test result status updated successfully."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - The test_result_id must exist in the system.
            - The new_status must be a non-empty string.
        """
        if test_result_id not in self.test_results:
            return {"success": False, "error": "Test result ID does not exist."}

        if not isinstance(new_status, str) or new_status.strip() == "":
            return {"success": False, "error": "Invalid new status value."}

        self.test_results[test_result_id]['status'] = new_status.strip()

        return {"success": True, "message": "Test result status updated successfully."}

    def delete_test_result(self, test_result_id: str) -> dict:
        """
        Remove a test result from the system (e.g., erroneous entry handling).
    
        Args:
            test_result_id (str): The unique identifier for the test result to remove.
    
        Returns:
            dict: {
                "success": True,
                "message": "Test result deleted"
            }
            or
            {
                "success": False,
                "error": "Test result not found"
            }

        Constraints:
            - TestResult must exist in the system to be deleted.
            - No referential clean-up in test order; dependent application logic should handle orphaned orders if needed.
        """
        if test_result_id not in self.test_results:
            return {"success": False, "error": "Test result not found"}

        del self.test_results[test_result_id]
        return {"success": True, "message": "Test result deleted"}

    def delete_test_order(self, test_order_id: str, delete_associated_results: bool = False) -> dict:
        """
        Remove a test order from the system. Optionally, also remove all associated test results.

        Args:
            test_order_id (str): The unique ID of the test order to remove.
            delete_associated_results (bool): If True, also delete all test results associated with this test order. 
                                              If False and there are associated results, operation is blocked to maintain integrity.

        Returns:
            dict: 
                - On success: {
                    "success": True, 
                    "message": "Test order deleted." / 
                               "Test order and X associated test results deleted."
                  }
                - On failure: {
                    "success": False, 
                    "error": "Test order does not exist." /
                             "Associated test results exist; pass delete_associated_results=True to delete them."
                  }

        Constraints:
            - Cannot leave test results without their associated test order.
            - Deletion of order with associated results only allowed if delete_associated_results is True.
        """
        if test_order_id not in self.test_orders:
            return { "success": False, "error": "Test order does not exist." }
    
        # Find associated test results
        associated_result_ids = [
            tr_id for tr_id, tr in self.test_results.items()
            if tr["test_order_id"] == test_order_id
        ]
        if associated_result_ids and not delete_associated_results:
            return {
                "success": False,
                "error": (
                    "Associated test results exist; pass delete_associated_results=True to delete them."
                )
            }
        # Delete test results if requested
        deleted_results_count = 0
        if associated_result_ids and delete_associated_results:
            for tr_id in associated_result_ids:
                del self.test_results[tr_id]
            deleted_results_count = len(associated_result_ids)
    
        # Delete the test order
        del self.test_orders[test_order_id]
    
        if deleted_results_count:
            return {
                "success": True,
                "message": f"Test order and {deleted_results_count} associated test result(s) deleted."
            }
        else:
            return {
                "success": True,
                "message": "Test order deleted."
            }

    def delete_sample(self, sample_id: str) -> dict:
        """
        Remove a sample from the LIS if it is allowed (i.e., if it is not referenced by any test order).

        Args:
            sample_id (str): The unique identifier for the sample to remove.

        Returns:
            dict:
                - success (bool)
                - message (str) if successful
                - error (str) if failed

        Constraints:
            - Cannot delete a sample if it is referenced by any test order.
            - Sample must exist to be deleted.
        """
        # Check if the sample exists
        if sample_id not in self.samples:
            return {"success": False, "error": f"Sample '{sample_id}' does not exist."}

        # Check if any test order references this sample
        for test_order in self.test_orders.values():
            if test_order.get("sample_id") == sample_id:
                return {
                    "success": False,
                    "error": f"Cannot delete sample '{sample_id}': it is referenced by test order '{test_order['test_order_id']}'."
                }

        # Passed checks, safe to delete
        del self.samples[sample_id]
        return {"success": True, "message": f"Sample '{sample_id}' deleted."}


class LaboratoryInformationSystem(BaseEnv):
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

    def get_patient_by_id(self, **kwargs):
        return self._call_inner_tool('get_patient_by_id', kwargs)

    def find_patient_by_demographics(self, **kwargs):
        return self._call_inner_tool('find_patient_by_demographics', kwargs)

    def list_samples_by_patient(self, **kwargs):
        return self._call_inner_tool('list_samples_by_patient', kwargs)

    def get_sample_by_id(self, **kwargs):
        return self._call_inner_tool('get_sample_by_id', kwargs)

    def list_test_orders_by_patient(self, **kwargs):
        return self._call_inner_tool('list_test_orders_by_patient', kwargs)

    def list_test_orders_by_sample(self, **kwargs):
        return self._call_inner_tool('list_test_orders_by_sample', kwargs)

    def get_test_order_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_order_by_id', kwargs)

    def list_test_results_by_patient(self, **kwargs):
        return self._call_inner_tool('list_test_results_by_patient', kwargs)

    def list_test_results_by_order(self, **kwargs):
        return self._call_inner_tool('list_test_results_by_order', kwargs)

    def get_test_result_by_id(self, **kwargs):
        return self._call_inner_tool('get_test_result_by_id', kwargs)

    def get_latest_test_result_by_patient(self, **kwargs):
        return self._call_inner_tool('get_latest_test_result_by_patient', kwargs)

    def list_test_results_by_time_range(self, **kwargs):
        return self._call_inner_tool('list_test_results_by_time_range', kwargs)

    def add_patient(self, **kwargs):
        return self._call_inner_tool('add_patient', kwargs)

    def update_patient_info(self, **kwargs):
        return self._call_inner_tool('update_patient_info', kwargs)

    def add_sample(self, **kwargs):
        return self._call_inner_tool('add_sample', kwargs)

    def update_sample_status(self, **kwargs):
        return self._call_inner_tool('update_sample_status', kwargs)

    def add_test_order(self, **kwargs):
        return self._call_inner_tool('add_test_order', kwargs)

    def update_test_order_status(self, **kwargs):
        return self._call_inner_tool('update_test_order_status', kwargs)

    def add_test_result(self, **kwargs):
        return self._call_inner_tool('add_test_result', kwargs)

    def update_test_result_status(self, **kwargs):
        return self._call_inner_tool('update_test_result_status', kwargs)

    def delete_test_result(self, **kwargs):
        return self._call_inner_tool('delete_test_result', kwargs)

    def delete_test_order(self, **kwargs):
        return self._call_inner_tool('delete_test_order', kwargs)

    def delete_sample(self, **kwargs):
        return self._call_inner_tool('delete_sample', kwargs)
