from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.llm_service import backport_patch
from app.services.patch_service import fetch_patch, apply_patches, test_repo

app = FastAPI()

class BackportRequest(BaseModel):
    repo_url: str
    commit_hash: str
    target_version: str

@app.post("/backport/")
async def backport(request: BackportRequest):
    """
    Fetches a patch, backports it using LLM, applies all changes, and runs tests.
    """
    try:
        repo_path = "/tmp/repo"

        # 1️⃣ First, test if the original repo is stable
        original_test_output, original_test_status = test_repo(repo_path)
        if original_test_status != 0:
            return {
                "status": "error",
                "message": "Original codebase has failing tests, cannot proceed.",
                "test_output": original_test_output
            }

        # 2️⃣ Fetch all modified files + their patches
        patch_dict = fetch_patch(request.repo_url, request.commit_hash)
        if not patch_dict:
            raise HTTPException(status_code=400, detail="No Python files found in the patch.")

        # 3️⃣ Use LLM to backport each patch
        adapted_patches = {}
        explanations = {}

        for file_path, patch in patch_dict.items():
            llm_result = backport_patch(patch, request.target_version)
            adapted_patches[file_path] = llm_result["modified_patch"]
            explanations[file_path] = llm_result["explanation"]

        # 4️⃣ Apply all patches atomically
        if not apply_patches(patch_dict.keys(), adapted_patches):
            return {
                "status": "error",
                "message": "Failed to apply patches. No changes were made."
            }

        # 5️⃣ Run tests to validate the changes
        test_output, test_status = test_repo(repo_path)

        # 6️⃣ If tests fail, rollback all changes
        if test_status != 0:
            apply_patches(patch_dict.keys(), patch_dict)  # Restore originals
            return {
                "status": "error",
                "message": "Patched version failed tests. Reverted to original.",
                "test_output": test_output,
                "llm_explanations": explanations
            }

        return {
            "status": "success",
            "message": "Patch successfully applied and passed all tests!",
            "llm_explanations": explanations,
            "test_output": test_output
        }

    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
