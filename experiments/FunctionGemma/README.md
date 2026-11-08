# FunctionGemma Experiments

## Sequence Call

Follows this guideline: https://ai.google.dev/gemma/docs/functiongemma/full-function-calling-sequence-with-functiongemma

> FunctionGemma is a specialized version of the Gemma 3 270M model, trained specifically for function calling improvements. It has the same architecture as Gemma, but uses a different chat format and tokenizer.

Install torch and transformer

```bash
pip install torch
pip install transformers
```

Go to https://huggingface.co/google/functiongemma-270m-it and requests for model access.

Export HuggingFace token

```bash
export HF_TOKEN="...."
```

Run the example:

```bash
python experiments/FunctionGemma/run.py
```
