import csv
import random
import time
from dataclasses import dataclass

from btree import BPlusTree, BStarTree, BTree


DATA_FILE = "student.csv"
ORDERS = [3, 5, 10]
SEARCH_QUERY_COUNT = 10_000
DELETE_QUERY_COUNT = 2_000
RANGE_LOW = 202000000
RANGE_HIGH = 202100000
RANDOM_SEED = 321


@dataclass
class StudentRecord:
    student_id: int
    name: str
    gender: str
    gpa: float
    height: float
    weight: float


def load_records(path):
    records = []
    with open(path, newline="", encoding="utf-8") as csv_file:
        reader = csv.DictReader(csv_file)
        for row in reader:
            records.append(
                StudentRecord(
                    student_id=int(row["Student ID"]),
                    name=row["Name"],
                    gender=row["Gender"],
                    gpa=float(row["GPA"]),
                    height=float(row["Height"]),
                    weight=float(row["Weight"]),
                )
            )
    return records


def build_tree(tree_class, records, order):
    tree = tree_class(order)
    start = time.perf_counter()
    for rid, record in enumerate(records):
        tree.insert(record.student_id, rid)
    elapsed = time.perf_counter() - start
    return tree, elapsed


def run_point_search(tree, keys):
    start = time.perf_counter()
    found = 0
    for key in keys:
        if tree.search(key) is not None:
            found += 1
    elapsed = time.perf_counter() - start
    return elapsed, elapsed / len(keys), found


def run_range_query(tree, records, low, high):
    start = time.perf_counter()
    rids = tree.range_query(low, high)
    male_count = 0
    gpa_sum = 0.0
    height_sum = 0.0
    for rid in rids:
        record = records[rid]
        if record.gender == "Male":
            male_count += 1
            gpa_sum += record.gpa
            height_sum += record.height
    elapsed = time.perf_counter() - start
    avg_gpa = gpa_sum / male_count if male_count else 0.0
    avg_height = height_sum / male_count if male_count else 0.0
    return elapsed, male_count, avg_gpa, avg_height


def run_delete_workload(tree, keys):
    start = time.perf_counter()
    deleted = 0
    for key in keys:
        if tree.delete(key):
            deleted += 1
    elapsed = time.perf_counter() - start
    return elapsed, deleted


def print_header():
    columns = [
        "tree",
        "order",
        "insert_time",
        "search_total",
        "search_mean",
        "range_time",
        "delete_time",
        "height",
        "nodes",
        "utilization",
        "splits",
        "redistributions",
        "merges",
        "2to3_splits",
        "range_males",
        "range_avg_gpa",
        "range_avg_height",
        "deleted",
        "valid",
    ]
    print(",".join(columns))


def print_result(row):
    print(
        ",".join(
            [
                row["tree"],
                str(row["order"]),
                f"{row['insert_time']:.6f}",
                f"{row['search_total']:.6f}",
                f"{row['search_mean']:.9f}",
                f"{row['range_time']:.6f}",
                f"{row['delete_time']:.6f}",
                str(row["height"]),
                str(row["nodes"]),
                f"{row['utilization']:.6f}",
                str(row["splits"]),
                str(row["redistributions"]),
                str(row["merges"]),
                str(row["two_to_three_splits"]),
                str(row["range_males"]),
                f"{row['range_avg_gpa']:.6f}",
                f"{row['range_avg_height']:.6f}",
                str(row["deleted"]),
                str(row["valid"]),
            ]
        )
    )


def run_all_experiments():
    random.seed(RANDOM_SEED)
    records = load_records(DATA_FILE)
    all_keys = [record.student_id for record in records]
    search_keys = random.sample(all_keys, min(SEARCH_QUERY_COUNT, len(all_keys)))
    delete_keys = random.sample(all_keys, min(DELETE_QUERY_COUNT, len(all_keys)))
    tree_classes = [BTree, BStarTree, BPlusTree]

    print_header()
    for order in ORDERS:
        for tree_class in tree_classes:
            tree, insert_time = build_tree(tree_class, records, order)
            search_total, search_mean, found = run_point_search(tree, search_keys)
            if found != len(search_keys):
                raise RuntimeError(f"{tree_class.name} failed point search before deletion")

            range_time, male_count, avg_gpa, avg_height = run_range_query(
                tree, records, RANGE_LOW, RANGE_HIGH
            )
            delete_time, deleted = run_delete_workload(tree, delete_keys)
            valid = tree.validate()

            print_result(
                {
                    "tree": tree_class.name,
                    "order": order,
                    "insert_time": insert_time,
                    "search_total": search_total,
                    "search_mean": search_mean,
                    "range_time": range_time,
                    "delete_time": delete_time,
                    "height": tree.height(),
                    "nodes": tree.count_nodes(),
                    "utilization": tree.utilization(),
                    "splits": tree.split_count,
                    "redistributions": tree.redistribution_count,
                    "merges": tree.merge_count,
                    "two_to_three_splits": tree.two_to_three_split_count,
                    "range_males": male_count,
                    "range_avg_gpa": avg_gpa,
                    "range_avg_height": avg_height,
                    "deleted": deleted,
                    "valid": valid,
                }
            )


if __name__ == "__main__":
    run_all_experiments()
