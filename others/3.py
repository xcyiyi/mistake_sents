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
    
    dict_sents_confuse = {10: [], 20: [], 30: []}
    dict_sents_mistake = {10: [], 20: [], 30: []}
    
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
                print(confuse_sent)
         
    return dict_sents_confuse, dict_sents_mistake


def save_results(data, filename):
    """ 保存到当前路径 """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


class QUEST_definition_infer():
    def __init__(
        self,
        sent_list,
        quest_type=None,
        task_folder="result/言语_歧义病句",
    ):
        """
        初始化即执行整个流程：
        - 题目生成
        - AI 验证
        - 分类保存
        """
        self.sent_list = sent_list
        self.task_folder = task_folder


        # 创建保存目录
        os.makedirs(task_folder, exist_ok=True)
        os.makedirs(os.path.join(task_folder, "通过验证"), exist_ok=True)
        os.makedirs(os.path.join(task_folder, "失败试题"), exist_ok=True)

        # 随机题型
        self.quest_type = quest_type or random.choice(["选是题", "选非题"])

        # === 执行流程 ===
        info = self.step_01_generate_question(self.sent_list, self.quest_type)
        ai_ans = self.step_02_check_by_ai(info["options_only"])
        result = self.step_03_judge_and_sort(info["file_path"], info["correct_answer"], ai_ans)


    def step_01_generate_question(self, sent_list, quest_type):
        """生成题目 + 保存到txt"""

        assert len(sent_list) == 4, "必须传入4个句子！"

        error_type = "病句" if "sent_mistake" in sent_list[0] else "歧义句"
        answer_letter = random.choice(["A", "B", "C", "D"])
        list_choices = []

        for c, item in zip(["A", "B", "C", "D"], sent_list):
            wrong = item.get("sent_mistake") or item.get("sent_confuse")
            right = item["sent_correct"]
            list_choices.append(
                right if c == answer_letter and quest_type == "选是题"
                else wrong if c == answer_letter and quest_type == "选非题"
                else right
            )

        # 构造题干
        stem = f"下列句子中，{'没有语病' if quest_type == '选是题' else '有语病'}的一项是：" if error_type == "病句" \
            else f"下列句子中，{'不存在歧义' if quest_type == '选是题' else '存在歧义'}的一项是："

        options = "\n".join([f"{c}. {txt}" for c, txt in zip(["A", "B", "C", "D"], list_choices)])
        correct_sent = list_choices[["A", "B", "C", "D"].index(answer_letter)]

        prompt = f"""
你是一名专业语文出题老师，请根据以下题干与选项，生成一道标准选择题，包括详细解析。
题干：{stem}
选项：
{options}

正确答案：{answer_letter}
正确选项内容：{correct_sent}

输出示例：
下列句子中，有语病的是：
A.中国农业对外开放的大门不会关上，如果中美贸易摩擦不断升级，其他竞争对手将占据美国在中国失去的市场份额。
B.新疆地广人稀，面积166万平方公里，是中国陆地面积最大的省级行政区。
C.八十挂零的耄耋老翁，还能在网球场上跑动，还能跳起拦网，这多少还是能引起很多人的好奇和点赞的！
D.有一晚风大雨大，早上出门只见地下厚厚一层落叶被晨光照得一片金黄，抬头看树上的叶子也是一片金黄，宛如一幅巨大的立体油画。
答案：C
解析：
第一步，审题干，找出有病句的一项。
第二步，对比选项。C项“耄耋”指八九十岁，“八十挂零”指八十多岁，两者语义重复。A项、B项和D项表述明确，没有语病。
因此，选择C选项
""".strip()

        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}]
        )
        full_question = response.choices[0].message.content.strip()

        quest_id = datetime.now().strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())
        file_path = os.path.join(self.task_folder, f"{quest_id}.txt")
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(full_question)

        return {
            "question_id": quest_id,
            "file_path": file_path,
            "question_text": full_question,
            "correct_answer": answer_letter,
            "options_only": f"{stem}\n{options}"
        }


    def step_02_check_by_ai(self, options_only):
        """让AI做题，只输出A~D"""
        prompt = f"""你是一位语文考生，请阅读下列选择题并选择一个你认为正确的答案（只输出选项字母A~D）：

{options_only}

请严格只输出一个大写字母，例如 A、B、C 或 D。
"""
        response = client.chat.completions.create(
            model=MODEL_ID,
            messages=[{"role": "user", "content": prompt}]
        )
        ai_choice = response.choices[0].message.content.strip().upper()
        return ai_choice if ai_choice in "ABCD" else "无效"


    def step_03_judge_and_sort(self, file_path, correct_answer, ai_answer):
        """对比AI答案并移动文件"""
        result = "通过验证" if ai_answer == correct_answer else "失败试题"
        if ai_answer != correct_answer:
            print(f" AI选择错误：应为 {correct_answer}，AI 选了 {ai_answer}")
        dst_folder = os.path.join(self.task_folder, result)
        shutil.move(file_path, os.path.join(dst_folder, os.path.basename(file_path)))
        return result
    

if __name__ == '__main__':
    os.makedirs("result/言语_歧义病句/通过验证", exist_ok=True)
    os.makedirs("result/言语_歧义病句/失败试题", exist_ok=True)

    # 从 JSON 文件加载数据
    with open("20250325_web_gongwu.json_articles.json", "r", encoding="utf-8") as f:
        material_list = json.load(f)

    dict_sents = extract_senteces(material_list, n=5)
    save_results(dict_sents, "句子.json")
    # with open('句子.json', 'r', encoding='utf-8') as f:
    #     dict_sents = json.load(f)
    dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    save_results(dict_sents_confuse, "歧义句.json")
    save_results(dict_sents_mistake, "病句.json")
    print(f"文件已保存至：{os.getcwd()}")

    # dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    list_sents = random.choices(dict_sents_confuse[20], k=4)
    QUEST_definition_infer(list_sents)