# AiAS Agents

AiAS Agents is a collection of focused command-line research agents powered by
the AiAssist API.

## Included agents

| Agent | Purpose | Documentation |
|---|---|---|
| Angel | Discover investors, funds, portfolios, and public contact signals | [angel/README.md](./angel/README.md) |
| Journey | Find publications, journalists, editors, and public contact details | [journey/README.md](./journey/README.md) |
| MIA | Build company intelligence, team profiles, outreach angles, CSVs, and PDF dossiers | [mia/README.md](./mia/README.md) |

## Requirements

- Python 3.10+
- An AiAssist API key with access to the endpoints required by the selected
  agent

## Quick start

Choose an agent and install its dependencies:

```bash
cd angel
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
# Set AIASSIST_API_KEY in .env
python angel.py "AI infrastructure"
```

Use `journey/journey.py`, `mia/mia.py`, or `mia/mia_v3.py` for the other
agents. Each agent keeps generated research in a gitignored `output/` or
`runs/` directory.

## Data and usage responsibilities

These agents collect and synthesize public web information. Review output for
accuracy, respect site terms and rate limits, follow applicable privacy and
anti-spam laws, and verify contact data before using it. Generated analysis
may contain errors and should not be treated as authoritative.

## Repository layout

```text
aias_agents/
├── angel/
├── journey/
└── mia/
```

Each directory is independently runnable and includes its own detailed README,
dependency list, environment template, ignore rules, and license.

## Documentation archive

The `docs/workspace/` directory preserves the project Markdown corpus with
source-relative paths. It includes READMEs, specifications, architecture
documents, workplans, guides, and generated Markdown reports from the
workspace, so related research and product context can be reviewed alongside
the agents.

The archive intentionally excludes Replit operational metadata
(`.git`, `.local`, and `.agents`) plus dependency and build trees. Generated
runtime data, secrets, and environment files are excluded by the repository
ignore rules.

## License

MIT. See [LICENSE](./LICENSE) and the per-agent license files.