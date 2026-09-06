from pydantic import BaseModel, Field
from tracer import trace_step

# 1. Define strict tool schema
class TransferSchema(BaseModel):
    user_id: str = Field(description="Target account identifier")
    amount: float = Field(description="Amount in INR to transfer")
    note: str = Field(default="Standard transfer", description="Transfer description")

# 2. Attach schema to the traced tool
@trace_step(step_name="process_payment", step_type="tool", schema=TransferSchema)
def process_payment(user_id: str, amount: float, note: str):
    print(f"Executing transfer -> User: {user_id}, Amount: {amount}, Note: {note}")
    return {"status": "completed", "reference_id": "TXN_77492"}

if __name__ == "__main__":
    # Simulate a typical agent hallucination:
    # - Key misspelled: 'user_identifier' instead of 'user_id'
    # - Wrong type: amount passed as string "$750" instead of float 750.0
    bad_agent_call = {
        "user_identifier": "usr_alpha_9",
        "amount": "$750",
    }

    print("Sending malformed agent payload...")
    result = process_payment(**bad_agent_call)
    print("Execution Result:", result)