# Cloud ML Inference Benchmark

A comparative study of ResNet-18 inference deployments across Google Cloud Run, Google Kubernetes Engine, and a hybrid architecture. A Rust coordinator routes requests to a Python gRPC inference service; a background training service updates model artifacts.

Developed collaboratively for SFU CMPT 756. The repository retains the team’s original Git history and upstream relationship. Contribution examples include [coordinator tracing](https://github.com/Parikshit97/cloud-ml-inference-benchmark/commit/7ab8990), [Python service instrumentation](https://github.com/Parikshit97/cloud-ml-inference-benchmark/commit/f229057), and [GKE tracing deployment](https://github.com/Parikshit97/cloud-ml-inference-benchmark/commit/92a0f7f).

## Architecture

| Component | Responsibility |
|---|---|
| `coordinator/` | Rust HTTP API, gRPC routing, training uploads, OpenTelemetry |
| `ml-grpc-service/` | Python model inference and model reloads |
| `training-service/` | Background training and model artifact updates |
| `infra/inference/` | Terraform and Kubernetes configuration for the deployment variants |
| `cloudbuild/` | Container build and deployment pipelines |
| `k6/` | Load scenarios and recorded request metrics |
| `frontend/` | React demonstration interface |

## Recorded results

The following table is calculated from the committed k6 JSON-lines exports. It is historical evidence, not a new cloud benchmark. Durations are client-side HTTP request durations in milliseconds; failure percentages come from `http_req_failed` samples.

| Recorded run | Requests | p50 ms | p95 ms | p99 ms | Failed % |
|---|---:|---:|---:|---:|---:|
| baseline_cloudrun | 32 | 430.88 | 3682.62 | 7714.83 | 0.00 |
| baseline_gke | 44 | 315.15 | 482.85 | 680.91 | 0.00 |
| baseline_hybrid | 41 | 395.37 | 589.26 | 1549.00 | 0.00 |
| burst_cloudrun | 2301 | 323.86 | 2087.33 | 15445.24 | 0.00 |
| burst_gke | 2395 | 349.02 | 867.48 | 1261.18 | 0.00 |
| bust_hybrid | 2394 | 380.95 | 804.23 | 1003.85 | 0.00 |
| cold_start_cloudrun | 1 | 30351.22 | 30351.22 | 30351.22 | 0.00 |
| cold_start_gke | 1 | 842.36 | 842.36 | 842.36 | 0.00 |
| cold_start_hybrid | 1 | 843.99 | 843.99 | 843.99 | 0.00 |
| gradual_cloudrun | 1234 | 425.34 | 5244.14 | 20608.55 | 0.00 |
| gradual_gke | 1356 | 350.91 | 960.49 | 1446.75 | 0.52 |
| gradual_hybrid | 1284 | 389.89 | 1216.35 | 1990.55 | 0.00 |
| model_swap_gke | 1045 | 294.10 | 416.22 | 643.73 | 0.00 |


The cold-start exports contain **one request each**. Their values are observations, not estimates of a latency distribution. File names identify the recorded runs; the exports do not establish that hardware, payloads, scaling settings, and software revisions were identical. The `bust_hybrid` filename is retained from the original artifact. Cost, resource utilization, and confidence intervals are not available in these exports.

## Reproduce the result summary locally

Python 3.10 or later is sufficient. No cloud account or third-party Python packages are required for this step.

```sh
python3 tools/summarize_results.py k6/results
python3 tools/summarize_results.py k6/results --format json
python3 -m unittest discover -s tests -v
```

The summary command validates JSON records and reports p50/p95/p99, request counts, and failures. JSON output also includes a request rate over the observed request timestamp window; this is not the configured k6 arrival rate.

## Run the services

Service setup is documented in [coordinator/README.md](coordinator/README.md), [infra/inference/README.md](infra/inference/README.md), and [k6/README.md](k6/README.md). The inference and training services require their configured GCS model artifacts and cloud credentials. Do not place credentials or Terraform state in Git.

For the frontend:

```sh
cd frontend
npm ci
npm run build
```

## Repeat the benchmark

Use the same model, input images, load script, and workload parameters for each architecture. Record the Git revision, region, instance limits, cold/warm state, and run start/end times. Repeat independent trials before drawing comparative conclusions. Collect billing and monitoring data separately when reporting cost or utilization.

The local checks in this update validate result processing. They do not provision infrastructure, verify the historical live demo, or rerun cloud inference/training.
