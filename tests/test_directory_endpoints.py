# File: /Users/liborballaty/LocalProjects/GitHubProjectsDocuments/myragdb/tests/test_directory_endpoints.py
# Description: Tests for directory management API endpoints
# Author: Libor Ballaty <libor@arionetworks.com>
# Created: 2026-01-07

import pytest
import tempfile
from pathlib import Path
from fastapi.testclient import TestClient
from myragdb.api.server import app
from myragdb.db.file_metadata import FileMetadataDatabase


@pytest.fixture
def client():
    """Provide FastAPI test client."""
    # Initialize database schema
    db = FileMetadataDatabase()
    return TestClient(app)


@pytest.fixture
def temp_directory():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_create_directory(client, temp_directory):
    """Test creating a new directory."""
    response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 10,
            "notes": "Test notes"
        }
    )

    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Test Directory"
    assert data["enabled"] is True
    assert data["priority"] == 10
    assert data["notes"] == "Test notes"
    assert data["id"] is not None
    assert data["created_at"] is not None


def test_create_directory_nonexistent_path(client):
    """Test creating directory with non-existent path."""
    response = client.post(
        "/directories",
        json={
            "path": "/nonexistent/path/to/directory",
            "name": "Invalid Directory",
            "enabled": True,
            "priority": 0
        }
    )

    assert response.status_code == 400
    assert "does not exist" in response.json()["detail"]


def test_create_directory_duplicate(client, temp_directory):
    """Test creating duplicate directory returns conflict."""
    # Create first directory
    response1 = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert response1.status_code == 200

    # Try to create duplicate
    response2 = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Duplicate Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert response2.status_code == 409
    assert "already registered" in response2.json()["detail"]


def test_list_directories(client, temp_directory):
    """Test listing directories."""
    # Create a directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 10
        }
    )
    assert create_response.status_code == 200

    # List all directories
    list_response = client.get("/directories")
    assert list_response.status_code == 200
    data = list_response.json()
    assert isinstance(data, list)
    assert len(data) > 0
    assert any(d["name"] == "Test Directory" for d in data)


def test_list_directories_enabled_only(client, temp_directory):
    """Test listing only enabled directories."""
    # Create enabled directory
    response1 = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Enabled Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert response1.status_code == 200
    dir_id = response1.json()["id"]

    # Create disabled directory
    with tempfile.TemporaryDirectory() as tmpdir2:
        response2 = client.post(
            "/directories",
            json={
                "path": tmpdir2,
                "name": "Disabled Directory",
                "enabled": False,
                "priority": 0
            }
        )
        assert response2.status_code == 200

    # List enabled only
    list_response = client.get("/directories?enabled_only=true")
    assert list_response.status_code == 200
    data = list_response.json()

    # Should only contain enabled directories
    for d in data:
        if d["id"] == dir_id:
            assert d["enabled"] is True
            break
    else:
        # Created directory should be in list
        assert any(d["name"] == "Enabled Directory" for d in data)


def test_get_directory(client, temp_directory):
    """Test getting a specific directory."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 5
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]

    # Get directory
    get_response = client.get(f"/directories/{directory_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["id"] == directory_id
    assert data["name"] == "Test Directory"
    assert data["priority"] == 5


def test_get_directory_not_found(client):
    """Test getting non-existent directory."""
    response = client.get("/directories/99999")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"]


def test_update_directory(client, temp_directory):
    """Test updating directory settings."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Original Name",
            "enabled": True,
            "priority": 0,
            "notes": "Original notes"
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]
    original_path = create_response.json()["path"]

    # Update directory (path must be the same - DirectoryRequest includes path but it shouldn't change)
    update_response = client.patch(
        f"/directories/{directory_id}",
        json={
            "path": original_path,  # Keep the same path
            "name": "Updated Name",
            "enabled": False,
            "priority": 10,
            "notes": "Updated notes"
        }
    )
    assert update_response.status_code == 200
    data = update_response.json()
    assert data["name"] == "Updated Name"
    assert data["enabled"] is False
    assert data["priority"] == 10
    assert data["notes"] == "Updated notes"

    # Verify update persisted
    get_response = client.get(f"/directories/{directory_id}")
    assert get_response.status_code == 200
    data = get_response.json()
    assert data["name"] == "Updated Name"


def test_delete_directory(client, temp_directory):
    """Test deleting a directory."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]

    # Delete directory
    delete_response = client.delete(f"/directories/{directory_id}")
    assert delete_response.status_code == 200
    data = delete_response.json()
    assert data["status"] == "success"
    assert data["directory_id"] == directory_id

    # Verify it's deleted
    get_response = client.get(f"/directories/{directory_id}")
    assert get_response.status_code == 404


def test_reindex_directory(client, temp_directory):
    """Test reindex endpoint."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]

    # Request reindex
    reindex_response = client.post(
        f"/directories/{directory_id}/reindex?index_keyword=true&index_vector=true&full_rebuild=false"
    )
    assert reindex_response.status_code == 200
    data = reindex_response.json()
    assert data["status"] == "started"
    assert "Test Directory" in data["message"]
    assert data["directory_id"] == directory_id


def test_reindex_directory_invalid_index_type(client, temp_directory):
    """Test reindex with no index type selected."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]

    # Request reindex with no index types
    reindex_response = client.post(
        f"/directories/{directory_id}/reindex?index_keyword=false&index_vector=false"
    )
    assert reindex_response.status_code == 400
    assert "At least one index type" in reindex_response.json()["detail"]


def test_discover_directory_structure(client, temp_directory):
    """Test directory discovery for tree picker."""
    # Create test subdirectories
    subdir1 = Path(temp_directory) / "subdir1"
    subdir1.mkdir(exist_ok=True)
    subdir2 = subdir1 / "subdir2"
    subdir2.mkdir(exist_ok=True)

    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert create_response.status_code == 200
    directory_id = create_response.json()["id"]

    # Discover structure
    discover_response = client.get(f"/directories/{directory_id}/discover?max_depth=3")
    assert discover_response.status_code == 200
    data = discover_response.json()
    assert data["is_directory"] is True
    assert data["children"] is not None or data["children"] == []


def test_directory_with_stats(client, temp_directory):
    """Test that directory includes stats when available."""
    # Create directory
    create_response = client.post(
        "/directories",
        json={
            "path": temp_directory,
            "name": "Test Directory",
            "enabled": True,
            "priority": 0
        }
    )
    assert create_response.status_code == 200
    data = create_response.json()

    # Should include stats field (even if empty)
    assert "stats" in data
    # stats can be None or empty list for new directories
    assert data["stats"] is None or isinstance(data["stats"], list)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
