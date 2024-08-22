import pandas as pd
import argparse
from transformers import pipeline
from tqdm import tqdm
import json
import os

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ')

def main(excel_path, category, model):
    # Load the model from Hugging Face
    text_gen_pipeline = pipeline("text-generation", model=model)

    df = pd.read_excel(excel_path, sheet_name=category)
    
    # Check if all required columns exist
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: One or more required columns are missing in sheet '{category}'.")
        return

    json_filename = f"{category.replace(' ', '-')}_{model.split('/')[-1]}_MC.json"
    
    # Ensure the JSON file exists
    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as f:
            json.dump([], f)  # Initialize with an empty list

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
        correct_answer_key = answer2key[correct_answer_text]
        print("AAAA", correct_answer_text, correct_answer_key)
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
        print(content)
        try:
            response = text_gen_pipeline(messages, max_length=4096)
            generated_text = response[0]['generated_text'][-1]['content']
            model_answer = eval(generated_text)['answer'].strip()
            print("Model answer: ", model_answer)
            print("Risposta corretta: ", correct_answer_key)
            # Evaluate the model's answer
            is_correct = model_answer == correct_answer_key

            # Create result dictionary
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
            
            # Append result to JSON file
            with open(json_filename, 'r+') as f:
                data = json.load(f)
                data.append(result)
                f.seek(0)
                json.dump(data, f, indent=4)
            
            print(result)
        except Exception as e:
            print(f"Error in model request: {e}")

    print(f'Updated results for sheet "{category}" in {json_filename}')

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiments on the model.')
    parser.add_argument('--excel_path', type=str, help='Path to the Excel file')
    parser.add_argument('--category', type=str, help='Category to filter')
    parser.add_argument('--model', type=str, help='Model name')

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model)
