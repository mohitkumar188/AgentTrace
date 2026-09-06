import time
from pydantic import BaseModel, Field
from tracer import trace_step, start_trace_session

# --- Tool Schemas ---
class BalanceSchema(BaseModel):
    account_id: str = Field(description="Target account ID")

class FraudCheckSchema(BaseModel):
    account_id: str
    amount: float

class PaymentSchema(BaseModel):
    user_id: str
    amount: float
    note: str = Field(default="Transfer")

# --- Traced Tools ---
@trace_step(step_name="check_balance", step_type="tool", schema=BalanceSchema)
def check_balance(account_id: str):
    time.sleep(0.1)
    return {"account_id": account_id, "available_balance": 5000.0}

@trace_step(step_name="run_fraud_check", step_type="tool", schema=FraudCheckSchema)
def run_fraud_check(account_id: str, amount: float):
    time.sleep(0.15)
    # Passed fraud check
    return {"account_id": account_id, "risk_score": 0.05, "status": "approved"}

@trace_step(step_name="execute_payout", step_type="tool", schema=PaymentSchema)
def execute_payout(user_id: str, amount: float, note: str):
    time.sleep(0.2)
    return {"status": "success", "tx_hash": "0x9ab81c7f", "amount": amount}

# --- Multi-Step Execution Simulation ---
def run_autonomous_agent_workflow():
    session_id = start_trace_session()
    print(f"\n[Agent] Starting Workflow with Session ID: {session_id}")
    
    target_user = "acc_user_44"
    transfer_amount = 1200.0

    # Step 1: Check balance
    print("[Agent Step 1] Querying balance...")
    balance_res = check_balance(account_id=target_user)
    print(f"  -> Balance Output: {balance_res}")

    # Step 2: Fraud Evaluation
    print("[Agent Step 2] Checking fraud metrics...")
    fraud_res = run_fraud_check(account_id=target_user, amount=transfer_amount)
    print(f"  -> Fraud Check Output: {fraud_res}")

    # Step 3: Execution with deliberate hallucination to test auto-healing in-loop
    print("[Agent Step 3] Executing payout with malformed parameters...")
    malformed_args = {
        "user_identifier": target_user,  # Wrong key: should be user_id
        "amount": f"{transfer_amount} INR", # Wrong type: string instead of float
    }
    payout_res = execute_payout(**malformed_args)
    print(f"  -> Payout Output: {payout_res}")
    
    print("\n[Agent] Workflow completed successfully!")

if __name__ == "__main__":
    run_autonomous_agent_workflow()