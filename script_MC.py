import pandas as pd
import requests
import json
import re

excel_path = r'C:\Users\traet\Desktop\TESI\Dataset\DataExtraction\DataExtraction.xlsx'

# Endpoint
base_url = "http://localhost:1234/v1/chat/completions"

# Connessione al server
try:
    response = requests.get(base_url)
    response.raise_for_status()
    print("Server is reachable.")
except requests.RequestException as e:
    print(f"Errore nella connessione al server: {e}")
    exit()

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ').replace(' ', '')

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
        answer = data.get('answer') or data.get('Answer')
        return answer.strip().upper() if answer else None
    except (json.JSONDecodeError, KeyError):
        return None

# Carica tutti i fogli di calcolo
xls = pd.ExcelFile(excel_path)
sheet_names = xls.sheet_names

# Itera su tutti i fogli di calcolo
for sheet_name in sheet_names:
    df = pd.read_excel(xls, sheet_name=sheet_name)

    # Verifica che tutte le colonne necessarie esistano
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Errore: uno o più colonne richieste mancano nel foglio '{sheet_name}'.")
        continue

    results = []

    for _, row in df.iterrows():
        category = row['Category']
        question = row['Question']
        answers = {
            'A': row['AnswerA'],
            'B': row['AnswerB'],
            'C': row['AnswerC'],
            'D': row['AnswerD'],
            'E': row['AnswerE']
        }
        correct_answer_text = clean_text(row['Correct Answer'])
        percentage_correct = row['Percentage Correct']

        # Trova la lettera della risposta corretta
        correct_answer_letter = None
        for letter, text in answers.items():
            cleaned_text = clean_text(text)
            if cleaned_text == correct_answer_text:
                correct_answer_letter = letter
                break

        if correct_answer_letter is None:
            print(f"Errore: La risposta corretta '{row['Correct Answer']}' non corrisponde a nessuna delle opzioni.")
            continue

        # Prepara il messaggio da inviare al modello (PROMPT)
        answers_formatted = [f"{chr(65 + i)}. {a}" for i, a in enumerate(answers.values())]
        answers_text = "\n".join(answers_formatted)
        message_content = (
            f"Di seguito è riportata una domanda attinente al dominio medico. Sei un esperto di domande a risposta multipla nell'ambito clinico. Scegli la risposta corretta tra le cinque opzioni disponibili. \n"
            f"Categoria: {category}\n"
            f"Domanda: {question}\n"
            f"A: {answers['A']}\n"
            f"B: {answers['B']}\n"
            f"C: {answers['C']}\n"
            f"D: {answers['D']}\n"
            f"E: {answers['E']}\n"
            f"Istruzione:\n"
            f"Restituisci il tuo risultato in formato JSON contenente un campo 'answer' che indica la lettera corrispondente alla risposta corretta (A, B, C, D oppure E). Il campo non può mai essere vuoto.\n"
            f"Model Answer:"
        )

        messages = [
            {
                "role": "user",
                "content": message_content
            }
        ]

        # Richiede una risposta dal modello
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

            # Confronta le risposte convertendo entrambe in maiuscolo
            if model_answer_letter and correct_answer_letter:
                is_correct = model_answer_letter == correct_answer_letter.upper()
            else:
                is_correct = False

            # Aggiungi i risultati alla lista
            results.append({
                'Category': category,
                'Task': 'Multiple Choice',
                'Models': 'BioMistral-7B-GGUF',
                'Question': question,
                'Correct Answer': correct_answer_letter.upper(),
                'Model Answer': model_answer,
                'Percentage Correct': percentage_correct,
                'Is Correct': is_correct,
                #'Sheet': sheet_name  
            })
        except requests.RequestException as e:
            print(f"Errore nella richiesta al modello: {e}")

    results_df = pd.DataFrame(results)
    csv_filename = f'{sheet_name}_BioMistral_MC.csv'
    results_df.to_csv(csv_filename, index=False)
    print(f'Saved results for sheet "{sheet_name}" to {csv_filename}')
