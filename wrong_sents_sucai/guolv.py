import json

# 读取你已经合并好的文件
with open("病句题_合并结果.json", "r", encoding="utf-8") as f:
    data = json.load(f)

# 过滤每一类中不满足条件的项
for key in ["25", "35", "45"]:
    data[key] = [item for item in data[key] if len(item["sent_mistake"]) >= 15]

# 保存过滤后的结果
with open("病句题_筛选后.json", "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("筛选完成，已保存为：病句题_筛选后.json")
