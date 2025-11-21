import os
import shutil
import random
from datetime import datetime
import argparse
import sys
from functools import partial
import hashlib
import cv2
import numpy as np
import pandas as pd  
import albumentations as A
from ultralytics import YOLO

# 强制刷新打印缓冲区
print = partial(print, flush=True)

def calculate_file_hash(file_path, block_size=65536):
    """计算文件MD5哈希值"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception:
        return None

def remove_duplicate_exact(train_dir, backup_confirmed):
    """MD5 精确去重"""
    if not backup_confirmed:
        print("ℹ️  未选择执行去重操作")
        return 0

    print(f"\n🔍 启动 MD5 精确去重...")
    total_deleted = 0
    hash_map = {}
    
    for class_name in os.listdir(train_dir):
        class_path = os.path.join(train_dir, class_name)
        if not os.path.isdir(class_path): continue
        
        files = sorted([f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        for img_name in files:
            img_path = os.path.join(class_path, img_name)
            file_hash = calculate_file_hash(img_path)
            if file_hash is None: continue
            
            if file_hash in hash_map:
                print(f"🗑️  删除重复: {img_name}")
                try:
                    os.remove(img_path)
                    total_deleted += 1
                except: pass
            else:
                hash_map[file_hash] = img_path
    
    print(f"✅ 去重结束：共删除 {total_deleted} 张")
    return total_deleted

def augment_dataset_offline(train_dir):
    """离线增强：生成动态模糊副本"""
    print("\n🎨 正在生成模拟病人运动的MRI图像...")
    
    transform = A.Compose([
        A.MotionBlur(blur_limit=(15, 31), p=1.0),
    ])

    aug_count = 0
    
    for root, dirs, files in os.walk(train_dir):
        for file in files:
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and "_aug_" not in file:
                file_name, ext = os.path.splitext(file)
                expected_aug_path = os.path.join(root, f"{file_name}_aug_mri{ext}")
                
                if os.path.exists(expected_aug_path): continue 

                img_path = os.path.join(root, file)
                try:
                    image = cv2.imread(img_path)
                    if image is None: continue
                    augmented = transform(image=image)['image']
                    cv2.imwrite(expected_aug_path, augmented)
                    aug_count += 1
                except: pass

    if aug_count > 0:
        print(f"✅ 增强完成：新生成 {aug_count} 张模糊图像")
    else:
        print("ℹ️  未生成新图像（可能已生成）")

def create_validation_split(train_dir, valid_dir, split_ratio=0.15):
    """划分验证集"""
    if os.path.exists(valid_dir) and any(os.scandir(valid_dir)): return

    print("\n🔄 正在划分验证集...")
    os.makedirs(valid_dir, exist_ok=True)
    total_moved = 0
    
    for class_name in os.listdir(train_dir):
        train_class_dir = os.path.join(train_dir, class_name)
        if not os.path.isdir(train_class_dir): continue
            
        valid_class_dir = os.path.join(valid_dir, class_name)
        os.makedirs(valid_class_dir, exist_ok=True)
        
        images = [f for f in os.listdir(train_class_dir) 
                 if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')) and "_aug_" not in f]
        
        random.shuffle(images)
        split_point = int(len(images) * split_ratio)
        
        for img in images[:split_point]:
            shutil.move(os.path.join(train_class_dir, img), os.path.join(valid_class_dir, img))
            total_moved += 1
            
    print(f"✅ 划分完成：移动了 {total_moved} 张图像")

def analyze_overfitting(results_dir):
    """
    过拟合分析
    """
    csv_path = os.path.join(results_dir, 'results.csv')
    if not os.path.exists(csv_path): return

    try:
        # 读取 CSV，去除列名的空格
        df = pd.read_csv(csv_path)
        df.columns = [c.strip() for c in df.columns]
        
        # 兼容不同 YOLO 版本的列名
        train_loss = df.get('train/loss')
        val_loss = df.get('val/loss')
        
        if train_loss is not None and val_loss is not None:
            # 取最后 5 轮的平均值
            last_n = df.tail(5)
            avg_train = last_n['train/loss'].mean()
            avg_val = last_n['val/loss'].mean()
            diff = avg_val - avg_train
            
            print("\n" + "="*40)
            print("📊 过拟合风险分析 (基于最后5轮)")
            print(f"   训练损失: {avg_train:.4f}")
            print(f"   验证损失: {avg_val:.4f}")
            print(f"   差值: {diff:.4f}")
            
            if diff > 0.15:
                print("⚠️  警告：验证损失偏高，可能存在过拟合倾向")
            elif diff < -0.05:
                print("✅ 状态极佳：验证集表现优于训练集")
            else:
                print("✅ 状态良好：模型拟合正常")
            print("="*40 + "\n")
    except Exception:
        pass

def rename_and_cleanup_models(results_save_dir, final_accuracy):
    """重命名模型并清理"""
    weights_dir = os.path.join(results_save_dir, 'weights')
    if not os.path.exists(weights_dir): return
    
    accuracy_str = f"{final_accuracy:.2f}%".replace('.', '_')
    best_pt = os.path.join(weights_dir, 'best.pt')
    new_best_name = f"best-{accuracy_str}.pt"
    
    if os.path.exists(best_pt):
        try:
            shutil.move(best_pt, os.path.join(weights_dir, new_best_name))
            print(f"✅ 模型已重命名为: {new_best_name}")
            # 清理其他文件(如last.pt)，只保留最佳模型
            for f in os.listdir(weights_dir):
                if f.endswith('.pt') and f != new_best_name:
                    try: os.remove(os.path.join(weights_dir, f))
                    except: pass
        except: pass

def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dataset', type=str, required=True)
    parser.add_argument('--epochs', type=int, required=True)
    parser.add_argument('--batch_size', type=int, required=True)
    parser.add_argument('--img_size', type=int, default=224)
    parser.add_argument('--model_type', type=str, required=True)
    parser.add_argument('--deduplicate', action='store_true')
    parser.add_argument('--backup_confirmed', action='store_true')
    return parser.parse_args()

def main():
    print("=== YOLOv8 阿尔茨海默症MRI分类训练 ===\n")
    args = parse_args()
    random.seed(42)

    dataset_root = args.dataset
    train_dir = os.path.join(dataset_root, 'train')
    valid_dir = os.path.join(dataset_root, 'valid')

    if not os.path.exists(train_dir):
        print(f"❌ 找不到训练目录: {train_dir}")
        return

    # 1. 去重
    if args.deduplicate and args.backup_confirmed:
        remove_duplicate_exact(train_dir, True)
    else:
        print("ℹ️  跳过去重")

    # 2. 验证集划分
    create_validation_split(train_dir, valid_dir)

    # 3. 离线增强
    augment_dataset_offline(train_dir)

    # 4. 启动训练
    try:
        model_name = f'yolov8{args.model_type}-cls.pt'
        print(f"\n🤖 加载模型: {model_name}")
        model = YOLO(model_name)

        results_name = f'alz_cls_v8_{args.model_type}_{datetime.now().strftime("%m%d_%H%M")}'
        
        print(f"\n🚀 开始训练 (日志将保存在 results/{results_name})...")
        print("=" * 60)
        
        # 训练开始
        results = model.train(
            data=dataset_root,
            epochs=args.epochs,
            batch=args.batch_size,
            imgsz=args.img_size,
            project='results',
            name=results_name,
            val=True,
            patience=10,
            save_period=-1,
            workers=4,
            device=0,
            cache=False,
            
            # augment=True,
            fliplr=0.5, degrees=15.0, shear=2.5, scale=0.2, translate=0.1,
            hsv_h=0.0, hsv_s=0.0, hsv_v=0.1
        )

        print("=" * 60)
        print(f"🎉 训练完成！")

        # 5. 获取准确率 & 6. 后处理
        final_acc = 0.0
        try:
            if hasattr(results, 'top1'):
                final_acc = float(results.top1) * 100
            else:
                # 备用方案：从 CSV 读取
                csv_path = os.path.join(results.save_dir, 'results.csv')
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    # 查找可能的列名
                    cols = [c.strip() for c in df.columns]
                    acc_key = next((c for c in cols if 'accuracy_top1' in c), None)
                    if acc_key:
                        final_acc = df[acc_key].iloc[-1] * 100
            
            print(f"🏆 最终验证准确率 (Top-1): {final_acc:.2f}%")
        except Exception:
            pass

        result_dir = str(results.save_dir)
        rename_and_cleanup_models(result_dir, final_acc)
        analyze_overfitting(result_dir)

    except Exception as e:
        print(f"❌ 训练出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()