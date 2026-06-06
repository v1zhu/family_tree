# Family Tree Tracker

A Python CLI tool to manage and visualize family relationships. Track people, connect them as parents/children or siblings, and discover how any two people are related — even complex relationships familial relations. This tools aims to be a way to keep track of the history of your family.

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
## usage

### Running the CLI

All commands should be run using `uv run` to ensure they execute inside the project environment:


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

# Delete a relationship
family-tree delete-relation 1 3 parent   # Remove Charlie as Alice's parent

# Reset everything
family-tree clear
```

### Launch the web UI

```bash
family-tree serve
```

Opens a browser at `http://localhost:8080` with an interactive graph.
