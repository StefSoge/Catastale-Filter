# Catastale Filter
### Plugin di QGIS per interrogare i layer catastali per comune, foglio e particella

Questo plugin utilizza i files dei dati catastali dei Comuni italiani forniti 
dal plugin **Italy Inspire Cadastre Downloader di Geoinnova** (https://github.com/geoinnova/italy_inspire_cadastre_downloader) 
per l'effettuazione di ricerche per Comune, Foglio, Pparticella ed individuazione 
della particella nel layer con evidenziazione mediante effetto visivo di lampeggio. 
I layer *_ple vengono rielaborati dalla apposita funzione 'Prepara layers _ple' 
da eseguire dopo l'importazione dei layers catastali.
### Istruzioni
1) Installare il plugin **Italy Inspire Cadastre Downloader** ed effettuare il download dei files dei Comuni desiderati con aggiunta dei layers alla mappa (per ulteriori informazioni sull'utilizzo del plugin riferirsi a: https://github.com/geoinnova/italy_inspire_cadastre_downloader);
2) Installare il plugin **Catastale Filter**;
3) lanciare in esecuzione la funzione *Prepara layers _ple* ed attendere il termine;
4) utilizzare la GUI *Filtro Catastale* per effettuare le proprie ricerche selezionando il Comune desiderato tramite la combobox dinamica (mostra solo i layers preparati) ed i campi di input foglio e particella;

### Note
- I nomi dei layer dei Comuni (così come importati dal Plugin di Geoinnova) devono avere il seguente formato:
  codcomune_COMUNE_map
  codcomune_COMUNE_ple
  es.
  G790_POLINO_map
  G790_POLINO_ple

- le tabelle dei layers *_map* e *_ple* devono contenere il campo INSPIREID_LOCALID
- qualora tali specifiche formali (oltre che sostanziali, relativamente al contenuto di INSPIREID_LOCALID) dovessero cambiare, il plugin dovrà essere adeguato 😉

![immagine](https://github.com/user-attachments/assets/642a3411-17a5-490a-90f1-dc35d1e9239e)

![immagine](https://github.com/user-attachments/assets/100bd255-75bd-401a-a83d-3580db2232a1)



  
