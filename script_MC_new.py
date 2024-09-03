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

def format_input(content, model):
    # Verifica quale modello è in uso e formatta l'input di conseguenza
    if model == "mistralai/Mistral-7B-Instruct-v0.1" or model == "mii-community/zefiro-7b-base-ITA" or model == "BioMistral/BioMistral-7B":
        # Formattazione per modelli Mistral
        formatted_content = f"""### Instruction:\n{content}\n### Response:"""
    elif model == "meta-llama/Meta-Llama-3-8B-Instruct" or model == "swap-uniba/LLaMAntino-3-ANITA-8B-Inst-DPO-ITA" or model == "ContactDoctor/Bio-Medical-Llama-3-8B":
        # Formattazione per modelli Llama
        formatted_content = f"""<s>[INST] <<SYS>>\nYou are a medical expert. Provide the best answer.\n<</SYS>>\n{content} [/INST]"""
    elif model == "google/gemma-2-9b-it" or model == "Shaleen123/gemma2-9b-medical":
        # Formattazione per modelli Gemma
        formatted_content = f"""<|startoftext|>\n{content}\n<|endoftext|>"""
    else:
        # Formattazione predefinita nel caso in cui il modello non sia riconosciuto
        formatted_content = content
    return formatted_content

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

        formatted_content = format_input(content, model)
        messages = [{"role": "user", "content": formatted_content}]
        
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
        
