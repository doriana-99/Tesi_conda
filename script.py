import pandas as pd
import requests
import argparse
import os

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ').replace(' ', '')

def main(excel_path, category, model):
    # Endpoint
    base_url = "http://localhost:1234/v1/chat/completions"

    # Connessione al server
    try:
        response = requests.get(base_url)
        response.raise_for_status()  
        print("Server is reachable.")
    except requests.RequestException as e:
        print(f"Errore nella connessione al server: {e}")
        return

    excel_file = pd.ExcelFile(excel_path)
    sheet_names = excel_file.sheet_names 

    for sheet_name in sheet_names:
        df = pd.read_excel(excel_path, sheet_name=sheet_name)
        
        # Verifica che tutte le colonne necessarie esistano
        required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
        if not all(col in df.columns for col in required_columns):
            print(f"Errore: uno o più colonne richieste mancano nel foglio '{sheet_name}'.")
            continue

        results = []

        for _, row in df.iterrows():
            if row['Category'] != category:
                continue

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

            # Trova la risposta corretta tra le opzioni
            correct_answer_text_display = None
            for letter, text in answers.items():
                cleaned_text = clean_text(text)
                if cleaned_text == correct_answer_text:
                    correct_answer_text_display = text
                    break

            if correct_answer_text_display is None:
                print(f"Errore: La risposta corretta '{row['Correct Answer']}' non corrisponde a nessuna delle opzioni.")
                continue

            # Prepara il messaggio da inviare al modello (PROMPT ITALIANO)
            answers_formatted = [f"{chr(65 + i)}. {a}" for i, a in enumerate(answers.values())]
            answers_text = "\n".join(answers_formatted)
            message_content = (
                f"Category: {category}\n"
                f"Question: {question}\n"
                f"Answers: {answers_text}\n"
                f"Instructions:\n"
                f"The following are multiple-choice questions about medical knowledge. Solve them in a step-by-step fashion, starting by summarizing the available information. Output a single option from the five options as the final answer.\n"
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

                # Valuta la risposta del modello
                model_answer_letter = model_answer.strip("[]")  

                # Confronta la risposta del modello con la risposta corretta
                is_correct = clean_text(model_answer_letter).startswith(clean_text(correct_answer_text_display)[0]) 

                # Aggiungi i risultati alla lista
                results.append({
                    'Category': category,
                    'Task': 'Multiple Choice',
                    'Models': model,
                    'Question': question,
                    'Correct Answer': correct_answer_text_display,
                    'Model Answer': model_answer_letter,
                    'Percentage Correct': percentage_correct,
                    'Is Correct': is_correct,
                })
            except requests.RequestException as e:
                print(f"Errore nella richiesta al modello: {e}")

        results_df = pd.DataFrame(results)
        csv_filename = f'{sheet_name}_{model}_MC.csv'
        results_df.to_csv(csv_filename, index=False)
        print(f'Saved results for sheet "{sheet_name}" to {csv_filename}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiments on the model.')
    parser.add_argument('excel_path', type=str, help='Path to the Excel file')
    parser.add_argument('category', type=str, help='Category to filter')
    parser.add_argument('model', type=str, help='Model name')

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model)
