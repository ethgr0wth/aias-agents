# Installing from GitHub (Pre-PyPI)

Install the AiAssist Python SDK directly from GitHub before it's published to PyPI.

---

## Option 1: pip install from GitHub

```bash
pip install git+https://github.com/AiAssistSecure/aiassist-python.git
```

With a specific branch:
```bash
pip install git+https://github.com/AiAssistSecure/aiassist-python.git@main
```

With a specific tag/version:
```bash
pip install git+https://github.com/AiAssistSecure/aiassist-python.git@v1.0.0
```

---

## Option 2: Clone and install locally

```bash
git clone https://github.com/AiAssistSecure/aiassist-python.git
cd aiassist-python
pip install -e .
```

The `-e` flag installs in "editable" mode - changes to the source reflect immediately.

---

## Option 3: Add to requirements.txt

```txt
# From main branch
aiassist-secure @ git+https://github.com/AiAssistSecure/aiassist-python.git@main

# From specific commit
aiassist-secure @ git+https://github.com/AiAssistSecure/aiassist-python.git@eebb1f4

# From tag
aiassist-secure @ git+https://github.com/AiAssistSecure/aiassist-python.git@v1.0.0
```

Then:
```bash
pip install -r requirements.txt
```

---

## Option 4: Add to pyproject.toml (Poetry/PDM)

### Poetry

```toml
[tool.poetry.dependencies]
aiassist-secure = { git = "https://github.com/AiAssistSecure/aiassist-python.git", branch = "main" }
```

Then:
```bash
poetry install
```

### PDM

```toml
[project]
dependencies = [
    "aiassist-secure @ git+https://github.com/AiAssistSecure/aiassist-python.git@main"
]
```

Then:
```bash
pdm install
```

---

## Option 5: Install from wheel/tarball

Download the pre-built distribution from the `dist/` folder:

```bash
# Wheel (faster)
pip install https://raw.githubusercontent.com/AiAssistSecure/aiassist-python/main/dist/aiassist_secure-1.0.0-py3-none-any.whl

# Or tarball
pip install https://raw.githubusercontent.com/AiAssistSecure/aiassist-python/main/dist/aiassist_secure-1.0.0.tar.gz
```

Or download and install locally:
```bash
curl -LO https://github.com/AiAssistSecure/aiassist-python/raw/main/dist/aiassist_secure-1.0.0-py3-none-any.whl
pip install aiassist_secure-1.0.0-py3-none-any.whl
```

---

## Option 6: Vendor directly (no pip)

Copy the `aiassist/` folder into your project:

```
your-project/
├── your_app.py
└── aiassist/
    ├── __init__.py
    └── client.py
```

Then import directly:
```python
from aiassist import AiAssistClient
```

Make sure `httpx` is installed:
```bash
pip install httpx
```

---

## Verify Installation

```python
from aiassist import AiAssistClient, SyncAiAssistClient

print("AiAssist SDK installed successfully!")

# Quick test (replace with your API key)
async def test():
    async with AiAssistClient(
        api_key="aai_test",
        base_url="https://your-instance.com"
    ) as client:
        models = await client.models.list()
        print(f"Available models: {len(models)}")

import asyncio
asyncio.run(test())
```

---

## Upgrading

### From GitHub
```bash
pip install --upgrade git+https://github.com/AiAssistSecure/aiassist-python.git
```

### Force reinstall
```bash
pip install --force-reinstall git+https://github.com/AiAssistSecure/aiassist-python.git
```

---

## Troubleshooting

### "Could not find a version that satisfies the requirement"
Make sure you have git installed and accessible:
```bash
git --version
```

### "Permission denied" on private repo
Use SSH URL:
```bash
pip install git+ssh://git@github.com/AiAssistSecure/aiassist-python.git
```

Or use a personal access token:
```bash
pip install git+https://YOUR_TOKEN@github.com/AiAssistSecure/aiassist-python.git
```

### Import errors after install
Ensure you're using the right Python environment:
```bash
which python
pip show aiassist-secure
```

---

## When PyPI is available

Once published, simply:
```bash
pip install aiassist-secure
```

Until then, use any of the methods above.
