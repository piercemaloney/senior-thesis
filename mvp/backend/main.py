from typing import List
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from openai_api import call_openai_gpt3
from prompts import generate_prompt, vote_prompt

from pydantic import BaseModel
from typing import List

# --- Pydantic ---

class VoteInput(BaseModel):
    current_proof: str
    proposed_steps: List[str]

class Proof(BaseModel):
    current_proof: str

# --- FastAPI ---

app = FastAPI()

origins = [
    "http://localhost:3000",   # React's default dev server address
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
async def generate(generate_input: Proof) -> List[str]:
    response = await call_openai_gpt3(generate_prompt.format(input=generate_input.current_proof))
    proposed_steps = [step.strip() for step in response.split("\n") if step.strip()]
    print("PROPOSED STEPS", proposed_steps)
    proposed_steps = [step[step.index(")")+1:] for step in proposed_steps]
    proposed_steps = [step.strip() for step in proposed_steps]
    print(proposed_steps)
    return proposed_steps

@app.post("/vote")
async def vote(vote_input: VoteInput):
    print(vote_input)
    proposed_steps_formatted = "\n".join([f"{i+1}) {tactic}" for i, tactic in enumerate(vote_input.proposed_steps)])
    result = await call_openai_gpt3(vote_prompt.format(input=vote_input.current_proof, proposed_steps=proposed_steps_formatted))
    return {"index": int(result) - 1, "step": vote_input.proposed_steps[int(result) - 1]}

@app.post("/run_coq")
async def run_coq(proof: Proof):
    return 

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
