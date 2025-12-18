from fastapi import APIRouter, UploadFile, File, Depends, Form
from fastapi.responses import JSONResponse 
from sqlmodel import Session
from database import get_session
from history_models import PredictionRecord
from ultralytics import YOLO
from PIL import Image
import numpy as np
import os
import shutil
import tempfile
import time
import uuid

# [新增] 引入 Grad-CAM 和图像处理库
import cv2
import torch
from pytorch_grad_cam import GradCAM
from pytorch_grad_cam.utils.image import show_cam_on_image
from pytorch_grad_cam.utils.model_targets import ClassifierOutputTarget

router = APIRouter(tags=["Prediction"])

@router.post("/predict")
async def predict(
    file: UploadFile = File(...),   # 上传的MRI图像
    model_file: UploadFile = File(...),  # 上传的分类模型（.pt）
    patient_name: str = Form(None),
    patient_gender: str = Form(None),
    patient_age: int = Form(None),
    medical_id: str = Form(None),
    session: Session = Depends(get_session)
):
    # 1. 保存上传图像
    upload_dir = os.path.join(os.path.dirname(__file__), "uploads")
    os.makedirs(upload_dir, exist_ok=True)
    filename = file.filename or f"{int(time.time())}.jpg"
    unique_name = f"{int(time.time())}_{uuid.uuid4().hex}_{filename}"
    img_abs_path = os.path.join(upload_dir, unique_name)
    image_rel_path = f"uploads/{unique_name}"

    try:
        with open(img_abs_path, "wb") as f:
            shutil.copyfileobj(file.file, f)
    except Exception as e:
        return JSONResponse({"error": f"保存图片失败: {str(e)}"}, status_code=500)

    # 2. 临时保存&加载模型，并进行推理
    current_model = None
    temp_model_path = None
    results = None
    heatmap_rel_path = None # 初始化热力图路径
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as temp_model:
            shutil.copyfileobj(model_file.file, temp_model)
            temp_model_path = temp_model.name
        
        # 加载 YOLO 模型
        current_model = YOLO(temp_model_path)

        # 读取图像
        image_pil = Image.open(img_abs_path).convert("RGB")
        image_np = np.array(image_pil)
        
        # [关键调整] 先进行推理！这会自动把模型移动到 GPU (如果可用)
        results = current_model(image_np)

        # --- [新增] Grad-CAM 热力图生成逻辑 (移到推理之后) ---
        try:
            # 只有当推理成功且有结果时才生成
            if results and len(results) > 0 and hasattr(results[0], "probs"):
                # 1. 确定目标层：Backbone 的最后一层
                target_layers = [current_model.model.model[-3]]

                # 2. 数据预处理
                target_size = (640, 640) 
                img_resized = cv2.resize(image_np, target_size)
                rgb_img_float = np.float32(img_resized) / 255.0
                input_tensor = torch.from_numpy(rgb_img_float).permute(2, 0, 1).unsqueeze(0)

                # ================= [修复的核心] =================
                # 此时模型肯定已经在正确的设备上了 (因为刚跑完 inference)
                device = next(current_model.model.parameters()).device
                input_tensor = input_tensor.to(device)
                # ===============================================
                input_tensor.requires_grad_(True)
                # 3. 初始化 GradCAM
                cam = GradCAM(model=current_model.model, target_layers=target_layers)

                # 4. 确定目标类别
                top_class_idx = results[0].probs.top1
                targets = [ClassifierOutputTarget(top_class_idx)]

                # 5. 生成热力图
                grayscale_cam = cam(input_tensor=input_tensor, targets=targets)
                
                # 6. 叠加与保存
                visualization = show_cam_on_image(rgb_img_float, grayscale_cam[0, :], use_rgb=True)
                
                heatmap_filename = f"heatmap_{unique_name}"
                heatmap_abs_path = os.path.join(upload_dir, heatmap_filename)
                
                # OpenCV 需要 BGR
                cv2.imwrite(heatmap_abs_path, cv2.cvtColor(visualization, cv2.COLOR_RGB2BGR))
                heatmap_rel_path = f"uploads/{heatmap_filename}"
                
        except Exception as cam_err:
            print(f"Grad-CAM 生成失败: {cam_err}")
            # 打印完整的错误堆栈，方便调试
            import traceback
            traceback.print_exc()
        # --- [新增] Grad-CAM 逻辑结束 ---

    except Exception as e:
        return JSONResponse({"error": f"推理过程失败: {str(e)}"}, status_code=500)
    finally:
        # 清理临时模型文件
        if temp_model_path and os.path.exists(temp_model_path):
            try:
                os.unlink(temp_model_path)
            except Exception as e:
                print(f"警告：临时模型文件删除失败: {str(e)}")

    # 3. 解析分类结果
    main_class = None
    main_confidence = None
    all_results_list = []
    class_scores_raw = []
    class_probs = []
    
    class_names = list(current_model.model.names.values())

    if results and len(results) > 0 and hasattr(results[0], "probs") and results[0].probs is not None:
        probs = results[0].probs.data.cpu().numpy()
        sorted_indices = np.argsort(probs)[::-1]
        
        all_results_list = [
            {"class": class_names[int(idx)], "confidence": float(probs[int(idx)])}
            for idx in sorted_indices
        ]
        class_scores_raw = [float(probs[int(idx)]) for idx in sorted_indices]
        class_probs = [float(probs[int(idx)]) for idx in sorted_indices]
    else:
        return JSONResponse({"error": "模型无有效分类输出"}, status_code=500)

    if all_results_list:
        main_result = all_results_list[0]
        main_class = main_result["class"]
        main_confidence = main_result["confidence"]
    else:
        return JSONResponse({"error": "未检测到任何类别结果"}, status_code=500)

    # 4. 数据库存储
    try:
        rec = PredictionRecord(
            patient_name=patient_name,
            patient_gender=patient_gender,
            patient_age=patient_age,
            medical_id=medical_id,
            label=main_class,
            model_name=model_file.filename,
            confidence=main_confidence,
            all_results=all_results_list,
            image_path=image_rel_path
        )
        session.add(rec)
        session.commit()
        session.refresh(rec)
    except Exception as e:
        return JSONResponse({
            "error": f"数据库存储失败: {str(e)}",
            "result": {
                "main_class": main_class,
                "confidence": main_confidence,
                "all_results": all_results_list,
                "image_path": image_rel_path,
                "heatmap_path": heatmap_rel_path
            }
        }, status_code=500)

    # 5. 返回结果
    return JSONResponse({
        "saved_id": rec.id,
        "medical_id": medical_id,
        "main_class": main_class,
        "confidence": main_confidence,
        "all_results": all_results_list,
        "class_scores_raw": class_scores_raw,
        "class_probs": class_probs,
        "image_path": image_rel_path,
        "heatmap_path": heatmap_rel_path, 
    })