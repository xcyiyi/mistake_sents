import json

# 读取筛选后的文件
with open("病句题_筛选后.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 创建新结构用于去重
deduped_data = {"25": [], "35": [], "45": []}
seen = set()

for key in ["25", "35", "45"]:
    for item in data[key]:
        # 用 sent_mistake 作为唯一性判断
        identifier = item["sent_mistake"]
        if identifier not in seen:
            seen.add(identifier)
            deduped_data[key].append(item)

# 保存去重后的结果
with open("病句题_最终结果.json", "w", encoding="utf-8") as f:
    json.dump(deduped_data, f, ensure_ascii=False, indent=2)

print("去重完成，保存为：病句题_最终结果.json")
