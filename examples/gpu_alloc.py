import argparse
import time

torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gb", type=float, default=1.0)
    parser.add_argument("--sleep", type=int, default=30)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if args.mock:
        print(f"[mock] alloc {args.gb} GB on {args.device}")
        return 0

    try:
        import torch as torch_module
    except Exception:
        torch_module = None
    global torch
    torch = torch_module

    if torch is None:
        print("PyTorch not installed. Exiting.")
        return 2

    if args.device == "cuda" and not torch.cuda.is_available():
        print("CUDA not available. Exiting.")
        return 3

    device = torch.device(args.device)
    num_bytes = int(args.gb * 1024 * 1024 * 1024)
    num_floats = num_bytes // 4
    print(f"Allocating {args.gb} GB on {device}...")
    tensor = torch.empty(num_floats, dtype=torch.float32, device=device)
    tensor.fill_(1.0)
    print("Allocation ok. Sleeping...")
    time.sleep(args.sleep)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
