import os
import shutil
import random
from datetime import datetime
import argparse
import sys
from functools import partial
import hashlib  # 哈希计算依赖

print = partial(print, flush=True)

def calculate_file_hash(file_path, block_size=65536):
    """计算文件MD5哈希值"""
    hasher = hashlib.md5()
    try:
        with open(file_path, 'rb') as f:
            while chunk := f.read(block_size):
                hasher.update(chunk)
        return hasher.hexdigest()
    except Exception as e:
        print(f"⚠️  计算 {file_path} 哈希失败：{str(e)}")
        return None


def remove_duplicate_exact(train_dir, backup_confirmed):
    """
    移除完全重复图像
    :param train_dir: 训练集目录
    :param backup_confirmed: 确认状态（True/False）
    :return: 总删除数量
    """
    if not backup_confirmed:
        print("ℹ️  未选择执行完全去重操作")
        return 0

    hash_map = {}
    total_deleted = 0

    # 按类别遍历去重
    for class_name in os.listdir(train_dir):
        class_path = os.path.join(train_dir, class_name)
        if not os.path.isdir(class_path):
            continue
        
        print(f"\n📂 处理类别：{class_name}")
        class_deleted = 0

        for img_name in os.listdir(class_path):
            img_path = os.path.join(class_path, img_name)
            if not img_name.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp')):
                continue

            img_hash = calculate_file_hash(img_path)
            if img_hash is None:
                continue
            
            if img_hash in hash_map:
                os.remove(img_path)
                print(f"🗑️  删除重复图像：{img_path}（与 {hash_map[img_hash]} 完全相同）")
                total_deleted += 1
                class_deleted += 1
            else:
                hash_map[img_hash] = img_path

        print(f"📊 类别 {class_name} 去重完成：删除 {class_deleted} 张重复图")
    
    return total_deleted


def create_validation_split(train_dir, valid_dir, split_ratio=0.15):
    """从训练集分出验证集"""
    if os.path.exists(valid_dir):
        shutil.rmtree(valid_dir)
    os.makedirs(valid_dir)
    total_moved = 0
    for class_name in os.listdir(train_dir):
        if not os.path.isdir(os.path.join(train_dir, class_name)):
            continue
        train_class_dir = os.path.join(train_dir, class_name)
        valid_class_dir = os.path.join(valid_dir, class_name)
        os.makedirs(valid_class_dir)
        images = [f for f in os.listdir(train_class_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
        random.shuffle(images)
        split_point = int(len(images) * split_ratio)
        for img in images[:split_point]:
            shutil.move(
                os.path.join(train_class_dir, img),
                os.path.join(valid_class_dir, img)
            )
            total_moved += 1
        print(f"📁 {class_name}: 训练集 {len(images)-split_point} 张, 验证集 {split_point} 张")
    print(f"✅ 总共分离了 {total_moved} 张图像到验证集")


def rename_and_cleanup_models(results_save_dir, final_accuracy):
    """重命名模型文件并清理"""
    weights_dir = os.path.join(results_save_dir, 'weights')
    if not os.path.exists(weights_dir):
        print("❌ weights文件夹不存在")
        return
    accuracy_str = f"{final_accuracy:.2f}%".replace('.', '_')
    best_pt = os.path.join(weights_dir, 'best.pt')
    if not os.path.exists(best_pt):
        print("❌ 找不到best.pt文件")
        return
    new_best_name = f"best-{accuracy_str}.pt"
    new_best_path = os.path.join(weights_dir, new_best_name)
    try:
        existing_best_files = [f for f in os.listdir(weights_dir) if f.startswith('best-') and f.endswith('.pt')]
        should_update_best = True
        if existing_best_files:
            for old_best in existing_best_files:
                old_acc_str = old_best.replace('best-', '').replace('.pt', '').replace('_', '.')
                try:
                    old_acc = float(old_acc_str.replace('%', ''))
                    if final_accuracy <= old_acc:
                        print(f"ℹ️  当前模型准确率({final_accuracy:.2f}%)不如现有best模型({old_acc:.2f}%)，保留现有best模型")
                        should_update_best = False
                        break
                    else:
                        os.remove(os.path.join(weights_dir, old_best))
                        print(f"🔄 删除旧的best模型: {old_best} (准确率: {old_acc:.2f}%)")
                except ValueError:
                    os.remove(os.path.join(weights_dir, old_best))
        if should_update_best:
            shutil.move(best_pt, new_best_path)
            print(f"✅ 保留最佳模型: {new_best_name}")
        else:
            os.remove(best_pt)
        for file in os.listdir(weights_dir):
            if file.endswith('.pt') and file != new_best_name:
                file_path = os.path.join(weights_dir, file)
                os.remove(file_path)
                print(f"🗑️  删除模型文件: {file}")
        remaining_models = [f for f in os.listdir(weights_dir) if f.endswith('.pt')]
        print(f"🎯 最终保留模型: {remaining_models[0] if remaining_models else '无'}")
        print(f"📁 weights文件夹中的模型文件数量: {len(remaining_models)}")
    except Exception as e:
        print(f"❌ 模型文件处理失败: {e}")


def analyze_overfitting(results_save_dir):
    """过拟合分析"""
    results_csv = os.path.join(results_save_dir, 'results.csv')
    if not os.path.exists(results_csv):
        print("⚠️  未找到训练指标文件（results.csv），无法分析过拟合")
        return
    
    try:
        import pandas as pd
        df = pd.read_csv(results_csv)
        
        # 兼容不同YOLOv8版本的列名
        train_loss_col = None
        val_loss_col = None
        if 'train/loss' in df.columns:
            train_loss_col = 'train/loss'
        elif 'metrics/train/loss' in df.columns:
            train_loss_col = 'metrics/train/loss'
        
        if 'val/loss' in df.columns:
            val_loss_col = 'val/loss'
        elif 'metrics/val/loss' in df.columns:
            val_loss_col = 'metrics/val/loss'
        
        if not train_loss_col or not val_loss_col:
            print(f"⚠️  指标文件中缺少训练/验证损失列，无法分析过拟合（现有列：{df.columns.tolist()}）")
            return
        
        # 过滤NaN值
        df_valid = df.dropna(subset=[train_loss_col, val_loss_col])
        last_n = len(df_valid) if len(df_valid) < 10 else 10
        last_n_data = df_valid.tail(last_n)
        
        avg_train_loss = last_n_data[train_loss_col].mean()
        avg_val_loss = last_n_data[val_loss_col].mean()
        loss_gap = avg_val_loss - avg_train_loss
        
        # 输出分析结果
        print("\n" + "="*60)
        print(f"📊 过拟合风险评估（基于最后{last_n}轮损失）")
        print("-"*60)
        print(f"训练损失均值: {avg_train_loss:.4f}")
        print(f"验证损失均值: {avg_val_loss:.4f}")
        print(f"损失差距（验证-训练）: {loss_gap:.4f}")
        print("-"*60)
        if loss_gap < 0.1:
            print("✅ 低风险：训练/验证损失接近，过拟合风险极低")
            print("   建议：保持当前参数，无需调整")
        elif 0.1 <= loss_gap < 0.5:
            print("⚠️  中等风险：验证损失略高于训练损失，存在轻微过拟合倾向")
            print("   建议：1. 增加训练轮数（若未到patience上限） 2. 后续可尝试数据增强")
        else:
            print("❌ 高风险：验证损失远高于训练损失，存在明显过拟合")
            print("   建议：1. 立即停止训练（避免继续过拟合） 2. 增加数据量或使用数据增强")
            print("        3. 尝试减小模型尺寸（如从yolov8s换成yolov8n）或添加正则化")
        print("="*60 + "\n")
    
    except ImportError:
        print("⚠️  未安装pandas，无法分析过拟合（需执行：pip install pandas）")
    except Exception as e:
        print(f"⚠️  过拟合分析失败：{str(e)}")


def parse_args():
    parser = argparse.ArgumentParser()
    # 核心训练参数
    parser.add_argument('--dataset', type=str, required=True, help='数据集根目录（含train文件夹）')
    parser.add_argument('--epochs', type=int, required=True, help='训练轮数')
    parser.add_argument('--batch_size', type=int, required=True, help='批次大小')
    parser.add_argument('--img_size', type=int, default=640, help='图像尺寸（默认640）')
    parser.add_argument('--model_type', type=str, required=True, help='模型类型（n/s/m/l/x）')
    # 去重控制参数
    parser.add_argument('--deduplicate', action='store_true', help='是否启用完全去重')
    parser.add_argument('--backup_confirmed', action='store_true', help='确认执行去重')
    return parser.parse_args()


def main():
    print("=== YOLOv8 阿尔茨海默症MRI图像分类训练 ===\n")
    args = parse_args()
    random.seed(42)

    dataset_root = args.dataset
    train_dir = os.path.join(dataset_root, 'train')
    if not os.path.exists(train_dir):
        print(f"❌ 训练集目录不存在：{train_dir}")
        return

    do_deduplicate = args.deduplicate and args.backup_confirmed
    if do_deduplicate:
        print("\n🔍 启动训练集完全去重（基于MD5哈希）...")
        total_dup_deleted = remove_duplicate_exact(train_dir, True)
        print(f"✅ 完全去重结束：共删除 {total_dup_deleted} 张重复图像")
    else:
        print("\nℹ️ 未启动完全去重或未备份，跳过去重步骤")

    # 3. 打印数据集信息
    class_names = [f for f in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, f))]
    class_names.sort()
    print(f"\n📊 数据集信息：")
    print(f"   路径: {dataset_root}")
    print(f"   模型类型: YOLOv8-{args.model_type}-cls")
    print(f"   训练轮数: {args.epochs} 轮")
    print(f"   批次大小: {args.batch_size} 张/批")
    print(f"   图像尺寸: {args.img_size}×{args.img_size}")
    print(f"   类别数量: {len(class_names)} 个（{', '.join(class_names)}）")
    
    # 统计每个类别的图像数量
    total_train_images = 0
    for class_name in class_names:
        class_dir = os.path.join(train_dir, class_name)
        img_count = len([f for f in os.listdir(class_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))])
        total_train_images += img_count
        print(f"   {class_name}: {img_count} 张MRI图像")
    print(f"   训练集总计: {total_train_images} 张图像")

    # 4. 分割验证集
    valid_dir = os.path.join(dataset_root, 'valid')
    if not os.path.exists(valid_dir):
        print("\n🔄 验证集不存在，正在从训练集分离15%作为验证集...")
        create_validation_split(train_dir, valid_dir)
    else:
        print("\n✅ 验证集已存在，跳过分割步骤")

    # 5. 启动模型训练
    try:
        from ultralytics import YOLO
        model_name = f'yolov8{args.model_type}-cls.pt'
        print(f"\n🤖 正在加载模型：{model_name}")
        if not os.path.exists(model_name):
            print(f"📥 首次使用，正在下载 {model_name}...")
        model = YOLO(model_name)
        print(f"✅ 成功加载模型: {model_name}")

        # 训练结果保存路径
        results_name = f'alzheimer_cls_v8_{args.model_type}_{datetime.now().strftime("%m%d_%H%M")}'
        print("\n🚀 开始训练 - YOLOv8 阿尔茨海默症MRI图像分类")
        print("=" * 60)

        results = model.train(
            data=dataset_root,
            epochs=args.epochs,
            batch=args.batch_size,
            imgsz=args.img_size,
            project='results',
            name=results_name,
            plots=True,  # YOLOv8会自动生成损失曲线（results.png）
            val=True,
            patience=10,  # 10轮无改善就停止
            save_period=-1,  # 禁用定期保存，只保存best和last
            workers=4,  # 减少worker数量避免内存问题
            device=0,  # 强制使用GPU 0
            cache=False,  # 不缓存图像到内存
            amp=True,  # 使用混合精度训练节省显存
            model=model_name,  # 明确指定模型
            #训练增强
            augment=True,
            fliplr=0.6,    # 水平翻转概率
            flipud=0.0,    # 垂直翻转概率（MRI一般不建议垂直翻转，设为0）
            hsv_h=0.015,   # 色调扰动（适合灰度图的细微调整）
            hsv_s=0.75,     # 饱和度扰动（增强对比度差异）
            hsv_v=0.45,     # 亮度扰动（突出脑结构细节）
            degrees=3.0,  # 随机旋转角度
            translate=0.12, # 平移扰动
            scale=0.15,     # 缩放扰动
            shear=0.0,    # 剪切变换
            perspective=0.0,  # 透视变换（模拟扫描角度差异）
            weight_decay=0.0005, # 权重衰减（L2正则化）
        )

        print("=" * 60)
        print("🎉 训练完成！阿尔茨海默症MRI分类模型训练成功！")
        print(f"📁 训练结果保存路径: {results.save_dir}")

        # 6. 处理训练结果
        final_accuracy = 0
        try:
            if hasattr(results, 'results_dict'):
                final_accuracy = results.results_dict.get('metrics/accuracy_top1', 0) * 100
            elif hasattr(results, 'best_fitness'):
                final_accuracy = results.best_fitness * 100
            else:
                results_csv = os.path.join(results.save_dir, 'results.csv')
                if os.path.exists(results_csv):
                    import pandas as pd
                    df = pd.read_csv(results_csv)
                    if 'val/accuracy_top1' in df.columns:
                        final_accuracy = df['val/accuracy_top1'].max() * 100
                    elif 'metrics/accuracy_top1' in df.columns:
                        final_accuracy = df['metrics/accuracy_top1'].max() * 100
            print(f"🎯 最终验证准确率: {final_accuracy:.2f}%")
            rename_and_cleanup_models(results.save_dir, final_accuracy)
            analyze_overfitting(results.save_dir)
            
        except Exception as e:
            print(f"⚠️  获取准确率失败，使用默认值: {e}")
            final_accuracy = 85.0
            rename_and_cleanup_models(results.save_dir, final_accuracy)
            analyze_overfitting(results.save_dir)
        
        # 提示损失曲线位置
        loss_curve_path = os.path.join(results.save_dir, 'results.png')
        if os.path.exists(loss_curve_path):
            print(f"📈 训练/验证损失曲线已保存至: {loss_curve_path}")
        print(f"🔖 使用的模型: {model_name}")

    except ImportError:
        print("❌ 请先安装 ultralytics: pip install ultralytics")
    except RuntimeError as e:
        if "CUDA error: out of memory" in str(e):
            print("❌ GPU显存不足！建议:")
            print("   🔧 重新运行，选择批次大小为 4 或 6")
            print("   💾 或者选择更小的模型 (yolo8n)")
            print("   🖥️  或者在代码中添加 device='cpu' 使用CPU训练")
        else:
            print(f"❌ 训练过程中出现错误: {e}")
    except Exception as e:
        print(f"❌ 训练失败: {e}")


if __name__ == "__main__":
    main()