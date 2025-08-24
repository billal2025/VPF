import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# -------------------------
# Salary slabs (fixed tax values for 2026)
# -------------------------
salary_slabs = {
    600000: 0,
    1200000: 6000,
    1800000: 72000,
    2400000: 162000,
    2700000: 231000,
    3000000: 300000,
    3600000: 466000,
    4200000: 651000,
    4800000: 861000,
    5400000: 1071000,
    6000000: 1281000,
    6600000: 1491000,
    7200000: 1701000,
    9600000: 2541000,
    12000000: 3692850,
    18000000: 5981850,
    24000000: 8270850,
    30000000: 10559850,
    33600000: 11933250,
    36000000: 12848850,
}

# -------------------------
# Business slabs (progressive)
# -------------------------
business_slabs = [
    (600000, 0, 0),
    (800000, 0, 0.05),
    (1200000, 10000, 0.125),
    (2400000, 60000, 0.175),
    (3000000, 270000, 0.225),
    (4000000, 405000, 0.275),
    (6000000, 680000, 0.325),
    (float("inf"), 1330000, 0.35),
]


def calculate_business_tax(annual_income):
    """Progressive tax calculation for business income."""
    if annual_income <= 600000:
        return 0
    for i, (limit, base_tax, rate) in enumerate(business_slabs):
        if annual_income <= limit:
            lower_bound = business_slabs[i - 1][0] if i > 0 else 0
            return base_tax + (annual_income - lower_bound) * rate
    return 0


def get_salaried_tax(annual_income):
    """Find nearest salaried tax slab based on income."""
    sorted_slabs = sorted(salary_slabs.keys())
    for slab in sorted_slabs:
        if annual_income <= slab:
            return salary_slabs[slab]
    return salary_slabs[sorted_slabs[-1]]


def pension_tax_calculator(income_type, annual_income, pension_invest=None):
    if income_type == "salaried":
        tax_2026 = get_salaried_tax(annual_income)
    elif income_type == "business":
        tax_2026 = calculate_business_tax(annual_income)
    else:
        return None

    if annual_income == 0:
        return None

    avg_tax_rate = tax_2026 / annual_income if tax_2026 > 0 else 0
    max_invest = 0.20 * annual_income

    if pension_invest is None or pension_invest == 0:
        invest = max_invest
    else:
        invest = min(pension_invest, max_invest)

    rebate = invest * avg_tax_rate
    new_tax = tax_2026 - rebate

    return {
        "Income Type": income_type.title(),
        "Annual Income": round(annual_income, 0),
        "Monthly Income": round(annual_income / 12, 0),
        "Tax Without Pension": round(tax_2026, 0),
        "Max Pension Investment (20%)": round(max_invest, 0),
        "Your Pension Investment": round(invest, 0),
        "Tax Saving": round(rebate, 0),
        "New Tax Payable": round(new_tax, 0),
        "Monthly Saving": round(rebate / 12, 0),
    }


# -------------------------
# File Export Helpers
# -------------------------
def export_excel(result_dict):
    df = pd.DataFrame(list(result_dict.items()), columns=["Field", "Value"])
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Tax Report")
    return output.getvalue()


def export_pdf(result_dict):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica", 12)
    y = 750
    c.drawString(200, 780, "📊 Pension Fund Tax Report (Pakistan 2026)")
    for k, v in result_dict.items():
        # If v is a number, format with commas
        if isinstance(v, (int, float)):
            c.drawString(50, y, f"{k}: {v:,}")
        else:
            c.drawString(50, y, f"{k}: {v}")
        y -= 20
    c.save()
    buffer.seek(0)
    return buffer.getvalue()


# -------------------------
# Streamlit UI
# -------------------------
st.set_page_config(page_title="Pension Fund Tax Calculator (Pakistan 2026)", page_icon="📊")
st.title("📊 Pension Fund Tax Benefit Calculator (Pakistan 2026)")

income_type = st.radio("Choose income type:", ["salaried", "business"])
income_input_type = st.radio("Enter income type:", ["Monthly", "Annual"])

if income_input_type == "Monthly":
    monthly_income = st.number_input("Enter your monthly income (PKR):", min_value=10000, step=1000)
    annual_income = monthly_income * 12
else:
    annual_income = st.number_input("Enter your annual income (PKR):", min_value=100000, step=50000)
    monthly_income = annual_income / 12

st.markdown("---")

max_invest = 0.20 * annual_income
st.info(f"👉 Max pension investment allowed (20% of annual income) = {max_invest:,.0f}")

pension_invest = st.number_input("Enter your pension investment amount (leave 0 for max allowed):", min_value=0.0, step=1000.0)

if st.button("Calculate Tax"):
    result = pension_tax_calculator(income_type, annual_income, pension_invest)

    if result:
        st.success("✅ Calculation Complete")

        # Show metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Annual Income", f"{result['Annual Income']:,.0f}")
        col2.metric("Tax Without Pension", f"{result['Tax Without Pension']:,.0f}")
        col3.metric("New Tax Payable", f"{result['New Tax Payable']:,.0f}")

        col4, col5, col6 = st.columns(3)
        col4.metric("Max Pension Investment", f"{result['Max Pension Investment (20%)']:,.0f}")
        col5.metric("Your Pension Investment", f"{result['Your Pension Investment']:,.0f}")
        col6.metric("Tax Saving", f"{result['Tax Saving']:,.0f}")

        st.metric("💰 Monthly Saving", f"{result['Monthly Saving']:,.0f}")

        with st.expander("📑 Detailed Breakdown"):
            st.json(result)

        # 📥 Download buttons
        st.markdown("### 📥 Download Report")
        excel_data = export_excel(result)
        pdf_data = export_pdf(result)

        st.download_button("⬇️ Download Excel Report", data=excel_data, file_name="tax_report.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        st.download_button("⬇️ Download PDF Report", data=pdf_data, file_name="tax_report.pdf", mime="application/pdf")

    else:
        st.error("❌ Invalid input. Please check your entries.")
