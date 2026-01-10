import argparse
import time

try:
    import torch
except Exception:
    torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--gb", type=float, default=1.0)
    parser.add_argument("--sleep", type=int, default=600)
    args = parser.parse_args()

    if torch is None:
        print("PyTorch not installed. Exiting.")
        return 2

    if not torch.cuda.is_available():
        print("CUDA not available. Exiting.")
        return 3

    device = torch.device("cuda")
    num_bytes = int(args.gb * 1024 * 1024 * 1024)
    num_floats = num_bytes // 4
    print(f"Holding {args.gb} GB on {device} for {args.sleep}s")
    tensor = torch.empty(num_floats, dtype=torch.float32, device=device)
    tensor.fill_(1.0)
    time.sleep(args.sleep)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
