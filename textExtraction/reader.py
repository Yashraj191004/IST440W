import fitz
import re
import pandas as pd

def text_extraction(pdf_path):
    oil_pattern = r"\b\d{1,2}W-\d{2}\b"
    negative_words = ["not", "avoid", "don't", "except", "never", "other than"]
    results = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")
            sentences = text.split('.')
            for sentence in sentences:
                clean_sentence = sentence.strip().lower()                
                matches = re.findall(oil_pattern, sentence, re.IGNORECASE)
                if matches:
                    is_negative = any(neg in clean_sentence for neg in negative_words)
                    if not is_negative:
                        for match in matches:
                            results.append(match)
                            
    return list(set(results))

def loop_car_bank(csv_path):
    df = pd.read_csv(csv_path)
    results = []
    for index, row in df.iterrows():
        file_path = row['path']
        try:
            data = text_extraction(file_path)
            results.append(", ".join(data) if isinstance(data, list) else data)
            print(data)
        except Exception as e:
            print(e)
            results.append("Error")
    df['viscosity'] = results
    df.to_csv(csv_path, index=False)

#test
def main():
    loop_car_bank("manuals.csv")

if __name__ == "__main__":
    main()