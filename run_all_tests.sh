#!/bin/bash

# Lista di modelli
models=(
     "mistralai/Mistral-7B-Instruct-v0.1"   # mistral base: già fatto
     "mii-community/zefiro-7b-base-ITA"  # mistral italiano
    # "BioMistral/BioMistral-7B"  # mistral medico
     "meta-llama/Meta-Llama-3-8B-Instruct"  # llama base
     "swap-uniba/LLaMAntino-3-ANITA-8B-Inst-DPO-ITA"  # llama italiano
     "ContactDoctor/Bio-Medical-Llama-3-8B"  # llama medico
    # "google/gemma-2-9b-it"  # gemma base
    "Shaleen123/gemma2-9b-medical" # gemma medico
)

# Lista di categorie
categories=(
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
     "Medicina dello sport "
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
# Percorso del file Excel
excel_path="/content/DataExtraction.xlsx"

# Loop attraverso tutti i modelli e categorie
for model in "${models[@]}"; do
    for category in "${categories[@]}"; do
        command="python script_MC_new.py --excel_path \"$excel_path\" --category \"$category\" --model \"$model\""
        echo "Esecuzione per modello: $model, categoria: $category"
        echo "Comando: $command"
        eval "$command"
    done
done
