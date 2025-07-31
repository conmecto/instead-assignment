import pdfplumber
import json

output = {}

with pdfplumber.open("f1040.pdf") as pdf:
    for i, page in enumerate(pdf.pages):
        # Extract words, including font size
        words = page.extract_words(extra_attrs=['size'])
        output[f"page_{i + 1}"] = words

# Save to JSON file
with open("f1040_words.json", "w", encoding="utf-8") as f:
    json.dump(output, f, indent=2)