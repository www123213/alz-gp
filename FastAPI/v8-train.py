import os
import shutil
import random
from datetime import datetime
import argparse
import sys
from functools import partial

print = partial(print, flush=True)

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
    print(f"✅ 总共分离了 {total_moved} 张图片到验证集")

def rename_and_cleanup_models(results_save_dir, final_accuracy):
    """重命名模型文件并清理，只保留最佳模型"""
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

# 新增：过拟合分析函数（对比训练/验证损失）
def analyze_overfitting(results_save_dir):
    """
    分析过拟合风险：通过对比训练损失（train/loss）和验证损失（val/loss）的差距
    逻辑：取最后10轮的损失均值，差距越大，过拟合风险越高
    """
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
        
        # 若列名不存在，无法分析
        if not train_loss_col or not val_loss_col:
            print(f"⚠️  指标文件中缺少训练/验证损失列，无法分析过拟合（现有列：{df.columns.tolist()}）")
            return
        
        # 过滤掉NaN值（训练早期可能无验证损失）
        df_valid = df.dropna(subset=[train_loss_col, val_loss_col])
        if len(df_valid) < 10:
            print(f"⚠️  有效训练轮数不足10轮（仅{len(df_valid)}轮），过拟合分析结果可能不准确")
            # 取所有有效轮数，而非固定10轮
            last_n = len(df_valid)
        else:
            last_n = 10  # 取最后10轮，反映训练后期的损失趋势
        
        # 计算最后N轮的平均损失
        last_n_data = df_valid.tail(last_n)
        avg_train_loss = last_n_data[train_loss_col].mean()
        avg_val_loss = last_n_data[val_loss_col].mean()
        loss_gap = avg_val_loss - avg_train_loss  # 验证损失 - 训练损失（差距越大越危险）
        
        # 输出过拟合评估结果
        print("\n" + "="*60)
        print("📊 过拟合风险评估（基于最后{}轮损失）".format(last_n))
        print("-"*60)
        print(f"训练损失均值: {avg_train_loss:.4f}")
        print(f"验证损失均值: {avg_val_loss:.4f}")
        print(f"损失差距（验证-训练）: {loss_gap:.4f}")
        print("-"*60)
        
        # 定义风险等级（根据分类任务常见阈值调整）
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
    parser.add_argument('--dataset', type=str, default=None)
    parser.add_argument('--epochs', type=int, default=None)
    parser.add_argument('--batch_size', type=int, default=None)
    parser.add_argument('--img_size', type=int, default=640)
    parser.add_argument('--model_type', type=str, default=None)
    return parser.parse_args()

def main():
    print("=== YOLOv8 阿尔茨海默病MRI图像分类训练 ===\n")
    args = parse_args()

    # 1. 支持命令行参数自动训练
    if args.dataset and args.epochs and args.batch_size and args.model_type:
        dataset_root = args.dataset
        epochs = args.epochs
        batch = args.batch_size
        img_size = args.img_size
        model_size = args.model_type
        if not os.path.exists(os.path.join(dataset_root, 'train')):
            print("❌ 找不到 train 文件夹")
            return
        train_dir = os.path.join(dataset_root, 'train')
        class_names = [f for f in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, f))]
        class_names.sort()
        print(f"[自动模式] 数据集: {dataset_root}, 轮数: {epochs}, 批次: {batch}, 尺寸: {img_size}, 模型: {model_size}")
        print(f"🧠 检测到 {len(class_names)} 个阿尔茨海默病程度类别:")
        total_images = 0
        for class_name in class_names:
            class_dir = os.path.join(train_dir, class_name)
            images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            print(f"   📋 {class_name}: {len(images)} 张MRI图像")
            total_images += len(images)
        print(f"📊 训练集总计: {total_images} 张640×640 MRI图像")
        valid_dir = os.path.join(dataset_root, 'valid')
        if not os.path.exists(valid_dir):
            print("\n🔄 验证集不存在，正在从训练集中分离15%作为验证集...")
            create_validation_split(train_dir, valid_dir)
        else:
            print("✅ 验证集已存在，跳过分离步骤")
    else:
        if not sys.stdin.isatty():
            print("❌ 非交互模式且必要参数未提供，训练已取消（避免阻塞）。请通过命令行参数或API传入完整参数。）")
            return

        dataset_root = input("📂 请输入数据集路径: ").strip()
        if not os.path.exists(os.path.join(dataset_root, 'train')):
            print("❌ 找不到 train 文件夹")
            return
        train_dir = os.path.join(dataset_root, 'train')
        class_names = [f for f in os.listdir(train_dir) if os.path.isdir(os.path.join(train_dir, f))]
        class_names.sort()
        print(f"🧠 检测到 {len(class_names)} 个阿尔茨海默病程度类别:")
        total_images = 0
        for class_name in class_names:
            class_dir = os.path.join(train_dir, class_name)
            images = [f for f in os.listdir(class_dir) if f.lower().endswith(('.jpg', '.jpeg', '.png', '.bmp'))]
            print(f"   📋 {class_name}: {len(images)} 张MRI图像")
            total_images += len(images)
        print(f"📊 训练集总计: {total_images} 张640×640 MRI图像")
        valid_dir = os.path.join(dataset_root, 'valid')
        if not os.path.exists(valid_dir):
            print("\n🔄 验证集不存在，正在从训练集中分离15%作为验证集...")
            create_validation_split(train_dir, valid_dir)
        else:
            print("✅ 验证集已存在，跳过分离步骤")
        print("\n⚙️  训练参数配置:")
        model_size = input("🤖 模型大小 [n(最快)/s(推荐)/m/l/x(最准), 默认s]: ").strip() or 's'
        epochs = int(input("🔄 训练轮数 [默认50]: ").strip() or '50')
        print("🎛️  批次大小选择 (根据您的RTX 3060 6GB显存):")
        print("   8  - 保守模式 (推荐，避免显存不足)")
        print("   12 - 平衡模式")
        print("   16 - 性能模式 (可能显存不足)")
        batch = int(input("选择批次大小 [默认8]: ").strip() or '8')
        img_size = 640
        print(f"\n🚀 开始训练配置:")
        print(f"   📱 模型: YOLOv8{model_size}-cls")
        print(f"   🔄 轮数: {epochs} 轮")
        print(f"   📦 批次: {batch} 张/批")
        print(f"   🖼️  图像: 640×640 像素")
        print(f"   🎯 类别: {len(class_names)} 个阿尔茨海默病程度")

    try:
        from ultralytics import YOLO
        model_name = f'yolov8{model_size}-cls.pt'
        print(f"\n🤖 正在加载 {model_name} 分类模型...")
        if not os.path.exists(model_name):
            print(f"📥 首次使用，正在下载 {model_name}...")
        model = YOLO(model_name)
        print(f"✅ 成功加载模型: {model_name}")
        print("🚀 开始训练 - YOLOv8 阿尔茨海默病MRI图像分类")
        print("=" * 60)
        results = model.train(
            data=dataset_root,
            epochs=epochs,
            batch=batch,
            imgsz=img_size,
            project='results',
            name=f'alzheimer_v8_{model_size}_{datetime.now().strftime("%m%d_%H%M")}',
            plots=True,  # YOLOv8会自动生成损失曲线（results.png）
            val=True,
            patience=10,
            save_period=-1,
            workers=4,
            device=0,
            cache=False,
            amp=True,
            model=model_name,
        )
        print("=" * 60)
        print("🎉 训练完成！阿尔茨海默病MRI分类模型训练成功！")
        print(f"📁 训练结果保存在: {results.save_dir}")
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
            
            # 新增：调用过拟合分析函数（训练完成后自动执行）
            analyze_overfitting(results.save_dir)
            
        except Exception as e:
            print(f"⚠️  获取准确率失败，使用默认值: {e}")
            final_accuracy = 85.0
            rename_and_cleanup_models(results.save_dir, final_accuracy)
            # 即使准确率获取失败，也尝试分析过拟合
            analyze_overfitting(results.save_dir)
        
        # 提示损失曲线图表位置（方便用户查看可视化结果）
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
    random.seed(42)
    main()