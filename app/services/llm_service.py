import os
from dotenv import load_dotenv
from transformers import AutoModelForCausalLM, AutoTokenizer, pipeline

load_dotenv()
HUGGINGFACE_API_TOKEN = os.getenv("HF_API_TOKEN")

llm = pipeline(
    "text-generation",
    model="bigcode/starcoder",
    token=HUGGINGFACE_API_TOKEN
)

def backport_patch(patch: str, target_version: str):
    """
    Uses Hugging Face LLM to modify a patch for compatibility with an older version.

    :param patch: The original patch.
    :param target_version: The version to backport to.
    :return: A dictionary with modified patch and explanation.
    """
    prompt = f"""
    The following is a patch meant for a newer version. Modify it to be compatible with version {target_version}.
    
    Ensure that:
    - Syntax is compatible with version {target_version}.
    - Dependencies that do not exist in {target_version} are replaced with alternatives.
    - The logic remains unchanged.
    - Explain the modifications.

    Patch:
    {patch}
    """

    response = llm(prompt, max_length=800)
    generated_text = response[0]['generated_text']

    # Extract the explanation and modified code
    split_text = generated_text.split("### Changes Made:")
    modified_patch = split_text[0].strip()
    explanation = split_text[1].strip() if len(split_text) > 1 else "No explanation provided."

    return {"modified_patch": modified_patch, "explanation": explanation}