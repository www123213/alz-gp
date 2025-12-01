import torch
import torchvision.models as models
from ultralytics import YOLO
import time
import numpy as np

# 1. 检查设备
device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
print(f"正在使用的测试设备: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

if device.type == 'cpu':
    print("正在使用CPU测试，请检查CUDA环境。")

# 2. 准备模型
print("正在加载模型...")
# ResNet50
resnet = models.resnet50(weights=models.ResNet50_Weights.IMAGENET1K_V1).to(device).eval()
# DenseNet121
densenet = models.densenet121(weights=models.DenseNet121_Weights.IMAGENET1K_V1).to(device).eval()
# YOLOv8
yolo_s = YOLO('yolov8s-cls.pt')
yolo_n = YOLO('yolov8n-cls.pt')

# 3. 创建虚拟数据 (模拟一张 MRI 图像 640x640)
dummy_input = torch.randn(1, 3, 640, 640).to(device)

def benchmark_torch(model, name, runs=100):
    # 预热
    with torch.no_grad():
        for _ in range(10):
            model(dummy_input)
    
    # 测试
    times = []
    with torch.no_grad():
        for _ in range(runs):
            start = time.time()
            model(dummy_input)
            torch.cuda.synchronize() if device.type == 'cuda' else None
            end = time.time()
            times.append((end - start) * 1000) # 转换为毫秒
    
    avg_time = np.mean(times)
    print(f"{name} 平均推理速度: {avg_time:.2f} ms/张")

def benchmark_yolo(model, name, runs=100):
    # YOLO 内部自带预热
    # 这里的 verbose=False 关掉打印，只测速度
    results = model.predict(source=np.zeros((640, 640, 3), dtype='uint8'), device=0, verbose=False)
    
    times = []
    for _ in range(runs):
        start = time.time()
        model.predict(source=np.zeros((640, 640, 3), dtype='uint8'), device=0, verbose=False)
        times.append((time.time() - start) * 1000)
        
    avg_time = np.mean(times)
    print(f"{name} 平均推理速度: {avg_time:.2f} ms/张")

print("-" * 30)
benchmark_torch(resnet, "ResNet50")
benchmark_torch(densenet, "DenseNet121")
print("-" * 30)
# YOLO这里我们测纯推理，不包含预处理耗时，为了和其他模型公平对比
benchmark_yolo(yolo_s, "YOLOv8s-cls")
benchmark_yolo(yolo_n, "YOLOv8n-cls")
print("-" * 30)