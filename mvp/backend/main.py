from typing import List
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from openai_api import call_openai_gpt3
from prompts import generate_prompt, vote_prompt

from pydantic import BaseModel
from typing import List
import os
from dotenv import load_dotenv

import requests, json
import asyncio

load_dotenv()

# --- Pydantic ---

class VoteInput(BaseModel):
    current_proof: str
    proposed_steps: List[str]

class Proof(BaseModel):
    current_proof: str

class GenerateTacticsInput(BaseModel):
    inputs: str


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

@app.post("/generate_tactics")
async def generate_tactics(input_data: GenerateTacticsInput) -> dict:
    proof_step_eval_txt = input_data.inputs
    if not proof_step_eval_txt:
        raise HTTPException(status_code=400, detail="proof_step_eval_txt is required")

    response = await call_openai_gpt3(generate_prompt.format(input=proof_step_eval_txt))
    proposed_steps = [step.strip() for step in response.split("\n") if step.strip()]
    print("PROPOSED STEPS", proposed_steps)
    proposed_steps = [step[step.index(")")+1:] for step in proposed_steps]
    proposed_steps = [step.strip() for step in proposed_steps]
    print(proposed_steps)
    return {"tactics": proposed_steps}



@app.post("/generate_tactics_llemma_base")
async def generate_tactics_llemma_base(input_data: GenerateTacticsInput) -> dict:
    # num_queries = 1  # Number of queries to generate tactics
    # tactics = await asyncio.gather(*(generate_tactic_llemma_base(input_data) for _ in range(num_queries)))
    # unique_tactics = list(set(tactics))  # Remove duplicates
    
    # First call without additional_bad_words_ids
    first_call_result, generated_ids_first_call = await generate_tactic_llemma_base(input_data)
    print(first_call_result)
    print(generated_ids_first_call)
    
    # Second call with generated_ids from the first call as additional_bad_words_ids
    second_call_result, generated_ids_second_call = await generate_tactic_llemma_base(input_data, additional_bad_words_ids=[generated_ids_first_call])
    print(second_call_result)
    print(generated_ids_second_call)

    third_call_result, generated_ids_third_call = await generate_tactic_llemma_base(input_data, additional_bad_words_ids=generated_ids_first_call)
    print(third_call_result)
    print(generated_ids_third_call)
    
    # Combine results from both calls, ensuring uniqueness
    tactics = list(set([first_call_result, second_call_result]))

    print(tactics)
    return {"tactics": tactics}

async def generate_tactic_llemma_base(input_data: GenerateTacticsInput, additional_bad_words_ids: List[List[int]] = None):
    proof_step_eval_txt = input_data.inputs
    url = "https://r2lzy96rgluppigc.us-east-1.aws.endpoints.huggingface.cloud"
    headers = {
        "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
        "Content-Type": "application/json",
    }
    
    data = json.dumps({
        "inputs": proof_step_eval_txt,
        "additional_bad_words_ids": additional_bad_words_ids  # Include additional bad words here
    })
    response = requests.request("POST", url, headers=headers, data=data)
    if response.status_code == 200:
        response_json = response.json()  # Parse the JSON response
        generated_text = response_json[0]['generated_text']
        generated_ids = response_json[0]['generated_ids']
    else:
        raise HTTPException(status_code=response.status_code, detail=response.text)
    # generated_text = generated_text.replace("\n", " ")  # Replace newline characters with spaces
    return generated_text, generated_ids


# @app.post("/evaluate")
# async def evaluate(input_data: GenerateTacticsInput) -> dict:
#     proof_step_eval_txt = input_data.inputs
#     if not proof_step_eval_txt:
#         raise HTTPException(status_code=400, detail="proof_step_eval_txt is required")
#     response = await call_openai_gpt3(evaluate_prompt.format(input=proof_step_eval_txt))
#     return {"evaluation": response}


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
