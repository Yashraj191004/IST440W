import fitz
import re

def extract_correct_viscosity(pdf_path):
    sae_pattern = r"\b\d{1,2}W-\d{2}\b"
    negative_words = ["not", "avoid", "don't", "except", "never", "other than"]
    results = []

    with fitz.open(pdf_path) as doc:
        for page in doc:
            text = page.get_text("text")
            sentences = text.split('.')
            for sentence in sentences:
                clean_sentence = sentence.strip().lower()                
                matches = re.findall(sae_pattern, sentence, re.IGNORECASE)
                if matches:
                    is_negative = any(neg in clean_sentence for neg in negative_words)
                    
                    if not is_negative:
                        for match in matches:
                            results.append(match)
                            
    return list(set(results))

#test
print(extract_correct_viscosity("manual1.pdf"))