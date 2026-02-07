import argparse

torch = None


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mb", type=int, default=256)
    parser.add_argument("--iters", type=int, default=10)
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--mock", action="store_true")
    args = parser.parse_args()

    if args.mock:
        print(f"[mock] transfer {args.mb}MB x{args.iters} on {args.device}")
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
    gpu_tensor = torch.randn(num_floats, device=device)
    for _ in range(args.iters):
        cpu_tensor = gpu_tensor.cpu()
        _ = cpu_tensor.sum().item()
    print("Transfer done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
