from fastapi import FastAPI
from predict_api import router as predict_router
from v8_train_api import router as train_router
from history_router import router as history_router
from database import init_db
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(predict_router)
app.include_router(train_router)
app.include_router(history_router)

# 在 app 定义之后，挂载 uploads 目录作为静态文件
UPLOAD_DIR = os.path.join(os.path.dirname(__file__), "uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

init_db()

@app.get("/")
def read_root():
    return {"msg": "Alzheimer YOLOv8 API running"}
