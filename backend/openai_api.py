import os
import openai
from fastapi import HTTPException
from dotenv import load_dotenv

load_dotenv()  # take environment variables from .env.
openai.api_key = os.getenv("OPENAI_API_KEY")
openai.organization = "org-wXczH2vyiAmy2mzvznzF7dfJ" # My Personal org id

async def call_openai_gpt3(prompt: str):
    try:
        response = openai.ChatCompletion.create(
          model="gpt-3.5-turbo",
          messages=[
              {
                  "role": "user",
                  "content": prompt
              }
          ],
          temperature=0.7
        )
        return response['choices'][0]['message']['content'].strip()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def call_openai_gpt4(prompt: str):
    try:
        response = openai.ChatCompletion.create( model="gpt-4-turbo", messages=[{"role": "user", "content": prompt}] )
        return response.choices[0]['message']['content']
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))