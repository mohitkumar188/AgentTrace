# test_agent.py
from tracer import trace_step
import time

@trace_step(step_name="fetch_user_balance", step_type="tool")
def fetch_user_balance(user_id: str):
    time.sleep(0.2)  # Simulate network latency
    return {"user_id": user_id, "balance": 1500, "currency": "INR"}

@trace_step(step_name="execute_transfer", step_type="tool")
def execute_transfer(user_id: str, amount: int):
    time.sleep(0.1)
    if amount > 1000:
        raise ValueError("Transaction limit exceeded for account")
    return {"status": "transferred", "amount": amount}

if __name__ == "__main__":
    fetch_user_balance("usr_9981")
    try:
        execute_transfer("usr_9981", 2500)
    except Exception:
        print("Agent caught error, trace sent to backend.")