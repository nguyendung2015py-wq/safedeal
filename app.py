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

        .stTabs [data-baseweb="tab-list"] { gap: 8px; background-color: #f8f9fa; padding: 5px; border-radius: 12px; border: 1px solid #e9ecef; flex-wrap: wrap; }
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
        
        /* ПОЛНОСТЬЮ НОВЫЙ БЛОК СОЦИАЛЬНЫХ КНОПОК С КАРТИНКАМИ (PNG) */
        .social-container {
            display: flex; justify-content: center; gap: 15px; margin-top: 30px; flex-wrap: wrap;
        }
        .social-btn-new {
            display: flex; align-items: center; justify-content: center;
            padding: 14px 20px; border-radius: 10px; color: white !important;
            text-decoration: none !important; font-weight: 700; font-size: 16px;
            min-width: 250px; transition: 0.2s; box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        }
        .social-btn-new img {
            width: 28px !important; height: 28px !important; margin-right: 12px; flex-shrink: 0;
        }
        .btn-tg { background-color: #2AABEE; }
        .btn-wa { background-color: #25D366; }
        .btn-vk { background-color: #0077FF; }
        .social-btn-new:hover { transform: translateY(-3px); box-shadow: 0 6px 15px rgba(0,0,0,0.1); opacity: 0.95; }
        
        .footer-disclaimer { text-align: center; font-size: 0.75rem; color: #9ca3af; margin-top: 3rem; border-top: 1px solid #f3f4f6; padding-top: 1.5rem; line-height: 1.5; }

        @media (max-width: 768px) {
            .hero-title { font-size: 1.6rem; }
            .hero-subtitle { font-size: 0.95rem; }
            .logo-img { width: 110px; height: 110px; }
            .decision-banner { flex-direction: column; align-items: flex-start; gap: 0.8rem; padding: 1rem; }
            .decision-score { font-size: 2.2rem; }
            .risk-table th:nth-child(1), .risk-table th:nth-child(2), .risk-table th:nth-child(3) { width: auto; }
            .social-btn-new { width: 100%; }
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
    # --- БАЗА РИСКОВ РАСШИРЕНА ПО ТВОЕМУ ЗАПРОСУ ---
    risks = [
        {"cat": "object", "what": "Объект в залоге (ипотека банка)", "kw": ["в ипотеке", "залог", "обременен", "под залогом"], "law": "ФЗ №102-ФЗ ст. 37. Имущество может быть отчуждено только с письменного согласия залогодержателя.", "fix": "Гашение долга через СБР или официальный перевод долга.", "w": 15.0},
        {"cat": "object", "what": "Арест или запрет на рег. действия", "kw": ["арест", "запрет", "пристав"], "law": "ФЗ №218-ФЗ ст. 56. Регистрация прав приостанавливается при наложении ареста.", "fix": "Погашение долгов до сделки, снятие ареста.", "w": 30.0},
        {"cat": "object", "what": "Маткапитал и детские доли", "kw": ["маткапитал", "детск", "опек"], "law": "ФЗ №256-ФЗ ст. 10. Обязательное выделение долей. Сделка без них ничтожна.", "fix": "Требовать выделения долей до сделки и приказ опеки.", "w": 20.0},
        {"cat": "object", "what": "Свежее наследство", "kw": ["наследств", "завещан", "умер"], "law": "ГК РФ ст. 1155. Суд может восстановить срок для других наследников.", "fix": "Нотариальное обязательство о фин. урегулировании претензий.", "w": 20.0},
        {"cat": "object", "what": "Приватизация (отказники)", "kw": ["приватиз", "отказ"], "law": "ФЗ №1541-1. Отказавшиеся от приватизации имеют право пожизненного проживания.", "fix": "Проверка архивной выписки и выписка лиц до сделки.", "w": 25.0},
        {"cat": "seller", "what": "Банкротство, долги и суды", "kw": ["банкрот", "пристав", "долг", "фссп"], "law": "ФЗ № 127-ФЗ ст. 61.2. Сделки должника до банкротства могут быть оспорены.", "fix": "Аудит по базам ФССП, ЕФРСБ, КАД.", "w": 25.0},
        {"cat": "seller", "what": "Судебные споры", "kw": ["суд ", "судебн", "спор"], "law": "ГПК РФ ст. 140. Риск наложения обеспечительных мер во время спора.", "fix": "Проверка судов по месту нахождения объекта и прописки.", "w": 25.0},
        {"cat": "seller", "what": "Справки ПНД/НД", "kw": ["пенсионер", "психиатр", "пнд"], "law": "ГК РФ ст. 177. Сделка лицом, не способным понимать свои действия, оспорима.", "fix": "Требовать личного получения справок, врач на сделке.", "w": 20.0},
        {"cat": "seller", "what": "Продажа по доверенности", "kw": ["доверенност", "представител"], "law": "ГК РФ ст. 188. Доверенность прекращается при ее отмене или смерти.", "fix": "Проверка доверенности по ФНП, видеозвонок.", "w": 20.0},
        {"cat": "seller", "what": "Согласие супруга", "kw": ["брак", "муж", "жена", "совмест"], "law": "СК РФ ст. 35. Для распоряжения общим имуществом нужно нотариальное согласие.", "fix": "Нотариальное согласие или брачный договор.", "w": 20.0},
        {"cat": "trigger", "what": "Занижение цены в договоре", "kw": ["занижен", "конверт", "минимальная"], "law": "ГК РФ ст. 170. Притворная сделка ничтожна. Риск возврата только суммы по ДКП.", "fix": "Указывать в ДКП полную реальную стоимость.", "w": 30.0},
    ]

    for cfg in risks:
        if _detect(text, cfg["kw"]):
            items.append(RiskItem(cfg["what"], cfg["law"], cfg["fix"], cfg["w"], cfg["cat"]))

    b_tot = sum(i.weight for i in items)
    critical_triggers = ["в конверте", "занижен", "банкрот", "наследств", "доли не выделены", "опек", "арест", "запрет", "отказ"]
    if _detect(text, critical_triggers): b_tot = max(b_tot, 85.0)

    if not items:
        b_tot = 40.0
        items.append(RiskItem("Недостаточно данных", "ГК РФ ст. 421. Явных стоп-маркеров нет, ответственность на покупателе.", "Проведите полный сбор документов.", 40.0, "object"))

    final_score = max(0, min(int(round(b_tot)), 100))
    return AnalysisResult(final_score, items)

def set_template_1(): st.session_state.my_text = "Продавец пенсионер 75 лет. Продает по доверенности. Свежее наследство."
def set_template_2(): st.session_state.my_text = "Квартира в ипотеке. Использовался маткапитал. Хотят занижение стоимости."
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

    tab1, tab2, tab3, tab4, tab5 = st.tabs(["🛡️ АУДИТ РИСКОВ", "💰 НАЛОГИ", "🏦 ИПОТЕКА vs АРЕНДА", "📉 ОЦЕНКА ПРОДАВЦА", "💼 СКРЫТЫЕ РАСХОДЫ"])

    with tab1:
        st.markdown("<b>⚡ Быстрые ситуации:</b>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)
        col1.button("👴 Доверенность", on_click=set_template_1, use_container_width=True)
        col2.button("👶 Маткапитал", on_click=set_template_2, use_container_width=True)
        col3.button("⚖️ Долги ФССП", on_click=set_template_3, use_container_width=True)

        text = st.text_area("Текст для экспертизы", key="my_text", height=140, placeholder="Опишите ситуацию своими словами...")
        
        if st.button("ЗАПУСТИТЬ ГЛУБОКУЮ ЭКСПЕРТИЗУ", key="run_audit"):
            if not text.strip(): 
                st.warning("Введите данные для анализа.")
            else:
                with st.status("🔍 Инициализация алгоритма...", expanded=True) as status:
                    time.sleep(0.5)
                    status.update(label="Анализ завершен!", state="complete", expanded=False)

                res = analyze_safedeal(text)
                
                if res.total_risk >= 70:
                    b_cls, z_lbl, sub_txt = "danger", "КРАСНАЯ ЗОНА", "Запрещено выходить на сделку без профильного юриста."
                elif res.total_risk >= 40:
                    b_cls, z_lbl, sub_txt = "warning", "ЖЕЛТАЯ ЗОНА", "Требуется сбор дополнительных документов."
                else:
                    b_cls, z_lbl, sub_txt = "safe", "ЗЕЛЕНАЯ ЗОНА", "Базовая проверка обязательна."
                
                report_id = random.randint(10000, 99999)
                current_date = datetime.now().strftime('%d.%m.%Y %H:%M')
                
                st.markdown(f"""
                <div class="decision-banner {b_cls}">
                    <div style="text-align: center; min-width: 120px;">
                        <div class="decision-score">{res.total_risk}%</div>
                    </div>
                    <div style="width: 100%;">
                        <div class="report-header">Акт проверки №{report_id}</div>
                        <div class="decision-text-main">{z_lbl}</div>
                        <div class="decision-text-sub">{sub_txt}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                table_html = "<div class='table-wrapper'><table class='risk-table'><thead><tr><th>УГРОЗА</th><th>ЗАКОН</th><th>ЗАЩИТА</th></tr></thead><tbody>"
                for i in res.items:
                    table_html += f"<tr><td><b>{i.what}</b></td><td>{i.law}</td><td>{i.fix}</td></tr>"
                table_html += "</tbody></table></div>"
                st.markdown(table_html, unsafe_allow_html=True)
                
                report_text = f"АКТ ПРОВЕРКИ №{report_id}\nИНДЕКС РИСКА: {res.total_risk}%\nРЕШЕНИЕ: {z_lbl}\n\nВЫЯВЛЕННЫЕ УГРОЗЫ:\n"
                for i in res.items: report_text += f"- {i.what}\n  Закон: {i.law}\n  Решение: {i.fix}\n\n"
                st.download_button("📥 СКАЧАТЬ АКТ ПРОВЕРКИ (TXT)", data=report_text, file_name=f"SafeDeal_{report_id}.txt", mime="text/plain")

    with tab2:
        st.markdown("### 🧮 Калькулятор НДФЛ с продажи (2025)")
        holding_period = st.radio("Срок владения:", ["Срок НЕ прошел (платить надо)", "Прошел минимальный срок (налог 0 ₽)"])
        
        if "Прошел" in holding_period:
            st.success("🎉 **Налог: 0 ₽.** Вы полностью освобождены от уплаты налогов и декларации.")
        else:
            sell_price = st.number_input("Цена продажи (₽)", min_value=0, step=100000, value=6000000)
            cadastral = st.number_input("Кадастровая стоимость (₽)", min_value=0, step=100000, value=5000000)
            deduction_type = st.radio("Вычет:", ["Расходы на покупку", "Стандартный вычет 1 млн ₽"])
            buy_price = st.number_input("За сколько покупали (₽)?", min_value=0, step=100000, value=3000000) if "Расходы" in deduction_type else 1000000
                
            if st.button("РАССЧИТАТЬ НАЛОГ", key="run_tax_prog"):
                tax_base = max(sell_price, cadastral * 0.7)
                total_tax, tax_13, tax_15 = calculate_progressive_tax(max(0, tax_base - buy_price))
                if total_tax > 0:
                    st.error(f"### Налог к уплате: {total_tax:,.0f} ₽".replace(',', ' '))
                    st.markdown(f"*Из них по ставке 13%: {tax_13:,.0f} ₽, по ставке 15%: {tax_15:,.0f} ₽*".replace(',', ' '))
                else:
                    st.success("✅ Налог к уплате: 0 ₽")

    with tab3:
        st.markdown("### 🏦 Ипотека vs Аренда")
        rent_price = st.number_input("Сколько платите за аренду? (₽/мес)", min_value=0, step=5000, value=40000)
        prop_price_m = st.number_input("Стоимость желаемой квартиры (₽)", min_value=0, step=100000, value=7000000)
        down_payment_m = st.number_input("Ваш взнос (₽)", min_value=0, step=100000, value=2000000)
        mortgage_rate_m = st.number_input("Ставка банка (%)", min_value=0.1, step=0.1, value=18.5)
        
        if st.button("СРАВНИТЬ ИПОТЕКУ И АРЕНДУ"):
            payment, overpay, total = calculate_mortgage(prop_price_m, down_payment_m, mortgage_rate_m, 25)
            rent_5_years = rent_price * 12 * 5
            st.error(f"🔥 За 5 лет вы подарите арендодателю: **{rent_5_years:,.0f} ₽**".replace(',', ' '))
            st.markdown(f"**Ваш платеж по ипотеке составит:** {payment:,.0f} ₽/мес".replace(',', ' '))

    with tab4:
        st.markdown("### 📉 Калькулятор жадности (Для продавцов)")
        wish_price = st.number_input("За сколько хотите продать? (₽)", min_value=0, step=100000, value=10000000)
        real_price = st.number_input("Средняя цена похожих квартир (₽)", min_value=0, step=100000, value=9000000)
        
        if st.button("УЗНАТЬ ПРАВДУ"):
            if wish_price <= real_price:
                st.success("✅ Цена в рынке. Объект уйдет быстро при правильной упаковке.")
            else:
                diff_percent = ((wish_price - real_price) / real_price) * 100
                lost_profit = wish_price * 0.18
                st.error(f"⚠️ Цена завышена на **{diff_percent:.1f}%**. Квартира зависнет в продаже.")
                st.markdown(f"За год простоя недополученная прибыль по банковскому вкладу составит **{lost_profit:,.0f} ₽**. Вы теряете деньги.".replace(',', ' '))

    with tab5:
        st.markdown("### 💼 Скрытые расходы покупателя")
        st.info("Узнайте, сколько ДЕЙСТВИТЕЛЬНО придется заплатить банку и государству поверх первоначального взноса.")
        
        obj_price_c = st.number_input("Стоимость покупаемой квартиры (₽)", min_value=1000000, step=100000, value=5000000, key="hidden_obj")
        down_payment_c = st.number_input("Ваш первоначальный взнос (₽)", min_value=0, step=100000, value=1000000, key="hidden_dp")
        
        is_mortgage = st.checkbox("Покупаю в ипотеку (нужна страховка и оценка)", value=True)
        is_sbr = st.checkbox("Платные услуги банка (СБР + Электронная регистрация)", value=True)
        is_shares = st.checkbox("Есть несовершеннолетние собственники или доли (нужен нотариус)?", value=False)
        
        if st.button("РАССЧИТАТЬ ПОБОРЫ"):
            total_hidden = 0
            details_text = ""
            
            if is_mortgage:
                loan_amount = max(0, obj_price_c - down_payment_c)
                # Страховка (жизнь+объект) ~0.8% от кредита + 10%
                insurance = (loan_amount * 1.1) * 0.008
                appraisal = 6000
                total_hidden += insurance + appraisal
                details_text += f"- Обязательная страховка (жизнь + объект): ~ {insurance:,.0f} ₽\n- Оценка недвижимости для банка: ~ {appraisal:,.0f} ₽\n"
            
            if is_sbr:
                sbr_er = 15000
                total_hidden += sbr_er
                details_text += f"- Безопасные расчеты (СБР) и Электронная регистрация: ~ {sbr_er:,.0f} ₽\n"
                
            if is_shares:
                notary = 25000
                total_hidden += notary
                details_text += f"- Услуги нотариуса (обязательно при долях): ~ {notary:,.0f} ₽\n"
                
            # Актуальная Госпошлина 2025: 4000 руб до 20 млн, свыше - 0.02%
            gosposhlina = 4000 if obj_price_c <= 20000000 else obj_price_c * 0.0002
            if gosposhlina > 500000: gosposhlina = 500000
            
            total_hidden += gosposhlina
            details_text += f"- Госпошлина за регистрацию права (тарифы 2025 г.): {gosposhlina:,.0f} ₽"
            
            st.error(f"### 💸 Дополнительные расходы составят: ~ {total_hidden:,.0f} ₽".replace(',', ' '))
            st.markdown(details_text.replace(',', ' '))
            
            st.markdown("""
            <div style="background-color: #f8fffc; padding: 15px; border-left: 4px solid #008a5e; border-radius: 5px; margin-top: 15px;">
            <b>Лайфхак от эксперта:</b> Банки часто навязывают свои страховки в 2-3 раза дороже рынка и добавляют платные "юридические проверки" за 20-30 тысяч, которые ничего не гарантируют. Я помогаю своим клиентам <b>сэкономить до 40%</b> на скрытых платежах легально.
            </div>
            """, unsafe_allow_html=True)
            st.markdown("<br><a href='https://t.me/nosov_s_blog' class='custom-btn' target='_blank'>👉 Узнать, как законно сэкономить на поборах банков</a>", unsafe_allow_html=True)

    st.markdown("""
        <div class="hook-card">
            <div class="hook-title">Без риелтора: как люди теряют задатки на ровном месте</div>
            <div style="font-size: 0.95rem; line-height: 1.5; color: #374151;">
            Типичная ситуация: покупатели сами нашли квартиру, перевели задаток на карту без нормальных бумаг... А потом сделка разваливается. В блоге разобрал реальные случаи.
            </div><br>
            <a href="https://t.me/nosov_s_blog/413" target="_blank" style="color: #008a5e; font-weight: bold; text-decoration: none; font-size: 1.05rem;">👉 Читать пост о рисках</a>
        </div>
        
        <h3 style="text-align: center; margin-top: 45px; font-size: 1.3rem; font-weight: 800;">СВЯЗАТЬСЯ СО МНОЙ НАПРЯМУЮ:</h3>
    """, unsafe_allow_html=True)

    # ⚠️ ССЫЛКИ ДЛЯ ЗАМЕНЫ ⚠️
    tg_link = "https://t.me/Artem_Nosov_Vrn"          
    wa_link = "https://wa.me/79601049146"      
    vk_link = "https://vk.com/artem_nosov_vrn"         

    # Ссылки на четкие PNG иконки
    icon_tg = "https://img.icons8.com/color/96/telegram-app.png"
    icon_wa = "https://img.icons8.com/color/96/whatsapp--v1.png"
    icon_vk = "https://img.icons8.com/color/96/vk-com.png"

    # НОВЫЙ БЛОК СОЦИАЛЬНЫХ КНОПОК КАК НА 1-м СКРИНШОТЕ
    st.markdown(f"""
        <div class="social-container">
            <a href="{tg_link}" class="social-btn-new btn-tg" target="_blank">
                <img src="{icon_tg}"> Telegram
            </a>
            <a href="{wa_link}" class="social-btn-new btn-wa" target="_blank">
                <img src="{icon_wa}"> WhatsApp
            </a>
            <a href="{vk_link}" class="social-btn-new btn-vk" target="_blank">
                <img src="{icon_vk}"> ВКонтакте
            </a>
        </div>
    """, unsafe_allow_html=True)

    st.markdown("""
        <div class="footer-disclaimer">
            ⚠️ <b>ПРАВОВОЕ УВЕДОМЛЕНИЕ:</b> Данный аудит сгенерирован алгоритмической моделью на основе скоринга маркеров риска.<br>
            Отчет носит информационно-аналитический характер. Для 100% гарантии обращайтесь к профильным юристам.
        </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()