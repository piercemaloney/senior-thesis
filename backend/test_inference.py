import requests, json
import os
from dotenv import load_dotenv
import time

load_dotenv()  # Load environment variables from .env file

API_URL = "https://r2lzy96rgluppigc.us-east-1.aws.endpoints.huggingface.cloud"

headers = {
  "Authorization": f"Bearer {os.getenv('HF_TOKEN')}",
  "Content-Type": "application/json",
}

def query(prompt: str):
    data = json.dumps({"inputs": prompt})
    response = requests.request("POST", API_URL, headers=headers, data=data)
    return response.json()

output = query("Theorem test_theorem: forall (n : nat), n =")

for _ in range(10):  # Loop to run the query 10 times
    output = query("Theorem test_theorem: forall (n : nat), n =")
    print(output)
    time.sleep(1)
  