from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openai_api import call_openai_gpt3
from prompts import generate_prompt, vote_prompt

# --- FastAPI ---

app = FastAPI()

origins = [
    "http://localhost:3000",   # React's default dev server address
    "http://your-production-frontend-url.com",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Routes ---

@app.post("/generate")
async def generate(current_proof: str) -> List[str]:
    response = await call_openai_gpt3(generate_prompt.format(input=current_proof))
    proposed_steps = [step.strip() for step in response.split(",")]
    return proposed_steps

@app.post("/vote")
async def vote(current_proof: str, proposed_steps: List[str]):
    """tactics_list is a comma separated string of tactics"""
    proposed_steps_formatted = "\n".join([f"{i+1}) {tactic}" for i, tactic in enumerate(proposed_steps)])
    result = await call_openai_gpt3(vote_prompt.format(input=current_proof, proposed_steps=proposed_steps_formatted))
    return {"index": int(result) - 1, "step": proposed_steps[int(result) - 1]}

# --- Test ---

input_proof = """
Lemma mult_is_zero : forall n m : nat, n * m = 0 <-> n = 0 \/ m = 0.
Proof.
  intros n m.
  split.
  - (* Forward direction: n * m = 0 implies n = 0 \/ m = 0 *)
    intros H."""

@app.get("/run")
async def run():
    proposed = await generate(input_proof)
    print(proposed)
    voted = await vote(input_proof, proposed)
    print(voted)
    return voted
