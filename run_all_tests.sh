#!/bin/bash

EXCEL_PATH="path/to/DataExtraction.xlsx"

# Definisci la lista dei modelli da testare
MODELS=(
    "mistralai/Mistral-7B-v0.1" # mistral base
    "mii-community/zefiro-7b-base-ITA" # mistral italiano
    #"BioMistral/BioMistral-7B" #mistral medico
   
    #"google/gemma-2-9b-it" #gemma base
    #gemma italiano: multilingual (?)
    "Shaleen123/gemma2-9b-medical" #gemma medico: 
    
    "meta-llama/Meta-Llama-3-8B-Instruct" #llama base
    "swap-uniba/LLaMAntino-3-ANITA-8B-Inst-DPO-ITA" #llama italiano
    "johnsnowlabs/JSL-MedLlama-3-8B-v2.0" #llama medico 
)

# Definisci la lista delle categorie da testare
CATEGORIES=(
    "Medicina Generale"
    "Allergologia e immunologia clin"
    "Dermatologia e venereologia"
    "Ematologia"
    "Endocrinologia e malattie del m"
    "Gastroenterologia"
    "Geriatria"
    "Malattie dell'apparato cardiova"
    "Malattie dell'apparato respirat"
    "Malattie infettive"
    "Medicina dello sport"
    "Medicina d'emergenza-urgenza"
    "Medicina di comunità"
    "Medicina interna"
    "Medicina termale"
    "Medicina tropicale"
    "Nefrologia"
    "Neurologia"
    "Neuropsichiatria infantile"
    "Oncologia"
    "Pediatria"
    "Psichiatria"
    "Reumatologia"
    "Scienza dell'alimentazione"
    "Cardiochirurgia"
    "Chirurgia dell'apparato digeren"
    "Chirurgia generale"
    "Chirurgia maxillo-facciale"
    "Chirurgia pediatrica"
    "Chirurgia plastica ricostruttiv"
    "Chirurgia toracica"
    "Chirurgia vascolare"
    "Ginecologia ed Ostetricia"
    "Neurochirurgia"
    "Oftalmologia"
    "Ortopedia e traumatologia"
    "Otorinolaringoiatra"
    "Urologia"
    "Anatomia patologica"
    "Anestesia e Rianimazione e Tera"
    "Audiologia e foniatria"
    "Biochimica clinica"
    "Farmacologia"
    "Genetica medica"
    "Igiene e medicina preventiva"
    "Medicina del lavoro"
    "Medicina fisica e riabilitativa"
    "Medicina legale"
    "Medicina nucleare"
    "Microbiologia e virologia"
    "Patologia clinica"
    "Radiodiagnostica"
    "Radioterapia"
    "Statistica sanitaria e Biometri"
    "Tossicologia medica"
    "Malattie dell'apparato digerent"
    "Malattie infettive e tropicali"
    "Chirurgia dell'apparato digeren"
    "Medicina dello sport e dell'ese"
    "Medicina di comunità e delle cu"
    "Oncologia medica"
    "Anestesia, Rianimazione, Terapi"
    "Patologia Clinica e Biochimica"
    "Farmacologia e Tossicologia Cli"
)

# Ciclo su tutti i modelli e categorie
for MODEL in "${MODELS[@]}"; do
    for CATEGORY in "${CATEGORIES[@]}"; do
        echo "Testing model: $MODEL on category: $CATEGORY"
        python script_MC_hugging_quantization.py --excel_path "$EXCEL_PATH" --category "$CATEGORY" --model "$MODEL"
    done
done

