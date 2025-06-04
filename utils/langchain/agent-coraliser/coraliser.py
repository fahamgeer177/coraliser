import os
from dotenv import load_dotenv
from openai import OpenAI
import prompts
import json

load_dotenv()

# Initialize OpenAI client
client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

class AgentCoraliser:
    def __init__(self, filename):
        self.filename = filename
    
    def read_file(self):
        try:
            with open(self.filename, 'r') as file:
                return file.read()
        except FileNotFoundError:
            raise FileNotFoundError(f"The file {self.filename} does not exist.")
        except Exception as e:
            raise Exception(f"An error occurred while reading the file: {e}")
    
    def agent_evaluation(self):
        try:
            python_content = self.read_file()
            # Use OpenAI's ChatCompletion API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                temperature=0.3,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "user", "content": prompts.agent_evaluation_prompt.format(python_content=python_content)}
                ]
            )
            return response.choices[0].message.content
        except Exception as e:
            raise Exception(f"An error occurred during agent evaluation: {e}")
        
    def agent_conversion(self):
        try:
            python_content = self.read_file()
            response = client.chat.completions.create(
                model="gpt-4.1-2025-04-14",
                temperature=0.3,
                response_format = {"type": "json_object"},
                messages=[{"role":"user","content": prompts.agent_conversion_prompt.format(
                    python_content=python_content,
                    EXAMPLE_AGENT_CONTENT=prompts.EXAMPLE_AGENT_CONTENT,
                    INTERFACE_AGENT_SYSTEM_PROMPT = prompts.INTERFACE_AGENT_SYSTEM_PROMPT
                    )}]
            )
            return response.choices[0].message.content
        
        except Exception as e:
            raise Exception(f"An error occurred during agent conversion: {e}")
        
    def save_file(self, conversion_result):
        try:
            filename = conversion_result.get('file_name')
            content = conversion_result.get('coral_agent_content')
            with open(filename, "w") as f:
                f.write(content)
                print(f"File '{filename}' created successfully.")
        except Exception as e:
            print(f"Failed to save file: {e}")
    
    def run(self):
        try:
            print("Evaluating if the provided file is an agent...")
            evaluation_result = self.agent_evaluation()
            evaluation_result = json.loads(evaluation_result)
            if evaluation_result["agent"].lower() == "yes":
                print("The file is an agent. Proceeding with coraliser...")
                conversion_result = self.agent_conversion()
                conversion_result = json.loads(conversion_result)
                self.save_file(conversion_result)
            else:
                print("Provided file does not appear to be an agent. Please verify format.")
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    file_name = input("Enter the filename to coralise: ")
    coraliser = AgentCoraliser(file_name)
    coraliser.run()
