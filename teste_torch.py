import torch

print(f"PyTorch version: {torch.__version__}")
print(f"CUDA disponível: {torch.cuda.is_available()}")

if torch.cuda.is_available():
    print(f"Nome da GPU: {torch.cuda.get_device_name(0)}")
    # Criar um tensor e mover para a GPU
    tensor = torch.randn(1000, 1000).to("cuda")
    print(f"Tensor está no dispositivo: {tensor.device}")
else:
    print("Nenhuma GPU CUDA disponível.")
