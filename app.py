import streamlit as st
import base64
import random
import html
import io
import math
import time
import os
from datetime import datetime
from dataclasses import dataclass
from typing import List, Tuple

# Сторонние библиотеки должны быть установлены (pip install reportlab)
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether, Flowable
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

st.set_page_config(
    page_title="SafeDeal — экспертиза сделки",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── КОНСТАНТЫ И НАСТРОЙКИ ───────────────────

# Имена файлов шрифтов, которые ДОЛЖНЫ лежать рядом с app.py
FONT_REGULAR_FILE = "DejaVuSans.ttf"
FONT_BOLD_FILE = "DejaVuSans-Bold.ttf"
LOGO_FILE = "logo.png"

RISKS_CONFIG = [
    # ── ФИНАНСОВЫЕ СХЕМЫ ──────────────────────────────────────────────────────
    {"cat": "Финансовые схемы", "what": "Занижение цены / Притворная сделка",
     "kw": ["занижен","конверт","минимальная","неполная","расписк","в половину","половину ниже","меньше в договоре","полцены","занизить"],
     "law": "ГК РФ ст. 170. Притворная сделка ничтожна. Риск: при расторжении вернут только сумму по ДКП, а не реально уплаченную.",
     "fix": "Указывать в ДКП строго 100% реальную стоимость. Никаких расписок 'за неотделимые улучшения'.", "w": 45.0},

    {"cat": "Финансовые схемы", "what": "Занижение до 1 млн рублей",
     "kw": ["до миллиона","один миллион","1 млн"],
     "law": "ГК РФ ст. 170 / НК РФ ст. 220. ФНС вправе доначислить налог с рыночной стоимости и назначить штраф 20-40% от суммы.",
     "fix": "Отказ от схемы. Минимум — 70% от кадастровой стоимости (ниже ФНС всё равно пересчитает).", "w": 60.0},

    {"cat": "Финансовые схемы", "what": "Субсидированная ипотека от застройщика (завышение цены)",
     "kw": ["субсидир","ипотека от застройщик","нулевая ставка","0.1%","0,1%","ставка от застройщик"],
     "law": "ЦБ РФ: схема 'завышение цены + субсидированная ставка' признана рискованной. Банк может отказать в одобрении. При продаже объекта — убыток из-за разрыва между ценой ДДУ и рынком.",
     "fix": "Требовать рыночную оценку и сравнить с ценой без субсидии. Просчитать реальную переплату.", "w": 30.0},

    # ── ОБЪЕКТ ────────────────────────────────────────────────────────────────
    {"cat": "Объект", "what": "Незаконная перепланировка",
     "kw": ["перепланировк","снесли стен","мокрая точк","объединили","неузакон","переделали","снос стены"],
     "law": "ЖК РФ ст. 29. Штраф 2 000–2 500 ₽ + обязанность привести в исходное состояние (расходы 50 000–500 000 ₽). При продаже банки отказывают в ипотеке на такой объект.",
     "fix": "Требовать узаконивания до сделки или корректировки цены на стоимость работ по টানвосстановлению.", "w": 30.0},

    {"cat": "Объект", "what": "Объект в залоге (ипотека банка)",
     "kw": ["в ипотеке","залог","обременен","под залогом","ипотечн"],
     "law": "ФЗ № 102-ФЗ ст. 37. Без согласия банка-залогодержателя сделка не пройдёт регистрацию.",
     "fix": "Гашение долга через аккредитив / СБР с одновременным снятием залога. Или перевод долга на покупателя при согласии банка.", "w": 20.0},

    {"cat": "Объект", "what": "Арест или запрет на рег. действия",
     "kw": ["арест","запрет","пристав","ограничени"],
     "law": "ФЗ № 218-ФЗ ст. 26. Росреестр приостановит регистрацию. Покупатель внёс деньги — а сделку не зарегистрируют.",
     "fix": "Проверить ЕГРН перед авансом. Настоять на снятии ареста до передачи денег.", "w": 35.0},

    {"cat": "Объект", "what": "Маткапитал и детские доли",
     "kw": ["маткапитал","детск","опек","пфр","материнск","материнский капитал"],
     "law": "ФЗ № 256-ФЗ ст. 10. Обязательное выделение долей всем членам семьи. Сделка без выделения — ничтожна. Суды регулярно расторгают такие сделки спустя годы.",
     "fix": "Запросить у продавца нотариальное обязательство о выделении долей или подтверждение, что доли уже выделены (ЕГРН + свидетельства).", "w": 35.0},

    {"cat": "Объект", "what": "Свежее наследство / Завещание",
     "kw": ["наследств","завещан","умер","наследник","по наследству"],
     "law": "ГК РФ ст. 1155 (восстановление сроков) и ст. 1149 (обязательная доля). Право на долю имеют несовершеннолетние, нетрудоспособные или иждивенцы, даже если их нет в завещании.",
     "fix": "Проверить круг наследников. Требовать нотариальное заявление об урегулировании претензий и проверку на наличие лиц с правом на обязательную долю.", "w": 25.0},

    {"cat": "Объект", "what": "Приватизация — отказники",
     "kw": ["приватиз","отказ от приватиз","отказник"],
     "law": "ФЗ № 1541-1 / ЖК РФ ст. 19. Лицо, отказавшееся от приватизации, сохраняет право бессрочного проживания. Это право не прекращается при продаже.",
     "fix": "Обязательно архивная выписка из домовой книги. Добровольная выписка всех отказников до сделки с проверкой через суд при необходимости.", "w": 30.0},

    {"cat": "Объект", "what": "Скрытые прописанные / временно отсутствующие",
     "kw": ["тюрьма","армия","интернат","психиатрическ","выписан","прописан","временно отсутств","не выписан"],
     "law": "ГК РФ ст. 71 / ЖК РФ. Осуждённые, военнослужащие, пациенты психиатрических учреждений сохраняют право пользования жильём на время отсутствия.",
     "fix": "Расширенная архивная выписка из домовой книги за весь период. Обязательство о снятии с учёта подкреплённое задатком.", "w": 35.0},

    {"cat": "Объект", "what": "Договор ренты / Пожизненное содержание",
     "kw": ["рент","пожизнен","иждивен","содержание с иждивен"],
     "law": "ГК РФ ст. 599, 605. Рентополучатель вправе расторгнуть договор при ненадлежащем исполнении. Наследники рентополучателя могут оспорить сделку.",
     "fix": "Тщательная проверка: свидетельство о смерти рентополучателя, справки об отсутствии судебных дел, удостоверение нотариуса о снятии обременения.", "w": 40.0},

    {"cat": "Объект", "what": "Частые перепродажи (цепочка)",
     "kw": ["перепрода","несколько раз","менее года","цепочк"],
     "law": "ГК РФ ст. 302. Если изначально имело место мошенничество, суд может истребовать имущество даже у добросовестного приобретателя.",
     "fix": "Запросить выписку ЕГРН с историями переходов. Проверить каждого предыдущего собственника на долги и судебные дела.", "w": 35.0},

    {"cat": "Объект", "what": "Покупка с торгов / Процедура банкротства",
     "kw": ["торг","аукцион","с торгов","конкурсн","арбитражн управляющ"],
     "law": "ФЗ № 127-ФЗ ст. 61.1. Кредиторы вправе оспорить результаты торгов в течение 3 лет. Риск: Росреестр зарегистрирует право, а суд потом его аннулирует.",
     "fix": "Проверить протоколы торгов, публикации в ЕФРСБ, наличие апелляций. Не покупать ранее 6 месяцев с даты торгов.", "w": 30.0},

    {"cat": "Объект", "what": "Апартаменты (не квартира)",
     "kw": ["апартамент","нежилое","офисн","лофт","студия в бизнес"],
     "law": "ЖК РФ: апартаменты — нежилые помещения. Нельзя оформить постоянную регистрацию. Тарифы ЖКХ выше на 15–25%. Имущественный вычет не применяется.",
     "fix": "Уточнить статус объекта по ЕГРН (тип 'нежилое'). Взвесить: нет прописки, нет вычета, выше коммунальные.", "w": 25.0},

    {"cat": "Объект", "what": "Дом под снос / Реновация",
     "kw": ["снос","реновац","аварийн","ветхий","расселен","программа реновац"],
     "law": "ЖК РФ ст. 32. Жильё в аварийном доме выкупается по кадастровой стоимости, которая может быть ниже рыночной.",
     "fix": "Проверить адрес в программе реновации. Уточнить сроки и условия переселения до покупки.", "w": 40.0},

    {"cat": "Объект", "what": "Самовольная постройка / ИЖС без разрешения",
     "kw": ["самовольн","без разрешения","не введён","незарегистрирован","недострой","ижс не оформлен"],
     "law": "ГК РФ ст. 222. Самовольная постройка может быть снесена по решению суда. Право на неё не возникает до регистрации.",
     "fix": "Проверить наличие разрешения на строительство и уведомления о вводе в ЕГРН. Покупать только зарегистрированный объект.", "w": 35.0},

    {"cat": "Объект", "what": "Наложение границ / Проблемы межевания",
     "kw": ["межеван","границы не установлен","наложение границ","спор с соседом","снт","кадастр"],
     "law": "ЗК РФ ст. 60, 62. Споры о границах могут тянуться годами. Банки отказывают в ипотеке на участки без межевания.",
     "fix": "Заказать выписку ЕГРН с координатами. Убедиться в отсутствии пересечений через публичную кадастровую карту.", "w": 20.0},

    # ── ПРОДАВЕЦ ──────────────────────────────────────────────────────────────
    {"cat": "Продавец", "what": "Банкротство или долги продавца",
     "kw": ["банкрот","долг","фссп","микрозайм","исполнительн","суд","торчит","задолжал"],
     "law": "ФЗ № 127-ФЗ ст. 61.2. Сделки за 3 года до банкротства оспариваются, если цена ниже рыночной. Покупатель возвращает имущество и встаёт в очередь кредиторов.",
     "fix": "Проверить: ФССП (fssp.gov.ru), ЕФРСБ (fedresurs.ru), картотека kad.arbitr.ru. Если есть долги — нотариальное заверение о дееспособности и отсутствии признаков банкротства.", "w": 40.0},

    {"cat": "Продавец", "what": "Долги по ЖКХ и капремонту",
     "kw": ["капремонт","жкх","коммунал","задолженность по жкх","долг за свет","долг за газ"],
     "law": "ЖК РФ ст. 158 ч. 3. Долги по взносам на капитальный ремонт переходят к новому собственнику. Долги за коммунальные — не переходят, но УК может отключить услуги.",
     "fix": "Справки от УК и регионального фонда капремонта об отсутствии задолженности. Получить в день сделки, не раньше.", "w": 15.0},

    {"cat": "Продавец", "what": "Дееспособность продавца (пожилой / на учёте)",
     "kw": ["пенсионер","психиатр","пнд","нарколог","бабушк","дед","учет","пожил","деменц"],
     "law": "ГК РФ ст. 177. Сделка, совершённая лицом в момент, когда оно не понимало значения своих действий, оспорима. Срок исковой давности — 3 года.",
     "fix": "Справки из ПНД и НД. Для пожилых — нотариальное освидетельствование дееспособности непосредственно на сделке.", "w": 20.0},

    {"cat": "Продавец", "what": "Продажа по доверенности",
     "kw": ["доверенност","представител","действует по","по нотариальн","генеральн доверенност"],
     "law": "ГК РФ ст. 188. Доверенность прекращается: при отмене доверителем, при его смерти, при признании недееспособным. Мошенники используют доверенности от живых людей.",
     "fix": "Проверить доверенность на сайте ФНП (notariat.ru) по QR. Добиваться личного присутствия собственника на сделке.", "w": 25.0},

    {"cat": "Продавец", "what": "Согласие супруга на продажу",
     "kw": ["брак","муж","жена","супруг","совместно нажит","развод","бывш"],
     "law": "СК РФ ст. 35. Имущество, нажитое в браке, — совместная собственность. Без нотариального согласия супруга сделка оспорима в течение 1 года.",
     "fix": "Нотариально заверенное согласие супруга. Если разведены — брачный договор или решение суда о разделе имущества.", "w": 20.0},

    {"cat": "Продавец", "what": "Иностранный гражданин / Нерезидент",
     "kw": ["иностран","нерезидент","внж","вид на жительство","гражданство другой"],
     "law": "Указы Президента № 81, 95, 618 (2022). Расчёты с недружественными нерезидентами — только через счета типа 'С'. НДФЛ нерезидента при продаже — 30%.",
     "fix": "Уточнить налоговый статус. Расчёты через счета в уполномоченных банках. Консультация с валютным юристом обязательна.", "w": 35.0},

    # ── СПЕЦИАЛЬНЫЕ СИТУАЦИИ ──────────────────────────────────────────────────
    {"cat": "Специальные ситуации", "what": "Военная ипотека",
     "kw": ["военная ипотека","военн ипотек","росвоенипотек","нис","накопительно-ипотечн"],
     "law": "ФЗ № 117-ФЗ. До погашения военной ипотеки объект в залоге одновременно у банка И у Росвоенипотеки.",
     "fix": "Проверить ЕГРН на двойное обременение. Схема продажи: гашение обоих долгов через аккредитив.", "w": 30.0},

    {"cat": "Специальные ситуации", "what": "Долевая собственность — преимущественное право",
     "kw": ["долев","совладелец","другой собственник","сособственник","продажа доли"],
     "law": "ГК РФ ст. 250. Другой сособственник имеет преимущественное право покупки доли. Нарушение — оспаривание сделки.",
     "fix": "Нотариально заверенные отказы всех сособственников от преимущественного права покупки. Сделка только через нотариуса.", "w": 25.0},

    {"cat": "Специальные ситуации", "what": "Региональные субсидии и жилищные сертификаты",
     "kw": ["субсидия","жилищный сертификат","гос субсидия","молодая семья","сертификат","жилищная программ"],
     "law": "Субсидии имеют ограничения по цене 1 кв. м, типу жилья, срокам использования. При нарушении — возврат субсидии.",
     "fix": "Уточнить условия конкретной программы. Убедиться, что объект соответствует всем требованиям.", "w": 20.0},
]

CRITICAL_TRIGGERS = [
    "в конверте","занижен","1 млн","до миллиона","банкрот","наследств",
    "доли не выделены","опек","арест","запрет","отказник","рент",
    "тюрьм","арми","в половину","полцены","снос","аварийн","реновац",
    "самовольн","доверенност","субсидир","апартамент",
]

HINTS = [
    ("👤 Продавец", "возраст, один/несколько, в браке, иностранец, по доверенности"),
    ("🏠 История объекта", "купил, наследство, подарок, приватизация, рента"),
    ("📋 Обременения", "ипотека, залог, арест, долги по ЖКХ, прописанные"),
    ("👶 Дети и доли", "маткапитал, детские доли, опека"),
    ("💰 Цена сделки", "занижение в договоре, конверт, схемы расчётов"),
    ("🔧 Объект", "перепланировка, снос стен, ИЖС/СНТ, котлован"),
]

# ─── DATACLASSES ─────────────────────────────

@dataclass
class RiskItem:
    what: str
    law: str
    fix: str
    weight: float
    category: str

@dataclass
class AnalysisResult:
    total_risk: int
    items: List[RiskItem]
    zone: str
    zone_label: str
    sub_text: str

# ─── HELPERS ─────────────────────────────────

def get_base64_image(path):
    try:
        if os.path.exists(path):
            with open(path, "rb") as f:
                return base64.b64encode(f.read()).decode()
    except Exception:
        return None
    return None

def _detect(text, keywords):
    t = text.lower()
    return any(kw in t for kw in keywords)

def fmt(n):
    return f"{n:,.0f}".replace(",", " ")

# ─── АНАЛИЗ ──────────────────────────────────

def analyze_safedeal(text):
    items = []
    seen = set()
    for cfg in RISKS_CONFIG:
        key = cfg["what"]
        if key not in seen and _detect(text, cfg["kw"]):
            seen.add(key)
            items.append(RiskItem(cfg["what"], cfg["law"], cfg["fix"], cfg["w"], cfg["cat"]))

    if not items:
        return AnalysisResult(0, [], "safe", "РИСКОВ НЕ ОБНАРУЖЕНО",
            "Автоматический анализ не выявил маркеров. Требуется полная проверка документов.")

    b_tot = sum(i.weight for i in items) + max(0, len(items) - 1) * 3
    if _detect(text, CRITICAL_TRIGGERS):
        b_tot = max(b_tot, 85.0)
    score = max(0, min(int(round(b_tot)), 100))

    if score >= 70:
        z, l, s = "danger", "КРАСНАЯ ЗОНА", "Запрещено выходить на сделку без профильного юриста."
    elif score >= 35:
        z, l, s = "warning", "ЖЁЛТАЯ ЗОНА", "Требуется сбор дополнительных документов и проверка."
    else:
        z, l, s = "safe", "ЗЕЛЁНАЯ ЗОНА", "Серьёзных маркеров не обнаружено. Базовая проверка обязательна."

    return AnalysisResult(score, items, z, l, s)

# ─── PDF ГЕНЕРАЦИЯ (С КРУГЛЫМ ЛОГОТИПОМ) ─────

C_GREEN = colors.HexColor("#008a5e")
C_RED   = colors.HexColor("#dc2626")
C_AMBER = colors.HexColor("#d97706")
C_SAFE  = colors.HexColor("#059669")
C_DARK  = colors.HexColor("#1a1a2e")
C_MUTED = colors.HexColor("#6b7280")
C_LIGHT = colors.HexColor("#f9fafb")
C_BORD  = colors.HexColor("#e5e7eb")

# Кастомный класс для обрезки картинки в идеальный круг
class CircularImage(Flowable):
    def __init__(self, img_path, size):
        Flowable.__init__(self)
        self.img_path = img_path
        self.size = size

    def wrap(self, availWidth, availHeight):
        return self.size, self.size

    def draw(self):
        c = self.canv
        # 1. Рисуем картинку, обрезанную по кругу
        c.saveState()
        p = c.beginPath()
        p.circle(self.size / 2.0, self.size / 2.0, self.size / 2.0)
        c.clipPath(p, stroke=0)
        c.drawImage(self.img_path, 0, 0, width=self.size, height=self.size)
        c.restoreState()
        
        # 2. Рисуем зеленую рамку поверх (стиль SafeDeal)
        c.saveState()
        c.setStrokeColor(C_GREEN)
        c.setLineWidth(1.5)
        c.circle(self.size / 2.0, self.size / 2.0, self.size / 2.0)
        c.restoreState()


def generate_pdf(res, report_id, input_text):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4,
        leftMargin=20*mm, rightMargin=20*mm, topMargin=15*mm, bottomMargin=15*mm,
        title=f"SafeDeal Акт №{report_id}", author="SafeDeal | Артем Носов")

    # Определение пути к шрифтам и лого
    curr_dir = os.path.dirname(os.path.abspath(__file__))
    path_reg = os.path.join(curr_dir, FONT_REGULAR_FILE)
    path_bold = os.path.join(curr_dir, FONT_BOLD_FILE)
    logo_path = os.path.join(curr_dir, LOGO_FILE)

    # Регистрация шрифтов
    font_regular = "Helvetica" 
    font_bold = "Helvetica-Bold"
    
    if os.path.exists(path_reg) and os.path.exists(path_bold):
        try:
            pdfmetrics.registerFont(TTFont('DejaVu', path_reg))
            pdfmetrics.registerFont(TTFont('DejaVu-Bold', path_bold))
            font_regular = 'DejaVu'
            font_bold = 'DejaVu-Bold'
        except Exception:
            pass
    
    def S(name, **kw):
        return ParagraphStyle(name, **kw)

    st_h1c = S("h1c", fontName=font_bold, fontSize=20, textColor=C_GREEN, alignment=TA_CENTER, leading=26, spaceAfter=2)
    st_sub = S("sub", fontName=font_regular, fontSize=9, textColor=C_MUTED, alignment=TA_CENTER, leading=13, spaceAfter=0)
    st_h2  = S("h2",  fontName=font_bold, fontSize=13, textColor=C_GREEN, spaceAfter=4, leading=18, spaceBefore=6)
    st_h3  = S("h3",  fontName=font_bold, fontSize=10, textColor=C_DARK, spaceAfter=2, leading=14)
    st_bd  = S("bd",  fontName=font_regular, fontSize=9, textColor=C_DARK, spaceAfter=2, leading=13)
    st_sm  = S("sm",  fontName=font_regular, fontSize=8, textColor=C_MUTED, spaceAfter=2, leading=12)
    st_fix = S("fx",  fontName=font_regular, fontSize=9, textColor=C_SAFE, spaceAfter=2, leading=13)

    zone_color = {"danger": C_RED, "warning": C_AMBER, "safe": C_SAFE}.get(res.zone, C_GREEN)
    zone_bg    = {"danger": colors.HexColor("#fff8f8"), "warning": colors.HexColor("#fffbeb"),
                  "safe": colors.HexColor("#f0fdf7")}.get(res.zone, C_LIGHT)

    story = []

    # Вставка круглого логотипа по центру
    if os.path.exists(logo_path):
        try:
            logo_size = 28 * mm
            c_img = CircularImage(logo_path, logo_size)
            # Обертываем в таблицу, чтобы выровнять строго по центру
            t_logo = Table([[c_img]], colWidths=[logo_size], hAlign='CENTER')
            t_logo.setStyle(TableStyle([
                ('ALIGN', (0,0), (-1,-1), 'CENTER'),
                ('VALIGN', (0,0), (-1,-1), 'CENTER'),
                ('LEFTPADDING', (0,0), (-1,-1), 0),
                ('RIGHTPADDING', (0,0), (-1,-1), 0),
                ('TOPPADDING', (0,0), (-1,-1), 0),
                ('BOTTOMPADDING', (0,0), (-1,-1), 0),
            ]))
            story.append(t_logo)
            story.append(Spacer(1, 3*mm))
        except Exception:
            pass

    # Заголовок
    story.append(Paragraph("Акт аудита сделки", st_h1c))
    story.append(Paragraph("Авторский сервис аудита недвижимости | Артем Носов", st_sub))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=2, color=C_GREEN))
    story.append(Spacer(1, 4*mm))

    meta_data = [
        ["Акт проверки №", str(report_id)],
        ["Дата:", datetime.now().strftime("%d.%m.%Y %H:%M")],
        ["Индекс риска:", f"{res.total_risk}%"],
        ["Решение:", res.zone_label],
    ]
    
    mt = Table(meta_data, colWidths=[50*mm, 120*mm])
    mt.setStyle(TableStyle([
        ("FONTNAME", (0,0), (-1,-1), font_regular),
        ("FONTNAME", (0,0), (0,-1),  font_bold),
        ("FONTSIZE", (0,0), (-1,-1), 9),
        ("TEXTCOLOR", (0,0), (0,-1), C_MUTED),
        ("TEXTCOLOR", (1,2), (1,3),  zone_color),
        ("FONTNAME", (1,2), (1,3),   font_bold),
        ("TOPPADDING", (0,0), (-1,-1), 3),
        ("BOTTOMPADDING", (0,0), (-1,-1), 3),
    ]))
    story.append(mt)
    story.append(Spacer(1, 3*mm))

    # Блок решения
    zt = Table([[Paragraph(f"{res.zone_label} - {res.sub_text}",
        S("zt", fontName=font_bold, fontSize=10, textColor=zone_color, leading=14))]],
        colWidths=[170*mm])
    zt.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), zone_bg),
        ("BOX", (0,0), (-1,-1), 1.5, zone_color),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
        ("LEFTPADDING", (0,0), (-1,-1), 10),
    ]))
    story.append(zt)
    story.append(Spacer(1, 5*mm))

    # Описание
    story.append(Paragraph("Описание ситуации", st_h2))
    story.append(Paragraph(html.escape(input_text[:600]), st_bd))
    story.append(Spacer(1, 4*mm))
    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORD))
    story.append(Spacer(1, 4*mm))

    # Риски
    if not res.items:
        story.append(Paragraph("Явных маркеров риска не обнаружено.", st_bd))
    else:
        story.append(Paragraph(f"Выявленные угрозы ({len(res.items)} шт.)", st_h2))
        cats = {}
        for item in res.items:
            cats.setdefault(item.category, []).append(item)

        for cat_name, cat_items in cats.items():
            story.append(Paragraph(cat_name, st_h3))
            tdata = [["Угроза", "Правовое основание", "Защита"]]
            for item in cat_items:
                tdata.append([
                    Paragraph(f"<b>{html.escape(item.what)}</b>", st_bd),
                    Paragraph(html.escape(item.law), st_sm),
                    Paragraph(html.escape(item.fix), st_fix),
                ])
            c_col = {"Финансовые схемы": C_RED, "Объект": C_AMBER, "Продавец": C_AMBER}.get(cat_name, C_GREEN)
            t = Table(tdata, colWidths=[50*mm, 65*mm, 55*mm])
            t.setStyle(TableStyle([
                ("BACKGROUND", (0,0), (-1,0), C_LIGHT),
                ("FONTNAME", (0,0), (-1,0), font_bold),
                ("FONTSIZE", (0,0), (-1,0), 8),
                ("TEXTCOLOR", (0,0), (-1,0), C_MUTED),
                ("ROWBACKGROUNDS", (0,1), (-1,-1), [colors.white, colors.HexColor("#fafafa")]),
                ("GRID", (0,0), (-1,-1), 0.4, C_BORD),
                ("TOPPADDING", (0,0), (-1,-1), 5),
                ("BOTTOMPADDING", (0,0), (-1,-1), 5),
                ("LEFTPADDING", (0,0), (-1,-1), 6),
                ("VALIGN", (0,0), (-1,-1), "TOP"),
                ("LINEAFTER", (0,1), (0,-1), 2, c_col),
            ]))
            story.append(KeepTogether([t]))
            story.append(Spacer(1, 3*mm))

    story.append(HRFlowable(width="100%", thickness=0.5, color=C_BORD))
    story.append(Spacer(1, 3*mm))
    story.append(Paragraph(
        "Данный акт создан алгоритмической моделью. Носит информационно-аналитический характер "
        "и не является юридической консультацией. SafeDeal | t.me/nosov_s_blog",
        S("ftr", fontName=font_regular, fontSize=7.5, textColor=C_MUTED, alignment=TA_CENTER)))

    try:
        doc.build(story)
        buf.seek(0)
        return buf.read()
    except Exception as e:
        print(f"Ошибка генерации PDF: {e}")
        return None

# ─── ФИНАНСЫ ─────────────────────────────────

def progressive_tax(taxable):
    T = 2_400_000
    if taxable <= 0: return 0.0, 0.0, 0.0
    elif taxable <= T: t = taxable * 0.13; return t, t, 0.0
    else: t13 = T * 0.13; t15 = (taxable - T) * 0.15; return t13+t15, t13, t15

def calc_mortgage(price, down, rate, years):
    loan = price - down
    if loan <= 0: return 0.0, 0.0, 0.0
    mr = (rate/100)/12; months = years*12
    pay = loan * (mr * (1 + mr)**months) / ((1 + mr)**months - 1) if mr != 0 else loan / months
    total = pay * months
    return pay, total - loan, total

def amort_yearly(price, down, rate, years):
    loan = price - down
    if loan <= 0: return []
    mr = (rate/100)/12; months = years*12
    pay = loan * (mr * (1 + mr)**months) / ((1 + mr)**months - 1) if mr != 0 else loan / months
    bal = loan; yearly = {}
    for m in range(1, months+1):
        y = (m-1)//12+1
        interest = bal*mr; principal = pay-interest; bal -= principal
        yearly.setdefault(y, {"principal":0,"interest":0})
        yearly[y]["principal"] += principal; yearly[y]["interest"] += interest
    return [{"Год":y,"Основной долг":round(d["principal"]),"Проценты":round(d["interest"])} for y,d in sorted(yearly.items())]

# ─── SVG GAUGE ────────────────────────────────

def render_gauge(score, zone):
    color = {"danger":"#dc2626","warning":"#d97706","safe":"#059669"}.get(zone,"#008a5e")
    cx, cy, r = 100, 100, 78
    angle_deg = -180 + (score/100)*180
    rad = math.radians(angle_deg)
    nx = cx + r*math.cos(rad); ny = cy + r*math.sin(rad)

    def arc(start, end):
        sr = math.radians(start); er = math.radians(end)
        sx = cx+r*math.cos(sr); sy = cy+r*math.sin(sr)
        ex = cx+r*math.cos(er); ey = cy+r*math.sin(er)
        lg = 1 if (end-start) > 180 else 0
        return f"M{sx:.1f} {sy:.1f} A{r} {r} 0 {lg} 1 {ex:.1f} {ey:.1f}"

    prog = arc(-180, angle_deg) if score > 0 else ""
    label = {"danger":"КРАСНАЯ ЗОНА","warning":"ЖЁЛТАЯ ЗОНА","safe":"ЗЕЛЁНАЯ ЗОНА"}.get(zone,"")

    return f"""
    <div class="gauge-wrap">
    <svg width="200" height="115" viewBox="0 0 200 115">
      <path d="{arc(-180,0)}" fill="none" stroke="#e5e7eb" stroke-width="14" stroke-linecap="round"/>
      {"" if not prog else f'<path d="{prog}" fill="none" stroke="{color}" stroke-width="14" stroke-linecap="round"/>'}
      <line x1="{cx}" y1="{cy}" x2="{nx:.1f}" y2="{ny:.1f}" stroke="{color}" stroke-width="3.5" stroke-linecap="round"/>
      <circle cx="{cx}" cy="{cy}" r="6" fill="{color}"/>
      <text x="{cx}" y="{cy-18}" text-anchor="middle" font-family="sans-serif" font-weight="900" font-size="24" fill="{color}">{score}%</text>
      <text x="{cx}" y="{cy-3}" text-anchor="middle" font-family="sans-serif" font-size="7.5" fill="#9ca3af">{label}</text>
      <text x="14" y="110" font-family="sans-serif" font-size="8.5" fill="#9ca3af">0%</text>
      <text x="172" y="110" font-family="sans-serif" font-size="8.5" fill="#9ca3af">100%</text>
    </svg>
    </div>"""

# ─── CSS ─────────────────────────────────────

def inject_styles():
    st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Unbounded:wght@700;900&family=Inter:wght@400;500;600&display=swap');
header,footer,#MainMenu,[data-testid="stHeader"],[data-testid="stToolbar"],[data-testid="stDecoration"],
.viewerBadge_container,.viewerBadge_link,[data-testid="stViewerBadge"],.stDeployButton,
section[data-testid="stSidebar"],[data-testid="collapsedControl"],
h1 a,h2 a,h3 a,h4 a,h5 a,h6 a,h1 svg,h2 svg,h3 svg{display:none!important;visibility:hidden!important}
:root{--g:#008a5e;--gd:#006f4b;--r:#dc2626;--a:#d97706;--s:#059669;--bg:#f9fafb;--bor:#e5e7eb;--tx:#1a1a2e;--mu:#6b7280;--rr:14px}
body{background:var(--bg);color:var(--tx);font-family:'Inter',sans-serif}
.main .block-container{padding-top:1.5rem;max-width:960px;padding-bottom:4rem}
.header-wrapper{display:flex;flex-direction:column;align-items:center;text-align:center;margin-bottom:2rem}
.logo-img{width:130px;height:130px;border-radius:50%;object-fit:cover;box-shadow:0 0 0 4px #fff,0 0 0 7px var(--g),0 8px 24px rgba(0,138,94,.18);margin-bottom:16px}
.hero-title{font-family:'Unbounded',sans-serif;font-size:1.9rem;font-weight:900;color:var(--tx);margin:0 0 4px}
.hero-sub{font-size:1rem;font-weight:500;color:var(--g);margin:0 0 18px}
.custom-btn{background:linear-gradient(135deg,var(--g) 0%,var(--gd) 100%);color:#fff!important;padding:12px 32px;border-radius:40px;font-weight:700;font-size:15px;text-decoration:none!important;box-shadow:0 4px 18px rgba(0,138,94,.28);transition:.25s;display:inline-block}
.custom-btn:hover{transform:translateY(-2px);box-shadow:0 8px 24px rgba(0,138,94,.35)}
.tip-box{background:#f0fdf7;border:1px dashed var(--g);border-radius:10px;padding:10px 16px;font-size:.88rem;text-align:center;margin-bottom:22px}
.stButton>button{background:var(--g);color:#fff;border:none;border-radius:10px;padding:.65rem 1rem;font-weight:700;font-size:.88rem;width:100%;transition:.2s}
.stButton>button:hover{background:var(--gd);transform:translateY(-1px)}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#fff;padding:6px;border-radius:14px;border:1px solid var(--bor);flex-wrap:wrap}
.stTabs [data-baseweb="tab"]{height:46px;white-space:nowrap;background:transparent;color:var(--mu);font-weight:600;border-radius:10px;padding:0 18px;border:none!important;transition:.2s;font-size:.87rem}
.stTabs [aria-selected="true"]{background:var(--g)!important;color:#fff!important;box-shadow:0 4px 14px rgba(0,138,94,.22)}
.stTabs [data-baseweb="tab-highlight"]{display:none}
.decision-banner{margin:1.2rem 0;padding:1.2rem 1.5rem;border-radius:var(--rr);border:1.5px solid;display:flex;align-items:center;gap:1.5rem}
.decision-banner.danger{border-color:var(--r);background:#fff8f8}
.decision-banner.warning{border-color:var(--a);background:#fffbeb}
.decision-banner.safe{border-color:var(--s);background:#f0fdf7}
.dscore{font-family:'Unbounded',sans-serif;font-size:3rem;font-weight:900;line-height:1}
.danger .dscore,.danger .dz{color:var(--r)}
.warning .dscore,.warning .dz{color:var(--a)}
.safe .dscore,.safe .dz{color:var(--s)}
.dz{font-weight:800;font-size:1rem;text-transform:uppercase}
.ds{font-size:.88rem;color:var(--mu);margin-top:4px}
.rnum{font-size:.78rem;color:var(--mu);margin-bottom:4px}
.rbw{width:100%;background:#f3f4f6;border-radius:99px;height:10px;margin:8px 0 0;overflow:hidden}
.rbf{height:10px;border-radius:99px}
.rbf.danger{background:linear-gradient(90deg,#fca5a5,var(--r))}
.rbf.warning{background:linear-gradient(90deg,#fde68a,var(--a))}
.rbf.safe{background:linear-gradient(90deg,#6ee7b7,var(--s))}
.gauge-wrap{display:flex;justify-content:center;margin:4px 0 8px}
.hint-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-bottom:12px}
.hint-item{background:#fff;border:1px solid var(--bor);border-radius:10px;padding:9px 12px;font-size:.82rem}
.hint-label{font-weight:700;color:var(--g);margin-bottom:2px;font-size:.8rem}
.hint-text{color:var(--mu);line-height:1.4}
.risk-card{background:#fff;border:1px solid var(--bor);border-radius:var(--rr);padding:14px 16px;margin-bottom:10px;border-left:4px solid}
.risk-card.danger{border-left-color:var(--r)}
.risk-card.warning{border-left-color:var(--a)}
.risk-card.safe{border-left-color:var(--s)}
.risk-title{font-weight:700;font-size:.95rem;margin-bottom:6px}
.risk-law{font-size:.88rem;color:var(--mu);margin-bottom:5px;line-height:1.5}
.risk-fix{font-size:.82rem;color:#065f46;background:#ecfdf5;border-radius:6px;padding:5px 9px}
.risk-fix::before{content:"✅ "}
.metric-card{background:#fff;border:1px solid var(--bor);border-radius:var(--rr);padding:16px 18px;text-align:center}
.metric-value{font-family:'Unbounded',sans-serif;font-size:1.4rem;font-weight:900;color:var(--g)}
.metric-label{font-size:.78rem;color:var(--mu);margin-top:4px;line-height:1.4}
.bank-row{display:flex;align-items:center;justify-content:space-between;background:#fff;border:1px solid var(--bor);border-radius:10px;padding:12px 16px;margin-bottom:8px}
.bank-name{font-weight:700;font-size:.92rem;min-width:140px}
.bank-rate{font-family:'Unbounded',sans-serif;font-size:1.1rem;color:var(--g);font-weight:900;min-width:60px}
.bank-note{font-size:.78rem;color:var(--mu);flex:1;text-align:center}
.bank-pay{font-weight:700;font-size:.88rem;min-width:120px;text-align:right}
.tl-box{border-left:3px solid var(--g);padding:0 0 22px 22px;position:relative}
.tl-box::before{content:"";position:absolute;left:-8px;top:3px;width:13px;height:13px;border-radius:50%;background:var(--g)}
.tl-box:last-child{border-left-color:transparent}
.tl-title{font-weight:700;font-size:1rem;margin-bottom:5px}
.tl-desc{font-size:.88rem;color:var(--mu);line-height:1.6}
.social-container{display:flex;justify-content:center;gap:14px;margin-top:28px;flex-wrap:wrap}
.social-btn{display:flex;align-items:center;justify-content:center;padding:13px 22px;border-radius:12px;color:#fff!important;text-decoration:none!important;font-weight:700;font-size:15px;min-width:210px;transition:.2s;box-shadow:0 3px 10px rgba(0,0,0,.08)}
.social-btn img{width:26px;height:26px;margin-right:10px;flex-shrink:0}
.btn-tg{background:#2AABEE}.btn-wa{background:#25D366}.btn-vk{background:#0077FF}
.social-btn:hover{transform:translateY(-3px);box-shadow:0 8px 18px rgba(0,0,0,.12)}
.hook-card{background:linear-gradient(to right,#fffbeb,#fff);border-left:4px solid var(--a);padding:18px;border-radius:12px;margin-top:28px;box-shadow:0 4px 18px rgba(0,0,0,.05)}
.hook-title{font-weight:800;font-size:1.1rem;margin-bottom:8px;color:var(--tx)}
.hl-box{background:#f0fdf7;padding:14px;border-left:4px solid var(--g);border-radius:6px;font-size:.9rem;margin:14px 0}
.warn-box{background:#fffbeb;padding:14px;border-left:4px solid var(--a);border-radius:6px;font-size:.9rem;margin:14px 0}
.footer-disc{text-align:center;font-size:.74rem;color:#9ca3af;margin-top:3rem;border-top:1px solid var(--bor);padding-top:1.5rem;line-height:1.6}
@media(max-width:768px){.hero-title{font-size:1.4rem}.decision-banner{flex-direction:column;gap:.8rem;padding:1rem}.dscore{font-size:2.4rem}.social-btn{width:100%}.hint-grid{grid-template-columns:1fr}.bank-row{flex-direction:column;align-items:flex-start;gap:4px}}
</style>""", unsafe_allow_html=True)

# ─── ШАБЛОНЫ ─────────────────────────────────

def set_t1(): st.session_state.my_text = "Продавец пенсионер 75 лет. Продаёт по доверенности. Свежее наследство."
def set_t2(): st.session_state.my_text = "Купили в браке, есть маткапитал. Сделана перепланировка (снесли стену)."
def set_t3(): st.session_state.my_text = "Собственник имеет долги у приставов, продаёт срочно. Хотят занижение цены в договоре (до миллиона рублей)."

# ─── ВКЛАДКИ ─────────────────────────────────

def tab_audit():
    st.markdown("<b>⚡ Быстрые ситуации:</b>", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    c1.button("👴 Доверенность + Наследство",  on_click=set_t1, use_container_width=True)
    c2.button("👶 Маткапитал + Перепланировка", on_click=set_t2, use_container_width=True)
    c3.button("⚖️ Долги + Занижение",          on_click=set_t3, use_container_width=True)

    with st.expander("💡 Что включить в описание? (подсказки)", expanded=False):
        st.markdown('<div class="hint-grid">' +
            "".join(f'<div class="hint-item"><div class="hint-label">{h[0]}</div><div class="hint-text">{h[1]}</div></div>' for h in HINTS) +
            '</div>', unsafe_allow_html=True)
        st.caption("Чем больше деталей — тем точнее анализ.")

    text = st.text_area("Опишите ситуацию по сделке", key="my_text", height=130,
        placeholder="⚠️ ПРАВИЛО: Пишите только факты, которые ЕСТЬ (БЕЗ слов «нет», «не»). \nПравильно: «наследство, арест, снос стены».\nНеправильно: «долгов нет, перепланировки нет».")

    if st.button("🔍 ЗАПУСТИТЬ АНАЛИЗ РИСКОВ", key="run_audit"):
        if not text.strip():
            st.warning("Введите описание ситуации для анализа."); return

        with st.status("Анализирую текст на маркеры риска...", expanded=True) as status:
            st.write("📋 Проверяю маркеры по 19 категориям рисков..."); time.sleep(0.4)
            st.write("⚖️ Сопоставляю с нормами ГК, СК, ЖК, НК РФ..."); time.sleep(0.4)
            st.write("🧮 Вычисляю индекс риска с учётом накопления..."); time.sleep(0.3)
            status.update(label="Анализ завершён!", state="complete", expanded=False)

        res = analyze_safedeal(text)
        rid = random.randint(10000, 99999)

        col_b, col_g = st.columns([2, 1])
        with col_b:
            st.markdown(f"""
            <div class="decision-banner {res.zone}">
              <div style="text-align:center;min-width:100px;">
                <div class="dscore">{res.total_risk}%</div>
                <div style="font-size:.7rem;color:#6b7280;margin-top:2px;">ИНДЕКС РИСКА</div>
              </div>
              <div style="width:100%">
                <div class="rnum">Акт №{rid} · {datetime.now().strftime("%d.%m.%Y %H:%M")}</div>
                <div class="dz">{res.zone_label}</div>
                <div class="ds">{html.escape(res.sub_text)}</div>
                <div class="rbw"><div class="rbf {res.zone}" style="width:{res.total_risk}%;"></div></div>
              </div>
            </div>""", unsafe_allow_html=True)
        with col_g:
            st.markdown(render_gauge(res.total_risk, res.zone), unsafe_allow_html=True)

        if not res.items:
            st.info("💡 Явных маркеров не найдено. Расширьте описание: кто продавец, как получена квартира, есть ли обременения."); return

        cat_color = {"Финансовые схемы":"danger","Объект":"warning","Продавец":"warning"}
        cats = {}
        for item in res.items:
            cats.setdefault(item.category, []).append(item)

        for cat, items in cats.items():
            n = len(items)
            suf = "а" if n in [2,3,4] else "ов" if n > 4 else ""
            st.markdown(f"#### {cat} &nbsp;<span style='font-size:.8rem;color:#6b7280;font-weight:400;'>({n} риск{suf})</span>", unsafe_allow_html=True)
            for item in items:
                color = cat_color.get(cat, "warning")
                st.markdown(f"""
                <div class="risk-card {color}">
                  <div class="risk-title">⚠️ {html.escape(item.what)}</div>
                  <div class="risk-law" style="font-size: 0.82rem;">📖 {html.escape(item.law)}</div>
                  <div class="risk-fix">{html.escape(item.fix)}</div>
                </div>""", unsafe_allow_html=True)

        st.markdown("---")
        c_pdf, c_txt = st.columns(2)
        # ГЕНЕРАЦИЯ PDF
        pdf_bytes = generate_pdf(res, rid, text)
        if pdf_bytes:
            c_pdf.download_button("📄 Скачать акт PDF", data=pdf_bytes,
                file_name=f"SafeDeal_{rid}.pdf", mime="application/pdf", use_container_width=True)
        else:
            c_pdf.error("Ошибка генерации PDF. Убедитесь, что файлы шрифтов на месте.")
        
        lines = [
            "=========================================",
            "АВТОРСКИЙ АУДИТ: АРТЕМ НОСОВ | SAFEDEAL",
            "Telegram: @Artem_Nosov_Vrn",
            "=========================================",
            "",
            f"АКТ №{rid}", 
            f"Дата: {datetime.now().strftime('%d.%m.%Y %H:%M')}",
            f"ИНДЕКС РИСКА: {res.total_risk}%", 
            f"РЕШЕНИЕ: {res.zone_label}", 
            ""
        ]
        for item in res.items:
            lines += [f"[{item.category}] {item.what}", f"  Закон: {item.law}", f"  Защита: {item.fix}", ""]
        c_txt.download_button("📥 Скачать акт TXT", data="\n".join(lines),
            file_name=f"SafeDeal_{rid}.txt", mime="text/plain", use_container_width=True)


def tab_tax():
    st.markdown("### 🧮 Калькулятор НДФЛ с продажи (2025)")
    how = st.selectbox("Как получена квартира?", [
        "Куплена по ДКП / ДДУ",
        "Улучшение жилищных условий (Семья с 2+ детьми)",
        "Получена в наследство",
        "Подарена близким родственником",
        "Приватизация",
        "Передача по договору ренты",
        "Это единственное жильё"
    ], key="tax_how")
    
    if "Семья с 2+ детьми" in how:
        st.success("🎉 **Семьи с двумя и более детьми могут быть освобождены от уплаты НДФЛ** при продаже жилья независимо от срока владения (п. 2.1 ст. 217.1 НК РФ).")
        st.warning("""
        ⚠️ **ОДНАКО, льгота работает только при одновременном выполнении 4 условий:**
        1. В семье двое или более детей до 18 лет (или до 24 лет, если учатся очно).
        2. Вы купили новую недвижимость в год продажи старой (или до 30 апреля следующего года), и она больше по площади или кадастровой стоимости.
        3. Кадастровая стоимость проданного жилья не превышает 50 млн рублей.
        4. На момент продажи ни у вас, ни у членов семьи нет в собственности более 50% другого жилья, площадь которого больше покупаемого.
        
        *Если хотя бы одно условие нарушено — налог придётся платить на общих основаниях!*
        """)
        return

    is_non_resident = st.checkbox("Продавец — налоговый нерезидент (более 183 дней вне РФ в году продажи)", key="tax_resident")
    if is_non_resident:
        st.error("⚠️ **Внимание:** Для нерезидентов РФ ставка НДФЛ составляет **30%**. Имущественные вычеты (в т.ч. 'доходы минус расходы' и 1 млн ₽) не применяются! Налог платится со всей суммы.")

    st.info("💡 **Нюанс по новостройкам (ДДУ):** Минимальный срок владения отсчитывается от даты полной оплаты договора застройщику, а не от даты регистрации собственности!")

    years_owned = st.number_input("Полных лет в собственности (от оплаты/регистрации)", min_value=0.0, step=0.5, value=2.0, key="tax_years")
    min_term = 3 if how != "Куплена по ДКП / ДДУ" else 5
    
    if years_owned >= min_term and not is_non_resident:
        st.success("🎉 Налог: 0 ₽. Срок истёк — освобождены от налога и декларации."); return
    
    sell = st.number_input("Цена продажи (₽)", min_value=0, step=100_000, value=6_000_000, key="tax_sell")
    cad  = st.number_input("Кадастровая стоимость (₽)", min_value=0, step=100_000, value=5_000_000, key="tax_cad")
    ded  = st.radio("Вычет:", ["Расходы на покупку (фактические)", "Стандартный вычет 1 млн ₽"], key="tax_ded") if not is_non_resident else ""
    buy  = st.number_input("Расходы на покупку (₽)", min_value=0, step=100_000, value=3_000_000, key="tax_buy") if "Расходы" in ded and not is_non_resident else 1_000_000
    
    if st.button("РАССЧИТАТЬ НАЛОГ", key="tax_btn"):
        base = max(sell, cad*0.7)
        if is_non_resident:
            taxable = base
            total = taxable * 0.30
            t13, t15 = 0, 0
        else:
            taxable = max(0, base-buy)
            total, t13, t15 = progressive_tax(taxable)
            
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{fmt(base)}</div><div class="metric-label">База налога (₽)</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{fmt(taxable)}</div><div class="metric-label">Налогооблагаемая сумма (₽)</div></div>', unsafe_allow_html=True)
        tc = "#dc2626" if total > 0 else "#059669"
        c3.markdown(f'<div class="metric-card" style="border-color:{tc}"><div class="metric-value" style="color:{tc}">{fmt(total)}</div><div class="metric-label">Налог к уплате (₽)</div></div>', unsafe_allow_html=True)
        
        if total > 0:
            if is_non_resident:
                st.markdown(f'<div class="warn-box">📊 Нерезидент РФ:<br>• Ставка 30% без права на вычеты: <b>{fmt(total)} ₽</b><br>• Срок подачи 3-НДФЛ: <b>до 30 апреля</b> следующего года.</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="warn-box">📊 Прогрессивная шкала 2025:<br>• 13% (до 2.4 млн): <b>{fmt(t13)} ₽</b><br>• 15% (сверх 2.4 млн): <b>{fmt(t15)} ₽</b><br>• Срок подачи 3-НДФЛ: <b>до 30 апреля</b> следующего года.</div>', unsafe_allow_html=True)
        
        if sell < cad*0.7:
            st.warning("⚠️ Цена продажи ниже 70% кадастровой — ФНС исчислит налог от кадастровой стоимости × 0.7.")


def tab_mortgage():
    st.markdown("### 🏦 Ипотека vs Аренда — детальный расчёт")
    st.markdown("#### 📊 Параметры ипотеки")
    cl, cr = st.columns(2)
    with cl:
        st.markdown("Кредит")
        price = st.number_input("Стоимость квартиры (₽)", min_value=500_000, step=100_000, value=7_000_000, key="mort_price")
        down  = st.number_input("Первоначальный взнос (₽)", min_value=0, step=100_000, value=2_000_000, key="mort_down")
        years = st.slider("Срок (лет)", 5, 30, 20, key="mort_years")
        rate  = st.number_input("Ставка банка (% годовых)", min_value=0.1, max_value=40.0, step=0.1, value=16.5, key="mort_rate")
    with cr:
        st.markdown("Сравнение с арендой")
        rent       = st.number_input("Аренда аналога (₽/мес)", min_value=0, step=1_000, value=40_000, key="mort_rent")
        rent_growth= st.number_input("Рост аренды (% год.)", min_value=0.0, step=0.5, value=5.0, key="mort_rent_growth")
        dep_rate   = st.number_input("Доходность вклада (% год.)", min_value=0.1, max_value=30.0, step=0.5, value=16.0, key="mort_dep_rate")

    st.caption("💡 Ставку уточняйте в своём банке — она зависит от вашего профиля и программы.")

    st.markdown("---")
    if st.button("РАССЧИТАТЬ И СРАВНИТЬ", key="mort_btn"):
        pay, overpay, total = calc_mortgage(price, down, rate, years)
        if pay == 0: st.error("Взнос превышает стоимость квартиры."); return
        
        loan = price - down
        hidden_costs = (loan / 2) * 0.008 * years
        
        rent_total = sum(rent*(1+rent_growth/100)**y*12 for y in range(years))
        dep_growth = down*((1+dep_rate/100)**years-1)
        
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value">{fmt(pay)}</div><div class="metric-label">Платёж/мес (₽)</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value">{fmt(overpay)}</div><div class="metric-label">Переплата банку (₽)<br><small>за {years} лет</small></div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{fmt(rent_total)}</div><div class="metric-label">Суммарная аренда (₽)<br><small>за {years} лет</small></div></div>', unsafe_allow_html=True)
        
        win = "ипотека" if (down+total+hidden_costs) <= rent_total else "аренда"
        diff = abs((down+total+hidden_costs)-rent_total)
        
        st.markdown(f"""<div class="hl-box">
        📊 <b>Итог за {years} лет:</b><br>
        • <b>Ипотека</b> (взнос + все выплаты банку): <b>{fmt(down+total)} ₽</b>. <span style="color:#008a5e;">Часть платежа формирует <b>ВАШ капитал</b> (тело долга).</span><br>
        • <b>Скрытые расходы собственника: ~{fmt(hidden_costs)} ₽</b> <span style="color:#6b7280;">(страхование кредита, налог на имущество, взносы на капремонт за весь срок).</span><br>
        • <b>Аренда</b> (с ростом {rent_growth}%/год): <b>{fmt(rent_total)} ₽</b>. <span style="color:#dc2626;">Это 100% безвозвратная потеря денег. Актива нет.</span><br>
        • Взнос на вкладе под {dep_rate}% вырос бы на <b>+{fmt(dep_growth)} ₽</b>.<br>
        {"✅ Ипотека финансово целесообразнее." if win=="ипотека" else f"💡 Аренда дешевле на {fmt(diff)} ₽, но в конце пути вы остаетесь без недвижимости."}
        </div>""", unsafe_allow_html=True)
        
        sched = amort_yearly(price, down, rate, years)
        if sched:
            import pandas as pd
            df = pd.DataFrame(sched).set_index("Год")
            st.bar_chart(df, color=["#008a5e","#f59e0b"])
            st.caption("Соотношение основного долга (зелёный) и процентов (жёлтый) по годам")


def tab_estimation():
    st.markdown("### 📉 Цена упрямства (для продавцов)")
    wish = st.number_input("Желаемая цена (₽)", min_value=0, step=100_000, value=10_000_000, key="est_wish")
    real = st.number_input("Средняя цена аналогов (₽)", min_value=0, step=100_000, value=9_000_000, key="est_real")
    comm = st.number_input("Коммунальные за пустой объект (₽/мес)", min_value=0, step=500, value=6_000, key="est_comm")
    dep  = st.number_input("Доходность вклада (% год.)", min_value=0.1, max_value=30.0, step=0.5, value=16.0, key="est_dep")
    if st.button("РАССЧИТАТЬ ПОТЕРИ", key="est_btn"):
        if wish <= real: st.success("✅ Цена в рынке. Объект будет продан в оптимальные сроки."); return
        diff_pct = ((wish-real)/real)*100; lost_m = (real*dep/100)/12; total_m = lost_m+comm
        payback = (wish-real)/total_m
        c1,c2,c3 = st.columns(3)
        c1.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#dc2626">{diff_pct:.1f}%</div><div class="metric-label">Завышение над рынком</div></div>', unsafe_allow_html=True)
        c2.markdown(f'<div class="metric-card"><div class="metric-value" style="color:#d97706">{fmt(total_m)}</div><div class="metric-label">Потери каждый месяц (₽)</div></div>', unsafe_allow_html=True)
        c3.markdown(f'<div class="metric-card"><div class="metric-value">{payback:.0f} мес.</div><div class="metric-label">Окупаемость скидки</div></div>', unsafe_allow_html=True)
        st.markdown(f"""<div class="warn-box">
        ⚠️ Цена выше рынка на <b>{diff_pct:.1f}%</b> ({fmt(wish-real)} ₽).<br>
        Каждый месяц простоя: упущенный доход <b>~{fmt(lost_m)} ₽</b> + коммунальные <b>~{fmt(comm)} ₽</b> = <b>~{fmt(total_m)} ₽/мес</b>.<br>
        За год: <b>~{fmt(total_m*12)} ₽</b>. Скидка окупится через <b>{payback:.0f} мес.</b>
        </div>""", unsafe_allow_html=True)


def tab_costs():
    st.markdown("### 💼 Детализация расходов по сделке")
    obj    = st.number_input("Стоимость квартиры (₽)", min_value=1_000_000, step=100_000, value=5_000_000, key="cost_obj")
    down_c = st.number_input("Первоначальный взнос (₽)", min_value=0, step=100_000, value=1_000_000, key="cost_down")
    is_m   = st.checkbox("Покупка в ипотеку (оценка, страхование)", value=True, key="cost_m")
    is_sbr = st.checkbox("Электронная регистрация и СБР через банк", value=True, key="cost_sbr")
    is_not = st.checkbox("Нотариальная сделка (доли, супруги, дети)", value=False, key="cost_not")
    is_tr  = st.checkbox("Банковские комиссии / аккредитив", value=True, key="cost_tr")
    is_ag  = st.checkbox("Риелторская комиссия", value=False, key="cost_ag")
    ag_pct = st.number_input("% комиссии агента", min_value=0.0, max_value=10.0, step=0.1, value=2.0, key="cost_ag_pct") if is_ag else 0.0
    if st.button("РАССЧИТАТЬ РАСХОДЫ", key="cost_btn"):
        rows = []; total = 0
        if is_m:
            ins = max(0, obj-down_c)*1.1*0.01
            rows += [("Страхование (жизнь + объект + титул)", ins),("Оценка недвижимости", 6_000)]; total += ins+6_000
        if is_sbr:  rows.append(("СБР + Электронная регистрация", 15_000)); total += 15_000
        if is_not:  rows.append(("Нотариальные расходы (тариф + УПТХ)", 25_000)); total += 25_000
        if is_tr:   rows.append(("Банковские комиссии / аккредитив", 3_000)); total += 3_000
        if is_ag:
            c = obj*ag_pct/100; rows.append((f"Риелторская комиссия ({ag_pct}%)", c)); total += c
        gp = min(500_000, max(4_000, obj*0.0002)) if obj > 20_000_000 else 4_000
        rows.append(("Государственная пошлина (ФЗ от 12.07.2024 №176-ФЗ)", gp)); total += gp
        st.markdown(f'<div class="warn-box">💸 <b>Итого: ~{fmt(total)} ₽</b> · {total/obj*100:.1f}% от стоимости объекта</div>', unsafe_allow_html=True)
        for name, val in rows:
            c1,c2 = st.columns([5,1]); c1.write(f"• {name}"); c2.write(f"{fmt(val)} ₽")


def tab_stages():
    st.markdown("### 📅 Регламент сделки: этапы и сроки")
    st.info("⏱️ Сроки ориентировочные — зависят от типа сделки, банка и региона. Ипотечные сделки всегда дольше наличных.")

    deal_type = st.radio("Тип сделки:", ["💵 Наличные / Свободная продажа", "🏦 Ипотека"], horizontal=True, key="stage_type")
    is_mortgage = "Ипотека" in deal_type

    stages = [
        {
            "num": "01",
            "title": "Поиск и просмотры",
            "duration_cash": "1–8 недель",
            "duration_mort": "1–8 недель",
            "buyer": "Анализ рынка, сравнение аналогов. Проверка объявления на красные флаги. Первичная проверка ЕГРН онлайн.",
            "seller": "Предпродажная подготовка объекта. Сбор первичного пакета документов для показа. Оценка рыночной стоимости.",
            "risk": "Эмоциональные решения на просмотре. Не торопитесь — рынок не исчезнет.",
        },
        {
            "num": "02",
            "title": "Аванс / Задаток",
            "duration_cash": "1–3 дня после выбора",
            "duration_mort": "1–3 дня после выбора",
            "buyer": "Проверка правоустанавливающих документов. Составление авансового соглашения / договора задатка с чёткими условиями возврата.",
            "seller": "Подписание соглашения. Снятие объекта с продажи. Согласование схемы расчётов и срока выхода на сделку.",
            "risk": "Задаток без нотариального или письменного оформления = потенциальная потеря денег. Никаких переводов на карту без договора.",
        },
        {
            "num": "03",
            "title": "Одобрение ипотеки",
            "duration_cash": "— (не требуется)",
            "duration_mort": "3–14 рабочих дней",
            "buyer": "Подача заявки в банк. Сбор справок о доходах. Одобрение объекта банком — оценка квартиры (3–5 дней). Согласование страховки.",
            "seller": "Предоставление документов на объект для банковской проверки. Ожидание одобрения.",
            "risk": "Банк может отказать в одобрении объекта (перепланировка, обременение). Это лучше выяснить до аванса.",
        },
        {
            "num": "04",
            "title": "Подготовка к сделке",
            "duration_cash": "1–2 недели",
            "duration_mort": "1–3 недели",
            "buyer": "Финальная проверка ЕГРН (не ранее чем за 3 дня до сделки). Изучение всех документов. Согласование даты и места сделки.",
            "seller": "Получение справок (ПНД/НД если нужно, ЖКХ, капремонт). Погашение всех долгов. Выписка зарегистрированных лиц до сделки или обязательство в договоре.",
            "risk": "Самый частый срыв: продавец не успевает собрать документы. Устанавливайте дедлайны с финансовой ответственностью.",
        },
        {
            "num": "05",
            "title": "День сделки",
            "duration_cash": "1 день (2–5 часов)",
            "duration_mort": "1 день (4–8 часов)",
            "buyer": "Подписание ДКП. Закладка денег в ячейку / аккредитив / СБР. Передача документов на регистрацию.",
            "seller": "Подписание ДКП. Подтверждение расчётов. Сдача документов в Росреестр через МФЦ или банк.",
            "risk": "Никогда не передавайте ключи до регистрации перехода права! Деньги раскрываются только после успешной регистрации.",
        },
        {
            "num": "06",
            "title": "Государственная регистрация",
            "duration_cash": "7–9 рабочих дней (МФЦ) / 3 дня (нотариус)",
            "duration_mort": "5–7 рабочих дней / 1 день (электронная)",
            "buyer": "Ожидание выписки из ЕГРН. Отслеживание статуса на сайте Росреестра.",
            "seller": "После регистрации — раскрытие аккредитива / ячейки. Продавец получает деньги.",
            "risk": "Росреестр может приостановить регистрацию (арест, ошибка в документах). Причину можно узнать онлайн и устранить.",
        },
        {
            "num": "07",
            "title": "Передача объекта",
            "duration_cash": "В день регистрации или по договорённости",
            "duration_mort": "В день регистрации или по договорённости",
            "buyer": "Осмотр квартиры по акту приёма-передачи. Проверка счётчиков. Получение ключей.",
            "seller": "Освобождение квартиры в согласованные сроки. Передача ключей, документов на квартиру, квитанций ЖКХ.",
            "risk": "Подписывайте акт только после реального осмотра. Обнаруженные дефекты фиксируйте письменно.",
        },
    ]

    for s in stages:
        duration = s["duration_mort"] if is_mortgage else s["duration_cash"]
        is_skip = duration == "— (не требуется)"
        opacity = "0.4" if is_skip else "1"
        border_color = "#e5e7eb" if is_skip else "#008a5e"

        if is_skip:
            inner_html = "<i style='color:#9ca3af;font-size:.85rem;'>Этап не нужен для данного типа сделки</i>"
        else:
            inner_html = f"<div style='display:grid;grid-template-columns:1fr 1fr;gap:10px;margin-bottom:8px;'><div style='font-size:.82rem;'><span style='font-weight:700;color:#2563eb;'>👤 Покупатель:</span><br>{s['buyer']}</div><div style='font-size:.82rem;'><span style='font-weight:700;color:#059669;'>🏠 Продавец:</span><br>{s['seller']}</div></div><div style='background:#fffbeb;border-radius:6px;padding:6px 10px;font-size:.8rem;color:#92400e;'>⚠️ <b>Риск:</b> {s['risk']}</div>"

        html_str = f"<div style='display:flex;gap:16px;margin-bottom:16px;opacity:{opacity}'><div style='display:flex;flex-direction:column;align-items:center;'><div style='width:36px;height:36px;border-radius:50%;background:{'#e5e7eb' if is_skip else '#008a5e'};color:{'#9ca3af' if is_skip else '#fff'};display:flex;align-items:center;justify-content:center;font-weight:900;font-size:.85rem;flex-shrink:0;'>{s['num']}</div><div style='width:2px;flex:1;background:{'#e5e7eb' if is_skip else '#d1fae5'};margin-top:4px;min-height:20px;'></div></div><div style='flex:1;background:#fff;border:1px solid {border_color};border-radius:14px;padding:14px 16px;margin-bottom:4px;'><div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px;margin-bottom:8px;'><div style='font-weight:800;font-size:1rem;'>{s['title']}</div><div style='background:{'#f3f4f6' if is_skip else '#f0fdf7'};color:{'#9ca3af' if is_skip else '#059669'};padding:3px 10px;border-radius:99px;font-size:.78rem;font-weight:700;white-space:nowrap;'>⏱ {duration}</div></div>{inner_html}</div></div>"
        
        st.markdown(html_str, unsafe_allow_html=True)

    total_cash = "3–10 недель"
    total_mort = "6–16 недель"
    total = total_mort if is_mortgage else total_cash
    st.markdown(f"""<div class="hl-box">
    🗓️ <b>Общий ориентировочный срок от выбора квартиры до ключей:</b> <span style="font-size:1.1rem;font-weight:800;color:#008a5e;">{total}</span><br>
    <small style="color:#6b7280;">Ипотека с одобрением банка — дольше. Альтернативная сделка (цепочка) — ещё на 2–4 недели больше. Нотариальная регистрация — быстрее.</small>
    </div>""", unsafe_allow_html=True)

    st.markdown('<div class="hl-box">💡 <b>Важно:</b> На каждом этапе цена ошибки — миллионы рублей. Задача профильного специалиста — организовать процесс так, чтобы исключить риск потери денег, судов и отказов в регистрации.</div>', unsafe_allow_html=True)


def tab_psychology():
    st.markdown("### 🧠 Психология переговоров: частые ошибки")
    st.info("Переговоры о цене — шахматная партия. Эмоции здесь стоят реальных денег.")
    
    mistakes = [
        ("❌ Позиция «Я тут главный» (Частая ошибка продавцов)",
         "Многие продавцы считают: «Моя квартира — мои правила». Это выражается в высокомерии на показах, отказе предоставить документы до задатка или фразах «не нравится — ищите дальше».<br><br><b>Почему это происходит:</b> Защитная реакция или переоценка ликвидности своего жилья.<br><b>Итог:</b> Адекватные покупатели с деньгами уходят. Объект превращается в «музей», висит в рекламе полгода и в итоге продается с огромным дисконтом из-за отчаяния."),

        ("❌ Синдром «Влюблённого покупателя»",
         "Самая дорогая ошибка — показать свою нужду. Вы приходите на просмотр всей семьей, восхищаетесь планировкой и прямо при продавце решаете, где будет стоять диван.<br><br><b>Почему это происходит:</b> Неумение контролировать эмоции, когда объект действительно подошел.<br><b>Итог:</b> Продавец моментально считывает вашу зависимость. Он понимает, что вы уже мысленно переехали, а значит — ни о каком торге не может быть и речи. Вы переплатите."),

        ("❌ Иллюзия «Идеального объекта»",
         "Покупатели склонны прощать квартире серьезные юридические угрозы (свежее наследство, мутные доверенности, долги), если у нее шикарный вид из окна или свежий дизайнерский ремонт.<br><br><b>Почему это происходит:</b> Визуальная эстетика отключает логику и инстинкт самосохранения.<br><b>Итог:</b> Покупка красивой «обертки» с юридической бомбой внутри. Прямой путь к многолетним судам и потере денег."),

        ("❌ Торг без аргументов («Нахрапом»)",
         "Покупатель с порога заявляет: «Скинете 500 тысяч — забираю прямо сейчас». Без объяснения причин.<br><br><b>Почему это происходит:</b> Иллюзия, что продавец сломается под давлением наглости.<br><b>Итог:</b> Такая тактика вызывает только ответную агрессию. Объективный торг строится строго на фактах: расчет сметы на устранение дефектов, сравнение с конкурентами в этом же доме, ваша готовность выйти на сделку без ипотеки хоть завтра.")
    ]
    
    for title, desc in mistakes:
        st.markdown(f'<div class="risk-card warning" style="border-left-color:#f59e0b;"><div class="risk-title">{html.escape(title)}</div><div class="risk-law" style="font-size: 0.88rem;">{desc}</div></div>', unsafe_allow_html=True)
    
    st.markdown('<div class="warn-box">🎯 <b>Мой подход:</b> Здесь описана только базовая теория. Жёсткие скрипты перехвата инициативы, техники экологичного снижения цены и аргументированный торг — я применяю лично, защищая интересы своих клиентов на реальных сделках.</div>', unsafe_allow_html=True)

# ─── MAIN ─────────────────────────────────────

def main():
    inject_styles()
    if "my_text" not in st.session_state:
        st.session_state.my_text = ""

    logo_b64 = get_base64_image(LOGO_FILE)
    logo_html = (f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">'
                 if logo_b64 else "<div style='font-size:52px;margin-bottom:14px;'>🏢</div>")

    st.markdown(f"""
    <div class="header-wrapper">
        {logo_html}
        <div class="hero-title">АРТЕМ НОСОВ | РИЕЛТОР</div>
        <div class="hero-sub">Авторский сервис аудита недвижимости</div>
        <a href="https://t.me/nosov_s_blog" class="custom-btn" target="_blank">👉 ПЕРЕЙТИ В БЛОГ «ПУТЬ БЕЗ ФАЛЬШИ»</a>
    </div>
    <div class="tip-box">📌 <b>Лайфхак:</b> Сохраните этот сайт в закладки телефона — шпаргалка по налогам и рискам всегда будет под рукой на просмотрах квартир.</div>
    """, unsafe_allow_html=True)

    tabs = st.tabs(["🛡️ АУДИТ","💰 НАЛОГИ","🏦 ИПОТЕКА","📉 ОЦЕНКА","💼 РАСХОДЫ","📅 ЭТАПЫ","🧠 ПСИХОЛОГИЯ"])
    with tabs[0]: tab_audit()
    with tabs[1]: tab_tax()
    with tabs[2]: tab_mortgage()
    with tabs[3]: tab_estimation()
    with tabs[4]: tab_costs()
    with tabs[5]: tab_stages()
    with tabs[6]: tab_psychology()

    st.markdown("""
    <div class="hook-card">
        <div class="hook-title">Без риелтора: как теряют задатки на ровном месте</div>
        <div style="font-size:.9rem;line-height:1.6;color:#374151;">Покупатели сами нашли квартиру, перевели задаток на карту без нормальных бумаг… А потом сделка разваливается. В блоге разобрал реальные случаи.</div><br>
        <a href="https://t.me/nosov_s_blog/413" target="_blank" style="color:#008a5e;font-weight:700;text-decoration:none;font-size:1rem;">👉 Читать пост о рисках →</a>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<h3 style='text-align:center;margin-top:40px;font-size:1.2rem;font-weight:800;'>СВЯЗАТЬСЯ СО МНОЙ:</h3>", unsafe_allow_html=True)

    TG = "https://t.me/Artem_Nosov_Vrn"
    WA = "https://wa.me/79000000000"   
    VK = "https://vk.com/artem_nosov_vrn"            

    st.markdown(f"""
    <div class="social-container">
        <a href="{TG}" class="social-btn btn-tg" target="_blank"><img src="https://img.icons8.com/color/96/telegram-app.png"> Telegram</a>
        <a href="{WA}" class="social-btn btn-wa" target="_blank"><img src="https://img.icons8.com/color/96/whatsapp--v1.png"> WhatsApp</a>
        <a href="{VK}" class="social-btn btn-vk" target="_blank"><img src="https://img.icons8.com/color/96/vk-com.png"> ВКонтакте</a>
    </div>
    <div class="footer-disc">
        ⚠️ <b>ПРАВОВОЕ УВЕДОМЛЕНИЕ:</b> Анализ выполнен алгоритмической моделью на основе скоринга маркеров риска.<br>
        Отчёт носит информационно-аналитический характер и не является юридической консультацией.<br>
        Для 100% гарантии безопасности сделки обращайтесь к профильным специалистам.
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()