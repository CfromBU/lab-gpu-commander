import argparse
import time

torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--size", type=int, default=2048)
    parser.add_argument("--iters", type=int, default=5)
    parser.add_argument("--sleep", type=int, default=5)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if args.mock:
        print(f"[mock] matmul size={args.size} iters={args.iters} on {args.device}")
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
    a = torch.randn(args.size, args.size, device=device)
    b = torch.randn(args.size, args.size, device=device)
    for _ in range(args.iters):
        c = a @ b
        if args.device == "cuda":
            torch.cuda.synchronize()
        _ = c.sum().item()
    print("Matmul done. Sleeping...")
    time.sleep(args.sleep)
    print("Done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
