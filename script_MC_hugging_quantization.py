import pandas as pd
from transformers import pipeline, BitsAndBytesConfig
from tqdm import tqdm
import json
import os
import argparse

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ')

def main(excel_path, category, model):
    # Configura la quantizzazione
    quantize = BitsAndBytesConfig(load_in_8bit=True)

    # Carica il modello da Hugging Face con quantizzazione
    text_gen_pipeline = pipeline("text-generation", model=model, quantization_config=quantize)

    df = pd.read_excel(excel_path, sheet_name=category)
    
    # Controlla se tutte le colonne richieste esistono
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Errore: Una o più colonne richieste sono mancanti nel foglio '{category}'.")
        return

    json_filename = f"{category.replace(' ', '-')}_{model.split('/')[-1]}_MC.json"
    
    # Assicurati che il file JSON esista
    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as f:
            json.dump([], f)  # Inizializza con una lista vuota

    for _, row in tqdm(df.iterrows(), total=len(df)):
        question = row['Question']
        answers = {
            'A': clean_text(row['AnswerA']),
            'B': clean_text(row['AnswerB']),
            'C': clean_text(row['AnswerC']),
            'D': clean_text(row['AnswerD']),
            'E': clean_text(row['AnswerE'])
        }
        answer2key = {v: k for k, v in answers.items()}

        correct_answer_text = clean_text(row['Correct Answer'])
        correct_answer_key = answer2key.get(correct_answer_text, 'Unknown')
        percentage_correct = row['Percentage Correct']

        content = f"""Di seguito è riportata una domanda attinente al dominio medico. Sei un esperto di domande a risposta multipla nell'ambito clinico. Scegli la risposta corretta tra le cinque opzioni disponibili. \n
            Categoria Medica: {category}\n
            Domanda Medica: {question}\n
            A: {answers['A']}\n
            B: {answers['B']}\n
            C: {answers['C']}\n
            D: {answers['D']}\n
            E: {answers['E']}\n
            Istruzione:
            Restituisci il tuo risultato in formato JSON contenente un campo 'answer' che indica la lettera corrispondente alla risposta corretta (A, B, C, D oppure E). Il campo non può mai essere vuoto."""

        messages = [{"role": "user", "content": content}]
        try:
            response = text_gen_pipeline(messages, max_length=4096)
            generated_text = response[0]['generated_text']
            model_answer = eval(generated_text)['answer'].strip()
            is_correct = model_answer == correct_answer_key

            result = {
                'Category': category,
                'Task': 'Multiple Choice',
                'Models': model,
                'Question': question,
                'Answer A': answers['A'],
                'Answer B': answers['B'],
                'Answer C': answers['C'],
                'Answer D': answers['D'],
                'Answer E': answers['E'],
                'Correct Answer': correct_answer_key,
                'Model Answer': model_answer,
                'Percentage Correct': percentage_correct,
                'Is Correct': is_correct,
            }
            
            # Aggiungi il risultato al file JSON
            with open(json_filename, 'r+') as f:
                data = json.load(f)
                data.append(result)
                f.seek(0)
                json.dump(data, f, indent=4)
            
            print(result)
        except Exception as e:
            print(f"Errore nella richiesta del modello: {e}")

    print(f'Risultati aggiornati per il foglio "{category}" in {json_filename}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Elaborazione dei dati con un modello di Hugging Face.')
    parser.add_argument('--excel_path', type=str, required=True, help='Percorso al file Excel')
    parser.add_argument('--category', type=str, required=True, help='Categoria del foglio da elaborare')
    parser.add_argument('--model', type=str, required=True, help='Nome del modello di Hugging Face')

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model)
