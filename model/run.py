import subprocess

with open("../example.py") as f:
    code = f.read()

prompt = f""" 
You are a helpful coding assistant Please explain the following Python function in details, including its purpose, inputs and outputs  {code}  
"""

# Model qwen2.5-coder:7b (quantized) require ~8gb of ram

result = subprocess.run(
    ["ollama", "run", "qwen2.5-coder:7b"],
    input=prompt.encode("utf-8"),
    capture_output=True,
)
print(result.stdout.decode("utf-8"))
