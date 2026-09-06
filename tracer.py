import functools
import time
import requests
import uuid
import copy
from typing import Optional, Type
from pydantic import BaseModel
from self_healing import validate_and_heal

COLLECTOR_URL = "http://127.0.0.1:8000/api/v1/trace"

CURRENT_SESSION_ID = None
STEP_COUNTER = 0

def start_trace_session() -> str:
    global CURRENT_SESSION_ID, STEP_COUNTER
    CURRENT_SESSION_ID = f"sess_{uuid.uuid4().hex[:8]}"
    STEP_COUNTER = 0
    return CURRENT_SESSION_ID

def trace_step(step_name: str, step_type: str = "tool", schema: Optional[Type[BaseModel]] = None):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            global CURRENT_SESSION_ID, STEP_COUNTER
            start_time = time.time()
            was_healed = False
            heal_notes = "None"
            original_raw_input = None
            
            if CURRENT_SESSION_ID is None:
                start_trace_session()

            STEP_COUNTER += 1
            current_step = STEP_COUNTER
            
            if schema is not None:
                combined_payload = {**kwargs}
                if args and isinstance(args[0], dict):
                    combined_payload.update(args[0])
                
                # Capture unhealed raw input for the diff inspector
                original_raw_input = copy.deepcopy(combined_payload)
                
                try:
                    healed_instance, was_healed, heal_notes = validate_and_heal(schema, combined_payload)
                    kwargs = healed_instance.model_dump()
                    args = ()
                except Exception as val_err:
                    trace_data = {
                        "session_id": CURRENT_SESSION_ID,
                        "step_number": current_step,
                        "step_name": step_name,
                        "step_type": step_type,
                        "inputs": combined_payload,
                        "original_inputs": original_raw_input,
                        "output": str(val_err),
                        "status": "schema_validation_failed",
                        "latency_ms": round((time.time() - start_time) * 1000, 2),
                        "was_healed": False,
                        "heal_notes": str(val_err)
                    }
                    try:
                        requests.post(COLLECTOR_URL, json=trace_data, timeout=0.5)
                    except Exception:
                        pass
                    raise val_err

            trace_data = {
                "session_id": CURRENT_SESSION_ID,
                "step_number": current_step,
                "step_name": step_name,
                "step_type": step_type,
                "inputs": {"args": args, "kwargs": kwargs},
                "original_inputs": original_raw_input,
                "status": "running",
                "was_healed": was_healed,
                "heal_notes": heal_notes
            }
            
            try:
                result = func(*args, **kwargs)
                trace_data["output"] = result
                trace_data["status"] = "success"
                return result
            except Exception as e:
                trace_data["output"] = str(e)
                trace_data["status"] = "execution_failed"
                raise e
            finally:
                trace_data["latency_ms"] = round((time.time() - start_time) * 1000, 2)
                try:
                    requests.post(COLLECTOR_URL, json=trace_data, timeout=0.5)
                except Exception:
                    pass
        return wrapper
    return decorator