from typing import Optional, List
from datetime import datetime
from zoneinfo import ZoneInfo
from sqlmodel import SQLModel, Field, Column, JSON, Text

# 存储检测历史表
class PredictionRecord(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)

    # 表单信息
    patient_name: Optional[str] = Field(default=None, index=True)
    patient_gender: Optional[str] = Field(default=None)
    patient_age: Optional[int] = Field(default=None)
    medical_id: Optional[str] = Field(default=None, index=True)

    # 推理结果
    label: Optional[str] = Field(default=None, index=True)
    confidence: Optional[float] = Field(default=None)

    all_results: Optional[List[dict]] = Field(
        default=None,
        sa_column=Column(JSON),  
    )

    bboxes: Optional[List[dict]] = Field(
        default=None,
        sa_column=Column(JSON),
        description="检测任务专用：存储边界框信息（xyxy格式），含class、confidence、x1、y1、x2、y2"
    )

    image_path: Optional[str] = Field(default=None)

    # 使用北京时间
    created_at: datetime = Field(default_factory=lambda: datetime.now(tz=ZoneInfo('Asia/Shanghai')))


# DTO（创建 / 更新）
class PredictionCreate(SQLModel):
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    medical_id: Optional[str] = None
    label: Optional[str] = None
    confidence: Optional[float] = None
    all_results: Optional[List[dict]] = None
    bboxes: Optional[List[dict]] = None
    image_path: Optional[str] = None


class PredictionUpdate(SQLModel):
    patient_name: Optional[str] = None
    patient_gender: Optional[str] = None
    patient_age: Optional[int] = None
    medical_id: Optional[str] = None
    label: Optional[str] = None
    confidence: Optional[float] = None
    all_results: Optional[List[dict]] = None
    bboxes: Optional[List[dict]] = None
    image_path: Optional[str] = None
