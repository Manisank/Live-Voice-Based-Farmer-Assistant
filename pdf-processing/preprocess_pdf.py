import pdfplumber
import sqlite3
from nltk.tokenize import sent_tokenize
import nltk

# Download required NLTK resources
nltk.download('punkt')

# Create SQLite Database
def create_database(db_name="preprocessed_pdf.db"):
    conn = sqlite3.connect(db_name)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS pdf_text (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            page_number INTEGER,
            sentence TEXT
        )
    """)
    conn.commit()
    return conn, cursor

# Preprocess a range of pages and insert into the database
def preprocess_pdf_chunk(pdf_path, db_name="preprocessed_pdf.db", start_page=0, end_page=100):
    conn, cursor = create_database(db_name)
    with pdfplumber.open(pdf_path) as pdf:
        total_pages = len(pdf.pages)
        if start_page >= total_pages:
            print(f"Start page ({start_page}) exceeds total pages ({total_pages}). Skipping.")
            return
        end_page = min(end_page, total_pages)  # Ensure end_page does not exceed total_pages
        print(f"Processing pages {start_page + 1} to {end_page}...")

        for page_number in range(start_page, end_page):
            page = pdf.pages[page_number]
            page_text = page.extract_text()
            if page_text:
                sentences = sent_tokenize(page_text)
                for sentence in sentences:
                    cursor.execute("INSERT INTO pdf_text (page_number, sentence) VALUES (?, ?)",
                                   (page_number + 1, sentence))
            else:
                cursor.execute("INSERT INTO pdf_text (page_number, sentence) VALUES (?, ?)",
                               (page_number + 1, "[No text found on this page]"))
        conn.commit()
        print(f"Committed pages {start_page + 1} to {end_page} to the database.")
    conn.close()

# Process the PDF in smaller chunks
pdf_path = "/content/Encyclopedia_of_agriculture_and_food_systems.pdf"  # Replace with your file path
db_name = "/content/preprocessed_pdf.db"

chunk_size = 100  # Number of pages to process at a time
with pdfplumber.open(pdf_path) as pdf:
    total_pages = len(pdf.pages)
    for start_page in range(0, total_pages, chunk_size):
        end_page = start_page + chunk_size
        preprocess_pdf_chunk(pdf_path, db_name, start_page, end_page)

# Download the SQLite Database
from google.colab import files
files.download(db_name)
