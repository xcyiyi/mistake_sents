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
from loguru import logger


class QUEST_definition_infer():

    def step_01_analysis(self, list_sents, quest_type):
        """ 给出对应试题的解析结果
        """
        answer_letter = random.choice(["A", "B", "C", "D"])
        list_choices = []
        if quest_type == "选是题":
            for choice, c in zip(list_sents, ["A", "B", "C", "D"]):
                if c == answer_letter:
                    list_choices.append(choice["sent_correct"])
                else:
                    list_choices.append(choice["sent_mistake"])
        return list_choices, analysis, answer_letter

    def step_02_machine_check(self, quest_str, choices_str):
        """ 给出命题解析，从做题角度，再对 AI 做一次，从而判断
        """
        ai_answer = "A" # 由新的 GPT 来完成结果
        return quest_analysis, ai_answer

    def step_03_checker(self, quest_analysis, ai_answer, set_answer):
        """ 对结果进行质检，筛选出更符合要求的结果
        """
        quest_status = "通过验证"
        # 1.直接判断答案，不符合要求，则解析不合格，直接 PASS
        if ai_answer != set_answer:
            print("答案验证失败 AI %s, 命题 %s" % (ai_answer, set_answer))
            return "失败试题"
        return quest_status

    # @utils.try_except_decorator
    def __init__(self, list_sents, quest_type=None):
        """ 定义所有初始化变量场景
        """
        ts = time.time()
        current_time = datetime.now()
        if quest_type is None:
            quest_type = random.choice(["选是题", "选非题"])
        logger.info("\n%s, %s" % ("\n".join(list_sents), quest_type))

        self.quest_uuid = current_time.strftime("%Y%m%d_%H%M%S_") + str(uuid.uuid4())
        self.list_sents = list_sents
        self.quest_type = quest_type
        self.total_tokens = 0
        self.task_folder = "result/言语_歧义病句"
        self.file_log = os.path.join(self.task_folder, self.quest_uuid + ".txt")

        # 1.解析这个题
        list_choices, analysis, set_answer = self.step_01_analysis(list_sents, quest_type)
        # 2.机器视角解题
        quest_analysis, ai_answer = self.step_02_machine_check(list_choices, analysis)
        
        # # =================================
        # # 输出最后结果与可视化
        # # =================================
        # print("*" * 50)
        # print("total tokens", self.total_tokens, "cost time", round(time.time() - ts, 3))
        # print("*" * 50)
        # quest_res = {
        #     "stem": "依次填入画横线部分最恰当的一项是：", 
        #     "choices": choices_str.replace("\\n", "\n"),
        #     "answer_letter": ai_answer, 
        #     "analysis": analysis.strip(), 
        #     "quest_type": num_blanks, 
        #     "knowledge": "",
        #     "material": material_for_student,
        #     "tokens": self.total_tokens,
        #     "quest_uuid": self.quest_uuid
        # }
        # self.quest_res = quest_res
        # self.quest_res_vis = "\n".join(utils.print_vis(quest_res, self.file_log))

        # 将数据移动检测后数据文件夹
        # 3.质检试题结果
        quest_status = self.step_03_checker(analysis, ai_answer, set_answer)
        logger.info(quest_status)
        shutil.move(self.file_log, os.path.join(self.task_folder, quest_status, self.quest_uuid + ".txt"))


######################################
# 准备本题基础素材与内容
######################################
def extract_senteces(material):

    """ 从材料里抽取合适用于命题的句子
    """
    # 存储对应句子与内容
    dict_sents = {10: [], 20: [], 30: []}
    material_for_split = re.sub("[？！。]", lambda m: m.group() + "###", material)
    for sent in material_for_split.split("###"):
        sent_len = len(re.findall(r'[\u4e00-\u9fa5]', sent))
        if sent_len <= 10: continue
        if sent_len <= 15: dict_sents[10].append(sent)
        elif sent_len <= 25: dict_sents[20].append(sent)
        elif sent_len <= 30: dict_sents[30].append(sent)
    
    for num_len in dict_sents:
        print(num_len)
        print("\n".join(dict_sents[num_len]))
    return dict_sents


def make_mistake_errors(dict_sents):
    """ 为句子创造合适的病句，从不同的类型里选择。任务：病句/歧义句
    """
    # 0. 判断句子适合歧义句还是病句？
    # 1. 语病句合成（适合哪种错误？生成该错误句子）
    # 2. 歧义句合成
    dict_sents_confuse = {10: [], 20: [], 30: []}
    dict_sents_mistake = {10: [], 20: [], 30: []}
    # {"sent_correct": "", "sent_mistake": "", "error_type": ""}
    # 最后目的是在同等长度句子里，选择合适不同的错误，构建试题
    return dict_sents_confuse, dict_sents_mistake


if __name__ == '__main__':
    # ##########################
    # #    逻辑类比题
    # ##########################
    os.makedirs("result/言语_歧义病句/通过验证", exist_ok=True)
    os.makedirs("result/言语_歧义病句/部分通过", exist_ok=True)
    os.makedirs("result/言语_歧义病句/失败试题", exist_ok=True)
    material = "人才培养是一个循序渐进的过程，需认识、把握、尊重人才成长规律，坚持“严管”和“厚爱”相结合，人才干事创业的过程中难免有失误，如果培养者因为害怕犯错而顾虑重重、因噎废食，则违背了人才培育的初衷。所以要为人才“松绑”，建立健全正向激励和容错纠错机制，为人才成长创造宽容的环境。成员国认为，世界政治、经济形势正经历重大演变。国际体系正朝着更加公正和多极化方向发展，为各国发展和开展平等互利国际合作提供更多机遇。与此同时，强权政治抬头，践踏国际法准则的行径愈演愈烈，地缘政治对抗和冲突加剧，全球和上合组织地区稳定面临更多风险。既挂帅又出征，要坚定有力地擎起改革大旗，保持以党的自我革命引领社会革命的高度自觉，坚持用改革精神管党治党。要发挥党总揽全局、协调各方的领导核心作用，把党的领导贯穿改革各方面全过程，确保改革始终沿着正确政治方向前进。近年来因程序违法败诉的行政诉讼案件不少。尽管有前车之鉴，但是依然不乏职能部门重蹈覆辙。说到底，还是“重结果，轻程序”，不把程序当回事，行政行为自然经不起推敲。程序是保证我们有效实现结果的合理设计，程序正当得不到尊重，必然给我们的事业造成损害。画面展示了夺取七月革命胜利关键时刻的巷战场面。构图：全画采取顶天立地的三角构图形式，倒在地上的尸体、战斗的勇士以及高举法兰西旗帜的女子，构成一个稳定又蕴藏动势的三角形，象征自由、平等、博爱的三色旗位于等腰三角形的顶点，远景处是朦胧的圣母院塔楼，构图井然有序，细节刻画丰富生动。内容：以一个象征自由女神的女子形象为主体，招呼着后方的人民，将神话中的自由女神与浴血奋战的人民安排到一起，紧跟她前后左右的是工人、市民、孩子、学生等。要有啃硬骨头的勇气。改革进入攻坚期和深水区，深层次的矛盾日益凸显。同时，随着社会结构和利益格局发生深刻变化，协调各方面利益和达成改革共识、形成改革合力的难度加大；改革越来越触及现有利益格局，涉及深层次利益调整的重大改革阻力较大；经济社会双重转型的压力，思想观念多元多样的碰撞，让深化改革的脚步面临新的重重羁绊。小切口带来大突破，由此观察新时代科技体制改革，从“大局上谋势”绘制改革蓝图，到“细微处落子”解决科研人员的烦心事，从破除“四唯”，到建立“揭榜挂帅”制度，科技体制改革全面发力、多点突破、纵深发展，以改革的点火系点燃了创新的新引擎。“天问”“嫦娥”叩问浩瀚苍穹，“奋斗者”号、“深海一号”突破极限海深，“新三样”铸就中国名片，创新成果喷涌、创新活力奔涌、创新动能潮涌，展现着新时代全面深化改革的壮丽气象。此外，保险公司还利用科技手段提升应急响应能力。通过大数据和人工智能技术，保险公司可以实时监测灾害动态，预测风险，优化资源调度，提高理赔效率。例如，为确保受灾客户能快速获得赔付，阳光财险第一时间开通报案理赔“绿色通道”，95510客服专线、“阳光财险”小程序、“阳光车生活”APP等客户端提供24小时自助报案服务及线上查勘定损服务，线上“一键赔”团队全员在岗待命。数字赋能，文旅融合，以旅彰文，得到活化利用的运河文化成为时尚潮流，彰显古今共融的历史文化魅力。在北源头白浮泉，人们欣赏着“国风音乐节”，在运河集市上选购着国潮文创；在大光楼边，灯光变幻着古代漕运的景象，孔明灯升起，AI水兽将燃灯塔的故事缓缓道来。北京通州大运河智慧景区创建工作，通过AR、VR、MR等数字技术手段，打造漕粮进京、运河风韵、通州八景等一系列场景，一部手机“游”运河已成游客的独特体验，在大运河博物馆，人们可以沉浸式体验运河码头繁忙场景，让游客沉浸式体验大运河的古今交融。“和而不同”思想作为中国传统文化中的一个重要理念，最早见于《论语·子路》。《国语·郑语》记载：“去和而取同。夫和实生物，同则不继”，“和”是一种差异性、多样性的统一，强调在和谐的基础上包容差异，既追求和谐共处，又尊重和包容多样性。在祖国东北，从黑龙江哈尔滨站启程，乘坐“冰雪列车”前往中国最北端，一路穿行于林海雪原之间，眼前尽是无垠的北国雪景。而在西北边陲，从新疆乌鲁木齐出发，登上“雪国列车”驶向阿勒泰，沿途跨越天山山脉，目光所及则是层峦叠嶂的雪山风光……这个冬天，铁路不仅仅是交通工具，还化身为连接现实与冰雪童话世界的纽带，让每位旅客都能感受到冬日限定的浪漫与激情。"

    dict_sents = extract_senteces(material)
    dict_sents_confuse, dict_sents_mistake = make_mistake_errors(dict_sents)
    list_sents = random.choices(dict_sents_confuse[20], k=4)

    QUEST_definition_infer(list_sents)