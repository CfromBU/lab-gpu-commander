import argparse
import time

torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=20)
    parser.add_argument("--mb", type=int, default=128)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if args.mock:
        print(f"[mock] spin {args.seconds}s with {args.mb}MB on {args.device}")
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
    num_bytes = int(args.mb * 1024 * 1024)
    num_floats = max(1, num_bytes // 4)
    tensor = torch.randn(num_floats, device=device)
    end_time = time.time() + args.seconds
    while time.time() < end_time:
        tensor = tensor * 1.0001 + 0.0001
        if args.device == "cuda":
            torch.cuda.synchronize()
    print("Spin done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
