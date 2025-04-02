import json

# 读取原始 JSON 文件
with open("病句题结构化结果_4.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 创建新的分类结构
new_data = {"25": [], "35": [], "45": []}

# 遍历原有的三个分类，重新按句子长度分类
for category in ["25", "35", "45"]:
    for item in data.get(category, []):
        mistake_len = len(item["sent_mistake"])
        if mistake_len <= 30:
            new_data["25"].append(item)
        elif 30 < mistake_len <= 40:
            new_data["35"].append(item)
        else:
            new_data["45"].append(item)

# 保存为新的 JSON 文件
with open("病句题_重新分类_4.json", "w", encoding="utf-8") as f:
    json.dump(new_data, f, ensure_ascii=False, indent=2)

print("处理完成")
