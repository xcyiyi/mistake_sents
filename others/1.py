# -*- coding: utf-8 -*-
import os
import re
import time
import uuid
import glob
import json
import shutil
import random
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
    
    dict_sents_confuse = {10: [], 20: [], 30: []}
    dict_sents_mistake = {10: [], 20: [], 30: []}
    
    for length in dict_sents:
        for sent in dict_sents[length]:
            response = client.chat.completions.create(
            model= MODEL_ID,
            messages=[{"role": "user", "content":
                        f"你是一名经验丰富的语文老师，请站在出题的角度，判断下面这个句子适合改写为病句还是歧义句，两者一定得选一种：{sent}\n"
                        '''输出要求：如果适合改写为病句，请直接输出:“病句”；如果适合改写为歧义句；请直接输出“歧义句”
                           输出示例：病句''' }]
    )
            sent_type = response.choices[0].message.content.strip()
            print(sent_type)
            if sent_type == "病句":
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages = [{"role": "user", "content": 
                        f"""你是一位专业的语文教师，需要将下面这个正确的句子改写为病句，并输出所选的错误类型和改写后的句子。
                        
                        原句：
                        {sent}

                        错误类型列表（只选一个大类）：
                        {grammar_error_types}

                        要求：
                        1. 仔细分析原句，选出最合适的一种错误类型
                        2. 根据该错误类型进行改写
                        3. 仅对必要部分进行调整，保持句子长度相近
                        4. 禁止添加解释，不使用任何标注

                        最终输出格式：
                        错误类型：XXX
                        改写句：YYY

                        示例输出：
                        错误类型：成分残缺
                        改写句：虽然他很努力。

                        注意：只输出这两行，不要附加解释。"""
                    }]
                )
                content = response.choices[0].message.content.strip()

                # 解析错误类型和改写句
                match = re.search(r"错误类型[:：]\s*(.+?)\s*改写句[:：]\s*(.+)", content)
                if match:
                    error_type = match.group(1).strip()
                    mistake_sent = match.group(2).strip()
                else:
                    error_type = "未知"
                    mistake_sent = content  # fallback

                dict_sents_mistake[length].append({
                    "sent_correct": sent,
                    "sent_mistake": mistake_sent,
                    "error_type": error_type
                })

                print(mistake_sent)
            else:
                response = client.chat.completions.create(
                    model=MODEL_ID,
                    messages = [{"role": "user", "content":
                        f"""请你作为出题教师，将下面这个句子改写为一种歧义句，并指出所使用的歧义类型。
                        
                        原句：
                        {sent}

                        可选歧义类型列表（只选一种大类）：
                        {ambiguity_error_types}

                        输出格式：
                        歧义类型：XXX
                        改写句：YYY

                        注意：只输出这两行，不要附加解释。"""
                    }]
                )
                content = response.choices[0].message.content.strip()
                match = re.search(r"歧义类型[:：]\s*(.+?)\s*改写句[:：]\s*(.+)", content)
                if match:
                    error_type = match.group(1).strip()
                    confuse_sent = match.group(2).strip()
                else:
                    error_type = "未知"
                    confuse_sent = content

                dict_sents_confuse[length].append({
                    "sent_correct": sent,
                    "sent_confuse": confuse_sent,
                    "error_type": error_type
                })

         
    return dict_sents_confuse, dict_sents_mistake

def save_results(data, filename):
    """ 保存到当前路径 """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    os.makedirs("result/言语_歧义病句/通过验证", exist_ok=True)
    os.makedirs("result/言语_歧义病句/部分通过", exist_ok=True)
    os.makedirs("result/言语_歧义病句/失败试题", exist_ok=True)

    # 从 JSON 文件加载数据
    with open("20250325_web_gongwu.json_articles.json", "r", encoding="utf-8") as f:
        material_list = json.load(f)

    dict_sents = extract_senteces(material_list, n=1)
    save_results(dict_sents, "句子.json")
    # with open('句子.json', 'r', encoding='utf-8') as f:
    #     dict_sents = json.load(f)
    dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    save_results(dict_sents_confuse, "歧义句.json")
    save_results(dict_sents_mistake, "病句.json")
    print(f"文件已保存至：{os.getcwd()}")
    # dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    # list_sents = random.choices(dict_sents_confuse[20], k=4)