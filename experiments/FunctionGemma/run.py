# Load Model

from transformers import AutoProcessor, AutoModelForCausalLM

GEMMA_MODEL_ID = "google/functiongemma-270m-it"

processor = AutoProcessor.from_pretrained(GEMMA_MODEL_ID, device_map="auto")
model = AutoModelForCausalLM.from_pretrained(
    GEMMA_MODEL_ID, dtype="auto", device_map="auto"
)

# Define a function that our model can use.


def get_current_weather(location: str, unit: str = "celsius"):
    """
    Gets the current weather in a given location.

    Args:
        location: The city and state, e.g. "San Francisco, CA" or "Tokyo, JP"
        unit: The unit to return the temperature in. (choices: ["celsius", "fahrenheit"])

    Returns:
        temperature: The current temperature in the given location
        weather: The current weather in the given location
    """
    return {"temperature": 15, "weather": "sunny"}


# Model's Turn
print("-" * 80)
prompt = "Hey, what's the weather in Tokyo right now?"
tools = [get_current_weather]

message = [
    # ESSENTIAL SYSTEM PROMPT:
    # This line activates the model's function calling logic.
    {
        "role": "developer",
        "content": "You are a model that can do function calling with the following functions",
    },
    {"role": "user", "content": prompt},
]

inputs = processor.apply_chat_template(
    message,
    tools=tools,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
)
output = processor.decode(inputs["input_ids"][0], skip_special_tokens=False)
print(f"Inputs for model: {output}")

out = model.generate(
    **inputs.to(model.device), pad_token_id=processor.eos_token_id, max_new_tokens=128
)
generated_tokens = out[0][len(inputs["input_ids"][0]) :]
output = processor.decode(generated_tokens, skip_special_tokens=False)

print(f"Prompt: {prompt}")
print(f"Tools: {tools}")
print(f"Output: {output}")

# Developer's Turn
print("-" * 80)

import re


def extract_tool_calls(text):
    def cast(v):
        try:
            return int(v)
        except:
            try:
                return float(v)
            except:
                return {"true": True, "false": False}.get(v.lower(), v.strip("'\""))

    return [
        {
            "name": name,
            "arguments": {
                k: cast((v1 or v2).strip())
                for k, v1, v2 in re.findall(
                    r"(\w+):(?:<escape>(.*?)<escape>|([^,}]*))", args
                )
            },
        }
        for name, args in re.findall(
            r"<start_function_call>call:(\w+)\{(.*?)\}<end_function_call>",
            text,
            re.DOTALL,
        )
    ]


calls = extract_tool_calls(output)
if calls:
    message.append(
        {
            "role": "assistant",
            "tool_calls": [{"type": "function", "function": call} for call in calls],
        }
    )
    print(message[-1])

    # Call the function and get the result
    #####################################
    # WARNING: This is a demonstration. #
    #####################################
    # Using globals() to call functions dynamically can be dangerous in
    # production. In a real application, you should implement a secure way to
    # map function names to actual function calls, such as a predefined
    # dictionary of allowed tools and their implementations.
    results = [
        {"name": c["name"], "response": globals()[c["name"]](**c["arguments"])}
        for c in calls
    ]

    message.append({"role": "tool", "content": results})
    print(message[-1])

# Final Response
print("-" * 80)

inputs = processor.apply_chat_template(
    message,
    tools=tools,
    add_generation_prompt=True,
    return_dict=True,
    return_tensors="pt",
)
output = processor.decode(inputs["input_ids"][0], skip_special_tokens=False)
print(f"Inputs for model: {output}")

out = model.generate(
    **inputs.to(model.device), pad_token_id=processor.eos_token_id, max_new_tokens=128
)
generated_tokens = out[0][len(inputs["input_ids"][0]) :]
output = processor.decode(generated_tokens, skip_special_tokens=False)
print(f"Output: {output}")
message.append({"role": "assistant", "content": output})

# full history
print("-" * 80)
for item in message:
    print(item)

print("-" * 80)
output = processor.decode(out[0], skip_special_tokens=False)
print(f"Output: {output}")
