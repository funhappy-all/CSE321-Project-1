import csv
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt


RESULTS_FILE = Path("results.csv")
FIGURE_DIR = Path("figures")


def read_results():
    with RESULTS_FILE.open(newline="", encoding="utf-8") as csv_file:
        rows = list(csv.DictReader(csv_file))
    for row in rows:
        row["order"] = int(row["order"])
        for field in [
            "insert_time",
            "search_total",
            "search_mean",
            "range_time",
            "delete_time",
            "utilization",
            "range_avg_gpa",
            "range_avg_height",
        ]:
            row[field] = float(row[field])
        for field in [
            "height",
            "nodes",
            "splits",
            "redistributions",
            "merges",
            "2to3_splits",
            "range_males",
            "deleted",
        ]:
            row[field] = int(row[field])
    return rows


def plot_metric(rows, metric, ylabel, filename, scale=1.0):
    FIGURE_DIR.mkdir(exist_ok=True)
    trees = ["B-tree", "B*-tree", "B+tree"]
    orders = sorted({row["order"] for row in rows})

    plt.figure(figsize=(6.2, 3.8))
    for tree in trees:
        y_values = []
        for order in orders:
            match = next(row for row in rows if row["tree"] == tree and row["order"] == order)
            y_values.append(match[metric] * scale)
        plt.plot(orders, y_values, marker="o", linewidth=2, label=tree)

    plt.xlabel("Order d")
    plt.ylabel(ylabel)
    plt.xticks(orders)
    plt.grid(True, axis="y", alpha=0.3)
    plt.legend()
    plt.tight_layout()
    output_path = FIGURE_DIR / filename
    plt.savefig(output_path)
    plt.savefig(output_path.with_suffix(".pdf"))
    plt.close()


def make_figures(rows):
    plot_metric(rows, "insert_time", "Insertion time (sec)", "insert_time.svg")
    plot_metric(rows, "search_mean", "Mean search time (microsec)", "search_mean.svg", 1_000_000)
    plot_metric(rows, "range_time", "Range query time (sec)", "range_time.svg")
    plot_metric(rows, "delete_time", "Deletion time (sec)", "delete_time.svg")
    plot_metric(rows, "utilization", "Node utilization", "utilization.svg")
    plot_metric(rows, "height", "Tree height", "height.svg")
    plot_metric(rows, "nodes", "Node count", "node_count.svg")
    plot_metric(rows, "splits", "Split count", "split_count.svg")


def main():
    rows = read_results()
    make_figures(rows)
    print(f"Wrote SVG and PDF figures to {FIGURE_DIR}/")


if __name__ == "__main__":
    main()
