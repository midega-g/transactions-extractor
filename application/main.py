import io
import pandas as pd
import streamlit as st
from datetime import datetime
import pdfplumber
from util_funcs.pre_process import process_dataframe, filter_dataframe_by_date, compute_aggregates

st.set_page_config(layout="wide", page_title="PDF and Excel Data Processor")

st.title("PDF and Excel Data Processor")
st.markdown(
  """
  ### How to Use
  1. **Extract Data from PDF**: Upload the COOP Bank's transaction PDF file, extract transaction data, filter it by desired dates, and export it to an Excel file.
  2. **Validate and Upload Excel File**: Upload a validated Excel file, which should contain the same data as the extracted data, and compute aggregates.
  """
)

st.markdown("---")

# Section 1: PDF Processing
st.header("Extract Data from PDF")
st.markdown("**Upload a PDF file to extract transaction data, filter it by date, and export it to an Excel file.**")
uploaded_pdf = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_pdf is not None:
    password = st.text_input("Enter PDF password (if required)", type="password")

    try:
        with pdfplumber.open(uploaded_pdf, password=password) as pdf:
            st.success("PDF opened successfully! Processing...")

            extracted_data = pd.concat(
                [pd.DataFrame(page.extract_table()[1:], columns=page.extract_table()[0]) 
                 for page in pdf.pages if page.extract_table()],
                ignore_index=True
            )

        if not extracted_data.empty:
            processed_data = process_dataframe(extracted_data)
            max_posting_date = processed_data['Posting Date'].max().strftime('%Y-%m-%d')

            st.sidebar.header("Filter Configuration")
            start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1), min_value=datetime(2024, 1, 1))
            end_date = st.sidebar.date_input("End Date", datetime(2024, 2, 10), max_value=datetime.strptime(max_posting_date, '%Y-%m-%d'))

            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())

            filtered_data = filter_dataframe_by_date(processed_data, start_date, end_date)

            st.subheader("Filtered Data Preview")
            st.dataframe(filtered_data)

            st.sidebar.header("Export Options")
            excel_file_name = st.sidebar.text_input("Excel File Name", value="Filtered_Data.xlsx")

            if st.sidebar.button("Export as Excel"):
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    filtered_data.to_excel(writer, index=False)
                buffer.seek(0)
                st.download_button(
                    label="Download filtered data as Excel",
                    data=buffer,
                    file_name=excel_file_name,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )
        else:
            st.warning("No data found in the uploaded PDF. Please check the file.")
    
    except Exception as e:
        st.error(f"Failed to open the PDF. Please check if the password is correct. Error: {e}")

st.markdown("---")

# Section 2: Excel Aggregation
st.header("Generate Aggregates from Excel")
st.markdown("**Upload the validated Excel file to generate aggregates.**")
uploaded_excel = st.file_uploader("Upload your Excel file", type="xlsx")

if uploaded_excel is not None:
    try:
        # Load the uploaded Excel file into a DataFrame
        df_validated = pd.read_excel(uploaded_excel)
        st.markdown("#### Validated Excel Data Preview")
        st.dataframe(df_validated.head())

        # Generate the aggregate
        result = compute_aggregates(df_validated)

        st.markdown("#### Aggregated Data Preview")
        st.dataframe(result.head())

        # Export the aggregated data
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
            result.to_excel(writer, index=False, sheet_name="Aggregates")
        buffer.seek(0)

        st.download_button(
            label="Download aggregated data as Excel",
            data=buffer,
            file_name="Aggregated_Data.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    except Exception as e:
        st.error(f"Error processing the Excel file. Please check the format. Error: {e}")
