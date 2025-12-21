import os
import shutil
import random
import numpy as np
import cv2
import hashlib
import pandas as pd
import albumentations as A
import matplotlib.pyplot as plt
from sklearn.model_selection import StratifiedKFold
from ultralytics import YOLO

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

def remove_duplicate_exact(target_dir):
    """MD5 精确去重 (针对源目录)"""
    print(f"\n🔍 正在对源数据集进行 MD5 精确去重...")
    total_deleted = 0
    hash_map = {}
    
    for class_name in os.listdir(target_dir):
        class_path = os.path.join(target_dir, class_name)
        if not os.path.isdir(class_path): continue
        
        files = sorted([f for f in os.listdir(class_path) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        for img_name in files:
            if "_aug_" in img_name: continue
            
            img_path = os.path.join(class_path, img_name)
            file_hash = calculate_file_hash(img_path)
            if file_hash is None: continue
            
            if file_hash in hash_map:
                try:
                    os.remove(img_path)
                    total_deleted += 1
                except: pass
            else:
                hash_map[file_hash] = img_path
    
    if total_deleted > 0:
        print(f"✅ 去重结束：共删除 {total_deleted} 张重复原图")
    else:
        print("✅ 无重复图片")

def clean_aug_files(directory):
    """清理目录下所有的增强副本(_aug_)"""
    print(f"🧹 正在清理 {directory} 下的旧增强文件，确保数据纯净...")
    count = 0
    for root, dirs, files in os.walk(directory):
        for file in files:
            if "_aug_" in file:
                try:
                    os.remove(os.path.join(root, file))
                    count += 1
                except: pass
    if count > 0:
        print(f"✅ 清理完成，共删除 {count} 个历史副本文件")
    else:
        print("✅ 数据集很干净，没有历史副本")

def augment_folder_offline(target_dir):
    """对指定文件夹执行离线增强"""
    print(f"🎨 正在对当前折的训练集执行增强: {os.path.basename(target_dir)}...")
    
    transform = A.Compose([
        A.MotionBlur(blur_limit=(25, 45), p=1.0),
        A.GaussNoise(limit=(10.0, 25.0), p=0.7),
        A.RandomBrightnessContrast(brightness_limit=0.3, contrast_limit=0.3, p=0.8)
    ])
    
    aug_count = 0
    augment_ratio = 0.3 # 30% 增强
    
    for root, dirs, files in os.walk(target_dir):
        for file in files:
            if not file.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')): continue
            if "_aug_" in file: continue 

            if random.random() > augment_ratio: continue

            img_path = os.path.join(root, file)
            file_name, ext = os.path.splitext(file)
            save_path = os.path.join(root, f"{file_name}_aug_mri{ext}")
            
            try:
                image = cv2.imread(img_path)
                if image is None: continue
                augmented = transform(image=image)['image']
                cv2.imwrite(save_path, augmented)
                aug_count += 1
            except: pass
    
    print(f"✅ 当前折增强完成：新生成 {aug_count} 张图像")

def rename_and_cleanup_models(results_save_dir, final_accuracy):
    """重命名模型文件并清理"""
    weights_dir = os.path.join(results_save_dir, 'weights')
    if not os.path.exists(weights_dir): return
    
    NEW_PREFIX = "Top1-"
    accuracy_str = f"{final_accuracy:.2f}%".replace('.', '_')
    best_pt = os.path.join(weights_dir, 'best.pt')
    new_best_name = f"{NEW_PREFIX}{accuracy_str}.pt"
    new_best_path = os.path.join(weights_dir, new_best_name)
    
    if os.path.exists(best_pt):
        try:
            if os.path.exists(new_best_path): os.remove(new_best_path)
            shutil.move(best_pt, new_best_path)
            print(f"✅ [当前折] 最佳模型已保存为: {new_best_name}")
            
            for file in os.listdir(weights_dir):
                if file.endswith('.pt') and file != new_best_name:
                    try: os.remove(os.path.join(weights_dir, file))
                    except: pass
        except Exception as e:
            print(f"⚠️ 模型重命名失败: {e}")

def analyze_overfitting(results_save_dir):
    """过拟合分析"""
    results_csv = os.path.join(results_save_dir, 'results.csv')
    if not os.path.exists(results_csv): return
    
    try:
        df = pd.read_csv(results_csv)
        df.columns = [c.strip() for c in df.columns]
        
        train_loss_col = 'train/loss' if 'train/loss' in df.columns else None
        val_loss_col = 'val/loss' if 'val/loss' in df.columns else None
        
        if train_loss_col and val_loss_col:
            last_n = df.tail(5)
            avg_train_loss = last_n[train_loss_col].mean()
            avg_val_loss = last_n[val_loss_col].mean()
            loss_gap = avg_val_loss - avg_train_loss
            
            print("-" * 40)
            print(f"📊 [当前折] 过拟合风险评估:")
            print(f"   Train Loss: {avg_train_loss:.4f} | Val Loss: {avg_val_loss:.4f}")
            print(f"   Gap: {loss_gap:.4f}")
            
            if loss_gap < 0.1: print("   ✅ 低风险")
            elif 0.1 <= loss_gap < 0.5: print("   ⚠️ 中等风险")
            else: print("   ❌ 高风险")
            print("-" * 40)
    except: pass

def plot_kfold_summary(acc_scores, output_file='kfold_summary.png'):
    """自动生成五折结果汇总图"""
    print("\n📊 正在生成五折汇总图表...")
    try:
        folds = [f'Fold {i+1}' for i in range(len(acc_scores))]
        mean_acc = np.mean(acc_scores)
        std_acc = np.std(acc_scores)

        plt.figure(figsize=(10, 6))
        bars = plt.bar(folds, acc_scores, color='#4e79a7', alpha=0.8, width=0.6, label='Accuracy')
        plt.axhline(y=mean_acc, color='#e15759', linestyle='--', linewidth=2, label=f'Mean: {mean_acc:.2f}%')

        for bar in bars:
            height = bar.get_height()
            plt.text(bar.get_x() + bar.get_width()/2., height,
                     f'{height:.2f}%', ha='center', va='bottom', fontsize=11, fontweight='bold')

        # 动态设置Y轴范围，让差异更明显
        min_acc = min(acc_scores)
        plt.ylim(min_acc - 1.0, 100.5 if max(acc_scores) > 99 else max(acc_scores) + 1.0) 
        
        plt.title(f'5-Fold Cross-Validation Results\n(Mean: {mean_acc:.2f}% ± {std_acc:.2f}%)', fontsize=14)
        plt.ylabel('Top-1 Accuracy (%)', fontsize=12)
        plt.legend(loc='lower right')
        plt.grid(axis='y', linestyle='--', alpha=0.5)
        
        plt.tight_layout()
        plt.savefig(output_file, dpi=300)
        print(f"✅ 图表已保存为: {output_file}")
        # plt.show() # 服务器环境可注释掉
    except Exception as e:
        print(f"⚠️ 绘图失败: {e}")

def main():
    print(f"=== YOLOv8 交叉验证 (K-Fold Cross-Validation) ===\n")
    random.seed(42)
    
    # --- 参数输入 ---
    dataset_root = input("📂 请输入数据集路径: ").strip()
    if not dataset_root or not os.path.exists(dataset_root):
        print("❌ 路径无效")
        return

    do_dedup = input("❓ 是否对源数据集进行 MD5 去重? (y/N) [默认N]: ").strip().lower()
    
    k_input = input("🔄 请输入交叉验证折数 (默认5): ").strip()
    kfold_num = int(k_input) if k_input.isdigit() else 5
    
    e_input = input("⏳ 请输入每折训练轮数 (默认50): ").strip()
    epochs = int(e_input) if e_input.isdigit() else 50
    
    b_input = input("📦 请输入批次大小 (默认8): ").strip()
    batch_size = int(b_input) if b_input.isdigit() else 8
    
    m_size = input("🤖 模型大小 [n/s/m/l, 默认s]: ").strip() or 's'
    
    print(f"\n⚙️  配置确认:")
    print(f"   数据集: {dataset_root}")
    print(f"   模型: YOLOv8{m_size}-cls")
    print(f"   K-Fold: {kfold_num} 折")
    print(f"   Epochs: {epochs}")
    print(f"   Batch : {batch_size}")
    
    if input("\n确认开始? [y/N]: ").lower() not in ['y', 'yes', '是']:
        return

    train_source = os.path.join(dataset_root, 'train')
    if not os.path.exists(train_source):
        print("❌ 找不到 train 文件夹。请先将 valid 中的图片移回 train。")
        return

    # 1. 初始清理
    clean_aug_files(train_source)
    
    # 2. 全局去重 (只跑一次)
    if do_dedup in ['y', 'yes', '是']:
        remove_duplicate_exact(train_source)
    
    # 3. 收集数据
    print("📦 正在索引原始数据集...")
    all_data = [] 
    y_labels = []
    classes = [d for d in os.listdir(train_source) if os.path.isdir(os.path.join(train_source, d))]
    classes.sort()
    
    for cls in classes:
        cls_dir = os.path.join(train_source, cls)
        files = [f for f in os.listdir(cls_dir) if f.lower().endswith(('.jpg', '.png', '.jpeg', '.bmp'))]
        for f in files:
            all_data.append((os.path.join(cls_dir, f), cls))
            y_labels.append(cls)
            
    print(f"📊 原始数据总量: {len(all_data)} 张")
    print(f"📊 类别分布: {pd.Series(y_labels).value_counts().to_dict()}")

    # 4. K-Fold 循环
    kf = StratifiedKFold(n_splits=kfold_num, shuffle=True, random_state=42)
    acc_scores = []
    
    temp_work_dir = os.path.join(dataset_root, 'kfold_temporary')
    if os.path.exists(temp_work_dir): shutil.rmtree(temp_work_dir)
    
    for fold, (train_idx, val_idx) in enumerate(kf.split(all_data, y_labels)):
        print(f"\n{'='*20} Fold {fold+1} / {kfold_num} {'='*20}")
        
        fold_train_labels = [y_labels[i] for i in train_idx]
        fold_val_labels = [y_labels[i] for i in val_idx]
        print(f"📊 当前折训练集类别分布: {pd.Series(fold_train_labels).value_counts().to_dict()}")
        print(f"📊 当前折验证集类别分布: {pd.Series(fold_val_labels).value_counts().to_dict()}")

        # (A) 创建目录
        current_fold_dir = os.path.join(temp_work_dir, f'fold_{fold+1}')
        fold_train_dir = os.path.join(current_fold_dir, 'train')
        fold_val_dir = os.path.join(current_fold_dir, 'val')
        
        for cls in classes:
            os.makedirs(os.path.join(fold_train_dir, cls), exist_ok=True)
            os.makedirs(os.path.join(fold_val_dir, cls), exist_ok=True)
            
        # (B) 分发数据
        print("🚚 分发数据到临时目录...")
        for idx in train_idx:
            src, cls = all_data[idx]
            shutil.copy(src, os.path.join(fold_train_dir, cls, os.path.basename(src)))
        for idx in val_idx:
            src, cls = all_data[idx]
            shutil.copy(src, os.path.join(fold_val_dir, cls, os.path.basename(src)))

        # (C) 增强训练集
        augment_folder_offline(fold_train_dir)
        
        # (D) 训练
        print(f"🚀 开始训练 Fold {fold+1}...")
        try:
            model_name = f'yolov8{m_size}-cls.pt'
            if not os.path.exists(model_name):
                print(f"正在下载 {model_name}...")
            
            model = YOLO(model_name) 
            
            results = model.train(
                data=current_fold_dir,
                epochs=epochs,
                batch=batch_size,
                imgsz=640,
                project='kfold_results', 
                name=f'fold_{fold+1}',
                
                patience=10,     
                save_period=-1,  
                workers=4,      
                device=0,       
                cache=False,    
                amp=True,        
                verbose=True,    # 开启日志
                plots=True,      # 确保生成混淆矩阵等图表
                
                # --- YOLO 在线增强参数 ---
                fliplr=0.5,      
                degrees=15.0,    
                shear=2.5,       
                scale=0.2,       
                translate=0.1,   
                hsv_h=0.0,       
                hsv_s=0.0,       
                hsv_v=0.1        
            )
            
            # (E) 获取准确率
            fold_acc = 0.0
            if hasattr(results, 'top1'):
                fold_acc = results.top1 * 100
            else:
                csv_path = os.path.join(results.save_dir, 'results.csv')
                if os.path.exists(csv_path):
                    df = pd.read_csv(csv_path)
                    df.columns = [c.strip() for c in df.columns]
                    if 'metrics/accuracy_top1' in df.columns:
                        fold_acc = df['metrics/accuracy_top1'].max() * 100
                    elif 'val/accuracy_top1' in df.columns:
                        fold_acc = df['val/accuracy_top1'].max() * 100
            
            acc_scores.append(fold_acc)
            print(f"🏆 Fold {fold+1} 最佳准确率: {fold_acc:.2f}%")
            
            # (F) 重命名模型 & 过拟合分析
            rename_and_cleanup_models(results.save_dir, fold_acc)
            analyze_overfitting(results.save_dir)
            
        except Exception as e:
            print(f"❌ Fold {fold+1} 训练出错: {e}")
            acc_scores.append(0.0)

    # 5. 最终统计与绘图
    print("\n" + "-"*50)
    print(f"📊 {kfold_num}折分层交叉验证最终报告")
    print("-"*50)
    print(f"各折准确率: {[f'{x:.2f}%' for x in acc_scores]}")
    
    if len(acc_scores) > 0:
        avg_acc = np.mean(acc_scores)
        std_dev = np.std(acc_scores)
        print(f"✅ 平均准确率: {avg_acc:.2f}%")
        print(f"📉 标准差: ±{std_dev:.2f}%")
        print("\n📝 实验结论:")
        print(f" 泛化验证 (K-Fold): {avg_acc:.2f}%")
        
        # 自动绘图
        plot_kfold_summary(acc_scores)
        
    print("#"*50)
    
    if os.path.exists(temp_work_dir):
        print("🧹 清理临时工作目录...")
        shutil.rmtree(temp_work_dir)
        print("✨ 完成")

if __name__ == "__main__":
    main()