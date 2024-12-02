import easyocr

# Initialize the EasyOCR reader
reader = easyocr.Reader(['en'])

# Load the image
image_path = "test.png"

# Perform OCR on the image
results = reader.readtext(image_path)

# Open a file to save the results
output_file = "ocr_results.txt"

with open(output_file, "w") as file:
    # Write results to the file
    for bbox, text, prob in results:
        file.write(f"Text: {text}\n")
        file.write(f"Confidence: {prob:.2f}\n")
        file.write("-" * 40 + "\n")
