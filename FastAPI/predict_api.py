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
import tempfile
import time
import uuid

router = APIRouter(tags=["prediction"])

@router.post("/predict")
async def predict(
    file: UploadFile = File(...),   # 上传的MRI图像
    model_file: UploadFile = File(...),  # 上传的模型（分类.cls.pt / 检测.pt）
    patient_name: str = Form(None),
    patient_gender: str = Form(None),
    patient_age: int = Form(None),
    medical_id: str = Form(None),
    session: Session = Depends(get_session)
):
    # 保存上传图像（逻辑不变）
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

    # 临时保存&加载模型（逻辑不变）
    current_model = None
    temp_model_path = None
    results = None
    # 【新增】初始化分类/检测共用变量，避免未定义报错
    class_scores_raw = None
    class_probs = None
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pt") as temp_model:
            shutil.copyfileobj(model_file.file, temp_model)
            temp_model_path = temp_model.name
        current_model = YOLO(temp_model_path)

        # 读取图像（逻辑不变）
        image = Image.open(img_abs_path).convert("RGB")
        image_np = np.array(image)
        results = current_model(image_np)

    except Exception as e:
        return JSONResponse({"error": f"推理过程失败: {str(e)}"}, status_code=500)
    finally:
        if temp_model_path and os.path.exists(temp_model_path):
            try:
                os.unlink(temp_model_path)
            except Exception as e:
                print(f"警告：临时模型文件删除失败: {str(e)}")

    # 解析结果：统一提取“多类别概率”
    main_class = None
    main_confidence = None
    all_results_list = []
    bboxes_list = []
    class_names = list(current_model.model.names.values())  # 所有类别名

    # 情况1：分类模型（有 probs 且非 None）
    if results and len(results) > 0 and hasattr(results[0], "probs") and results[0].probs is not None:
        probs = results[0].probs.data.cpu().numpy()
        sorted_indices = np.argsort(probs)[::-1]  # 按置信度降序排列
        all_results_list = [
            {"class": class_names[int(idx)], "confidence": float(probs[int(idx)])}
            for idx in sorted_indices
        ]
        # 【新增】分类任务的原始分数=概率，归一化概率=概率（无需额外计算）
        class_scores_raw = [float(probs[int(idx)]) for idx in sorted_indices]
        class_probs = [float(probs[int(idx)]) for idx in sorted_indices]

    # 情况2：检测模型（提取所有检测框的类别+置信度）
    elif results and len(results) > 0 and hasattr(results[0], "boxes") and results[0].boxes is not None:
        boxes = results[0].boxes
        det_results = []
        xyxy = boxes.xyxy.cpu().numpy() if hasattr(boxes.xyxy, 'cpu') else np.array(boxes.xyxy)
        confs = boxes.conf.data.cpu().numpy() if hasattr(boxes.conf, 'data') else np.array(boxes.conf)
        clss = boxes.cls.data.cpu().numpy() if hasattr(boxes.cls, 'data') else np.array(boxes.cls)

        for (xy, c, conf) in zip(xyxy, clss, confs):
            cls_idx = int(c)
            conf_val = float(conf)
            det_results.append({
                "class": class_names[cls_idx],
                "confidence": conf_val,
            })
            bboxes_list.append({
                "xyxy": [float(xy[0]), float(xy[1]), float(xy[2]), float(xy[3])],
                "class": class_names[cls_idx],
                "confidence": conf_val,
            })

        # 检测任务：按类别取最大置信度作为原始分数，再归一化
        class_scores = {name: 0.0 for name in class_names}
        for d in det_results:
            cname = d["class"]
            class_scores[cname] = max(class_scores.get(cname, 0.0), d["confidence"])
        class_scores_raw = [float(class_scores[name]) for name in class_names]
        total = sum(class_scores_raw)
        class_probs = [score/total if total>0 else 0.0 for score in class_scores_raw]
        # 检测任务的all_results_list按类别顺序排列
        all_results_list = [
            {"class": class_names[i], "confidence": class_probs[i]}
            for i in range(len(class_names))
        ]

    else:
        return JSONResponse({"error": "模型无有效输出（请确认是分类或检测模型）"}, status_code=500)

    # 提取“主要结果”（置信度最高的类别）
    if all_results_list:
        main_result = max(all_results_list, key=lambda x: x["confidence"])
        main_class = main_result["class"]
        main_confidence = main_result["confidence"]
    else:
        return JSONResponse({"error": "未检测到任何类别结果"}, status_code=500)

    # 数据库存储 + 返回结果（逻辑不变，仅确保变量存在）
    try:
        rec = DetectionRecord(
            patient_name=patient_name,
            patient_gender=patient_gender,
            patient_age=patient_age,
            medical_id=medical_id,
            label=main_class,
            confidence=main_confidence,
            all_results=all_results_list,
            bboxes=bboxes_list,  # 分类任务自动为[]，检测任务为边界框列表
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
                "bboxes": bboxes_list,
                "image_path": image_rel_path
            }
        }, status_code=500)

    # 【修改】返回时判断变量是否存在，避免返回未定义字段
    return JSONResponse({
        "saved_id": rec.id,
        "medical_id": medical_id,
        "main_class": main_class,
        "confidence": main_confidence,
        "all_results": all_results_list,
        "bboxes": bboxes_list,
        "class_scores_raw": class_scores_raw if class_scores_raw is not None else [],
        "class_probs": class_probs if class_probs is not None else [],
        "image_path": image_rel_path,
    })