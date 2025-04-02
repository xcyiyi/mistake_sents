import json
import glob

# 初始化合并结果
merged_data = {"25": [], "35": [], "45": []}

# 找到当前目录下所有 JSON 文件（你可以改为具体路径或文件名列表）
json_files = ["病句题_重新分类.json", "病句题_重新分类_1.json", "病句题_重新分类_2.json", "病句题_重新分类_3.json", "病句题_重新分类_4.json"]


# 遍历每个 JSON 文件并合并
for file in json_files:
    with open(file, "r", encoding="utf-8") as f:
        data = json.load(f)
        for key in ["25", "35", "45"]:
            merged_data[key].extend(data.get(key, []))

# 保存合并后的结果
with open("病句题_合并结果.json", "w", encoding="utf-8") as f:
    json.dump(merged_data, f, ensure_ascii=False, indent=2)

print("合并完成，保存为：病句题_合并结果.json")
