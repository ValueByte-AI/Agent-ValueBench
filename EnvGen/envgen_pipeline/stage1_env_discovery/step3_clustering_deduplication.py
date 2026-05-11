"""Step 3: cluster and deduplicate environment themes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from typing import Any, Dict, List

import numpy as np
from sklearn.cluster import KMeans

from utils.call_llm import openai_batch_embedding_inference
from utils.process_file import read_file, save_file
from utils.resumable import build_resume_progress, load_resume_state, save_resume_state


def add_embeddings_to_samples(samples, field, model, timeout):
    """Generate embeddings for a batch of samples and add them to each sample."""
    # Extract all input texts
    inputs = [sample[field] for sample in samples]

    # Generate embeddings via API
    embeddings = openai_batch_embedding_inference(
        model=model,
        texts=inputs,
        raise_on_failure=True,
    )
    for sample, embedding in zip(samples, embeddings):
        sample[field + "_embedding"] = embedding
    return samples



def _is_complete(item, field):
    value = item.get(field + "_embedding") if isinstance(item, dict) else None
    return isinstance(value, list) and len(value) > 0


def batch_add_embeddings(
    data,
    field,
    model,
    batch_size,
    timeout=60,
    save_file_path=None,
    progress_desc=None,
    progress_position=None,
):
    """Process data in batches and add embeddings to each batch."""
    if save_file_path:
        ordered_keys, result_map, working_items = load_resume_state(
            data,
            save_file_path,
            key_fn=lambda item: str(item.get("task", "")).strip(),
        )
    else:
        ordered_keys = [str(item.get("task", "")).strip() for item in data]
        result_map = {}
        working_items = list(data)

    # Process in batches
    pending = [
        item
        for item in working_items
        if not (
            str(item.get("task", "")).strip() in result_map
            and _is_complete(result_map[str(item.get("task", "")).strip()], field)
        )
    ]
    progress = build_resume_progress(
        ordered_keys=ordered_keys,
        result_map=result_map,
        is_complete_fn=lambda item: _is_complete(item, field),
        step_label="EnvDiscovery-ThemeEmbedding",
        progress_desc=progress_desc,
        progress_position=progress_position,
    )
    try:
        for i in range(0, len(pending), batch_size):
            batch = pending[i:i + batch_size]
            batch_with_emb = add_embeddings_to_samples(samples=batch, field=field, model=model, timeout=timeout)
            for sample in batch_with_emb:
                result_map[str(sample.get("task", "")).strip()] = sample
            progress.update(len(batch_with_emb))
            if save_file_path:
                save_resume_state(save_file_path, ordered_keys=ordered_keys, result_map=result_map)
    except KeyboardInterrupt:
        if save_file_path:
            save_resume_state(save_file_path, ordered_keys=ordered_keys, result_map=result_map)
        raise
    finally:
        progress.close()

    if save_file_path:
        save_resume_state(save_file_path, ordered_keys=ordered_keys, result_map=result_map)
        return [result_map[key] for key in ordered_keys if key in result_map]
    return [result_map.get(key, item) for key, item in zip(ordered_keys, working_items)]

def deduplicate_environments(env_list):
    """Deduplicate environments by environment_summary, keeping item with highest Modelability and Usefulness scores."""
    # key: environment_summary, value: best record
    best_env_map = {}

    for env in env_list:
        summary = env.get("environment_summary", "").strip()
        model_score = env.get("metrics", {}).get("modelability", 0)
        useful_score = env.get("metrics", {}).get("usefulness", 0)

        if summary not in best_env_map:
            best_env_map[summary] = env
        else:
            current_best = best_env_map[summary]
            best_model_score = current_best.get("metrics", {}).get("modelability", 0)
            best_useful_score = current_best.get("metrics", {}).get("usefulness", 0)

            # Prioritize Modelability
            if model_score > best_model_score:
                best_env_map[summary] = env
            elif model_score == best_model_score:
                # If Modelability is equal, compare Usefulness
                if useful_score > best_useful_score:
                    best_env_map[summary] = env

    return list(best_env_map.values())


def filter_environments(env_list, modelability_threshold=0, usefulness_threshold=0):
    """Filter environments by Modelability and Usefulness score thresholds."""
    filtered = []
    for env in env_list:
        model_score = env.get("metrics", {}).get("modelability", 0)
        useful_score = env.get("metrics", {}).get("usefulness", 0)

        if model_score >= modelability_threshold and useful_score >= usefulness_threshold:
            filtered.append(env)

    return filtered


def cluster_deduplicate(items: List[Dict[str, Any]], embedding_field, n_clusters: int) -> List[Dict[str, Any]]:
    """Cluster items by embeddings using KMeans and return the closest item to each cluster center."""
    if not items:
        return []

    # Extract all embeddings
    embeddings = np.array([np.array(item[embedding_field]) for item in items])

    # Perform clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init="auto")
    labels = kmeans.fit_predict(embeddings)

    # Find closest item to center for each cluster
    closest_items = []
    for cluster_id in range(n_clusters):
        cluster_indices = np.where(labels == cluster_id)[0]
        if len(cluster_indices) == 0:
            continue
        cluster_embeddings = embeddings[cluster_indices]
        center = kmeans.cluster_centers_[cluster_id]

        # Calculate distances and find minimum
        distances = np.linalg.norm(cluster_embeddings - center, axis=1)
        closest_index_in_cluster = cluster_indices[np.argmin(distances)]
        closest_items.append(items[closest_index_in_cluster])

    return closest_items


if __name__ == "__main__":
    # Configuration
    modelability_threshold = 7
    usefulness_threshold = 7
    n_clusters = 2
    # Read data
    data = read_file("stage1_env_discovery/temp_result/step3_clustering_deduplication.embeddings.json")
    print(len(data))
    # Deduplicate by environment_summary
    new_data = deduplicate_environments(data)
    print(len(new_data))
    # Filter by metrics
    new_data = filter_environments(new_data, modelability_threshold=modelability_threshold, usefulness_threshold=usefulness_threshold)
    new_data = cluster_deduplicate(new_data, embedding_field="env_summary_and_introduction_embedding", n_clusters=n_clusters)
    print(len(new_data))
    save_file("stage1_env_discovery/temp_result/step3_clustering_deduplication.selected.json", new_data)
    # Save final result
    final_data = []
    for item in new_data:
        final_data.append({
            "task": item["task"],
            "environment_summary": item["environment_summary"],
            "environment_introduction": item["environment_introduction"],
        })
    print("Final result saved to: stage1_env_discovery/final_result/discovered_environment_themes.json")
    save_file("stage1_env_discovery/final_result/discovered_environment_themes.json", final_data)
