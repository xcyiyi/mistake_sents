import os
import time
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

        # 随机题型（如未指定）
        self.quest_type = quest_type or random.choice(["选是题", "选非题"])

        # === 执行流程 ===
        info = self.step_01_generate_question(self.sent_list, self.quest_type)
        ai_ans = self.step_02_check_by_ai(info["options_only"])
        result = self.step_03_judge_and_sort(info["file_path"], info["correct_answer"], ai_ans)


    def step_01_generate_question(self, sent_list, quest_type="选是题"):
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

请输出完整题目如下格式：
{stem}
A. ...
B. ...
C. ...
D. ...

正确答案：X
解析：
第一步：……
第二步：……
因此，选择X。
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
        """让GPT做题，只输出A~D"""
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
            print(f"❌ AI选择错误：应为 {correct_answer}，AI 选了 {ai_answer}")
        dst_folder = os.path.join(self.task_folder, result)
        shutil.move(file_path, os.path.join(dst_folder, os.path.basename(file_path)))
        return result

if __name__ == '__main__':

    with open('病句.json', 'r', encoding='utf-8') as f:
        dict_sents = json.load(f)
    print(dict_sents.keys())
    for _ in range(5):
        list_sents = random.choices(dict_sents['20'], k=4)

        # 一行出题 + 检查 + 保存
        QUEST_definition_infer(list_sents)
