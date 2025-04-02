import os
import time
import re
import json
import random



def extract_sentences(material_list, n=None):
    """从材料中抽取适合用于命题的较长句子（30、40、50字左右）"""
    if n and 0 < n <= len(material_list):
        selected_materials = random.sample(material_list, n)
    else:
        selected_materials = material_list

    dict_sents = {30: [], 40: [], 50: []}

    for material in selected_materials:
        text = material.get('text', '').replace('\n', '').strip()
        # 添加分隔符用于切分句子
        material_for_split = re.sub(r"[？！。]", lambda m: m.group() + "###", text)

        for sent in material_for_split.split("###"):
            sent = sent.strip()
            sent_len = len(re.findall(r'[\u4e00-\u9fa5]', sent))

            if sent_len < 25:
                continue
            elif sent_len <= 35:
                dict_sents[30].append(sent)
            elif sent_len <= 45:
                dict_sents[40].append(sent)
            elif sent_len <= 55:
                dict_sents[50].append(sent)

    return dict_sents



def save_results(data, filename):
    """ 保存到当前路径 """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


with open("20250325_web_gongwu.json_articles.json", "r", encoding="utf-8") as f:
    material_list = json.load(f)

dict_sents = extract_sentences(material_list, n=5)
save_results(dict_sents, "句子_long_1.json")   