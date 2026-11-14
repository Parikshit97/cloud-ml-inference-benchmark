"""Summarize committed k6 JSON-lines exports without contacting cloud services."""
import argparse
import json
import math
from datetime import datetime
from pathlib import Path


def percentile(values, percent):
    if not values:
        return None
    ordered = sorted(values)
    index = (len(ordered) - 1) * percent / 100
    lower, upper = math.floor(index), math.ceil(index)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def summarize(path):
    durations, failures, timestamps = [], [], []
    requests = 0
    with path.open() as source:
        for number, line in enumerate(source, 1):
            if not line.strip():
                continue
            try:
                record = json.loads(line)
                if record.get('type') != 'Point':
                    continue
                metric, data = record['metric'], record['data']
                value = float(data['value'])
                if not math.isfinite(value):
                    raise ValueError('non-finite metric value')
                if metric == 'http_req_duration':
                    durations.append(value)
                elif metric == 'http_req_failed':
                    failures.append(value)
                elif metric == 'http_reqs':
                    requests += value
                    timestamps.append(datetime.fromisoformat(data['time'].replace('Z', '+00:00')))
            except (ValueError, KeyError, TypeError) as error:
                raise ValueError(f'{path}:{number}: {error}') from error
    elapsed = (max(timestamps) - min(timestamps)).total_seconds() if len(timestamps) > 1 else 0
    return {
        'run': path.stem, 'requests': int(requests), 'samples': len(durations),
        'p50_ms': percentile(durations, 50), 'p95_ms': percentile(durations, 95),
        'p99_ms': percentile(durations, 99),
        'failure_percent': 100 * sum(failures) / len(failures) if failures else None,
        'observed_requests_per_second': requests / elapsed if elapsed > 0 else None,
    }


def markdown(rows):
    lines = ['| Recorded run | Requests | p50 ms | p95 ms | p99 ms | Failed % |',
             '|---|---:|---:|---:|---:|---:|']
    for row in rows:
        def show(key):
            return 'N/A' if row[key] is None else f'{row[key]:.2f}'
        lines.append(f"| {row['run']} | {row['requests']} | {show('p50_ms')} | {show('p95_ms')} | {show('p99_ms')} | {show('failure_percent')} |")
    return '\n'.join(lines)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('directory', type=Path)
    parser.add_argument('--format', choices=['json', 'markdown'], default='markdown')
    args = parser.parse_args()
    paths = sorted(args.directory.glob('*.json'))
    if not paths:
        parser.error('directory contains no JSON exports')
    rows = [summarize(path) for path in paths]
    print(json.dumps(rows, indent=2) if args.format == 'json' else markdown(rows))
