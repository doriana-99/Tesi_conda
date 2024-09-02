import pandas as pd
import argparse
from transformers import pipeline
from tqdm import tqdm
import torch
import json
import os
import re

# Variabile globale per tenere traccia dello stato di inizializzazione del modello
model_initialized = False
text_gen_pipeline = None

def clean_text(text):
    if pd.isna(text):
        return ''
    return str(text).strip().lower().replace('\n', ' ').replace(";", "")

def process_sheet(df, category, model, json_filename, text_gen_pipeline):
    # Verifica che tutte le colonne richieste esistano
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: Una o più colonne richieste mancano nel foglio '{category}'.")
        return

    # Assicurati che il file JSON esista
    if not os.path.exists(json_filename):
        with open(json_filename, 'w') as f:
            json.dump([], f)  # Inizializza con una lista vuota

    for i, row in tqdm(df.iterrows(), total=len(df)):
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
            print("ERROR!")
            print("   Question: ", question)
            print("   Answers: ", answers)
            print("   Correct answer: ", correct_answer_text)
            continue
        percentage_correct = row['Percentage Correct']

        content = f"""Di seguito è riportata una domanda attinente al dominio medico di {category}. Sei un esperto di domande a risposta multipla nell'ambito clinico. Scegli la risposta corretta tra le cinque opzioni disponibili. \n
            Categoria Medica: {category}\n
            Domanda Medica: {question}\n
            A: {answers['A']}\n
            B: {answers['B']}\n
            C: {answers['C']}\n
            D: {answers['D']}\n
            E: {answers['E']}\n
            Instruction:
            Return the result containing an ‘answer’ field indicating the letter corresponding to the correct answer (A, B, C, D or E).
            WITH ONLY NECESSARY THIS STRUCTURE:
             {{"answer": "(letter corresponding to the correct answer)"}}
            The field can never be empty.
            """

        messages = [{"role": "user", "content": content}]
        try:
            response = text_gen_pipeline(
                          messages,
                          max_new_tokens=128,
                          do_sample=True,
                          temperature=0.7,
                          top_k=50,
                          top_p=0.95
                      )
            generated_text = response[0]['generated_text'][-1]['content'] 
            response_dict = json.loads(generated_text)
            model_answer = response_dict['answer']

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

        except Exception as e:
            print(f"Error in model request: {e}")

    print(f'Updated results for sheet "{category}" in {json_filename}')

def initialize_model(model):
    global model_initialized, text_gen_pipeline
    if not model_initialized:
        print("Initializing the model...")
        text_gen_pipeline = pipeline("text-generation",
                                     model=model,
                                     model_kwargs={
                                        "torch_dtype": torch.float16,
                                        "quantization_config": {"load_in_4bit": True}
                                      },
                                    )
        model_initialized = True
        print("Model initialized.")

def main(excel_path, category, model):
    initialize_model(model)

    if category.lower() == "all":
        # Carica tutti i fogli
        sheets = pd.read_excel(excel_path, sheet_name=None)
        for sheet_name, df in sheets.items():
            json_filename = f"{sheet_name.replace(' ', '-').replace(',','')}_{model.split('/')[-1]}_MC.json"
            if os.path.exists(json_filename):
                print(f"Saltato foglio '{sheet_name}' perché il file di output '{json_filename}' esiste già.")
            else:
                print(f"Elaborazione foglio '{sheet_name}'...")
                process_sheet(df, sheet_name, model, json_filename, text_gen_pipeline)
    else:
        df = pd.read_excel(excel_path, sheet_name=category)
        json_filename = f"{category.replace(' ', '-').replace(',','')}_{model.split('/')[-1]}_MC.json"
        if os.path.exists(json_filename):
            print(f"Saltato foglio '{category}' perché il file di output '{json_filename}' esiste già.")
        else:
            process_sheet(df, category, model, json_filename, text_gen_pipeline)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Esegui lo script per elaborare un file Excel e generare le risposte.")
    parser.add_argument('--excel_path',"excel_path", help="Percorso del file Excel.")
    parser.add_argument('--category',"category", help="Nome del foglio di lavoro o 'all' per tutti i fogli.")
    parser.add_argument('--model',"model", help="Nome del modello da utilizzare.")

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model)
