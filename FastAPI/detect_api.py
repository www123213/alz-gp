from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import JSONResponse 
from sqlmodel import Session
from database import get_session
from history_models import DetectionRecord
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os
import shutil
import tempfile  # 用于临时保存上传的模型
import time
import uuid

router = APIRouter()

@router.post("/predict")
async def predict(
    file: UploadFile = File(...),   # 上传的MRI图像
    model_file: UploadFile = File(...),  # 上传的模型文件
    
    patient_name: str = Form(None),
    patient_gender: str = Form(None),
    patient_age: int = Form(None),
    medical_id: str = Form(None),
    
    name: str = Form(None),
    gender: str = Form(None),
    age: int = Form(None),
    id: str = Form(None),
    session: Session = Depends(get_session)
):
    # 保存上传的MRI图像
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)

    # 生成唯一文件名（防重名覆盖）
    filename = file.filename or f"{int(time.time())}.jpg"
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"
    img_abs_path = os.path.join(upload_dir, unique_name)
    image_rel_path = f"uploads/{unique_name}"  # 前端可访问的相对路径

    try:
        with open(img_abs_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"error": f"保存图片失败: {str(e)}"}, status_code=500)

    # 临时保存并加载模型文件
    current_model = None
    temp_model_path = None
    try:
        # 临时保存模型文件（推理后自动删除）
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as temp_model:
            shutil.copyfileobj(model_file.file, temp_model)
            temp_model_path = temp_model.name  # 记录临时文件路径
        # 加载YOLO模型
        current_model = YOLO(temp_model_path)
    except Exception as e:
        # 模型加载失败时清理临时文件
        if temp_model_path and os.path.exists(temp_model_path):
            os.unlink(temp_model_path)
        return JSONResponse({"error": f"模型加载失败: {str(e)}"}, status_code=500)

    # 模型推理
    try:
        image = Image.open(img_abs_path).convert("RGB")
        results = current_model(image)
    except Exception as e:
        # 推理失败时清理临时文件
        if temp_model_path and os.path.exists(temp_model_path):
            os.unlink(temp_model_path)
        return JSONResponse({"error": f"推理过程失败: {str(e)}"}, status_code=500)

    # 推理完成后删除临时模型文件
    if temp_model_path and os.path.exists(temp_model_path):
        os.unlink(temp_model_path)

    # 解析推理结果
    main_class = None
    main_confidence = None
    all_results_list = []
    bboxes_list = []  # 新增：存储边界框信息（如果是检测任务）

    # 分类任务
    if results and len(results) > 0 and hasattr(results[0], "probs"):
        probs = results[0].probs.data.cpu().numpy()
        sorted_indices = np.argsort(probs)[::-1]  # 按置信度降序排列
        top_idx = int(sorted_indices[0])
        main_confidence = float(probs[top_idx])
        class_names = list(current_model.model.names.values())
        main_class = class_names[top_idx]
        # 整理所有结果（取前5）
        all_results_list = [
            {"class": class_names[int(idx)], "confidence": float(probs[int(idx)])}
            for idx in sorted_indices[:5]
        ]

    # 检测任务
    elif results and len(results) > 0 and hasattr(results[0], "boxes"):
        boxes = results[0].boxes
        if len(boxes) > 0:
            # 提取主要结果（置信度最高的）
            main_confidence = boxes.conf[0].item()
            cls_idx = boxes.cls[0].item()
            class_names = list(current_model.model.names.values())
            main_class = class_names[int(cls_idx)]
            
            # 整理所有结果
            all_results_list = [
                {"class": class_names[int(c)], "confidence": float(conf)}
                for c, conf in zip(boxes.cls, boxes.conf)
            ]
            
            # 提取边界框信息
            bboxes = boxes.xyxy.cpu().numpy()  # 转换为numpy数组
            bboxes_list = [
                {
                    "x1": float(bbox[0]),
                    "y1": float(bbox[1]),
                    "x2": float(bbox[2]),
                    "y2": float(bbox[3])
                }
                for bbox in bboxes
            ]

    # 推理结果无效的情况
    else:
        return JSONResponse({"error": "推理失败或任务类型不匹配"}, status_code=500)

    # 数据库存储
    try:
        # 创建数据库记录
        final_patient_name = patient_name if patient_name is not None else name
        final_patient_gender = patient_gender if patient_gender is not None else gender
        final_patient_age = patient_age if patient_age is not None else age
        final_medical_id = medical_id if medical_id is not None else id

        rec = DetectionRecord(
            patient_name=final_patient_name,
            patient_gender=final_patient_gender,
            patient_age=final_patient_age,
            medical_id=final_medical_id,
            label=main_class,
            confidence=main_confidence,
            all_results=all_results_list,
            bboxes=bboxes_list,  # 存储边界框信息
            image_path=image_rel_path  # 存储前端可访问的图片路径
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
    except Exception as e:
        # 数据库存储失败时，仍返回推理结果
        return JSONResponse({
            "error": f"数据库存储失败: {str(e)}",
            "result": {
                "main_class": main_class,
                "confidence": main_confidence,
                "all_results": all_results_list,
                "image_path": image_rel_path
            }
        }, status_code=500)

    # 返回最终结果
    return JSONResponse({
        "saved_id": rec.id,  # 数据库记录ID（用于历史查询）
        "medical_id": final_medical_id,
        "main_class": main_class,
        "confidence": main_confidence,
        "all_results": all_results_list,
        "bboxes": bboxes_list,  # 边界框信息
        "image_path": image_rel_path  # 前端可访问的图片路径
    })
