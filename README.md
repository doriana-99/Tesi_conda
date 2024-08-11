# Run Experiments

## Introduzione

Questo script esegue esperimenti sul task Multiple Choice utilizzando un file Excel come input. Lo script invia richieste a un local server su porto 1234 per ottenere risposte del modello e confronta le risposte con le risposte corrette.

## Prerequisiti

- [Conda](https://docs.conda.io/projects/conda/en/latest/user-guide/install/index.html)
- [Python 3.8](https://www.python.org/downloads/release/python-380/)
- [LM Studio](https://lmstudio.ai/)

## Installazione

1. Clona questo repository o scarica i file.

2. Crea e attiva l'ambiente Conda:

   ```bash
   conda env create -f environment.yml
   conda activate myenv

## Utilizzo

1. Prima di eseguire lo script, è necessario avviare il modello sul portale 1234 utilizzando LM Studio. Assicurati che il server del modello sia in esecuzione all'indirizzo http://localhost:1234/v1/chat/completions (endpoint di LMstudio).

2. Esegui lo script passando il percorso del file Excel, la categoria e il modello come argomenti:

    ```bash
    python script_ITA.py path/to/DataExtraction.xlsx "Categoria" "Modello"

path/to/DataExtraction.xlsx: Percorso al file Excel.
"Categoria": Categoria da filtrare.
"Modello": Nome del modello da utilizzare.

## Output

I risultati verranno salvati come file CSV con il nome del foglio e del modello.