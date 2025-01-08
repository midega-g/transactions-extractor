import pdfplumber
import pandas as pd

def extract_name(narration):
    """
    Extracts and formats the name from the narration string.
    Emphasis laid on transactions that made by Mpesa paybill
    """
    if '62412' in narration.split('~')[0]:
        name_part = narration.split('~')[-1]
        name_part = ''.join(name_part.split())
    else:
        name_part = narration.split('~')[-1]
        name_part = ''.join(name_part.split())
        return name_part.title()
    return narration


def read_pdf_to_dataframe(pdf_path, password=None):
    """
    Reads a PDF file and extracts tables into a Pandas DataFrame, with optional password handling.

    Parameters:
    -----------
    pdf_path : str or file-like object
        The path to the PDF file or a file-like object (for Streamlit upload).
    password : str, optional
        The password required to open the PDF, if it is password-protected.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing extracted tables from the PDF.

    Raises:
    -------
    ValueError
        If no tables are found in the PDF or if incorrect password is provided.
    """
    combined_df = pd.DataFrame()

    try:
        with pdfplumber.open(pdf_path, password=password) as pdf:
            for page in pdf.pages:
                table = page.extract_table()
                if table:
                    df = pd.DataFrame(table[1:], columns=table[0])
                    if 'Narration' in df.columns:
                        # Filter out unwanted rows based on 'Narration'
                        df = df[~df['Narration'].str.contains(r'mobile wallet|maint fee|excise charges', case=False, na=False)]
                        # Apply name extraction on 'Narration'
                        df['Narration'] = df['Narration'].apply(extract_name)
                    combined_df = pd.concat([combined_df, df], ignore_index=True)
        if combined_df.empty:
            raise ValueError("No tables found in the PDF.")
        return combined_df

    except pdfplumber.PasswordError as e:
        raise ValueError("Incorrect password or unable to open the PDF.") from e


def process_dataframe(df):
    """
    Cleans and processes the extracted DataFrame by converting numeric and date columns.
    """
    numeric_cols = ['Debit Amount', 'Credit Amount', 'Running Balance']
    date_cols = ['Posting Date', 'Value Date']
    df[numeric_cols] = df[numeric_cols].replace({',': '', '': None}, regex=True).astype('float')
    df[date_cols] = df[date_cols].apply(pd.to_datetime, format='%d-%m-%Y', errors='coerce')
    return df


def filter_dataframe_by_date(df, start_date, end_date):
    """
    Filters the DataFrame based on a date range.
    """
    return df[(df['Posting Date'] >= start_date) & (df['Posting Date'] <= end_date)]


def compute_aggregates(df: pd.DataFrame) -> pd.DataFrame:
    """
    Computes the aggregate sum of the 'Credit Amount' column grouped by 'Narration',
    and renames the columns to 'Member' and 'Amount'.

    Parameters:
    -----------
    df : pd.DataFrame
        The input DataFrame containing at least the columns 'Narration' and 'Credit Amount'.

    Returns:
    --------
    pd.DataFrame
        A DataFrame containing the aggregate sum of 'Credit Amount' grouped by 'Narration',
        with columns renamed to 'Member' and 'Amount'.
    """
    # Ensure necessary columns are present
    if 'Narration' not in df.columns or 'Credit Amount' not in df.columns:
        raise ValueError("The input DataFrame must contain 'Narration' and 'Credit Amount' columns.")
    
    # Group by 'Narration' and compute the sum of 'Credit Amount'
    result = df.groupby(['Narration'])['Credit Amount'].sum().reset_index()
    
    # Rename columns to 'Member' and 'Amount'
    result.columns = ['Member', 'Amount']
    
    return result

