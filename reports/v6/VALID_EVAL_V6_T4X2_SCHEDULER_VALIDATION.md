# ValidEval V6 T4×2 Scheduler Validation

Gate: `T4X2_SCHEDULER_READY`

The scheduler deterministically uses longest-estimated-job-first assignment over two isolated
processes. Worker 0 receives physical GPU 0 and worker 1 physical GPU 1 through per-process
`CUDA_VISIBLE_DEVICES`; each process addresses its isolated device as `cuda:0`. Outputs and status
files live below worker-specific directories, preventing concurrent collisions.

Validated behavior includes deterministic balancing, two healthy workers, process isolation,
single-device configuration, duplicate task rejection, crash classification, OOM fallback,
bounded retry exhaustion, stale heartbeat detection, atomic status, exact-config resume, completed
job reuse, config mismatch refusal, deterministic merge, and contradictory duplicate rejection.
Worker state records worker/GPU/current job/start/heartbeat/last item/retry/memory failure/exit
state.

Single-GPU fallback is disabled in the frozen S1 configs. A machine with fewer than two visible
GPUs receives `INSUFFICIENT_GPU` before model download.
