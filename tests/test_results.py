import json
import tempfile
import unittest
from pathlib import Path
from tools.summarize_results import percentile, summarize


class ResultTests(unittest.TestCase):
    def test_interpolated_percentile_and_missing_samples(self):
        self.assertEqual(percentile([10, 30, 20, 40], 50), 25)
        self.assertAlmostEqual(percentile([10, 30, 20, 40], 95), 38.5)
        self.assertIsNone(percentile([], 95))

    def test_export_counts_failures_and_elapsed_request_window(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'run.json'
            rows = [{'type': 'Metric', 'metric': 'http_reqs', 'data': {}}]
            for time, duration, failed in [('2025-01-01T00:00:00Z', 100, 0), ('2025-01-01T00:00:02Z', 300, 1)]:
                for metric, value in [('http_reqs', 1), ('http_req_duration', duration), ('http_req_failed', failed)]:
                    rows.append({'type': 'Point', 'metric': metric, 'data': {'time': time, 'value': value}})
            path.write_text('\n'.join(json.dumps(row) for row in rows))
            result = summarize(path)
            self.assertEqual(result['requests'], 2)
            self.assertEqual(result['p50_ms'], 200)
            self.assertEqual(result['failure_percent'], 50)
            self.assertEqual(result['observed_requests_per_second'], 1)

    def test_bad_export_names_the_file_and_line(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / 'bad.json'
            path.write_text('{}\nnot json')
            with self.assertRaisesRegex(ValueError, 'bad.json:2'):
                summarize(path)


if __name__ == '__main__':
    unittest.main()
