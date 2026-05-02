from fpdf import FPDF
import base64

def generate_pdf_report(prediction, reliability, condition, rh, trend, peak):
    pdf = FPDF()
    pdf.add_page()
    
    # Header
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(200, 10, "Aviation Weather Stability Report (SIM)", ln=True, align='C')
    pdf.set_font("Arial", '', 10)
    pdf.cell(200, 10, "Bandaranaike International Airport (BIA) - Forecast System", ln=True, align='C')
    pdf.line(10, 30, 200, 30)
    
    # Input Data Section
    pdf.ln(10)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "1. Input Parameters (METAR Obs):", ln=True)
    pdf.set_font("Arial", '', 11)
    pdf.cell(0, 8, f"- Relative Humidity: {rh}%", ln=True)
    pdf.cell(0, 8, f"- Pressure Trend (QNH Diff): {trend} hPa", ln=True)
    pdf.cell(0, 8, f"- Humidity Peak Detected: {'Yes' if peak == 1 else 'No'}", ln=True)
    
    # Forecast Results
    pdf.ln(5)
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, "2. Forecast Results (T+3h Prediction):", ln=True)
    pdf.set_font("Arial", 'B', 14)
    pdf.cell(0, 10, f"Predicted QNH: {prediction:.2f} hPa", ln=True)
    pdf.cell(0, 10, f"Stability Status: {condition}", ln=True)
    pdf.cell(0, 10, f"Confidence Score: {reliability}%", ln=True)
    
    # Official Disclaimer
    pdf.ln(10)
    pdf.set_font("Arial", 'I', 10)
    pdf.multi_cell(0, 8, "Disclaimer: This is an AI-generated predictive report based on historical SIM patterns. Pilots are advised to cross-check with real-time ATIS and Tower observations.")
    
    # Footer
    pdf.ln(20)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, "Researcher: P.K.V.K. Jayathilaka", ln=True)
    
    return pdf.output(dest='S').encode('latin-1')