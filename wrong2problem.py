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



class QUEST_definition_infer():
    def __init__(
        self,
        sent_list,
        quest_type=None,
        task_folder="result1/言语_歧义病句",
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
    # # 从 JSON 文件加载数据
    # with open("20250325_web_gongwu.json_articles.json", "r", encoding="utf-8") as f:
    #     material_list = json.load(f)

    # dict_sents = extract_senteces(material_list, n=5)
    # save_results(dict_sents, "句子.json")
    # # with open('句子.json', 'r', encoding='utf-8') as f:
    # #     dict_sents = json.load(f)
    # dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    # save_results(dict_sents_confuse, "歧义句.json")
    # save_results(dict_sents_mistake, "病句.json")
    # print(f"文件已保存至：{os.getcwd()}")

    # dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    with open("病句.json", "r", encoding="utf-8") as f:
        dict_sents_mistake = json.load(f)

    for key in ["10", "20", "30"]:
        print(f"\n===== 类别 {key} 开始抽样 =====")
        for i in range(4):
            list_sents = random.sample(dict_sents_mistake[key], k=4)
            print(list_sents)
            QUEST_definition_infer(list_sents)