import os
import json
# Need a library to read PDF files, e.g., PyPDF2 or pdfminer.six
# You might need to install it: pip install PyPDF2
# import PyPDF2

# Define paths
PAPERS_DIR = '/Users/julius/julProg/paper_writing_helper/backend_algo/papers'
QUESTIONS_FILE = '/Users/julius/julProg/paper_writing_helper/datas/questions_q_a_r.json'
OUTPUT_FILE = '/Users/julius/julProg/paper_writing_helper/datas/papers.json'

def load_topics(questions_file):
    """Loads classification topics from the questions JSON file."""
    with open(questions_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    topics = set()
    for item in data:
        if 'Q' in item:
            for section, keywords in item['Q']:
                topics.add(section)
                for keyword in keywords:
                    topics.add(keyword)
    return list(topics)

def extract_text_from_pdf(pdf_path):
    """Extracts text from a PDF file (requires PyPDF2 or similar)."""
    # This is a placeholder. Actual implementation depends on the library.
    # Example with PyPDF2:
    # try:
    #     with open(pdf_path, 'rb') as f:
    #         reader = PyPDF2.PdfReader(f)
    #         text = ''
    #         for page_num in range(len(reader.pages)):
    #             text += reader.pages[page_num].extract_text()
    #     return text
    # except Exception as e:
    #     print(f"Error reading {pdf_path}: {e}")
    #     return ""
    print(f"Placeholder: Reading {pdf_path}")
    # Return dummy text for now
    return f"This is the content of {os.path.basename(pdf_path)}. It is about Information Security and Network Security."

def classify_paper(text, topics):
    """Classifies paper based on text content and predefined topics."""
    found_topics = []
    # Simple keyword matching for demonstration
    for topic in topics:
        if topic.lower() in text.lower():
            found_topics.append(topic)
    return found_topics

def main():
    topics = load_topics(QUESTIONS_FILE)
    papers_data = []
    paper_id = 1

    if not os.path.exists(PAPERS_DIR):
        print(f"Error: Papers directory not found at {PAPERS_DIR}")
        return

    for filename in os.listdir(PAPERS_DIR):
        if filename.endswith('.pdf'):
            pdf_path = os.path.join(PAPERS_DIR, filename)
            relative_path = os.path.join('papers', filename) # Assuming papers dir is relative to some root
            
            # Extract text (using placeholder for now)
            text = extract_text_from_pdf(pdf_path)
            
            # Extract title (placeholder - needs proper PDF metadata extraction)
            title = filename.replace('.pdf', '') # Using filename as title for now
            
            # Classify
            paper_topics = classify_paper(text, topics)
            
            papers_data.append({
                "id": paper_id,
                "path": relative_path,
                "title": title,
                "topics": paper_topics # Added topics field
            })
            paper_id += 1

    # Write to output JSON file
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(papers_data, f, ensure_ascii=False, indent=4)

    print(f"Processed {len(papers_data)} papers and saved data to {OUTPUT_FILE}")

if __name__ == "__main__":
    main()