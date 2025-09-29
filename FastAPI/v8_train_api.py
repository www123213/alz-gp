from fastapi import APIRouter, BackgroundTasks, Form
from fastapi.responses import JSONResponse
import subprocess
import os
import sys
import time
import signal

router = APIRouter()

# 可配置的数据集根目录（当前端只传文件夹名时，会从此目录拼接），可通过环境变量覆盖
DATASETS_ROOT = os.environ.get('DATASETS_ROOT', r'D:\毕设')

@router.post("/train")
async def train(
    dataset_path: str = Form(...),
    epochs: int = Form(50),
    batch_size: int = Form(16),
    img_size: int = Form(640),
    model_type: str = Form("s"),
    background_tasks: BackgroundTasks = None
):
    # 训练前清空日志
    with open("train.log", "w", encoding="utf-8"):
        pass

    # 解析 dataset_path：如果前端传来绝对路径则直接使用，否则从 DATASETS_ROOT 拼接
    if os.path.isabs(dataset_path):
        dataset_root = dataset_path
    else:
        dataset_root = os.path.join(DATASETS_ROOT, dataset_path)

    # 校验数据集路径及其中的 train 子目录存在性，若不存在则返回错误
    train_dir_check = os.path.join(dataset_root, 'train')
    if not os.path.exists(train_dir_check):
        return JSONResponse({"status": "error", "msg": f"找不到 train 文件夹: {train_dir_check}"}, status_code=400)

    # 使用当前 Python 解释器，并开启 unbuffered 模式(-u)
    python_exe = sys.executable or "python"
    cmd = [
        python_exe, "-u", "v8-train.py",
        "--dataset", dataset_root,
        "--epochs", str(epochs),
        "--batch_size", str(batch_size),
        "--img_size", str(img_size),
        "--model_type", model_type
    ]
    env = os.environ.copy()
    env.setdefault('PYTHONUNBUFFERED', '1')
    env.setdefault('PYTHONIOENCODING', 'utf-8')
    env.setdefault('PYTHONUTF8', '1')

    # 打开日志文件供子进程写入
    f = open("train.log", "a", encoding="utf-8", buffering=1)
    try:
        f.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TRAIN_STARTED\n")
        f.flush()
    except Exception:
        pass

    proc = subprocess.Popen(cmd, stdout=f, stderr=subprocess.STDOUT, bufsize=1, universal_newlines=True, env=env)

    # 将 pid 写入文件，方便查询或终止
    try:
        with open("train.pid", "w", encoding="utf-8") as pf:
            pf.write(str(proc.pid))
    except Exception:
        pass

    # 后台等待线程：等待进程完成并写入 TRAIN_FINISHED（使用 background_tasks 来等待）
    def waiter(p, log_file_path="train.log"):
        p.wait()
        try:
            with open(log_file_path, "a", encoding="utf-8") as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TRAIN_FINISHED\n")
                lf.flush()
        except Exception:
            pass
        try:
            # 关闭父进程打开的
            f.close()
        except Exception:
            pass

    if background_tasks:
        background_tasks.add_task(waiter, proc)

    return JSONResponse({"status": "训练已启动", "pid": proc.pid})

@router.get("/train/log")
async def get_train_log():
    try:
        with open("train.log", "r", encoding="utf-8") as f:
            content = f.read()
        return {"log": content}
    except FileNotFoundError:
        return {"log": ""}


@router.post("/train/stop")
async def stop_train():
    # 尝试从 train.pid 读取 pid 并终止进程（跨平台）
    try:
        with open("train.pid", "r", encoding="utf-8") as pf:
            pid = int(pf.read().strip())
    except Exception:
        return JSONResponse({"status": "no_pid", "msg": "找不到 train.pid 或 pid 无效"})

    # 尝试优雅终止
    try:
        if os.name == 'nt':
            # Windows 使用 taskkill 强制终止
            subprocess.run(["taskkill", "/F", "/PID", str(pid)], check=False)
        else:
            os.kill(pid, signal.SIGTERM)
        # 写入 TRAIN_STOPPED 到日志，说明是被外部终止
        try:
            with open("train.log", "a", encoding="utf-8") as lf:
                lf.write(f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] TRAIN_STOPPED (pid={pid})\n")
                lf.flush()
        except Exception:
            pass
        # 尝试删除 pid 文件
        try:
            if os.path.exists("train.pid"):
                os.remove("train.pid")
        except Exception:
            pass
        return JSONResponse({"status": "stopped", "pid": pid})
    except Exception as e:
        return JSONResponse({"status": "error", "msg": str(e)})