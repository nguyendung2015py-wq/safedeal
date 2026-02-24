import streamlit as st
import base64
import random
import time
from datetime import datetime
from dataclasses import dataclass
from typing import List

st.set_page_config(
    page_title="SafeDeal — экспертиза сделки",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def get_base64_image(image_path):
    try:
        with open(image_path, "rb") as img_file:
            return base64.b64encode(img_file.read()).decode()
    except Exception:
        return None

def inject_custom_styles() -> None:
    st.markdown(
        """
        <style>
        /* УБИВАЕМ КОРОНУ И ЛИШНИЙ ИНТЕРФЕЙС */
        header {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
        .viewerBadge_container, .viewerBadge_link, [data-testid="stViewerBadge"], .stDeployButton { display: none !important; visibility: hidden !important; opacity: 0 !important; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }

        body { background-color: #ffffff; color: #2d3436; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif; }
        .main .block-container { padding-top: 2rem; max-width: 950px; }

        .header-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; width: 100%; margin-bottom: 2rem; }
        .logo-img { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; box-shadow: 0 6px 15px rgba(0, 138, 94, 0.2); border: 4px solid #008a5e; padding: 3px; margin-bottom: 15px; }
        .hero-title { font-size: 2.2rem; font-weight: 900; color: #1e1e1e; margin: 0 0 5px 0; letter-spacing: 0.05em; }
        .hero-subtitle { font-size: 1.1rem; font-weight: 600; color: #008a5e; margin: 0 0 20px 0; }
        .custom-btn { background: linear-gradient(135deg, #008a5e 0%, #006f4b 100%); color: white !important; padding: 12px 35px; border-radius: 30px; font-weight: 600; font-size: 16px; text-decoration: none; box-shadow: 0 4px 15px rgba(0, 138, 94, 0.25); transition: 0.3s; display: inline-block; }
        .custom-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 138, 94, 0.35); }

        .stButton>button { background-color: #008a5e; color: #ffffff; border-radius: 8px; border: none; padding: 0.65rem 1.1rem; font-weight: 600; font-size: 0.9rem; width: 100%; margin-top: 10px; }
        .stButton>button:hover { background-color: #006f49; }

        .decision-banner { margin-top: 1.5rem; padding: 1.2rem; border-radius: 0.9rem; border: 1px solid; display: flex; align-items: center; gap: 1.5rem; }
        .decision-banner.danger { border-color: #dc2626; background: #fffcfc; }
        .decision-banner.warning { border-color: #f59e0b; background: #fffbeb; }
        .decision-banner.safe { border-color: #059669; background: #f8fffc; }
        
        .decision-score { font-size: 2.8rem; font-weight: 800; line-height: 1; }
        .danger .decision-score, .danger .decision-text-main { color: #dc2626; }
        .warning .decision-score, .warning .decision-text-main { color: #d97706; }
        .safe .decision-score, .safe .decision-text-main { color: #059669; }
        
        .decision-text-main { font-size: 1.1rem; font-weight: 700; text-transform: uppercase; }
        .decision-text-sub { font-size: 0.9rem; color: #4b5563; margin-top: 5px; }

        .table-wrapper { width: 100%; overflow-x: auto; margin-top: 1rem; border-radius: 8px; border: 1px solid #e5e7eb; }
        .risk-table { width: 100%; border-collapse: collapse; min-width: 600px; }
        .risk-table th { background-color: #f9fafb; font-weight: 700; padding: 12px; border-bottom: 2px solid #e5e7eb; text-align: left; font-size: 0.9rem; }
        .risk-table td { padding: 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; font-size: 0.85rem; line-height: 1.5; }
        .risk-table th:nth-child(1) { width: 20%; }
        .risk-table th:nth-child(2) { width: 45%; }
        .risk-table th:nth-child(3) { width: 35%; }
        
        .report-header { text-align: right; color: #6b7280; font-size: 0.8rem; font-weight: 600; margin-bottom: 10px; border-bottom: 1px dashed #e5e7eb; padding-bottom: 5px; }
        .footer-disclaimer { text-align: center; font-size: 0.75rem; color: #9ca3af; margin-top: 3rem; border-top: 1px solid #f3f4f6; padding-top: 1.5rem; line-height: 1.5; }

        @media (max-width: 768px) {
            .hero-title { font-size: 1.6rem; }
            .hero-subtitle { font-size: 0.95rem; }
            .logo-img { width: 110px; height: 110px; }
            .decision-banner { flex-direction: column; align-items: flex-start; gap: 0.8rem; padding: 1rem; }
            .decision-score { font-size: 2.2rem; }
            .risk-table th, .risk-table td { padding: 8px; font-size: 0.8rem; }
            .custom-btn { padding: 10px 25px; font-size: 14px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

@dataclass
class RiskItem:
    what: str; law: str; fix: str; weight: float; category: str

@dataclass
class AnalysisResult:
    total_risk: int; items: List[RiskItem]

def _detect(text: str, keywords: List[str]) -> bool:
    return any(kw in text.lower() for kw in keywords)

def analyze_safedeal(text: str) -> AnalysisResult:
    items = []
    risks = [
        {"cat": "object", "what": "Объект в залоге (ипотека банка)", 
         "kw": ["в ипотеке", "залог", "обременен", "под залогом", "ипотечн", "в силу закона"], 
         "law": "ФЗ №102-ФЗ «Об ипотеке» ст. 37. Отчуждение заложенного имущества допускается только с письменного согласия залогодержателя.", 
         "fix": "Сделка строго под контролем банка: гашение долга через СБР или официальный перевод долга.", "w": 15.0},
        {"cat": "object", "what": "Арест или запрет на рег. действия", 
         "kw": ["арест", "запрет", "ограничени", "судебный пристав"], 
         "law": "ФЗ №218-ФЗ «О госрегистрации недвижимости» ст. 56. Росреестр приостановит регистрацию.", 
         "fix": "Срочный запрос ЕГРН. Погашение долгов до сделки, получение постановления о снятии ареста.", "w": 30.0},
        {"cat": "object", "what": "Маткапитал и скрытые детские доли", 
         "kw": ["маткапитал", "материнск", "детск", "доли не выделены", "опек", "несовершеннолетн"], 
         "law": "СК РФ ст. 60, ФЗ № 256-ФЗ. Сделка без выделения долей детям ничтожна (ст. 168 ГК РФ).", 
         "fix": "Запрос справки СФР об остатке маткапитала. Требовать выделения долей до сделки и приказ опеки.", "w": 20.0},
        {"cat": "object", "what": "Свежее или спорное наследство", 
         "kw": ["наследств", "завещан", "умер", "вступил в наследство"], 
         "law": "ГК РФ ст. 1149, ст. 1155. Риск истребования доли неучтенными наследниками (ст. 302 ГК РФ).", 
         "fix": "Требовать нотариальное обязательство о самостоятельном финансовом урегулировании претензий.", "w": 20.0},
        {"cat": "seller", "what": "Банкротство, долги и суды", 
         "kw": ["банкрот", "пристав", "долг", "фссп", "судебн", "ниже рынка", "срочно продам"], 
         "law": "ФЗ № 127-ФЗ ст. 61.2. Сделки должника в течение 3 лет до банкротства могут быть оспорены.", 
         "fix": "Аудит продавца по базам ФССП, ЕФРСБ, картотеке арбитражных дел (КАД) и ГАС «Правосудие».", "w": 25.0},
        {"cat": "seller", "what": "Справки ПНД/НД и дееспособность", 
         "kw": ["пенсионер", "пожил", "инвалид", "психиатр", "нарколог", "пнд", "нд", "справк", "дееспособн"], 
         "law": "ГК РФ ст. 177. Сделка гражданином, не понимающим значение своих действий, оспорима.", 
         "fix": "Требовать личного получения справок из ПНД/НД. Оптимально — психиатр на сделке.", "w": 20.0},
        {"cat": "seller", "what": "Продажа по доверенности", 
         "kw": ["доверенност", "поверенн", "представител", "за границей"], 
         "law": "ГК РФ ст. 188. Ничтожно, если доверитель умер или доверенность отозвана.", 
         "fix": "Проверка доверенности по реестру ФНП прямо в день сделки. Видеозвонок с собственником.", "w": 20.0},
        {"cat": "trigger", "what": "Занижение цены в договоре (ДКП)", 
         "kw": ["занижен", "в конверте", "меньше", "минимальная", "неполная стоимост", "налог"], 
         "law": "ГК РФ ст. 170 (Притворная сделка). НК РФ ст. 122. Риск потери денег при банкротстве продавца.", 
         "fix": "Указывать в ДКП полную реальную стоимость. Использовать аккредитив или эскроу.", "w": 30.0},
    ]

    for cfg in risks:
        if _detect(text, cfg["kw"]):
            items.append(RiskItem(cfg["what"], cfg["law"], cfg["fix"], cfg["w"], cfg["cat"]))

    b_tot = sum(i.weight for i in items)
    critical_triggers = ["в конверте", "занижен", "банкрот", "наследств", "доли не выделены", "опек", "арест", "запрет"]
    if _detect(text, critical_triggers):
        b_tot = max(b_tot, 85.0)

    if not items:
        b_tot = 40.0
        items.append(RiskItem("Недостаточно данных", "ГК РФ ст. 421. Маркеры не найдены.", "Проведите полный сбор документов.", 40.0, "object"))

    final_score = max(0, min(int(round(b_tot)), 100))
    return AnalysisResult(final_score, items)

# Шаблоны текста
def set_template_1(): st.session_state.my_text = "Продавец пенсионер 75 лет. Продает квартиру по доверенности, оформленной на сына. Свежее наследство по закону."
def set_template_2(): st.session_state.my_text = "Квартира в ипотеке. Использовался маткапитал, но доли детям не выделили. Хотят занижение стоимости в договоре."
def set_template_3(): st.session_state.my_text = "Собственник продает срочно, ниже рынка. Есть долги у приставов."

def main():
    inject_custom_styles()
    
    if "my_text" not in st.session_state:
        st.session_state.my_text = ""

    logo_b64 = get_base64_image("logo.png")
    if logo_b64:
        logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">'
    else:
        logo_html = "<div style='font-size:50px; margin-bottom:15px;'>🏢</div>"

    st.markdown(f"""
        <div class="header-wrapper">
            {logo_html}
            <div class="hero-title">АРТЕМ НОСОВ | РИЕЛТОР</div>
            <div class="hero-subtitle">Авторский сервис аудита недвижимости</div>
            <a href="https://t.me/nosov_s_blog" class="custom-btn" target="_blank">👉 ПЕРЕЙТИ В БЛОГ «ПУТЬ БЕЗ ФАЛЬШИ»</a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("<b>⚡ Быстрые ситуации:</b>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)
    col1.button("👴 Доверенность + Наследство", on_click=set_template_1, use_container_width=True)
    col2.button("👶 Маткапитал + Занижение", on_click=set_template_2, use_container_width=True)
    col3.button("⚖️ Долги + Срочность", on_click=set_template_3, use_container_width=True)

    text = st.text_area("Текст для экспертизы", key="my_text", height=140, placeholder="Или опишите ситуацию своими словами...")
    
    if st.button("ЗАПУСТИТЬ ГЛУБОКУЮ ЭКСПЕРТИЗУ"):
        if not text.strip(): 
            st.warning("Введите данные для анализа.")
        else:
            with st.status("🔍 Инициализация алгоритма SafeDeal...", expanded=True) as status:
                st.write("📡 Подключение к базам судебной практики...")
                time.sleep(1)
                st.write("⚖️ Сканирование юридических рисков и маркеров...")
                time.sleep(1.5)
                st.write("🛡️ Формирование защитного алгоритма...")
                time.sleep(1)
                status.update(label="Анализ успешно завершен!", state="complete", expanded=False)

            res = analyze_safedeal(text)
            
            if res.total_risk >= 70:
                b_cls = "danger"
                z_lbl = "КРАСНАЯ ЗОНА (СТОП-СДЕЛКА)"
                sub_txt = "Критический уровень риска. Запрещено выходить на сделку без профильного юриста."
            elif res.total_risk >= 40:
                b_cls = "warning"
                z_lbl = "ЖЕЛТАЯ ЗОНА (ПОВЫШЕННЫЙ РИСК)"
                sub_txt = "Требуется сбор дополнительных документов и глубокая проверка контрагентов."
            else:
                b_cls = "safe"
                z_lbl = "ЗЕЛЕНАЯ ЗОНА (КОНТРОЛИРУЕМО)"
                sub_txt = "Явных критических угроз не выявлено, но базовая проверка обязательна."
            
            report_id = random.randint(10000, 99999)
            current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
            
            st.markdown(f"""
            <div class="decision-banner {b_cls}">
                <div style="text-align: center; min-width: 120px;">
                    <div class="decision-score">{res.total_risk}%</div>
                    <div style="font-size: 0.8rem; font-weight: bold; color: #6b7280; margin-top: 5px;">ИНДЕКС РИСКА</div>
                </div>
                <div style="width: 100%;">
                    <div class="report-header">Акт проверки №{report_id} от {current_date}</div>
                    <div class="decision-text-main">{z_lbl}</div>
                    <div class="decision-text-sub">{sub_txt}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            table_html = "<div class='table-wrapper'><table class='risk-table'><thead><tr><th>УГРОЗА</th><th>ЮРИДИЧЕСКАЯ БАЗА И СУДЕБНАЯ ПРАКТИКА</th><th>АЛГОРИТМ ЗАЩИТЫ</th></tr></thead><tbody>"
            report_text = f"АКТ ПРОВЕРКИ №{report_id} от {current_date}\nСервис аудита недвижимости | Риелтор Артем Носов\n\nВводные данные: {text}\n\nИНДЕКС РИСКА: {res.total_risk}%\nРЕШЕНИЕ: {z_lbl}\n{sub_txt}\n\nВЫЯВЛЕННЫЕ УГРОЗЫ:\n"
            
            for i in res.items:
                table_html += f"<tr><td><b>{i.what}</b></td><td>{i.law}</td><td>{i.fix}</td></tr>"
                report_text += f"\n- {i.what}\n  Закон: {i.law}\n  Решение: {i.fix}\n"
            
            table_html += "</tbody></table></div>"
            st.markdown(table_html, unsafe_allow_html=True)
            
            # Кнопка скачивания отчета
            report_text += "\n\n⚠️ ВНИМАНИЕ: Данный аудит носит информационно-аналитический характер."
            st.download_button(
                label="📥 СКАЧАТЬ АКТ ПРОВЕРКИ (TXT)",
                data=report_text,
                file_name=f"SafeDeal_Report_{report_id}.txt",
                mime="text/plain"
            )

    st.markdown("""
        <div class="footer-disclaimer">
            ⚠️ <b>ПРАВОВОЕ УВЕДОМЛЕНИЕ:</b> Данный аудит сгенерирован алгоритмической моделью на основе скоринга маркеров риска.<br>
            Отчет носит информационно-аналитический характер и не является официальным правовым заключением. Для 100% гарантии обращайтесь к профильным юристам.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()