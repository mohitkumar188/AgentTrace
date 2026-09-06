import json
import re
from typing import Type, Any, Tuple
from pydantic import BaseModel, ValidationError
from groq import Groq

groq_client = Groq(api_key="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")

def extract_json(raw_text: str) -> dict:
    """Extracts JSON even if model wraps it in markdown backticks."""
    cleaned = raw_text.strip()
    match = re.search(r"\{.*\}", cleaned, re.DOTALL)
    if match:
        return json.loads(match.group(0))
    return json.loads(cleaned)

def repair_payload_with_llm(invalid_payload: dict, schema_json: str, error_msg: str) -> dict:
    """
    Uses openai/gpt-oss-120b without brittle json_object constraints 
    to reliably repair arguments.
    """
    prompt = f"""You are an API schema repair engine. Return ONLY valid JSON. No markdown ticks, no commentary.

Target Schema:
{schema_json}

Invalid Input Sent:
{json.dumps(invalid_payload)}

Validation Error:
{error_msg}

Fixed JSON payload matching the target schema:"""

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-120b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=300
    )
    
    raw_content = response.choices[0].message.content
    return extract_json(raw_content)

def validate_and_heal(schema_class: Type[BaseModel], incoming_data: dict) -> Tuple[BaseModel, bool, str]:
    """Validates payload against schema with self-healing fallback."""
    try:
        valid_obj = schema_class(**incoming_data)
        return valid_obj, False, "Payload strictly valid on first try."
    except ValidationError as e:
        error_details = str(e)
        schema_schema = json.dumps(schema_class.model_json_schema())
        
        try:
            repaired_dict = repair_payload_with_llm(incoming_data, schema_schema, error_details)
            healed_obj = schema_class(**repaired_dict)
            return healed_obj, True, f"Auto-repaired from validation failure: {error_details}"
        except Exception as heal_err:
            raise ValueError(f"Self-healing failed to satisfy schema. Error: {str(heal_err)}")