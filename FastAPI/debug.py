import os
from collections import Counter

labels_root = r'D:\GraduationProject\yolo_alzheimer\labels\valid\Very Mild Impairment'  # 改成你的 labels 父目录（递归查找）
cnt = Counter()
for root, _, files in os.walk(labels_root):
    for f in files:
        if f.endswith('.txt'):
            p = os.path.join(root, f)
            with open(p,'r') as fh:
                for line in fh:
                    parts = line.strip().split()
                    if not parts: continue
                    cls = int(float(parts[0]))
                    cnt[cls]+=1
print('class id counts:', cnt)