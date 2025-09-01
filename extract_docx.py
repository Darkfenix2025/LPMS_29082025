from docx import Document

def extract_text_from_docx(file_path):
    doc = Document(file_path)
    full_text = []
    for para in doc.paragraphs:
        full_text.append(para.text)
    return '\n'.join(full_text)

if __name__ == "__main__":
    file_path = 'plantillas/mediacion/acuerdo_base.docx'
    text = extract_text_from_docx(file_path)
    print(text)