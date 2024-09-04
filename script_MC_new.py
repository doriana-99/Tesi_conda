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
    required_columns = ['Category', 'Question', 'AnswerA', 'AnswerB', 'AnswerC', 'AnswerD', 'AnswerE', 'Correct Answer', 'Percentage Correct']
    if not all(col in df.columns for col in required_columns):
        print(f"Error: Una o più colonne richieste mancano nel foglio '{category}'.")
        return

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
        
        if model == "mistralai/Mistral-7B-Instruct-v0.1":
            formatted_content = f"<s>[INST] {content} [/INST]</s>"
            messages = [{"role": "user", "content": formatted_content}]
            max_length = 2048
        elif model == "mii-community/zefiro-7b-base-ITA":
            sys_prompt = "Sei un assistente disponibile, rispettoso e onesto. " \
                         "Rispondi sempre nel modo piu' utile possibile, pur essendo sicuro. " \
                         "Le risposte non devono includere contenuti dannosi, non etici, razzisti, sessisti, tossici, pericolosi o illegali. " \
                         "Assicurati che le tue risposte siano socialmente imparziali e positive. " \
                         "Se una domanda non ha senso o non e' coerente con i fatti, spiegane il motivo invece di rispondere in modo non corretto. " \
                         "Se non conosci la risposta a una domanda, non condividere informazioni false."
            user_prompt = content 
            messages = [
                {'role': 'assistant', 'content': sys_prompt},
                {'role': 'user', 'content': user_prompt}
            ]
            max_length = 2048
        elif model == "BioMistral/BioMistral-7B":
            messages = [{"role": "user", "content": content}]
            max_length = 2048
        elif model == "meta-llama/Meta-Llama-3-8B-Instruct":
            formatted_content = f"""<s>[INST] <<SYS>>\nYou are a medical expert. Provide the best answer.\n<</SYS>>\n{content} [/INST]"""
            messages = [{"role": "user", "content": formatted_content}]
            max_length = 2048
        elif model == "swap-uniba/LLaMAntino-3-ANITA-8B-Inst-DPO-ITA":
            sys_prompt = "Tu sei un assistente medico esperto. Fornisci la migliore risposta possibile."
            user_prompt = content
            formatted_content = f"<|start_header_id|>system<|end_header_id|>\n{sys_prompt}<|eot_id|>\n<|start_header_id|>user<|end_header_id|>\n{user_prompt}<|eot_id|>\n<|start_header_id|>assistant<|end_header_id|>\n"
            messages = [{"role": "user", "content": formatted_content}]
            max_length = 2048
        elif model == "ContactDoctor/Bio-Medical-Llama-3-8B":
            sys_prompt = "You are an expert trained on healthcare and biomedical domain!"
            messages = [
                {"role": "system", "content": sys_prompt},
                {"role": "user", "content": content}
            ]
            max_length = 2048
        elif model == "google/gemma-2-9b-it":
            messages = [{"role": "user", "content": content}]
            max_length = 2048
        elif model == "Shaleen123/gemma2-9b-medical":
            messages = [{"role": "user", "content": content}]
            max_length = 2048
        else:
            messages = [{"role": "user", "content": content}]
            max_length = 4096

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
    print("Sono in script_MC_new...")
    initialize_model(model)

    if category.lower() == "all":
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
    parser.add_argument('--excel_path', help="Percorso del file Excel.", required=True)
    parser.add_argument('--category', help="Nome del foglio di lavoro o 'all' per tutti i fogli.", required=True)
    parser.add_argument('--model', help="Nome del modello da utilizzare.", required=True)

    args = parser.parse_args()
    main(args.excel_path, args.category, args.model)
