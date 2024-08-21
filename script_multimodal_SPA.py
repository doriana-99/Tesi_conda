import pandas as pd
import requests
import json
from io import BytesIO
import re
import string

# Percorso del file Excel
excel_path = r'C:\Users\traet\Desktop\TESI\Dataset\DataExtraction\DataExtractionSpanish_img.xlsx'

# Endpoint
base_url = "http://localhost:1234/v1/chat/completions"

# Funzione di pulizia
def clean_text(text):
    if pd.isna(text):
        return ''
    text = str(text).strip().lower()
    text = text.translate(str.maketrans('', '', string.punctuation))
    return ' '.join(text.split())

def normalize_answers(answers):
    return {letter: clean_text(text) for letter, text in answers.items()}

def correct_json_format(json_str):
    # Sostituisce virgolette tipografiche con virgolette standard
    json_str = json_str.replace('“', '"').replace('”', '"')
    # Aggiunge una parentesi graffa di chiusura se manca
    if json_str.count('{') > json_str.count('}'):
        json_str += '}'
    return json_str

def extract_answer_from_json(json_str):
    try:
        json_str = correct_json_format(json_str)
        data = json.loads(json_str)
        # Normalizza la chiave dell'answer
        answer = data.get('answer') or data.get('Answer') or data.get('respuesta') or data.get('Respuesta')
        return answer.strip().upper() if answer else None
    except (json.JSONDecodeError, KeyError):
        return None
    
# Verifica connessione al server
try:
    response = requests.get(base_url)
    response.raise_for_status()
    print("Server is reachable.")
except requests.RequestException as e:
    print(f"Errore nella connessione al server: {e}")
    exit()

# Leggi tutti i fogli dell'Excel
excel_file = pd.ExcelFile(excel_path)

# Definizione delle colonne richieste
required_columns = ['Category', 'Question', 'Image url', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer']

for sheet_name in excel_file.sheet_names:
    print(f"Processing sheet: {sheet_name}")
    
    # Leggi il foglio corrente
    df = pd.read_excel(excel_path, sheet_name=sheet_name)
    
    # Verifica che tutte le colonne necessarie esistano
    if not all(col in df.columns for col in required_columns):
        print(f"Errore: una o più colonne richieste mancano nel foglio '{sheet_name}'.")
        continue
    
    results = []

    for _, row in df.iterrows():
        category = row['Category']
        question = row['Question']
        image_url = row['Image url']
        answers = {
            'A': row['AnswerA'],
            'B': row['AnswerB'],
            'C': row['AnswerC'],
            'D': row['AnswerD'],
            'E': row['AnswerE']
        }
        correct_answer_text = row['Correct Answer']

        # Pulizia delle risposte
        cleaned_answers = normalize_answers(answers)
        cleaned_correct_answer_text = clean_text(correct_answer_text)

        # Trova la lettera della risposta corretta
        correct_answer_letter = None
        for letter, cleaned_text in cleaned_answers.items():
            if cleaned_text == cleaned_correct_answer_text:
                correct_answer_letter = letter
                break

        if correct_answer_letter is None:
            print(f"Errore: La risposta corretta '{correct_answer_text}' non corrisponde a nessuna delle opzioni.")
            print(f"Opzioni disponibili:")
            for letter, text in answers.items():
                print(f"{letter}: {text}")
            continue

        # Prepara il prompt per il modello
        image_prompt = f"Image: {image_url}" if image_url else ""
        prompt_text = f"{image_prompt}\n{question}" if image_url else question
        choices_text = "\n".join([f"{chr(65 + i)}: {a}" if a else f"{chr(65 + i)}: [Empty]" for i, a in enumerate(answers.values())])

        message_content = (
            f"A continuación se muestra una imagen y una pregunta relevante para el ámbito médico. Eres un experto en preguntas multimodales de opción múltiple en el entorno clínico. Sabe reconocer imágenes clínicas. Elija la respuesta correcta entre las cinco opciones disponibles.\n"
            f"Immagine: {image_url}\n"
            f"{prompt_text}\n"
            f"{choices_text}\n\n"
            f"Instrucción:\n"
            f"Devuelve tu resultado en formato JSON que contiene un campo de 'answer' que indica la letra correspondiente a la respuesta correcta (A, B, C, D o E). El campo nunca puede estar vacío.\n"
            f"Model Answer:"
        )

        messages = [
            {
                "role": "user",
                "content": message_content
            }
        ]

        # Richiedi una risposta dal modello
        try:
            response = requests.post(
                base_url,
                json={"messages": messages},
                timeout=180
            )
            response.raise_for_status()
            data = response.json()
            model_answer = data['choices'][0]['message']['content'].strip()
            
            # Estrai la risposta dal JSON del modello
            model_answer_letter = extract_answer_from_json(model_answer)

            # Confronta le risposte
            if model_answer_letter and correct_answer_letter:
                is_correct = model_answer_letter == correct_answer_letter.upper()
            else:
                is_correct = False

            # Aggiungi i risultati alla lista
            results.append({
                'Category': category,
                'Task': 'Multiple Choice Multimodal',
                'Models': 'BioMedGPT-LM-7B-GGUF',
                'Question': question,
                'Image url': image_url,
                'Correct Answer': correct_answer_letter,
                'Model Answer': model_answer,
                'Is Correct': is_correct
            })
        except requests.RequestException as e:
            print(f"Errore nella richiesta al modello: {e}")

    # Salva i risultati per il foglio corrente in un CSV
    results_df = pd.DataFrame(results)
    csv_filename = f'{sheet_name}_BioMedGPT_Multimodal_SPA.csv'
    results_df.to_csv(csv_filename, index=False)
    print(f'Saved results for sheet "{sheet_name}" to {csv_filename}')
