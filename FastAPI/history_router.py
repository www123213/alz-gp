from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlmodel import select
from fastapi import Query
from database import get_session
from history_models import PredictionRecord, PredictionCreate, PredictionUpdate
from typing import List
import shutil, os

router = APIRouter(prefix="/Predictions", tags=["Predictions"])

UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/", response_model=PredictionRecord)
def create_Prediction(d: PredictionCreate, session=Depends(get_session)):
    rec = PredictionRecord.from_orm(d)
    session.add(rec)
    session.commit()
    session.refresh(rec)
    return rec


@router.get("/", response_model=List[PredictionRecord])
def list_Predictions(
    patient_name: str | None = Query(None, description="按病人姓名模糊匹配"),
    medical_id: str | None = Query(None, description="按病历号精准匹配"),
    session=Depends(get_session)
):
    stmt = select(PredictionRecord)
    if patient_name:
        stmt = stmt.where(PredictionRecord.patient_name.contains(patient_name))
    if medical_id:
        stmt = stmt.where(PredictionRecord.medical_id == medical_id)
    stmt = stmt.order_by(PredictionRecord.created_at.desc())
    q = session.exec(stmt)
    return q.all()

@router.get("/{id}", response_model=PredictionRecord)
def get_Prediction(id: int, session=Depends(get_session)):
    rec = session.get(PredictionRecord, id)
    if not rec:
        raise HTTPException(status_code=404, detail="not found")
    return rec

@router.put("/{id}", response_model=PredictionRecord)
def update_Prediction(id: int, d: PredictionUpdate, session=Depends(get_session)):
    rec = session.get(PredictionRecord, id)
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
def delete_Prediction(id: int, session=Depends(get_session)):
    rec = session.get(PredictionRecord, id)
    if not rec:
        raise HTTPException(status_code=404)
    session.delete(rec)
    session.commit()
    return {"ok": True}