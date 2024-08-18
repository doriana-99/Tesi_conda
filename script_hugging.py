import pandas as pd
import argparse
from transformers import pipeline

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ').replace(' ', '')

def main(excel_path, category, model):
    # Carica il modello da Hugging Face
    qa_pipeline = pipeline("question-answering", model="MaziyarPanahi/BioMistral-7B-GGUF")

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

            # Prepara il contesto e la domanda per il modello
            context = "\n".join([f"{letter}: {text}" for letter, text in answers.items()])
            qa_input = {
                'question': question,
                'context': context
            }

            try:
                response = qa_pipeline(qa_input)
                model_answer = response['answer'].strip()

                # Valuta la risposta del modello
                model_answer_letter = None
                for letter, text in answers.items():
                    if clean_text(text).startswith(clean_text(model_answer)):
                        model_answer_letter = letter
                        break

                if model_answer_letter is None:
                    print(f"Errore: La risposta del modello '{model_answer}' non corrisponde a nessuna delle opzioni.")
                    continue

                # Confronta la risposta del modello con la risposta corretta
                is_correct = model_answer_letter == correct_answer_text_display[0]

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
            except Exception as e:
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