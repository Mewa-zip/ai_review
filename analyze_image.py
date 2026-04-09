import fitz  # PyMuPDF
import ollama
import io
from PIL import Image


def analyze_visuals(pdf_path):
    doc = fitz.open(pdf_path)
    visual_reports = []

    print(f"--- Analiza wizualna pliku: {pdf_path} ---")

    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)

        if not image_list:
            continue

        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]

            prompt = """
            Analyze this image from a scientific paper. 
            Check:
            1. Correctness: Are the axes labeled? Is the scale logical?
            2. Sense: Does it convey clear information or is it cluttered?
            3. Readability: Is the font size sufficient? Are colors distinguishable?
            Provide a short, critical assessment.
            """

            response = ollama.chat(
                model='llama3.2-vision',
                messages=[{
                    'role': 'user',
                    'content': prompt,
                    'images': [image_bytes]
                }]
            )

            report = f"Page {page_index + 1}, Image {img_index + 1}: {response['message']['content']}"
            visual_reports.append(report)

    return "\n".join(visual_reports) if visual_reports else "No images found to analyze."