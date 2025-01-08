import io
import pandas as pd
import streamlit as st
from datetime import datetime
import pdfplumber
from util_funcs.pre_process import process_dataframe, filter_dataframe_by_date

st.set_page_config(layout="wide", page_title="PDF to Excel Tool")

st.title("PDF to Excel Data Processor")
st.markdown("Upload a PDF file to extract transaction data, filter it by date, and export it to an Excel file.")

uploaded_file = st.file_uploader("Upload your PDF file", type="pdf")

if uploaded_file is not None:
    # Password input for protected PDFs
    password = st.text_input("Enter PDF password (if required)", type="password")

    try:
        # Try to open the PDF with the provided password (if any)
        with pdfplumber.open(uploaded_file, password=password) as pdf:
            st.success("PDF opened successfully! Processing...")
            
            # Extract tables from the PDF
            extracted_data = pd.concat(
                [pd.DataFrame(page.extract_table()[1:], columns=page.extract_table()[0]) 
                 for page in pdf.pages if page.extract_table()],
                ignore_index=True
            )

        # Process and Display Data
        if not extracted_data.empty:
            processed_data = process_dataframe(extracted_data)
            max_posting_date = processed_data['Posting Date'].max().strftime('%Y-%m-%d')

            # Date Range Filter
            st.sidebar.header("Filter Configuration")
            start_date = st.sidebar.date_input("Start Date", datetime(2024, 1, 1), min_value=datetime(2024, 1, 1))
            end_date = st.sidebar.date_input("End Date", datetime(2024, 2, 10), max_value=datetime.strptime(max_posting_date, '%Y-%m-%d'))

            # Convert date_input values to datetime
            start_date = datetime.combine(start_date, datetime.min.time())
            end_date = datetime.combine(end_date, datetime.min.time())

            filtered_data = filter_dataframe_by_date(processed_data, start_date, end_date)

            # Display Data
            st.subheader("Filtered Data Preview")
            st.dataframe(filtered_data)

            # Excel Export
            st.sidebar.header("Export Options")
            excel_file_name = st.sidebar.text_input("Excel File Name", value="Filtered_Data.xlsx")
            
            if st.sidebar.button("Export as Excel"):
                # An in-memory buffer
                buffer = io.BytesIO()
                
                # Write the filtered data to the buffer as an Excel file
                with pd.ExcelWriter(buffer, engine='xlsxwriter') as writer:
                    filtered_data.to_excel(writer, index=False)
                
                buffer.seek(0)  # Reset the buffer's position to the beginning
                
                # Download button with the buffer as the file content
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
