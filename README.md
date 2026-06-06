# Family Tree Tracker

A Python CLI tool to **manage and visualize family relationships**. Track people, connect them as parents/children or siblings, and discover how any two people are related — even complex relationships like "second cousin once removed" or "great-grandparent".

## Features

- **Interactive web visualization** — a force-directed graph of your family tree, with click-to-edit and drag-to-explore
- **Relationship engine** — computes genealogical relationships (siblings, cousins, aunts/uncles, grandparents, and all removed/n-th variants)
- **Person profiles** — store name, age, gender, and a free-form biography for each person
- **CLI tool** — full command-line interface for adding, editing, deleting, and querying family data
- **Data stored locally** — all data is saved to `~/.family_tree/data.json`

## Quickstart

### Install

```bash
# Install from GitHub
uv add "git+https://github.com/v1zhu/family_tree.git"

# Or install in editable mode for development
git clone https://github.com/v1zhu/family_tree.git
cd family_tree
uv pip install -e .
```

### Launch the web UI

```bash
family-tree serve
```

Opens a browser at `http://localhost:8080` with an interactive graph.

## usage

```bash
# Add people
family-tree add-person --name Alice --age 30 --gender female --bio "Lives in Chicago"
family-tree add-person --name Bob --age 10 --gender male
family-tree add-person --name Charlie --age 60

# Link them
family-tree add-relation 2 1 parent     # Alice is parent of Bob
family-tree add-relation 1 3 parent     # Charlie is parent of Alice

# Add a spouse relationship
family-tree add-person --name Diana --age 55 --gender female
family-tree add-relation 3 4 spouse     # Charlie and Diana are spouses

# Find how two people are related
family-tree relation 3 2
# Output: Bob is the grandchild of Charlie

# List everyone
family-tree list

# Show person details
family-tree info 1

# Update a person
family-tree update-person 1 --name "Alice Smith" --bio "Moved to Seattle"

# Reset everything
family-tree clear
```

## How the Relationship Engine Works

The tool stores **parent** and **sibling** relationships. The engine traces parent-child links upward to find common ancestors, then classifies the relationship:

| Distance to common ancestor | Relationship |
|---|---|
| (0, 1) | parent / child |
| (0, 2) | grandparent / grandchild |
| (0, N) | great-...-grandparent / great-...-grandchild |
| (1, 1) | siblings |
| (1, 2) | aunt/uncle — niece/nephew |
| (1, N) | great-...-aunt/uncle — great-...-niece/nephew |
| (2, 2) | first cousins |
| (2, 3) | first cousins once removed |
| (3, 3) | second cousins |
| (N, M) | (min(N,M)-1)th cousins, \|N-M\| times removed |

## Project Structure

```
family_tree/
├── __init__.py
├── __main__.py        # python -m family_tree
├── cli.py             # CLI entry point (argparse)
├── engine.py          # FamilyTree data model + relationship engine
├── server.py          # HTTP server for the web UI
└── static/
    ├── index.html     # Interactive graph viewer
    ├── style.css
    └── script.js
```
