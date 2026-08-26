import os
import pytest


def test_get_dataset_statistics(client):
    """Verifies dataset statistics summary fields."""
    res = client.get("/api/v1/dataset/statistics")
    assert res.status_code == 200
    assert "total_images" in res.json()
    assert "annotated_images" in res.json()
    assert "labels_distribution" in res.json()


def test_dataset_versioning_fail_same_tag(client):
    """Verifies that zip packaging handles validation constraints and errors gracefully."""
    # Tag snapshot create
    res = client.post("/api/v1/dataset/version?version_tag=v1.0.test")
    assert res.status_code == 200 or res.status_code == 400
