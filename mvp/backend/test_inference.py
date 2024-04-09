import requests, json
import os
from dotenv import load_dotenv

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

output = query("(* Goal: )")

print(output)