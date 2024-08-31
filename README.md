# Run Experiments

## Introduzione

Questo script esegue esperimenti sul task Multiple Choice utilizzando un file Excel come input. Lo script sfrutta un modello di generazione del testo (text-generation) per determinare la risposta corretta e confrontarla con quella fornita nel file. Inoltre, è possibile attivare la quantizzazione del modello per ridurre il consumo di memoria.

## Prerequisiti

- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Python 3.8](https://www.python.org/downloads/release/python-380/)
- [Hugging Face Transformers](https://huggingface.co/docs/transformers/it/index)

## Installazione

1. Clona questo repository o scarica i file.

2. Crea e attiva l'ambiente Conda:

   ```bash
   conda env create -f environment.yml
   conda activate myenv

## Utilizzo

1. Prima di eseguire lo script, assicurati che il modello specificato sia configurato correttamente. Verifica di avere un modello di generazione del testo pronto per l'uso. Questo script utilizza la pipeline text-generation di Hugging Face. 

2. Esegui lo script passando il percorso del file Excel, la categoria e il modello come argomenti:

    ```bash
    python script_MC_hugging_quantization.py --excel_path "path/to/DataExtraction.xlsx" --category "Categoria" --model "Modello"

--excel_path "path/to/DataExtraction.xlsx": Percorso al file Excel.
--category "Categoria": Categoria da filtrare. Se vuoi processare tutti i fogli, usa all.
--model "Modello": Nome del modello da utilizzare.

## Output

I risultati verranno salvati in un file JSON per ogni foglio del file Excel, con il nome del foglio e del modello specificati nel nome del file.
