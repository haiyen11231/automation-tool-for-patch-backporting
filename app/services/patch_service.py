import git
import subprocess
import os
from services.llm_service import backport_patch

def fetch_patch(repo_url: str, commit_hash: str):
    """
    Fetches the patch for a specific commit in the given repository.
    Returns a dictionary where keys are file paths and values are patch diffs.
    """
    repo_path = "/tmp/repo"

    if os.path.exists(repo_path):
        repo = git.Repo(repo_path)
        repo.remotes.origin.pull()
    else:
        repo = git.Repo.clone_from(repo_url, repo_path)

    # Get diff only for Python files
    diff_output = repo.git.diff(commit_hash + "^!", "--", "*.py")

    # Split the diff into per-file sections
    patches = {}
    current_file = None
    current_patch = []

    for line in diff_output.split("\n"):
        if line.startswith("diff --git"):
            if current_file and current_patch:
                patches[current_file] = "\n".join(current_patch)
            current_file = line.split(" ")[-1]  # Extract filename
            current_patch = []
        if current_file:
            current_patch.append(line)

    if current_file and current_patch:
        patches[current_file] = "\n".join(current_patch)

    return patches

def apply_patches(original_files, adapted_patches):
    """
    Applies multiple patches atomically. If any step fails, no changes are kept.
    """
    backup_files = {}  # Store original content for rollback

    try:
        # Backup original files
        for file, new_patch in adapted_patches.items():
            if os.path.exists(file):
                with open(file, "r") as f:
                    backup_files[file] = f.read()  # Save original content
            
            # Apply the patch
            with open(file, "w") as f:
                f.write(new_patch)

        return True  # Success

    except Exception as e:
        # If any failure, rollback changes
        for file, original_content in backup_files.items():
            with open(file, "w") as f:
                f.write(original_content)

        return False  # Failure

def test_repo(repo_path: str):
    """
    Runs tests in the repo.
    """
    result = subprocess.run(["pytest", repo_path], capture_output=True, text=True)
    return result.stdout, result.returncode  # Exit code 0 means tests passed
