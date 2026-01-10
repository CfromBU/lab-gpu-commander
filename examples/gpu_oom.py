import argparse
import sys

torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-gb", type=float, default=1.0)
    parser.add_argument("--step-gb", type=float, default=1.0)
    parser.add_argument("--max-gb", type=float, default=64.0)
    parser.add_argument("--mock-oom", action="store_true")
    args = parser.parse_args()

    if args.mock_oom:
        print("RuntimeError: CUDA out of memory. Tried to allocate 2.0 GiB", file=sys.stderr)
        return 1

    try:
        import torch as torch_module
    except Exception:
        torch_module = None
    global torch
    torch = torch_module

    if torch is None:
        print("PyTorch not installed. Exiting.")
        return 2

    if not torch.cuda.is_available():
        print("CUDA not available. Exiting.")
        return 3

    device = torch.device("cuda")
    gb = args.start_gb
    tensors = []
    while gb <= args.max_gb:
        num_bytes = int(gb * 1024 * 1024 * 1024)
        num_floats = num_bytes // 4
        try:
            print(f"Allocating {gb} GB...")
            tensors.append(torch.empty(num_floats, dtype=torch.float32, device=device))
            gb += args.step_gb
        except RuntimeError as exc:
            print(str(exc), file=sys.stderr)
            return 1
    print("Reached max without OOM.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
