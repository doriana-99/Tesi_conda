import pandas as pd
import argparse
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from tqdm import tqdm
import json
import os
from concurrent.futures import ThreadPoolExecutor
import torch

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ').replace(";", "")

def load_model(model_name, quantize):
    print(f"Loading model '{model_name}' with quantization set to {quantize}...")
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    
    if quantize:
        model = AutoModelForCausalLM.from_pretrained(model_name, torch_dtype=torch.float16, load_in_8bit=True, device_map="auto")
    else:
        model = AutoModelForCausalLM.from_pretrained(model_name)
    
    text_gen_pipeline = pipeline("text-generation", model=model, tokenizer=tokenizer, device=0)
    return text_gen_pipeline

def process_sheet(df, category, model, quantize, json_filename):
    text_gen_pipeline = load_model(model, quantize)
    
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: One or more required columns are missing in sheet '{category}'.")
        return

    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as f:
            json.dump([], f)

    def process_row(row):
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
        try:
            correct_answer_key = answer2key[correct_answer_text]
        except:
            print(f"Error in processing question: {question}")
            return None

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

        if model == "epfl-llm/meditron-7b":
            messages = content
            max_length = 2048
        else:
            messages = [{"role": "user", "content": content}]
            max_length = 4096
        try:
            response = text_gen_pipeline(messages, max_length=max_length)
            if model == '':
                generated_text = response[0]['generated_text']
            else:
                generated_text = response[0]['generated_text'][-1]['content']
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
                'Percentage Correct': row['Percentage Correct'],
                'Is Correct': is_correct,
            }
            return result
        except Exception as e:
            print(f"Error in model request: {e}")
            return None

    results = []
    for i, row in tqdm(df.iterrows(), total=len(df)):
        result = process_row(row)
        results.append(result)

    with open(json_filename, 'w') as f:
        json.dump(results, f, indent=4)

    print(f'Updated results for sheet "{category}" in {json_filename}')

def main(excel_path, category, model, quantize):
    if category.lower() == "all":
        sheets = pd.read_excel(excel_path, sheet_name=None)
        for sheet_name, df in sheets.items():
            json_filename = f"{sheet_name.replace(' ', '-').replace(',','')}_{model.split('/')[-1]}_MC.json"
            if os.path.exists(json_filename):
                print(f"Skipping sheet '{sheet_name}' as output file '{json_filename}' already exists.")
            else:
                print(f"Processing sheet '{sheet_name}'...")
                process_sheet(df, sheet_name, model, quantize, json_filename)

    else:
        df = pd.read_excel(excel_path, sheet_name=category)
        json_filename = f"{category.replace(' ', '-').replace(',','')}_{model.split('/')[-1]}_MC.json"
        if os.path.exists(json_filename):
            print(f"Skipping sheet '{category}' as output file '{json_filename}' already exists.")
        else:
            process_sheet(df, category, model, quantize, json_filename)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Run experiments on the model.')
    parser.add_argument('--excel_path', type=str, help='Path to the Excel file')
    parser.add_argument('--category', type=str, default='all', help='Category to filter or "all" to process all sheets')
    parser.add_argument('--model', type=str, help='Model name')
    parser.add_argument('--quantize', action='store_true', help='Quantize the model')

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model, args.quantize)
