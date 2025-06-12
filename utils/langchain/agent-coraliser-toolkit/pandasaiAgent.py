from pandasai import SmartDataframe
from pandasai.llm.local_llm import LocalLLM
import os

question = "What is the total columns in coral_public_repo_docs.xlsx"
file_path = "coral_public_repo_docs.xlsx"
ollama_llm = LocalLLM(api_base= "http://localhost:11434/v1", model="llama3.1:latest")
df = SmartDataframe(file_path, config={"llm": ollama_llm})
answer = df.chat(output_type='string', query=question)

print(answer)