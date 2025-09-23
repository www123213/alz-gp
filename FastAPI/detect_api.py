from fastapi import APIRouter, UploadFile, File
from fastapi.responses import JSONResponse 
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os
import shutil
import tempfile  # 用于临时保存上传的模型

router = APIRouter()

@router.post("/predict")
async def predict(
    file: UploadFile = File(...),   # 上传的MRI图像
    model_file: UploadFile = File(...)  # 上传的模型文件
):
    # 保存上传的MRI图像
    upload_dir = "uploads"
    os.makedirs(upload_dir, exist_ok=True)
    img_path = os.path.join(upload_dir, file.filename)
    with open(img_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    # 临时保存并加载上传的模型文件
    current_model = None
    temp_model_path = None
    try:
        # 临时保存模型文件（后缀固定为.pt，确保YOLO能识别）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as temp_model:
            shutil.copyfileobj(model_file.file, temp_model)
            temp_model_path = temp_model.name  # 记录临时文件路径，用于后续清理
        # 加载模型
        current_model = YOLO(temp_model_path)
    except Exception as e:
        # 模型加载失败时，清理临时文件并返回错误
        if temp_model_path and os.path.exists(temp_model_path):
            os.unlink(temp_model_path)
        return JSONResponse({"error": f"模型加载失败: {str(e)}"}, status_code=500)

    # 模型推理
    image = Image.open(img_path).convert("RGB")
    results = current_model(image)

    # 清理临时模型文件（推理完成后删除）
    if temp_model_path and os.path.exists(temp_model_path):
        os.unlink(temp_model_path)

    # 根据任务类型解析结果
    # 分类任务（从 probs 获取结果）
    if results and len(results) > 0 and hasattr(results[0], "probs"):
        probs = results[0].probs.data.cpu().numpy()
        sorted_indices = np.argsort(probs)[::-1]  # 按置信度降序排列
        top_idx = int(sorted_indices[0])
        top_conf = float(probs[top_idx])
        class_names = list(current_model.model.names.values())
        return JSONResponse({
            "main_class": class_names[top_idx],
            "confidence": top_conf,
            "all_results": [
                {"class": class_names[int(idx)], "confidence": float(probs[int(idx)])}
                for idx in sorted_indices[:5]
            ]
        })
    # 检测任务（从 boxes 获取结果）
    elif results and len(results) > 0 and hasattr(results[0], "boxes"):
        boxes = results[0].boxes
        if len(boxes) > 0:
            conf = boxes.conf[0].item()
            cls_idx = boxes.cls[0].item()
            class_names = list(current_model.model.names.values())
            class_name = class_names[int(cls_idx)]
            return JSONResponse({
                "main_class": class_name,
                "confidence": conf,
                "all_results": [
                    {"class": class_names[int(c)], "confidence": float(conf)}
                    for c, conf in zip(boxes.cls, boxes.conf)
                ]
            })
    else:
        return JSONResponse({"error": "推理失败或任务类型不匹配"}, status_code=500)
