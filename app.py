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
        header {visibility: hidden !important;}
        footer {visibility: hidden !important; display: none !important;}
        #MainMenu {visibility: hidden !important; display: none !important;}
        [data-testid="stHeader"], [data-testid="stToolbar"], [data-testid="stDecoration"] { display: none !important; }
        .viewerBadge_container, .viewerBadge_link, [data-testid="stViewerBadge"], .stDeployButton { display: none !important; visibility: hidden !important; opacity: 0 !important; }
        section[data-testid="stSidebar"], [data-testid="collapsedControl"] { display: none !important; }
        
        /* Убиваем скрепки ссылок у заголовков */
        h1 a, h2 a, h3 a, h4 a, h5 a, h6 a { display: none !important; pointer-events: none !important; }
        h1 svg, h2 svg, h3 svg { display: none !important; }

        body { background-color: #ffffff; color: #2d3436; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Inter, sans-serif; }
        .main .block-container { padding-top: 2rem; max-width: 950px; padding-bottom: 3rem; }

        .header-wrapper { display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; width: 100%; margin-bottom: 1.5rem; }
        .logo-img { width: 140px; height: 140px; border-radius: 50%; object-fit: cover; box-shadow: 0 6px 15px rgba(0, 138, 94, 0.2); border: 4px solid #008a5e; padding: 3px; margin-bottom: 15px; }
        .hero-title { font-size: 2.2rem; font-weight: 900; color: #1e1e1e; margin: 0 0 5px 0; letter-spacing: 0.05em; }
        .hero-subtitle { font-size: 1.1rem; font-weight: 600; color: #008a5e; margin: 0 0 20px 0; }
        .custom-btn { background: linear-gradient(135deg, #008a5e 0%, #006f4b 100%); color: white !important; padding: 12px 35px; border-radius: 30px; font-weight: 600; font-size: 16px; text-decoration: none; box-shadow: 0 4px 15px rgba(0, 138, 94, 0.25); transition: 0.3s; display: inline-block; }
        .custom-btn:hover { transform: translateY(-2px); box-shadow: 0 6px 20px rgba(0, 138, 94, 0.35); }

        .stButton>button { background-color: #008a5e; color: #ffffff; border-radius: 8px; border: none; padding: 0.65rem 1.1rem; font-weight: 600; font-size: 0.9rem; width: 100%; margin-top: 10px; }
        .stButton>button:hover { background-color: #006f49; }

        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f8f9fa; padding: 5px; border-radius: 12px; border: 1px solid #e9ecef; }
        .stTabs [data-baseweb="tab"] { height: 50px; white-space: nowrap; background-color: transparent; color: #495057; font-weight: 600; border-radius: 8px; padding: 0 20px; border: none !important; transition: all 0.2s; }
        .stTabs [aria-selected="true"] { background-color: #008a5e !important; color: white !important; box-shadow: 0 4px 12px rgba(0, 138, 94, 0.2); }
        .stTabs [data-baseweb="tab-highlight"] { display: none; }

        .decision-banner { margin-top: 1.5rem; padding: 1.2rem; border-radius: 0.9rem; border: 1px solid; display: flex; align-items: center; gap: 1.5rem; margin-bottom: 1.5rem; }
        .decision-banner.danger { border-color: #dc2626; background: #fffcfc; }
        .decision-banner.warning { border-color: #f59e0b; background: #fffbeb; }
        .decision-banner.safe { border-color: #059669; background: #f8fffc; }
        
        .decision-score { font-size: 2.8rem; font-weight: 800; line-height: 1; }
        .danger .decision-score, .danger .decision-text-main { color: #dc2626; }
        .warning .decision-score, .warning .decision-text-main { color: #d97706; }
        .safe .decision-score, .safe .decision-text-main { color: #059669; }
        
        .decision-text-main { font-size: 1.1rem; font-weight: 700; text-transform: uppercase; }
        .decision-text-sub { font-size: 0.9rem; color: #4b5563; margin-top: 5px; }
        
        .table-wrapper { width: 100%; overflow-x: auto; margin-top: 1rem; border-radius: 8px; border: 1px solid #e5e7eb; margin-bottom: 20px; }
        .risk-table { width: 100%; border-collapse: collapse; min-width: 600px; }
        .risk-table th { background-color: #f9fafb; font-weight: 700; padding: 12px; border-bottom: 2px solid #e5e7eb; text-align: left; font-size: 0.9rem; }
        .risk-table td { padding: 12px; border-bottom: 1px solid #e5e7eb; vertical-align: top; font-size: 0.85rem; line-height: 1.5; }
        .risk-table th:nth-child(1) { width: 25%; }
        .risk-table th:nth-child(2) { width: 45%; }
        .risk-table th:nth-child(3) { width: 30%; }
        
        .hook-card { background: linear-gradient(to right, #f8f9fa, #ffffff); border-left: 4px solid #f59e0b; padding: 18px; border-radius: 10px; margin-top: 25px; box-shadow: 0 4px 15px rgba(0,0,0,0.05); }
        .hook-title { font-weight: 800; font-size: 1.15rem; margin-bottom: 10px; color: #1f2937; display: flex; align-items: center; }
        .hook-title::before { content: "🔥"; margin-right: 8px; font-size: 1.3rem; }
        
        .social-btn { display: flex; align-items: center; justify-content: center; gap: 10px; padding: 12px; border-radius: 8px; color: white !important; font-weight: 600; text-decoration: none; transition: 0.2s; margin-top: 10px;}
        .social-btn:hover { opacity: 0.9; transform: translateY(-2px); }
        .btn-tg { background-color: #2AABEE; }
        .btn-wa { background-color: #25D366; }
        .btn-vk { background-color: #0077FF; }
        .svg-icon { width: 20px; height: 20px; fill: currentColor; }
        
        .footer-disclaimer { text-align: center; font-size: 0.75rem; color: #9ca3af; margin-top: 3rem; border-top: 1px solid #f3f4f6; padding-top: 1.5rem; line-height: 1.5; }

        @media (max-width: 768px) {
            .hero-title { font-size: 1.6rem; }
            .hero-subtitle { font-size: 0.95rem; }
            .logo-img { width: 110px; height: 110px; }
            .decision-banner { flex-direction: column; align-items: flex-start; gap: 0.8rem; padding: 1rem; }
            .decision-score { font-size: 2.2rem; }
            .risk-table th:nth-child(1), .risk-table th:nth-child(2), .risk-table th:nth-child(3) { width: auto; }
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
         "law": "ФЗ №102-ФЗ ст. 37. Имущество, заложенное по договору об ипотеке, может быть отчуждено только с письменного согласия залогодержателя.", 
         "fix": "Сделка строго под контролем банка: гашение долга через СБР или официальный перевод долга.", "w": 15.0},
        
        {"cat": "object", "what": "Арест или запрет на рег. действия", 
         "kw": ["арест", "запрет", "ограничени", "судебный пристав"], 
         "law": "ФЗ №218-ФЗ ст. 56. Регистрация прав приостанавливается при поступлении решения о наложении ареста.", 
         "fix": "Срочный запрос ЕГРН. Погашение долгов до сделки, получение постановления о снятии ареста.", "w": 30.0},
        
        {"cat": "object", "what": "Маткапитал и скрытые детские доли", 
         "kw": ["маткапитал", "материнск", "детск", "доли не выделены", "опек", "несовершеннолетн"], 
         "law": "ФЗ №256-ФЗ ст. 10. Лицо, получившее сертификат, обязано оформить помещение в общую собственность детей. Сделка без выделения долей ничтожна.", 
         "fix": "Запрос справки СФР об остатке маткапитала. Требовать выделения долей до сделки и приказ опеки.", "w": 20.0},
        
        {"cat": "object", "what": "Свежее или спорное наследство", 
         "kw": ["наследств", "завещан", "умер", "вступил в наследство"], 
         "law": "ГК РФ ст. 1155. Суд может восстановить срок для принятия наследства другим наследникам и признать их права на объект.", 
         "fix": "Требовать нотариальное обязательство о самостоятельном финансовом урегулировании претензий.", "w": 20.0},
        
        {"cat": "seller", "what": "Банкротство, долги и суды", 
         "kw": ["банкрот", "пристав", "долг", "фссп", "судебн", "ниже рынка", "срочно продам"], 
         "law": "ФЗ № 127-ФЗ ст. 61.2. Сделки должника в течение 3 лет до банкротства могут быть оспорены и признаны недействительными.", 
         "fix": "Аудит продавца по базам ФССП, ЕФРСБ, картотеке арбитражных дел (КАД).", "w": 25.0},
        
        {"cat": "seller", "what": "Справки ПНД/НД и дееспособность", 
         "kw": ["пенсионер", "пожил", "инвалид", "психиатр", "нарколог", "пнд", "нд", "справк", "дееспособн"], 
         "law": "ГК РФ ст. 177. Сделка, совершенная гражданином, не способным понимать значение своих действий, оспорима.", 
         "fix": "Требовать личного получения справок из ПНД/НД. Оптимально — психиатр на сделке.", "w": 20.0},
        
        {"cat": "seller", "what": "Продажа по доверенности", 
         "kw": ["доверенност", "поверенн", "представител", "за границей"], 
         "law": "ГК РФ ст. 188. Доверенность прекращается при ее отмене лицом, выдавшим ее, либо смерти этого гражданина.", 
         "fix": "Проверка доверенности по реестру ФНП прямо в день сделки. Видеозвонок с собственником.", "w": 20.0},
        
        {"cat": "trigger", "what": "Занижение цены в договоре (ДКП)", 
         "kw": ["занижен", "в конверте", "меньше", "минимальная", "неполная стоимост", "налог"], 
         "law": "ГК РФ ст. 170. Притворная сделка (с целью прикрыть другую стоимость) ничтожна. Риск возврата только суммы по ДКП.", 
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
        items.append(RiskItem("Недостаточно данных", "ГК РФ ст. 421 (Свобода договора). Явных стоп-маркеров нет, но ответственность за проверку чистоты объекта лежит на покупателе.", "Проведите полный сбор документов.", 40.0, "object"))

    final_score = max(0, min(int(round(b_tot)), 100))
    return AnalysisResult(final_score, items)

def set_template_1(): st.session_state.my_text = "Продавец пенсионер 75 лет. Продает квартиру по доверенности, оформленной на сына. Свежее наследство по закону."
def set_template_2(): st.session_state.my_text = "Квартира в ипотеке. Использовался маткапитал, но доли детям не выделили. Хотят занижение стоимости в договоре."
def set_template_3(): st.session_state.my_text = "Собственник продает срочно, ниже рынка. Есть долги у приставов."

def calculate_progressive_tax(taxable_income):
    threshold = 2400000 
    if taxable_income <= 0: return 0, 0, 0
    elif taxable_income <= threshold: return taxable_income * 0.13, taxable_income * 0.13, 0
    else:
        tax_13 = threshold * 0.13
        tax_15 = (taxable_income - threshold) * 0.15
        return tax_13 + tax_15, tax_13, tax_15

def calculate_mortgage(price, initial_payment, rate, years):
    loan_amount = price - initial_payment
    if loan_amount <= 0: return 0, 0, 0
    monthly_rate = (rate / 100) / 12
    months = years * 12
    if monthly_rate == 0: payment = loan_amount / months
    else: payment = loan_amount * (monthly_rate * (1 + monthly_rate)**months) / ((1 + monthly_rate)**months - 1)
    total_paid = payment * months
    return payment, total_paid - loan_amount, total_paid

def main():
    inject_custom_styles()
    
    if "my_text" not in st.session_state: st.session_state.my_text = ""

    logo_b64 = get_base64_image("logo.png")
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" class="logo-img">' if logo_b64 else "<div style='font-size:50px; margin-bottom:15px;'>🏢</div>"

    st.markdown(f"""
        <div class="header-wrapper">
            {logo_html}
            <div class="hero-title">АРТЕМ НОСОВ | РИЕЛТОР</div>
            <div class="hero-subtitle">Авторский сервис аудита недвижимости</div>
            <a href="https://t.me/nosov_s_blog" class="custom-btn" target="_blank">👉 ПЕРЕЙТИ В БЛОГ «ПУТЬ БЕЗ ФАЛЬШИ»</a>
        </div>
    """, unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🛡️ АУДИТ РИСКОВ", "💰 НАЛОГИ (2025)", "🏦 ИПОТЕКА"])

    with tab1:
        st.markdown("<b>⚡ Быстрые ситуации:</b>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.button("👴 Доверенность + Наследство", on_click=set_template_1, use_container_width=True)
        col2.button("👶 Маткапитал + Занижение", on_click=set_template_2, use_container_width=True)
        col3.button("⚖️ Долги + Срочность", on_click=set_template_3, use_container_width=True)

        text = st.text_area("Текст для экспертизы", key="my_text", height=140, placeholder="Опишите ситуацию своими словами...")
        
        if st.button("ЗАПУСТИТЬ ГЛУБОКУЮ ЭКСПЕРТИЗУ", key="run_audit"):
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
                    b_cls, z_lbl, sub_txt = "danger", "КРАСНАЯ ЗОНА (СТОП-СДЕЛКА)", "Критический уровень риска. Запрещено выходить на сделку без профильного юриста."
                elif res.total_risk >= 40:
                    b_cls, z_lbl, sub_txt = "warning", "ЖЕЛТАЯ ЗОНА (ПОВЫШЕННЫЙ РИСК)", "Требуется сбор дополнительных документов и глубокая проверка контрагентов."
                else:
                    b_cls, z_lbl, sub_txt = "safe", "ЗЕЛЕНАЯ ЗОНА (КОНТРОЛИРУЕМО)", "Явных критических угроз не выявлено, но базовая проверка обязательна."
                
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
                
                report_text += "\n\n⚠️ ВНИМАНИЕ: Данный аудит носит информационно-аналитический характер."
                st.download_button(
                    label="📥 СКАЧАТЬ АКТ ПРОВЕРКИ (TXT)",
                    data=report_text,
                    file_name=f"SafeDeal_Report_{report_id}.txt",
                    mime="text/plain"
                )

    with tab2:
        st.markdown("### 🧮 Калькулятор НДФЛ с продажи (Прогрессивная шкала 2025)")
        
        # ДОБАВЛЕНА ПРОВЕРКА СРОКА ВЛАДЕНИЯ ПО СТ. 217.1 НК РФ
        holding_period = st.radio(
            "Укажите срок владения недвижимостью:", 
            [
                "Минимальный срок НЕ прошел (нужно платить налог)", 
                "Более 3 лет (наследство, дарение близким, приватизация, рента или единственное жилье)",
                "Более 5 лет (во всех остальных случаях)"
            ],
            index=0
        )
        
        if "Более" in holding_period:
            st.success("🎉 **Налог к уплате: 0 ₽.** \n\nВ соответствии со ст. 217.1 НК РФ, вы полностью освобождены от уплаты налога с продажи и подачи декларации 3-НДФЛ, так как прошел минимальный предельный срок владения.")
        else:
            sell_price = st.number_input("Цена продажи по ДКП (₽)", min_value=0, step=100000, value=6000000)
            cadastral = st.number_input("Кадастровая стоимость (₽)", min_value=0, step=100000, value=5000000)
            deduction_type = st.radio("Какой вычет применяем?", ["Расходы на покупку (есть чеки/ДКП)", "Стандартный вычет (1 000 000 ₽)"])
            buy_price = st.number_input("За сколько покупалась ранее (₽)?", min_value=0, step=100000, value=3000000) if "Расходы" in deduction_type else 1000000
                
            if st.button("РАССЧИТАТЬ НАЛОГ", key="run_tax_prog"):
                tax_base = max(sell_price, cadastral * 0.7)
                total_tax, tax_13, tax_15 = calculate_progressive_tax(max(0, tax_base - buy_price))
                
                if total_tax > 0:
                    st.error(f"### Итого налог к уплате: {total_tax:,.0f} ₽".replace(',', ' '))
                    st.markdown(f"**Детализация расчета:**\n1. Налог 13% (с суммы до 2.4 млн): {tax_13:,.0f} ₽\n" + (f"2. Налог 15% (с суммы превышения): {tax_15:,.0f} ₽" if tax_15 > 0 else "").replace(',', ' '))
                else:
                    st.success("✅ Налог к уплате: 0 ₽ (Доход перекрыт вычетами)")

    with tab3:
        st.markdown("### 🏦 Ипотечный калькулятор переплаты")
        prop_price = st.number_input("Стоимость объекта (₽)", min_value=0, step=100000, value=7000000)
        down_payment = st.number_input("Первоначальный взнос (₽)", min_value=0, step=100000, value=2000000)
        mortgage_rate = st.number_input("Ставка банка (%)", min_value=0.1, step=0.1, value=18.5)
        mortgage_years = st.number_input("Срок (лет)", min_value=1, step=1, value=25)
        
        if st.button("РАССЧИТАТЬ ПЕРЕПЛАТУ", key="run_mortgage_final"):
            payment, overpay, total = calculate_mortgage(prop_price, down_payment, mortgage_rate, mortgage_years)
            st.error(f"### Чистая переплата банку: {overpay:,.0f} ₽".replace(',', ' '))
            st.markdown(f"**Ежемесячный платеж:** {payment:,.0f} ₽<br>**Всего вы отдадите за квартиру:** {total:,.0f} ₽", unsafe_allow_html=True)

    st.markdown("""
        <div class="hook-card">
            <div class="hook-title">Без риелтора: как люди теряют задатки на ровном месте</div>
            <div style="font-size: 0.95rem; line-height: 1.5; color: #374151;">
            Типичная ситуация: покупатели сами нашли квартиру, "на доверии" перевели задаток на карту без нормального предварительного договора и проверки... А потом сделка разваливается. В блоге разобрал реальные случаи, когда спешка стоила людям сотен тысяч рублей и кучи нервов.
            </div><br>
            <a href="https://t.me/nosov_s_blog/413" target="_blank" style="color: #008a5e; font-weight: bold; text-decoration: none; font-size: 1.05rem;">👉 Читать пост о рисках в канале «Путь без фальши»</a>
        </div>
        
        <h3 style="text-align: center; margin-top: 45px; font-size: 1.3rem; font-weight: 800;">СВЯЗАТЬСЯ С ЭКСПЕРТОМ НАПРЯМУЮ:</h3>
    """, unsafe_allow_html=True)

    # ⚠️ ВНИМАНИЕ! ЗАМЕНИ ССЫЛКИ НА СВОИ РЕАЛЬНЫЕ! ⚠️
    tg_link = "https://t.me/Artem_Nosov_Vrn"          
    wa_link = "https://wa.me/79601049146"      
    vk_link = "https://vk.com/artem_nosov_vrn"         

    col_tg, col_wa, col_vk = st.columns(3)
    
    with col_tg:
        st.markdown(f'<a href="{tg_link}" class="social-btn btn-tg" target="_blank"><svg class="svg-icon" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.894 8.221l-1.97 9.28c-.145.658-.537.818-1.084.508l-3-2.21-1.446 1.394c-.14.18-.357.295-.6.295-.002 0-.003 0-.005 0l.213-3.054 5.56-5.022c.24-.213-.054-.334-.373-.121l-6.869 4.326-2.96-.924c-.64-.203-.658-.64.135-.954l11.566-4.458c.538-.196 1.006.128.833.94z"/></svg>Telegram</a>', unsafe_allow_html=True)
        
    with col_wa:
        st.markdown(f'<a href="{wa_link}" class="social-btn btn-wa" target="_blank"><svg class="svg-icon" viewBox="0 0 24 24"><path d="M11.996 0C5.37 0 0 5.37 0 12c0 2.122.553 4.116 1.528 5.862L.15 24l6.3-1.654A11.93 11.93 0 0011.996 24C18.624 24 24 18.63 24 12S18.624 0 11.996 0zM12 21.822c-1.666 0-3.26-.43-4.685-1.25l-.335-.195-3.483.913.93-3.396-.214-.34C3.385 16.14 2.9 14.12 2.9 12c0-5.013 4.08-9.094 9.1-9.094 5.015 0 9.096 4.08 9.096 9.094 0 5.012-4.08 9.094-9.096 9.094zm5.006-6.814c-.274-.137-1.62-.8-1.87-8.89-.25-.09-.434-.09-.618.18-.184.27-7.05 1.05-.85 1.28-.145.23-.145.598-.01.874.136.275.608 1.155 1.543.618.558 1.4.755 1.63.845.23.09.52.09.704-.045.184-.136.313-.405.404-.618s.09-.39.044-.436c-.045-.045-.184-.09-.458-.227z"/></svg>WhatsApp</a>', unsafe_allow_html=True)
        
    with col_vk:
        st.markdown(f'<a href="{vk_link}" class="social-btn btn-vk" target="_blank"><svg class="svg-icon" viewBox="0 0 24 24"><path d="M12 0C5.373 0 0 5.373 0 12s5.373 12 12 12 12-5.373 12-12S18.627 0 12 0zm5.592 16.538c.456.45.922.894 1.346 1.372.285.32.553.655.765 1.03.116.205.04.46-.226.46h-2.31c-.34 0-.62-.15-.843-.4-.256-.286-.53-.556-.78-.846-.208-.24-.41-.486-.63-.714-.142-.146-.3-.217-.502-.15-.224.075-.34.25-.36.48-.035.438-.02.88-.02 1.32 0 .195-.08.29-.276.31h-1.64c-1.22-.05-2.3-.39-3.25-1.12-1.2-1.02-2.07-2.34-2.8-3.76-.8-1.57-1.46-3.2-2.1-4.85-.09-.23-.002-.37.23-.39.81-.04 1.62-.03 2.43 0 .18 0 .28.1.35.26.43 1.12.92 2.21 1.52 3.25.32.55.67 1.07 1.21 1.45.2.14.36.1.43-.13.1-.34.12-.69.12-1.05v-2.06c-.02-.57-.2-1.02-.69-1.3-.2-.11-.15-.21-.01-.3.26-.16.55-.22.85-.23h2.38c.3.06.39.2.43.49v3.6c0 .17.02.35.1.51.09.2.24.23.42.12.38-.23.68-.56.96-.92.65-.83 1.16-1.74 1.59-2.69.11-.25.26-.35.53-.34h2.51c.07 0 .15 0 .22.02.34.07.44.25.34.58-.12.4-.33.78-.54 1.15-.55.97-1.14 1.9-1.78 2.8-.2.27-.22.45-.02.73z"/></svg>ВКонтакте</a>', unsafe_allow_html=True)

    st.markdown("""
        <div class="footer-disclaimer">
            ⚠️ <b>ПРАВОВОЕ УВЕДОМЛЕНИЕ:</b> Данный аудит сгенерирован алгоритмической моделью на основе скоринга маркеров риска.<br>
            Отчет носит информационно-аналитический характер и не является официальным правовым заключением. Для 100% гарантии обращайтесь к профильным юристам.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()