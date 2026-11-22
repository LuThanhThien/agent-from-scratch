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

Install for app window:

```bash
sudo apt-get install -y \
    python3-gi \
    gir1.2-gtk-3.0
```

For a Python virtual environment that cannot import `gi`, install its build
dependencies and Python bindings (on Ubuntu 24.04):

```bash
sudo apt-get install -y gcc pkg-config libcairo2-dev libgirepository1.0-dev
python -m pip install 'PyGObject==3.48.2'
```

Run the chat app:

```bash
python -m demo.LLMChat
```

To choose a model, add `--model` followed by its Hugging Face ID or local path.

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
