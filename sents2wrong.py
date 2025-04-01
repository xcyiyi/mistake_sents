import os
import time
import re
import uuid
import random
import shutil
import json
from datetime import datetime
from openai import OpenAI

API_KEY = "6a6c1dd5-e0a2-4503-b93d-8a6e055a8da8"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL_ID = "ep-m-20250324154533-l67m6"

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)

grammar_error_types = {
    "搭配不当": {
        "主谓搭配不当": {
            "description": "主语与谓语逻辑或语法不匹配",
            "examples": ["他的笑容和教导出现在眼前（'教导'无法'出现'）"]
        },
        "主宾搭配不当": {
            "description": "主语与宾语关系矛盾",
            "examples": ["影视作品的上映受到喜爱（'上映'与'代入感'无关）"]
        },
        "动宾搭配不当": {
            "description": "动词与宾语逻辑冲突",
            "examples": ["减轻喧嚣（'喧嚣'应搭配'减少'）"]
        },
        "关联词搭配不当": {
            "description": "关联词逻辑关系错误",
            "examples": ["只要...才...（应改为'只有...才...'）"]
        },
        "两面对一面": {
            "description": "前文包含正反两面，后文仅对应单面",
            "examples": ["能否成为读书人...关键在于兴趣（应补充'是否'）"]
        }
    },
    "成分残缺": {
        "缺主语": ["通过举办活动，让同学们...（删'通过'或'让'）"],
        "缺谓语": ["人们通过平台一系列交易（补'完成'）"],
        "缺宾语": ["满足未来（补'需求'）"]
    },
    "成分冗余": {  
        "语义重复": ["智商智力（删其一）", "愈发日久弥坚（删'愈发'）"],
        "虚词多余": ["超过200多万人（删'超过'或'多'）"]
    },
    "语序不当": {
        "谓语顺序错误": ["纠正并发现（应'发现并纠正'）"],
        "修饰语位置错误": {
            "定语": ["灿烂辉煌的许多（应'许多灿烂辉煌的'）"],
            "状语": ["应该发挥充分的作用（'充分'应置'发挥'前）"]
        },
        "虚词位置错误": {
            "副词": ["不努力搞好（应'不把...搞好'）"],
            "关联词": ["不但他学习...（应'他不但...'）"]
        }
    },
    "句式杂糅": {
        "混合句式": [
            "原因主要是...造成的（删'造成的'）",
            "成分是由...配制而成（删'由'或'成分是'）"
        ]
    },
    "不合逻辑": {
        "自相矛盾": ["基本上彻底解决（删'彻底'）"],
        "语义重复": ["大约5000只左右（删'大约'或'左右'）"],
        "否定不当": ["避免不犯错误（删'避免'或'不'）"],
        "分类不当": ["报刊、电视和一切出版物（删'报刊'）"],
        "表意不明": ["说服老师和你一起去（加'让我'）"]
    }
}


ambiguity_error_types = {
    "歧义句": {
        "停顿歧义": {
            "description": "句子停顿位置不同导致语义分歧",
            "examples": [
                "咬死猎人的狗（① 咬死/猎人的狗 → 狗被咬死；② 咬死猎人/的狗 → 狗咬死人）"
            ]
        },
        "主语省略歧义": {
            "description": "主语缺失引发动作主体不明确",
            "examples": [
                "他有一个儿子，在医院工作（① 儿子在医院工作；② 他在医院工作）"
            ]
        },
        "多音字歧义": {
            "description": "多音字不同发音导致语义变化",
            "examples": [
                "他还欠款两千元（① hái：仍欠款；② huán：已还款）"
            ]
        },
        "多义词歧义": {
            "description": "词语多义性引发理解分歧",
            "examples": [
                "我看不上他的演出（① 无法到场观看；② 不认可演出质量）"
            ]
        },
        "指代歧义": {
            "description": "代词指代对象不明确",
            "examples": [
                "妈妈要王玲和她的同学一起去（① 妈妈的同学；② 王玲的同学）"
            ]
        },
        "受施者歧义": {
            "description": "动作施事者与受事者关系不明确",
            "examples": [
                "这个人连王刚都不认识（① 王刚不认识此人；② 此人不认识王刚）"
            ]
        }
    }
}

######################################
# 准备本题基础素材与内容
######################################
def extract_senteces(material_list, n=None):
    """ 从材料里抽取合适用于命题的句子 """
    # 随机选择n个材料（如果n指定且有效）
    if n and 0 < n <= len(material_list):
        selected_materials = random.sample(material_list, n)
    else:
        selected_materials = material_list
    
    dict_sents = {10: [], 20: [], 30: []}
    
    for material in selected_materials:  # 遍历随机筛选后的材料
        text = material.get('text', '').replace('\n', '').strip()
        material_for_split = re.sub(r"[？！。]", lambda m: m.group() + "###", text)
        
        for sent in material_for_split.split("###"):
            sent_len = len(re.findall(r'[\u4e00-\u9fa5]', sent))
            
            if sent_len <= 10:
                continue

            if sent_len <= 15:
                dict_sents[10].append(sent)
            elif sent_len <= 25:
                dict_sents[20].append(sent)
            elif sent_len <= 30:
                dict_sents[30].append(sent)
    
    return dict_sents


def make_mistake_errors(dict_sents):
    """ 为句子创造合适的病句，从不同的类型里选择。任务：病句/歧义句 """
    
    dict_sents_confuse = {"10": [], "20": [], "30": []}
    dict_sents_mistake = {"10": [], "20": [], "30": []}
    
    for length in dict_sents:
        for sent in dict_sents[length]:
            response = client.chat.completions.create(
            model= MODEL_ID,
            messages=[{"role": "user", "content":
                        f"你是一名经验丰富的语文老师，请站在出题的角度，判断下面这个句子适合改写为病句还是歧义句，两者一定得选一种：{sent}\n"
                        '''输出要求：如果适合改写为病句，请直接输出:“病句”；如果适合改写为歧义句；请直接输出“歧义句”
                           输出示例1：病句
                           输出示例2：歧义句
                           ''' }]
    )
            sent_type = response.choices[0].message.content.strip()
            print(sent_type)
                        # 步骤2：生成病句
            if sent_type == "病句":
                error_type = random.choice(list(grammar_error_types.keys()))
                print(error_type)

                prompt = f"""
你是一位专业的语文教师，请将下面这个句子改写为病句，必须体现指定的错误类型。

原句：
{sent}

指定错误类型：
{error_type}

要求：
1. 病句必须体现出该类型的问题；
2. 只对必要部分进行改写，保持整体句子长度相近；
3. 严禁添加任何解释说明，只输出结果。

输出格式：
错误类型：XXX
改写句：YYY
"""

                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.choices[0].message.content.strip()
                match = re.search(r"错误类型[:：]\s*(.+?)\s*改写句[:：]\s*(.+)", content)
                if match:
                    output_error_type = match.group(1).strip()
                    mistake_sent = match.group(2).strip()
                else:
                    output_error_type = error_type
                    mistake_sent = content

                dict_sents_mistake[length].append({
                    "sent_correct": sent,
                    "sent_mistake": mistake_sent,
                    "error_type": output_error_type
                })

                print(f"→ 病句（{output_error_type}）：{mistake_sent}")

            # 步骤3：生成歧义句
            elif sent_type == "歧义句":
                ambiguity_type = random.choice(list(ambiguity_error_types["歧义句"].keys()))

                prompt = f"""
你是一名语文教师，请将以下句子改写为一个歧义句，歧义类型必须是：{ambiguity_type}。

原句：
{sent}


要求：
1. 改写后的句子必须体现该类型歧义；
2. 保持长度相近，仅调整必要部分；
3. 严禁添加解释，只输出结果。

输出格式：
歧义类型：XXX
改写句：YYY
"""

                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages=[{"role": "user", "content": prompt}]
                )

                content = response.choices[0].message.content.strip()
                match = re.search(r"歧义类型[:：]\s*(.+?)\s*改写句[:：]\s*(.+)", content)
                if match:
                    output_error_type = match.group(1).strip()
                    confuse_sent = match.group(2).strip()
                else:
                    output_error_type = ambiguity_type
                    confuse_sent = content

                dict_sents_confuse[length].append({
                    "sent_correct": sent,
                    "sent_confuse": confuse_sent,
                    "error_type": output_error_type
                })

                print(f"→ 歧义句（{output_error_type}）：{confuse_sent}")

    return dict_sents_confuse, dict_sents_mistake


def save_results(data, filename):
    """ 保存到当前路径 """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)



if __name__ == '__main__':
    with open("句子.json", "r", encoding="utf-8") as f:
        sents_list = json.load(f)

    dict_sents_confuse, dict_sents_mistake = make_mistake_errors(sents_list)
    save_results(dict_sents_confuse, "歧义句.json")
    save_results(dict_sents_mistake, "病句.json")