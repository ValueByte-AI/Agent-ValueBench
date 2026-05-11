# -*- coding: utf-8 -*-
from __future__ import annotations

import copy
from typing import Any, Dict

from .BaseEnv import BaseEnv

from typing import Dict, Optional, TypedDict, List
import re
from typing import Optional, Dict, Any
from datetime import datetime, timezone



# Represents deployed machine learning models
class ModelInfo(TypedDict):
    model_id: str
    model_name: str
    version: str
    deployment_status: str  # Corrected from 'deployment_sta'

# Records an individual prediction event
class PredictionInfo(TypedDict):
    prediction_id: str
    model_id: str              # Foreign key to Model
    batch_id: Optional[str]    # Optional, references PredictionBatch
    timestamp: str             # ISO8601 format, consistent time zone
    input_data_reference: str
    predicted_value: float
    actual_value: Optional[float]  # May be absent for unscored predictions
    evaluation_status: str     # Corrected from 'evaluation_sta'

# Groups predictions in a batch
class PredictionBatchInfo(TypedDict):
    batch_id: str
    model_id: str
    batch_timestamp: str       # ISO8601 format
    batch_size: int
    description: str

# Stores calculated performance metrics
class PerformanceMetricInfo(TypedDict):
    metric_id: str
    model_id: str
    aggregation_scope: str     # e.g., 'date', 'batch'
    scope_value: str           # e.g., '2024-11-05' or batch_id
    metric_type: str           # 'accuracy', 'precision', etc.
    metric_value: float
    computed_at: str           # ISO8601 format

class _GeneratedEnvImpl:
    """
    Environment for ML prediction monitoring.

    Constraints:
    - Every prediction must reference a valid model and (optionally) a batch.
    - Actual values must be present to compute performance metrics.
    - Performance metrics should be consistent with the set of predictions they summarize.
    - Querying by date/model/batch should be supported across predictions and performance metrics.
    - Timestamps should use a consistent time zone.
    """

    def __init__(self):
        # Models: {model_id: ModelInfo}
        self.models: Dict[str, ModelInfo] = {}

        # Predictions: {prediction_id: PredictionInfo}
        self.predictions: Dict[str, PredictionInfo] = {}

        # Prediction Batches: {batch_id: PredictionBatchInfo}
        self.prediction_batches: Dict[str, PredictionBatchInfo] = {}

        # Performance Metrics: {metric_id: PerformanceMetricInfo}
        self.performance_metrics: Dict[str, PerformanceMetricInfo] = {}

    def list_models(self) -> dict:
        """
        Return all registered models and their details.

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[ModelInfo]  # List of models, empty if none registered
            }
        """
        models_list = list(self.models.values())
        return { "success": True, "data": models_list }

    def get_model_by_id(self, model_id: str) -> dict:
        """
        Retrieve detailed information for a single model by its model_id.

        Args:
            model_id (str): The unique identifier of the model to look up.

        Returns:
            dict: {
                "success": True,
                "data": ModelInfo,  # Model information if found
            }
            or
            {
                "success": False,
                "error": str  # Error message if model_id not found
            }

        Constraints:
            - Model with the given model_id must exist in the system.
        """
        model_info = self.models.get(model_id)
        if model_info is None:
            return { "success": False, "error": "Model ID not found" }
        return { "success": True, "data": model_info }

    def list_predictions_by_date(self, date: str, model_id: str = None, batch_id: str = None) -> dict:
        """
        Retrieve predictions made on a specified date (optionally filtered by model or batch).

        Args:
            date (str): The target date in 'YYYY-MM-DD' format (ISO8601).
            model_id (Optional[str]): Only include predictions from this model (if given).
            batch_id (Optional[str]): Only include predictions from this batch (if given).

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionInfo],  # List of matching predictions (may be empty if none found)
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., invalid date format)
            }

        Constraints:
            - The prediction timestamp is in ISO8601 and matched by prefix with the date.
            - Filtering is ANDed: date (required), and optionally model_id/batch_id.
        """
        # Basic date validation (should be YYYY-MM-DD)
        if not isinstance(date, str) or not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return { "success": False, "error": "Invalid date format; expected YYYY-MM-DD." }

        results = []
        for pred in self.predictions.values():
            if not pred['timestamp'].startswith(date):
                continue
            if model_id is not None and pred['model_id'] != model_id:
                continue
            if batch_id is not None and pred['batch_id'] != batch_id:
                continue
            results.append(pred)

        return { "success": True, "data": results }

    def list_predictions_by_model(self, model_id: str) -> dict:
        """
        Retrieve all predictions associated with a specific model.

        Args:
            model_id (str): The unique identifier of the model.

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionInfo],  # All predictions with this model_id
            }
            or
            {
                "success": False,
                "error": str  # If the model does not exist
            }
    
        Constraints:
            - model_id must exist in the system (must reference a valid model).
        """
        if model_id not in self.models:
            return { "success": False, "error": "Model ID not found" }

        predictions = [
            pred for pred in self.predictions.values()
            if pred["model_id"] == model_id
        ]

        return { "success": True, "data": predictions }

    def list_predictions_by_batch(self, batch_id: str) -> dict:
        """
        Retrieve all predictions belonging to a given prediction batch.

        Args:
            batch_id (str): The ID of the prediction batch to query.

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionInfo],  # All predictions in the given batch
            }
            or
            {
                "success": False,
                "error": str  # If the batch does not exist
            }

        Constraints:
            - The given batch must exist in the system.
            - Only predictions whose 'batch_id' equals the input will be returned.
        """
        if batch_id not in self.prediction_batches:
            return { "success": False, "error": "Batch does not exist" }

        results = [
            prediction for prediction in self.predictions.values()
            if prediction.get("batch_id") == batch_id
        ]
        return { "success": True, "data": results }

    def get_prediction_by_id(self, prediction_id: str) -> dict:
        """
        Retrieve the information of a specific prediction by its prediction_id.

        Args:
            prediction_id (str): The unique identifier of the prediction.

        Returns:
            dict: 
                - If found: { "success": True, "data": PredictionInfo }
                - If not found: { "success": False, "error": "Prediction not found" }

        Constraints:
            - The prediction must exist in the monitoring system.
        """
        prediction = self.predictions.get(prediction_id)
        if prediction is None:
            return { "success": False, "error": "Prediction not found" }
        return { "success": True, "data": prediction }

    def list_batches_by_model(self, model_id: str) -> dict:
        """
        List all prediction batches for a given model.

        Args:
            model_id (str): The ID of the model whose batches are to be listed.

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionBatchInfo],  # All batches belonging to the model (empty list if none)
            }
            or
            {
                "success": False,
                "error": str  # Description of the error, e.g. model not found
            }

        Constraints:
            - The given model_id must refer to an existing model.
            - The result includes all batches with that model_id.
        """
        if model_id not in self.models:
            return {"success": False, "error": "Model not found"}

        batches = [
            batch_info for batch_info in self.prediction_batches.values()
            if batch_info["model_id"] == model_id
        ]

        return {"success": True, "data": batches}

    def list_batches_by_date(self, date: str) -> dict:
        """
        List all prediction batches created on the specified date.

        Args:
            date (str): Date in 'YYYY-MM-DD' format.

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionBatchInfo],  # List of batches for the given date, possibly empty
            }
            or
            {
                "success": False,
                "error": str  # Reason for failure (e.g., bad format)
            }

        Constraints:
            - Timestamps in the system use a consistent time zone.
            - The date argument should be in 'YYYY-MM-DD' format.
        """
        # Basic validation of the input date format
        if not isinstance(date, str) or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date):
            return { "success": False, "error": "Date must be in YYYY-MM-DD format." }
    
        result = [
            batch_info for batch_info in self.prediction_batches.values()
            if batch_info["batch_timestamp"].startswith(date)
        ]
        return {"success": True, "data": result}

    def get_batch_by_id(self, batch_id: str) -> dict:
        """
        Retrieve details for a specific prediction batch by batch_id.

        Args:
            batch_id (str): The unique identifier for the prediction batch.

        Returns:
            dict: 
                If found:
                    {
                        "success": True,
                        "data": PredictionBatchInfo
                    }
                If not found:
                    {
                        "success": False,
                        "error": "Prediction batch not found"
                    }

        Constraints:
            - batch_id must exist in the system.
        """
        batch = self.prediction_batches.get(batch_id)
        if batch is None:
            return {
                "success": False,
                "error": "Prediction batch not found"
            }
        return {
            "success": True,
            "data": batch
        }

    def list_performance_metrics_by_date(self, date: str) -> dict:
        """
        Retrieve all performance metrics aggregated per given date.

        Args:
            date (str): Date in ISO8601 format (YYYY-MM-DD), for which to fetch performance metrics.

        Returns:
            dict:
                - Success: {
                      "success": True,
                      "data": List[PerformanceMetricInfo],  # May be empty list
                  }
                - Failure: {
                      "success": False,
                      "error": str,
                  }

        Constraints:
            - Query only metrics where aggregation_scope == 'date' and scope_value == date
            - 'date' must be ISO format (YYYY-MM-DD)
            - No permission checks required, empty results are valid
        """
        # Basic ISO8601 date validation
        if not re.match(r"^\d{4}-\d{2}-\d{2}$", date):
            return { "success": False, "error": "Invalid date format. Expected YYYY-MM-DD." }

        result = [
            metric for metric in self.performance_metrics.values()
            if metric["aggregation_scope"] == "date" and metric["scope_value"] == date
        ]

        return { "success": True, "data": result }

    def list_performance_metrics_by_batch(self) -> dict:
        """
        Retrieve all performance metrics with aggregation_scope 'batch'.

        Returns:
            dict: {
                "success": True,
                "data": List[PerformanceMetricInfo]
            }
            If no metrics are found with batch scope, data will be an empty list.
        """
        batch_metrics = [
            metric
            for metric in self.performance_metrics.values()
            if metric.get("aggregation_scope") == "batch"
        ]
        return { "success": True, "data": batch_metrics }

    def list_performance_metrics_by_model(self, model_id: str) -> dict:
        """
        Retrieve all performance metrics associated with a given model.

        Args:
            model_id (str): The ID of the model to query performance metrics for.

        Returns:
            dict:
              - If model exists:
                  {
                      "success": True,
                      "data": List[PerformanceMetricInfo]  # list of metrics (may be empty)
                  }
              - If model does NOT exist:
                  {
                      "success": False,
                      "error": "Model does not exist"
                  }

        Constraints:
            - The model_id must exist in self.models.
        """
        if model_id not in self.models:
            return {"success": False, "error": "Model does not exist"}

        metrics = [
            metric for metric in self.performance_metrics.values()
            if metric["model_id"] == model_id
        ]
        return {"success": True, "data": metrics}

    def get_performance_metric_by_id(self, metric_id: str) -> dict:
        """
        Retrieve a single performance metric entry by its metric_id.

        Args:
            metric_id (str): The unique performance metric identifier.

        Returns:
            dict: On success:
                {
                    "success": True,
                    "data": PerformanceMetricInfo
                }
                On failure (e.g., not found):
                {
                    "success": False,
                    "error": str
                }

        Constraints:
            - The metric_id must exist in the performance metrics table.
        """
        metric = self.performance_metrics.get(metric_id)
        if metric is None:
            return {"success": False, "error": f"Performance metric with id {metric_id} does not exist"}
        return {"success": True, "data": metric}

    def get_predictions_with_missing_actuals(self) -> dict:
        """
        Return all predictions with missing actual values (actual_value is None).

        Args:
            None

        Returns:
            dict: {
                "success": True,
                "data": List[PredictionInfo],  # All predictions where actual_value is missing
            }

        Constraints:
            - Operates across all predictions.
            - No input parameters or filtering.
            - Returns empty list if no such predictions exist.
        """
        missing_actuals = [
            pred for pred in self.predictions.values()
            if pred.get("actual_value") is None
        ]
        return { "success": True, "data": missing_actuals }

    def get_latest_metric_computation_time(self, aggregation_scope: str, scope_value: str) -> dict:
        """
        For a given aggregation scope and scope value, return the most recent recomputation timestamp
        (computed_at) among performance metrics.

        Args:
            aggregation_scope (str): The grouping, e.g. 'date', 'batch'.
            scope_value (str): The specific value for the scope, e.g. '2024-11-05', batch_id.

        Returns:
            dict:
                - success: True, data: str (ISO8601 latest computed_at timestamp) or None if not found.
                - success: False, error: str (problem description).
        Constraints:
            - Only queries; does not modify state.
            - Timestamps should use consistent time zone.
        """
        if not aggregation_scope or not scope_value:
            return { "success": False, "error": "Missing aggregation_scope or scope_value." }

        metrics = [
            metric for metric in self.performance_metrics.values()
            if metric["aggregation_scope"] == aggregation_scope
               and metric["scope_value"] == scope_value
        ]
        if not metrics:
            return { "success": True, "data": None }

        # Pick the metric with the latest computed_at (ISO8601)
        latest = max(metrics, key=lambda m: m["computed_at"])
        return { "success": True, "data": latest["computed_at"] }

    def add_or_update_prediction(self, prediction: dict) -> dict:
        """
        Add a new prediction record or update an existing prediction.

        Args:
            prediction (dict): Dictionary containing prediction fields. Must include at minimum:
                - prediction_id (str): Unique identifier for the prediction.
                - model_id (str): Must reference a valid model.
                - Optional: batch_id (str), must reference an existing batch if supplied.
                - timestamp (str)
                - input_data_reference (str)
                - predicted_value (float)
                - actual_value (Optional[float])
                - evaluation_status (str)

        Returns:
            dict: Success or failure status and message.
                On success:
                    {"success": True, "message": "Prediction added."}    # if new
                    {"success": True, "message": "Prediction updated."}  # if updated
                On failure:
                    {"success": False, "error": <reason>}

        Constraints:
            - model_id must reference an existing model.
            - If batch_id is provided, it must reference an existing batch.
            - If prediction_id already exists, update its content (upsert).
            - Do not raise exceptions.
        """
        required_fields = ["prediction_id", "model_id", "timestamp", "input_data_reference", "predicted_value", "evaluation_status"]
        for field in required_fields:
            if field not in prediction:
                return {"success": False, "error": f"Missing required field: {field}"}

        pred_id = prediction["prediction_id"]
        model_id = prediction["model_id"]
        batch_id = prediction.get("batch_id")

        # Check model_id
        if model_id not in self.models:
            return {"success": False, "error": "model_id does not reference a valid model"}

        # If batch_id is given, check existence
        if batch_id is not None and batch_id != "":
            if batch_id not in self.prediction_batches:
                return {"success": False, "error": "batch_id does not reference a valid prediction batch"}

        # If adding new
        if pred_id not in self.predictions:
            # Add as new prediction; assign defaults for missing optional fields
            new_prediction = {
                "prediction_id": pred_id,
                "model_id": model_id,
                "batch_id": batch_id,
                "timestamp": prediction["timestamp"],
                "input_data_reference": prediction["input_data_reference"],
                "predicted_value": prediction["predicted_value"],
                "actual_value": prediction.get("actual_value"),
                "evaluation_status": prediction["evaluation_status"]
            }
            self.predictions[pred_id] = new_prediction
            return {"success": True, "message": "Prediction added."}
        else:
            # Update existing prediction
            pred = self.predictions[pred_id]
            # Only allow update of allowed fields — update fields present in prediction argument
            updatable_fields = [
                "model_id", "batch_id", "timestamp", "input_data_reference",
                "predicted_value", "actual_value", "evaluation_status"
            ]
            for field in updatable_fields:
                if field in prediction:
                    # For batch_id, must check validity if updating
                    if field == "batch_id":
                        if prediction[field] is not None and prediction[field] != "":
                            if prediction[field] not in self.prediction_batches:
                                return {"success": False, "error": "batch_id does not reference a valid prediction batch"}
                    pred[field] = prediction[field]
            self.predictions[pred_id] = pred
            return {"success": True, "message": "Prediction updated."}

    def add_prediction_batch(
        self,
        batch_id: str,
        model_id: str,
        batch_timestamp: str,
        batch_size: int,
        description: str
    ) -> dict:
        """
        Add a new prediction batch to the monitoring system.

        Args:
            batch_id (str): Unique batch identifier.
            model_id (str): Existing model reference.
            batch_timestamp (str): When this batch was created (ISO8601, consistent time zone).
            batch_size (int): Number of predictions in the batch.
            description (str): Human-friendly description.

        Returns:
            dict: 
                On success: { "success": True, "message": f"Prediction batch {batch_id} added." }
                On failure: { "success": False, "error": <message> }

        Constraints:
            - batch_id must be unique.
            - model_id must exist in models.
            - batch_timestamp must be string (ISO8601).
        """
        if batch_id in self.prediction_batches:
            return { "success": False, "error": f"Batch with id {batch_id} already exists." }
        if model_id not in self.models:
            return { "success": False, "error": f"Model with id {model_id} does not exist." }

        self.prediction_batches[batch_id] = {
            "batch_id": batch_id,
            "model_id": model_id,
            "batch_timestamp": batch_timestamp,
            "batch_size": batch_size,
            "description": description
        }
        return { "success": True, "message": f"Prediction batch {batch_id} added." }

    def add_model(
        self,
        model_id: str,
        model_name: str,
        version: str,
        deployment_status: str
    ) -> dict:
        """
        Register a new model in the prediction monitoring system.

        Args:
            model_id (str): Unique identifier for the model (must not exist already).
            model_name (str): Human-readable name for the model.
            version (str): Version string for the model.
            deployment_status (str): Deployment status (e.g. 'deployed', 'inactive').

        Returns:
            dict:
                On success:
                    {
                        "success": True,
                        "message": "Model added successfully."
                    }
                On failure:
                    {
                        "success": False,
                        "error": <reason>
                    }

        Constraints:
            - model_id must be unique in the models registry.
            - All fields must be non-empty strings.
        """
        # Check for missing or empty parameters
        if not all([model_id, model_name, version, deployment_status]):
            return {"success": False, "error": "All parameters are required and must be non-empty."}

        if model_id in self.models:
            return {"success": False, "error": "Model ID already exists."}

        # Populate model info
        model_info: ModelInfo = {
            "model_id": model_id,
            "model_name": model_name,
            "version": version,
            "deployment_status": deployment_status
        }

        self.models[model_id] = model_info

        return {"success": True, "message": "Model added successfully."}

    def edit_actual_value_for_prediction(self, prediction_id: str, actual_value: Optional[float]) -> dict:
        """
        Change or supply an actual value for an existing prediction.

        Args:
            prediction_id (str): The ID of the prediction to update.
            actual_value (float): The value to set as the actual outcome.

        Returns:
            dict: {
                "success": True,
                "message": "Actual value updated for prediction."
            }
            or
            {
                "success": False,
                "error": "reason"
            }

        Constraints:
            - The prediction must exist.
            - Recalculation of performance metrics may be needed, but is not triggered here.
            - The evaluation_status field is set to 'scored' if actual_value is not None, else 'unscored'.
        """
        prediction = self.predictions.get(prediction_id)
        if not prediction:
            return { "success": False, "error": "Prediction does not exist." }
        prediction["actual_value"] = actual_value
        prediction["evaluation_status"] = "scored" if actual_value is not None else "unscored"
        self.predictions[prediction_id] = prediction
        # Note: Performance metric recalculation may be needed, but not performed here.
        return { "success": True, "message": "Actual value updated for prediction." }


    def recalculate_performance_metrics(
        self,
        *,
        model_id: Optional[str] = None,
        batch_id: Optional[str] = None,
        date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Recompute and update all performance metrics for a specified model, batch, or date.

        Args:
            model_id (str, optional): The model to target for recomputation.
            batch_id (str, optional): The batch to target for recomputation.
            date (str, optional): The ISO date ('YYYY-MM-DD') for which to recompute metrics.

        Returns:
            dict: {
                "success": True,
                "message": summary info (e.g., performance metrics recomputed for model X / batch Y / date Z)
            }
            or
            {
                "success": False,
                "error": reason
            }

        Constraints:
            - Exactly one of model_id, batch_id, or date must be specified.
            - Only predictions with non-null actual_value are used.
            - All existing affected PerformanceMetricInfo are replaced/updated.
            - Sets computed_at to now (UTC, ISO).
        """
        # Parameter validation
        filters = [model_id is not None, batch_id is not None, date is not None]
        if sum(filters) != 1:
            return {"success": False, "error": "Specify exactly one of model_id, batch_id, or date."}

        # Select predictions by filter
        all_predictions = list(self.predictions.values())
        if model_id is not None:
            if model_id not in self.models:
                return {"success": False, "error": f"Model ID {model_id} does not exist."}
            filtered_preds = [p for p in all_predictions if p["model_id"] == model_id]
            scope = "model"
            scope_value = model_id
        elif batch_id is not None:
            if batch_id not in self.prediction_batches:
                return {"success": False, "error": f"Batch ID {batch_id} does not exist."}
            filtered_preds = [p for p in all_predictions if p.get("batch_id") == batch_id]
            scope = "batch"
            scope_value = batch_id
        elif date is not None:
            # Filter predictions whose timestamp starts with the given date
            try:
                # Just validate date format
                datetime.strptime(date, "%Y-%m-%d")
            except Exception:
                return {"success": False, "error": f"Date '{date}' is not in 'YYYY-MM-DD' format."}
            filtered_preds = [p for p in all_predictions if p["timestamp"].startswith(date)]
            scope = "date"
            scope_value = date

        filtered_preds = [p for p in filtered_preds if p.get("actual_value") is not None]

        if not filtered_preds:
            return {"success": False, "error": "No predictions with actual values found for the given filter."}

        # Determine metric types present in performance_metrics for this scope
        metric_types = set()
        for metric in self.performance_metrics.values():
            if (
                metric["aggregation_scope"] == scope
                and metric["scope_value"] == scope_value
            ):
                metric_types.add(metric["metric_type"])
        if not metric_types:
            # Default to "accuracy" if none present (minimum required); extend as needed
            metric_types = {"accuracy"}

        metrics_result = {}
        for metric_type in metric_types:
            metric_key = str(metric_type).lower()
            if metric_key == "accuracy":
                # Treat accuracy as a binary classification metric using a 0.5 decision threshold.
                total = len(filtered_preds)
                correct = 0
                for p in filtered_preds:
                    pv = p["predicted_value"]
                    av = p["actual_value"]
                    predicted_label = 1 if pv >= 0.5 else 0
                    actual_label = 1 if av >= 0.5 else 0
                    correct += 1 if predicted_label == actual_label else 0
                accuracy = correct / total if total > 0 else 0.0
                metrics_result[metric_type] = accuracy
            elif metric_key == "mae":
                total = len(filtered_preds)
                mae = sum(abs(p["predicted_value"] - p["actual_value"]) for p in filtered_preds) / total if total > 0 else 0.0
                metrics_result[metric_type] = mae
            elif metric_key == "mse":
                total = len(filtered_preds)
                mse = sum((p["predicted_value"] - p["actual_value"]) ** 2 for p in filtered_preds) / total if total > 0 else 0.0
                metrics_result[metric_type] = mse
            else:
                # Unsupported metric type
                continue

        if not metrics_result:
            return {"success": False, "error": "No supported metric types found for the given filter."}

        # Remove old metrics for this scope
        to_remove = [
            mid for mid, m in self.performance_metrics.items()
            if m["aggregation_scope"] == scope and m["scope_value"] == scope_value
        ]
        for mid in to_remove:
            del self.performance_metrics[mid]

        # Add/update metrics
        computed_at = datetime.now(timezone.utc).isoformat()
        new_metrics = []
        for metric_type, value in metrics_result.items():
            metric_id = f"{metric_type}-{scope}-{scope_value}-{computed_at}"
            self.performance_metrics[metric_id] = {
                "metric_id": metric_id,
                "model_id": (
                    model_id
                    if model_id is not None else (
                        self.prediction_batches[batch_id]["model_id"] if batch_id is not None else filtered_preds[0]["model_id"]
                    )
                ),
                "aggregation_scope": scope,
                "scope_value": scope_value,
                "metric_type": metric_type,
                "metric_value": value,
                "computed_at": computed_at,
            }
            new_metrics.append((metric_type, value))

        return {
            "success": True,
            "message": (
                f"Performance metrics recalculated for {scope}='{scope_value}': " +
                ", ".join([f"{mt}={val:.4f}" for mt, val in new_metrics])
            )
        }

    def delete_prediction(self, prediction_id: str) -> dict:
        """
        Remove a prediction record from the monitoring system by its prediction_id.

        Args:
            prediction_id (str): The unique identifier of the prediction to remove.

        Returns:
            dict:
                On success:
                    {
                      "success": True,
                      "message": "Prediction <prediction_id> deleted successfully. Performance metrics may need to be recomputed."
                    }
                On failure:
                    {
                      "success": False,
                      "error": "Prediction with id <prediction_id> does not exist."
                    }

        Constraints:
            - Prediction must exist in the system.
            - Deletion may cause performance metrics to become inconsistent (does NOT recompute metrics).
        """
        if prediction_id not in self.predictions:
            return {
                "success": False,
                "error": f"Prediction with id {prediction_id} does not exist."
            }

        del self.predictions[prediction_id]
        return {
            "success": True,
            "message": f"Prediction {prediction_id} deleted successfully. Performance metrics may need to be recomputed."
        }

    def delete_prediction_batch(self, batch_id: str) -> dict:
        """
        Remove a prediction batch and all associated predictions. This operation deletes
        the PredictionBatch entry for the given batch_id and also deletes all Prediction
        entries whose 'batch_id' matches the given batch_id.

        Args:
            batch_id (str): The ID of the prediction batch to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Prediction batch '<batch_id>' and N associated predictions deleted."
            }
            or
            {
                "success": False,
                "error": "Prediction batch not found"
            }

        Constraints:
            - If the batch_id does not exist, returns an error.
            - All predictions with prediction['batch_id'] == batch_id are deleted (cascade).
            - Performance metric consistency is not handled directly in this operation.
        """
        # Check if the batch exists
        if batch_id not in self.prediction_batches:
            return { "success": False, "error": "Prediction batch not found" }

        # Find associated predictions
        associated_prediction_ids = [
            pred_id for pred_id, pred in self.predictions.items()
            if pred.get("batch_id") == batch_id
        ]
        # Delete all associated predictions
        for pred_id in associated_prediction_ids:
            del self.predictions[pred_id]

        # Delete the prediction batch
        del self.prediction_batches[batch_id]

        return {
            "success": True,
            "message": f"Prediction batch '{batch_id}' and {len(associated_prediction_ids)} associated predictions deleted."
        }

    def delete_model(self, model_id: str, cascade: bool = False) -> dict:
        """
        Remove a model from the registry.

        Args:
            model_id (str): Unique identifier of the model to delete.
            cascade (bool): If True, also deletes all related predictions, batches, and metrics.
                            If False, fails if model has related data.

        Returns:
            dict:
                - On success:
                    {"success": True, "message": "Model and associated data deleted."}
                    or {"success": True, "message": "Model deleted."}
                - On failure:
                    {"success": False, "error": "Model does not exist."}
                    {"success": False, "error": "Model has associated predictions/batches/metrics. Use cascade=True."}

        Constraints:
            - Model must exist.
            - Cascading deletes required if model has related data.
        """
        if model_id not in self.models:
            return {"success": False, "error": "Model does not exist."}

        # Find associated predictions, batches, metrics
        pred_ids = [pid for pid, pinfo in self.predictions.items() if pinfo["model_id"] == model_id]
        batch_ids = [bid for bid, binfo in self.prediction_batches.items() if binfo["model_id"] == model_id]
        metric_ids = [mid for mid, minfo in self.performance_metrics.items() if minfo["model_id"] == model_id]

        associated = bool(pred_ids or batch_ids or metric_ids)

        if associated and not cascade:
            parts = []
            if pred_ids: parts.append("predictions")
            if batch_ids: parts.append("batches")
            if metric_ids: parts.append("metrics")
            return {
                "success": False,
                "error": f"Model has associated {'/'.join(parts)}. Use cascade=True to delete all."
            }

        # Perform deletes
        del self.models[model_id]

        if cascade:
            for pid in pred_ids:
                del self.predictions[pid]
            for bid in batch_ids:
                del self.prediction_batches[bid]
            for mid in metric_ids:
                del self.performance_metrics[mid]
            return {
                "success": True,
                "message": "Model and all associated data deleted."
            }
        else:
            return {
                "success": True,
                "message": "Model deleted."
            }

    def delete_performance_metric(self, metric_id: str) -> dict:
        """
        Remove a performance metric entry by its metric_id.

        Args:
            metric_id (str): The unique identifier for the Performance Metric to delete.

        Returns:
            dict: {
                "success": True,
                "message": "Performance metric deleted."
            }
            or
            {
                "success": False,
                "error": "<reason>"
            }

        Constraints:
            - metric_id must exist in the performance metrics store.
            - No recomputation or cascading is triggered by this method.
        """
        if metric_id not in self.performance_metrics:
            return { "success": False, "error": "Performance metric not found." }

        del self.performance_metrics[metric_id]
        return { "success": True, "message": "Performance metric deleted." }

    def correct_batch_assignment(self, prediction_id: str, new_batch_id: 'Optional[str]') -> dict:
        """
        Update the batch_id assignment for a prediction in case of labeling errors.

        Args:
            prediction_id (str): The ID of the prediction to update.
            new_batch_id (Optional[str]): The batch_id to assign. If None, removes the batch assignment.

        Returns:
            dict: 
                { "success": True, "message": "Batch assignment updated for prediction <prediction_id>" }
                OR
                { "success": False, "error": <error_message> }
    
        Constraints:
            - The prediction must exist.
            - If new_batch_id is not None, it must reference an existing batch.
            - It is allowed to set the batch assignment to None.
        """
        # Check if prediction exists
        if prediction_id not in self.predictions:
            return { "success": False, "error": "Prediction not found" }
    
        # If setting to a non-None batch, confirm batch exists
        if new_batch_id is not None and new_batch_id not in self.prediction_batches:
            return { "success": False, "error": "Batch not found" }
    
        # Update the batch assignment
        self.predictions[prediction_id]["batch_id"] = new_batch_id

        return {
            "success": True,
            "message": f"Batch assignment updated for prediction {prediction_id}"
        }

    def update_model_deployment_status(self, model_id: str, new_status: str) -> dict:
        """
        Change the deployment status of a model.

        Args:
            model_id (str): The ID of the model to update.
            new_status (str): The new deployment status (e.g., 'active', 'retired').

        Returns:
            dict: {
                "success": True,
                "message": "Deployment status updated for model <model_id>."
            }
            or
            {
                "success": False,
                "error": "Model not found."
            }

        Constraints:
            - model_id must reference a valid model in the system.
            - Status value is not constrained (unless explicitly enforced elsewhere).
        """
        if model_id not in self.models:
            return { "success": False, "error": "Model not found." }

        self.models[model_id]["deployment_status"] = new_status

        return {
            "success": True,
            "message": f"Deployment status updated for model {model_id}."
        }


class PredictionMonitoringSystem(BaseEnv):
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

    def list_models(self, **kwargs):
        return self._call_inner_tool('list_models', kwargs)

    def get_model_by_id(self, **kwargs):
        return self._call_inner_tool('get_model_by_id', kwargs)

    def list_predictions_by_date(self, **kwargs):
        return self._call_inner_tool('list_predictions_by_date', kwargs)

    def list_predictions_by_model(self, **kwargs):
        return self._call_inner_tool('list_predictions_by_model', kwargs)

    def list_predictions_by_batch(self, **kwargs):
        return self._call_inner_tool('list_predictions_by_batch', kwargs)

    def get_prediction_by_id(self, **kwargs):
        return self._call_inner_tool('get_prediction_by_id', kwargs)

    def list_batches_by_model(self, **kwargs):
        return self._call_inner_tool('list_batches_by_model', kwargs)

    def list_batches_by_date(self, **kwargs):
        return self._call_inner_tool('list_batches_by_date', kwargs)

    def get_batch_by_id(self, **kwargs):
        return self._call_inner_tool('get_batch_by_id', kwargs)

    def list_performance_metrics_by_date(self, **kwargs):
        return self._call_inner_tool('list_performance_metrics_by_date', kwargs)

    def list_performance_metrics_by_batch(self, **kwargs):
        return self._call_inner_tool('list_performance_metrics_by_batch', kwargs)

    def list_performance_metrics_by_model(self, **kwargs):
        return self._call_inner_tool('list_performance_metrics_by_model', kwargs)

    def get_performance_metric_by_id(self, **kwargs):
        return self._call_inner_tool('get_performance_metric_by_id', kwargs)

    def get_predictions_with_missing_actuals(self, **kwargs):
        return self._call_inner_tool('get_predictions_with_missing_actuals', kwargs)

    def get_latest_metric_computation_time(self, **kwargs):
        return self._call_inner_tool('get_latest_metric_computation_time', kwargs)

    def add_or_update_prediction(self, **kwargs):
        return self._call_inner_tool('add_or_update_prediction', kwargs)

    def add_prediction_batch(self, **kwargs):
        return self._call_inner_tool('add_prediction_batch', kwargs)

    def add_model(self, **kwargs):
        return self._call_inner_tool('add_model', kwargs)

    def edit_actual_value_for_prediction(self, **kwargs):
        return self._call_inner_tool('edit_actual_value_for_prediction', kwargs)

    def recalculate_performance_metrics(self, **kwargs):
        return self._call_inner_tool('recalculate_performance_metrics', kwargs)

    def delete_prediction(self, **kwargs):
        return self._call_inner_tool('delete_prediction', kwargs)

    def delete_prediction_batch(self, **kwargs):
        return self._call_inner_tool('delete_prediction_batch', kwargs)

    def delete_model(self, **kwargs):
        return self._call_inner_tool('delete_model', kwargs)

    def delete_performance_metric(self, **kwargs):
        return self._call_inner_tool('delete_performance_metric', kwargs)

    def correct_batch_assignment(self, **kwargs):
        return self._call_inner_tool('correct_batch_assignment', kwargs)

    def update_model_deployment_status(self, **kwargs):
        return self._call_inner_tool('update_model_deployment_status', kwargs)
