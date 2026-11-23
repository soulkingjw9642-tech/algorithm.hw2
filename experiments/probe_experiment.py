#!/usr/bin/env python3
"""Compare separate-chaining probe counts with the topic 08 estimates."""

import csv
import random
import sys
from pathlib import Path

REPOSITORY_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPOSITORY_ROOT))

from src.hash_table import HashTable

BUCKET_COUNT = 4093
RANDOM_SEED = 2026
LOAD_STEPS = range(1, 17)


def random_url(generator, index, namespace):
    token = generator.getrandbits(64)
    return f"https://{namespace}-{token:016x}.example.test/item/{index}"


def measure_load(target_load, generator):
    item_count = round(target_load * BUCKET_COUNT)
    table = HashTable(bucket_count=BUCKET_COUNT, max_load=None)
    inserted_urls = []

    for index in range(item_count):
        url = random_url(generator, index, "short")
        table.put(url, index)
        inserted_urls.append(url)

    if len(table._buckets) != BUCKET_COUNT or table.size != item_count:
        raise RuntimeError("hash table resized or lost entries during measurement")

    successful_probes = 0
    for url in inserted_urls:
        value, probes = table.get_with_probes(url)
        if value is None:
            raise RuntimeError("inserted URL was not found")
        successful_probes += probes

    failed_query_count = max(BUCKET_COUNT, item_count)
    failed_probes = 0
    for index in range(failed_query_count):
        url = random_url(generator, index, "missing")
        value, probes = table.get_with_probes(url)
        if value is not None:
            raise RuntimeError("failed-search URL unexpectedly exists")
        failed_probes += probes

    actual_load = item_count / BUCKET_COUNT
    return {
        "target_load_factor": target_load,
        "actual_load_factor": actual_load,
        "bucket_count": BUCKET_COUNT,
        "items": item_count,
        "successful_measured": successful_probes / item_count,
        "successful_theoretical": 1 + actual_load / 2,
        "failed_measured": failed_probes / failed_query_count,
        "failed_theoretical": actual_load,
    }


def write_csv(rows, path):
    columns = (
        "target_load_factor",
        "actual_load_factor",
        "bucket_count",
        "items",
        "successful_measured",
        "successful_theoretical",
        "failed_measured",
        "failed_theoretical",
    )
    with path.open("w", newline="", encoding="utf-8") as output:
        writer = csv.DictWriter(output, fieldnames=columns, lineterminator="\n")
        writer.writeheader()
        writer.writerows(rows)


def write_svg(rows, path):
    width, height = 1000, 620
    left, right, top, bottom = 90, 35, 75, 90
    plot_width = width - left - right
    plot_height = height - top - bottom
    max_load = 4.0
    max_probes = 4.5

    def point(row, key):
        x = left + row["actual_load_factor"] / max_load * plot_width
        y = top + (max_probes - row[key]) / max_probes * plot_height
        return x, y

    series = (
        ("successful_measured", "성공 탐색 측정", "#1769aa", False),
        ("successful_theoretical", "성공 탐색 이론", "#1769aa", True),
        ("failed_measured", "실패 탐색 측정", "#d1495b", False),
        ("failed_theoretical", "실패 탐색 이론", "#d1495b", True),
    )
    svg = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        "<style>text{font-family:sans-serif;fill:#222}.grid{stroke:#ddd}.axis{stroke:#333}.measured{stroke-width:2.5;fill:none}.theory{stroke-width:2;stroke-dasharray:7 5;fill:none}</style>",
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="{width / 2}" y="32" text-anchor="middle" font-size="21">해시 테이블 탐색 비교 횟수와 적재율</text>',
    ]

    for tick in range(0, 9):
        load = tick * 0.5
        x = left + load / max_load * plot_width
        svg.append(f'<line class="grid" x1="{x:.1f}" y1="{top}" x2="{x:.1f}" y2="{top + plot_height}"/>')
        svg.append(f'<text x="{x:.1f}" y="{top + plot_height + 24}" text-anchor="middle" font-size="12">{load:g}</text>')

    for tick in range(10):
        probes = tick * 0.5
        y = top + (max_probes - probes) / max_probes * plot_height
        svg.append(f'<line class="grid" x1="{left}" y1="{y:.1f}" x2="{left + plot_width}" y2="{y:.1f}"/>')
        svg.append(f'<text x="{left - 12}" y="{y + 4:.1f}" text-anchor="end" font-size="12">{probes:g}</text>')

    svg.extend(
        (
            f'<line class="axis" x1="{left}" y1="{top + plot_height}" x2="{left + plot_width}" y2="{top + plot_height}"/>',
            f'<line class="axis" x1="{left}" y1="{top}" x2="{left}" y2="{top + plot_height}"/>',
            f'<text x="{left + plot_width / 2}" y="{height - 30}" text-anchor="middle" font-size="15">적재율 α</text>',
            f'<text x="22" y="{top + plot_height / 2}" transform="rotate(-90 22 {top + plot_height / 2})" text-anchor="middle" font-size="15">평균 비교 노드 수</text>',
        )
    )

    for key, label, color, dashed in series:
        points = [point(row, key) for row in rows]
        point_string = " ".join(f"{x:.1f},{y:.1f}" for x, y in points)
        css_class = "theory" if dashed else "measured"
        svg.append(f'<polyline class="{css_class}" stroke="{color}" points="{point_string}"/>')
        for x, y in points:
            svg.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="2.5" fill="{color}"/>')

    legend_x, legend_y = left + 18, top + 16
    for index, (_, label, color, dashed) in enumerate(series):
        y = legend_y + index * 23
        dash = ' stroke-dasharray="7 5"' if dashed else ""
        svg.append(f'<line x1="{legend_x}" y1="{y}" x2="{legend_x + 32}" y2="{y}" stroke="{color}" stroke-width="2.5"{dash}/>')
        svg.append(f'<text x="{legend_x + 40}" y="{y + 5}" font-size="13">{label}</text>')

    svg.append("</svg>")
    path.write_text("\n".join(svg) + "\n", encoding="utf-8")


def print_table(rows):
    headings = (
        ("α", "target_load_factor"),
        ("n", "items"),
        ("성공 측정", "successful_measured"),
        ("성공 이론", "successful_theoretical"),
        ("실패 측정", "failed_measured"),
        ("실패 이론", "failed_theoretical"),
    )
    widths = (6, 7, 11, 11, 11, 11)
    print(" ".join(title.rjust(width) for (title, _), width in zip(headings, widths)))
    for row in rows:
        values = (
            f'{row["target_load_factor"]:.2f}',
            str(row["items"]),
            f'{row["successful_measured"]:.3f}',
            f'{row["successful_theoretical"]:.3f}',
            f'{row["failed_measured"]:.3f}',
            f'{row["failed_theoretical"]:.3f}',
        )
        print(" ".join(value.rjust(width) for value, width in zip(values, widths)))


def main():
    generator = random.Random(RANDOM_SEED)
    rows = [measure_load(step / 4, generator) for step in LOAD_STEPS]
    experiment_directory = Path(__file__).resolve().parent
    write_csv(rows, experiment_directory / "results.csv")
    write_svg(rows, experiment_directory / "probe_experiment.svg")
    print_table(rows)
    print(f"\n저장: {experiment_directory / 'results.csv'}")
    print(f"저장: {experiment_directory / 'probe_experiment.svg'}")


if __name__ == "__main__":
    main()
