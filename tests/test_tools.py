import os
import tempfile
import shutil
import pytest
from tools import DevOpsTools

@pytest.fixture
def temp_repo():
    """Fixture to create a temporary dummy git repository for testing tools safely."""
    tmp_dir = tempfile.mkdtemp(prefix="test_repo_")
    
    # Create some dummy files and structure
    os.makedirs(os.path.join(tmp_dir, ".git")) # Mock git dir
    with open(os.path.join(tmp_dir, "README.md"), "w") as f:
        f.write("# Test Project\n")
        
    os.makedirs(os.path.join(tmp_dir, "src"))
    with open(os.path.join(tmp_dir, "src", "main.py"), "w") as f:
        f.write("API_KEY = 'secret_placeholder'\nprint('Hello World')\n")
        
    tools = DevOpsTools(tmp_dir)
    yield tools, tmp_dir
    
    # Cleanup
    shutil.rmtree(tmp_dir, ignore_errors=True)

def test_list_files(temp_repo):
    tools, _ = temp_repo
    files = tools.list_files()
    assert "README.md" in files
    assert os.path.join("src", "main.py") in files
    # Ensure .git contents are excluded
    for f in files:
        assert ".git" not in f

def test_read_file_success(temp_repo):
    tools, _ = temp_repo
    content = tools.read_file("README.md")
    assert "# Test Project" in content

def test_read_file_not_found(temp_repo):
    tools, _ = temp_repo
    result = tools.read_file("nonexistent.txt")
    assert "Error" in result

def test_read_file_path_traversal_protection(temp_repo):
    tools, _ = temp_repo
    # Attempt path traversal attack outside repo boundary
    result = tools.read_file("../../../etc/passwd")
    assert "Error" in result

def test_search_code(temp_repo):
    tools, _ = temp_repo
    result = tools.search_code("API_KEY")
    assert "main.py" in result or "API_KEY" in result