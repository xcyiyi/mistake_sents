import re
import json
import time
from docx import Document
from openai import OpenAI
from loguru import logger
from ast import literal_eval


API_KEY = "6a6c1dd5-e0a2-4503-b93d-8a6e055a8da8"
BASE_URL = "https://ark.cn-beijing.volces.com/api/v3"
MODEL_ID = "ep-m-20250326210421-j5plz"

client = OpenAI(
    base_url=BASE_URL,
    api_key=API_KEY
)


def clean_json_output(output):
    """清理非JSON内容，支持单引号、注释等不规范格式"""
    # 清理注释和空白
    output = re.sub(r'//.*|#.*', '', output)
    output = output.strip()

    # 精准替换外层单引号为双引号（保留内容中的单引号）
    json_str = re.sub(
        r"""(['"])((?:(?!\1).|\\\1)*)\1""",  # 匹配引号包裹的字符串
        lambda m: f'"{m.group(2)}"' if m.group(1) == "'" else m.group(0),
        output,
        flags=re.DOTALL
    )
    # 尝试标准JSON解析
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        logger.warning(f"标准JSON解析失败，尝试宽松解析: {e}")
    # 宽松解析：尝试Python字面量语法（支持单引号）
        try:
            return literal_eval(json_str)
        except Exception as e:
            logger.error(f"宽松解析失败: {e}")
            return None

# 第一步：从 Word 提取题目编号与题干
def extract_questions_from_doc(docx_path):
    doc = Document(docx_path)
    paragraphs = [p.text.strip() for p in doc.paragraphs if p.text.strip()]

    questions = {}
    current_q = None
    buffer = []

    for line in paragraphs:
        if re.match(r'^\d+．', line):  # 题号开头，如“8．”
            if current_q:
                questions[current_q] = "\n".join(buffer)
            current_q = re.match(r'^(\d+)．', line).group(1)
            buffer = [line]
        elif current_q:
            buffer.append(line)

    if current_q:
        questions[current_q] = "\n".join(buffer)

    return questions

# 第二步：调用 GPT 获取病句结构化信息
def ask_gpt(question_text, qid):
    prompt = f"""
你是一位语文病句分析专家，请从以下病句选择题中提取所有存在语病的选项。
你需要判断每个病句的原句长度，一定要严格按照字数分类，并将其分类如下：

- 25：如果原句长度小于等于30字；
- 35：如果原句在30-40字之间；
- 45：如果原句大于40字。

请按照以下格式严格返回（不要有额外解释）：

{{
  "25": [
    {{
      "sent_correct": "修改后的正确句子",
      "sent_mistake": "题干中的原句",
      "error_type": "语病类型"
    }}
  ],
  "35": [],
  "45": []
}}

要求：
1.每个病句的原句长度必须准确判断，不能根据字数猜测；
2.分类时一定按照原句长度严格划分，不能出现错误；
3.每个原句和病句必须完整保留选项中的原句，不能截断。

以下是题目内容：
{question_text}
"""


    for _ in range(3):  # 最多尝试三次
        try:
            response = client.chat.completions.create(
                model= MODEL_ID,
                messages=[{"role": "user", "content": prompt}]
            )
            print(response.choices[0].message.content.strip())
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"调用 GPT 失败：{e}")
            time.sleep(2)

    return None

# 第三步：遍历所有题目，保存结果为 JSON 文件
def build_error_json(docx_path, output_path):
    all_questions = extract_questions_from_doc(docx_path)
    final_result = {"25": [], "35": [], "45": []}  # 初始化分区结构

    # max_questions = 5  # 只处理前5题
    # count = 0

    for qid, qtext in all_questions.items():
        # if count >= max_questions:
        #     break

        print(f"📌 正在处理第 {qid} 题...")
        gpt_result = ask_gpt(qtext, qid)

        try:
            parsed = clean_json_output(gpt_result)
            for length_key in ["25", "35", "45"]:
                if length_key in parsed:
                    final_result[length_key].extend(parsed[length_key])
        except Exception as e:
            print(f"❌ 第 {qid} 题解析失败，GPT 返回内容：\n{gpt_result}\n错误信息：{e}")
            continue

        # count += 1  # 成功处理后增加计数

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(final_result, f, ensure_ascii=False, indent=2)

    print(f"\n处理完成，结果已保存至：{output_path}")

# 运行入口
if __name__ == "__main__":
    # 修改为你本地的文件路径
    docx_path = "初中_2.docx"
    output_path = "病句题结构化结果_4.json"
    build_error_json(docx_path, output_path)
