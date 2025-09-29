from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import select
from fastapi import Query
from database import get_session
from history_models import DetectionRecord, DetectionCreate, DetectionUpdate
from typing import List
import shutil, os

router = APIRouter(prefix="/detections", tags=["detections"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=DetectionRecord)
def create_detection(d: DetectionCreate, session=Depends(get_session)):
    rec = DetectionRecord.from_orm(d)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


@router.get("/", response_model=List[DetectionRecord])
def list_detections(
    patient_name: str | None = Query(None, description="按病人姓名模糊匹配"),
    medical_id: str | None = Query(None, description="按病历号精准匹配"),
    session=Depends(get_session)
):
    stmt = select(DetectionRecord)
    if patient_name:
        stmt = stmt.where(DetectionRecord.patient_name.contains(patient_name))
    if medical_id:
        stmt = stmt.where(DetectionRecord.medical_id == medical_id)
    stmt = stmt.order_by(DetectionRecord.created_at.desc())
    q = session.exec(stmt)
    return q.all()

@router.get("/{id}", response_model=DetectionRecord)
def get_detection(id: int, session=Depends(get_session)):
    rec = session.get(DetectionRecord, id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    return rec

@router.put("/{id}", response_model=DetectionRecord)
def update_detection(id: int, d: DetectionUpdate, session=Depends(get_session)):
    rec = session.get(DetectionRecord, id)
    if not rec:
        raise HTTPException(status_code=404)
    rec_data = d.dict(exclude_unset=True)
    for k, v in rec_data.items():
        setattr(rec, k, v)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec

@router.delete("/{id}", response_model=dict)
def delete_detection(id: int, session=Depends(get_session)):
    rec = session.get(DetectionRecord, id)
    if not rec:
        raise HTTPException(status_code=404)
    session.delete(rec)
    session.commit()
    return {"ok": True}