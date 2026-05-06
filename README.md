# CSE321 Project 1

This repository implements and evaluates the following tree-based index structures for CSE321 Database Systems Project 1:

* B-tree
* B*-tree
* B+tree

The program loads `student.csv` into an in-memory array.
The `Student ID` field is used as the index key, and the array index is used as the Record Identifier (RID).

## Experimental Environment

Tested environment:

* Python 3.10.13
* macOS

The main experiment uses only the Python standard library.

## Repository Files

* `main.py` : Runs all experiments
* `btree.py` : Implements B-tree, B*-tree, and B+-tree
* `make_report_assets.py` : Generates graph files from `results.csv`
* `student.csv` : Input dataset
* `requirements.txt`
* `README.md`

## Setup

Create and activate a virtual environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:
```bash
pip install -r requirements.txt
```
The dependencies are only required for generating graphs with `make_report_assets.py`.

## How to Run

Make sure `student.csv` is located in the same directory as `main.py`.

Run the experiment:

```bash
python3 main.py
```

Save the output:

```bash
python3 main.py > results.csv
```

## Order Definition

In this implementation, tree order `d` is treated as the minimum degree:

* Minimum keys in a non-root node: `d - 1`
* Maximum keys in a node: `2d - 1`

Experiments were conducted using:

```text
d = 3, 5, 10
```

## Reproducibility

The experiment uses a fixed random seed:

```text
RANDOM_SEED = 321
```

Execution times may vary depending on hardware and runtime environment.