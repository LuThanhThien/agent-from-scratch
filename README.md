# Agent From Scratch

## Set-up

You need Python 3 installed. Open a terminal in this project folder.

Create a virtual environment.

```bash
python3 -m venv .venv
```

Activate virtual environment.

```bash
source .venv/bin/activate
```

Install the project packages.

```bash
python -m pip install -r env/requirements.txt
```

Optionally create a `.env` file in the repository root:

```dotenv
HF_TOKEN=hf_your_token
```

## Development

### Github pre-commit

With your virtual environment active, run:

```bash
python -m pip install -r env/requirements-dev.txt
pre-commit install
```

To run it on all tracked files:

```bash
pre-commit run --all-files
```
