import os
import json
from openai import OpenAI
import re

def read_file(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        return f.read()

def write_file(filepath, content):
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

def agent_file_to_toolkit(agent_file_content, toolkit_name):
    # LLM prompt for code conversion
    code_prompt = f"""
    > **Instruction:**
    > You are an expert code converter.
    > Given the following Python file content, your task is to **wrap the entire file as a toolkit**, using these guidelines:
    >
    > 1. **Toolkit Format:**
    >    * Encapsulate the core logic as a function decorated with `@tool`. (you don't need to import extra package for `@tool`, it is already here)
    >    * Follow the function docstring style shown in the template (description, Args, Returns, Raises).
    >    * Use the function name `{toolkit_name}`.
    > 2. **Input/Output:**
    >    * Analyze the original file to determine all necessary inputs and outputs for the toolkit.
    >    * Expose these as the function’s parameters and return value(s).
    > 3. **Preserve Original Functionality:**
    >    * Include and adapt all original code, tool definitions, and agent logic inside the toolkit function.
    >    * Do **not** remove or simplify any core logic.
    >    * If the original file contains tools or agents, keep them inside the toolkit (as nested definitions if necessary).
    > 4. **No Extra Output:**
    >    * Only output the code for the toolkit file in the required format.
    >    * Do not add explanations or comments outside of the code.
    > 5. **Follow this exact template for the toolkit:**
    >
    > ```python
    > @tool
    > def {toolkit_name}(Arg1: type = ..., Arg2: type = ..., ...) -> Returns' type: ((you must make sure openai can create a json-schema for the type you set, or just remove it if it is not necessary))
    >     \"""
    >     Toolkit Description (you should make a detailed and pratical description to introduce this toolkit)
    >
    >     Args:
    >         Arg1 (type): ... 
    >         Arg2 (type): ...
    >
    >     Returns:
    >         type: ...
    >
    >     Raises:
    >         ...
    >     \"""
    >     # === Begin original logic, fully adapted ===
    >     ...
    >     # === End original logic ===
    >     return ...
    > ```
    >
    > ---
    >
    > **The file you need to convert is as follows:**
    >
    > ```python
    > {agent_file_content}
    > ```
    >
    > ---
    >
    > **Your output must be a single self-contained Python file implementing the above.**
    """
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": code_prompt}],
        max_tokens=4096,
        temperature=0,
    )
    toolkit_code = response.choices[0].message.content
    return toolkit_code

def clean_code_block(code_str):
    """
    Remove Markdown code block markers like ```python or ```
    """
    # 去掉```python或```包裹
    code_str = re.sub(r"^```(?:python)?\s*", "", code_str.strip())
    code_str = re.sub(r"\s*```$", "", code_str.strip())
    return code_str.strip()

def get_agent_description_from_toolkit(toolkit_code, agent_name):
    system_prompt = (
        "You are an AI system tasked with summarizing the purpose and capabilities of an agent, "
        "based solely on the following toolkit code (in Python):\n"
        "------------------\n"
        f"{toolkit_code}\n"
        "------------------\n"
        f"Write a concise 1-2 sentence description of what this agent is capable of doing, "
        f"starting with: 'I am an {agent_name} agent capable of...'. "
        "Your response must be a valid JSON object in the following format:\n"
        "{\"description\": \"<your concise summary here>\"}"
    )
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    response = client.chat.completions.create(
        model="gpt-4o",
        messages=[{"role": "system", "content": system_prompt}],
        max_tokens=512,
        temperature=0.3,
        response_format={"type": "json_object"}
    )
    content = response.choices[0].message.content
    description = json.loads(content)["description"]
    return description

def replace_template(base_template, toolkit_code, agent_desc, agent_name, toolkit_name):
 
    import re
    base_template = re.sub(
        r"@tool\s*\ndef\s+stock_ticker_toolkit\(.*?\):[\s\S]*?return output", 
        toolkit_code.strip(), 
        base_template, 
        flags=re.DOTALL
    )
    # replace agent description
    base_template = base_template.replace('"agentDescription": ""', f'"agentDescription": "{agent_desc}"')
    # replace agentId
    base_template = base_template.replace('"agentId": ""', f'"agentId": "{agent_name}"')
    # replace toolkit name
    base_template = base_template.replace("[stock_ticker_toolkit]", f"[{toolkit_name}]")
    return base_template

def main():
    # input
    base_template_file = "base-agent2agent-coraliser.py"
    agent_file = "livekitagent.py"
    output_file = "coralised_agent.py"
    agent_name = "livekit_agent"         
    toolkit_name = "livekit_toolkit"  

    
    base_template = read_file(base_template_file)
    agent_code = read_file(agent_file)

    print("Converting agent to toolkit...")
    toolkit_code = agent_file_to_toolkit(agent_code, toolkit_name)
    toolkit_code = clean_code_block(toolkit_code)

    print("Generating agent description...")
    agent_desc = get_agent_description_from_toolkit(toolkit_code, agent_name)

    print("Replacing template...")
    final_code = replace_template(base_template, toolkit_code, agent_desc, agent_name, toolkit_name)

    write_file(output_file, final_code)
    print(f"Coralised agent generated: {output_file}")
    print("Saved at:", os.path.abspath(output_file))

if __name__ == "__main__":
    main()
