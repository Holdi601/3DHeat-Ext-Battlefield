---
title: "Prima di iniziare"
nav_order: 1.5
lang: "it"
source: before-you-start.md
source_hash: "f55c65c6279e"
nav_exclude: true
search_exclude: true
---
# Prima di iniziare {#before-you-start}

Non hai mai usato la riga di comando? Questa pagina ti porta da zero alla prima esecuzione.
Ci vogliono circa quindici minuti, una volta sola.

## 1. Installa Python {#install-python}

Questo strumento richiede **Python 3.10 o successivo**.

- **Windows:** scarica Python da [python.org/downloads](https://www.python.org/downloads/)
  ed esegui l'installer. Nella sua prima schermata spunta **Add python.exe to PATH**,
  poi clicca **Install Now**.
- **macOS e Linux:** Python 3 spesso è già presente. Dove queste pagine dicono
  `python`, scrivi `python3`. (Battlefield 6 gira su Windows; lo strumento
  legge i suoi file dovunque si trovino.)

## 2. Ottieni questo strumento {#get-this-tool}

Apri [github.com/Holdi601/3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield), clicca il
pulsante verde **Code**, poi **Download ZIP**, e decomprimilo in una cartella a tua scelta. Se usi git:
`git clone https://github.com/Holdi601/3DHeat-Ext-Battlefield`.

## 3. Con lo strumento arriva 3DHeat GameFiles {#dheat-gamefiles-comes-with-it}

Lo strumento legge con [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(il suo scrittore glTF, la ricerca nelle librerie Steam, il caricatore di Oodle). Il passo 5 lo
installa per te. Senza pip - una cartella scaricata che esegui sul posto - metti GameFiles
accanto a questo strumento come `3DHeat-GameFiles`, oppure imposta `HEAT3D_GAMEFILES` sulla sua
cartella; dentro una copia di 3DHeat (`exporters/ext/battlefield-maps`) viene trovato da solo
in `exporters/gamefiles`.

## 4. Apri un terminale in quella cartella {#open-a-terminal-in-that-folder}

Un terminale è una finestra in cui scrivi i comandi.

- **Windows:** apri la cartella in Esplora file, clicca nella barra degli indirizzi, scrivi
  `powershell` e premi Invio. Si apre una finestra blu o nera, già dentro quella cartella.
- **macOS:** apri **Terminale**, scrivi `cd ` (con uno spazio), trascina la cartella
  nella finestra e premi Invio.

`cd` vuol dire "cambia cartella": `cd C:\Strumenti\3DHeat-Ext-Battlefield` va in quella cartella.

## 5. Installa lo strumento {#install-the-tool}

Scrivi questo e premi Invio:

```bash
python -m pip install -e .
```

Alla fine dovresti vedere: `Successfully installed heat3d-ext-battlefield-...`
(e `heat3d-gamefiles-...` insieme ad esso).

## 6. Eseguilo {#run-it}

```bash
heat3d-battlefield-maps levels
```

Dovresti vedere qualcosa di simile:

```text
<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6
  <level>                                    <size>  Data
  ...
```

Prossimo passo: [Livelli di Battlefield 6](level-battlefield.md).

## Come leggere i comandi di queste pagine {#how-to-read-the-commands-on-these-pages}

| Vedi | Significa |
|---|---|
| `<level>` | un segnaposto: scrivi il tuo valore al suo posto, senza i `< >` |
| `[--textures [PIXELS]]` | facoltativo: puoi ometterlo, oppure scriverlo come mostrato |
| `# a note` | un commento per te: non scriverlo |
| `"C:\My Files\x"` | metti tra virgolette un percorso che contiene spazi |

## Quando qualcosa va storto {#when-something-goes-wrong}

| Il messaggio | Cosa fare |
|---|---|
| `'python' is not recognized` | Python non è installato, oppure non hai spuntato la casella PATH: installalo di nuovo e spuntala (oppure scrivi `py` al posto di `python`). |
| `'heat3d-battlefield-maps' is not recognized` | Ripeti il passo 5 nella cartella dello strumento, oppure scrivi `python -m heat3d_ext_battlefield` al posto di `heat3d-battlefield-maps`: fa lo stesso. |
| `needs 3DHeat GameFiles: ...` | Il passo 5 non lo ha installato, oppure esegui la cartella sul posto: vedi il passo 3. |
| `no Frostbite game found in ...` | Installa il gioco, oppure indica la sua cartella: `--install "D:\Games\Battlefield 6"`. |
| `no Oodle library found` | Alcuni dati sono compressi con Oodle; il gioco include la libreria (`oo2core_*.dll`) che li decodifica. Imposta `HEAT3D_OODLE` su quel file (vedi [Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html)). |
| qualsiasi altra cosa | Leggi l'ultima riga del messaggio, poi apri una segnalazione su GitHub con quella riga. |

Ogni comando termina anche con uno **stato di uscita**: 0 vuol dire che ha funzionato, 2 che
non è stato trovato il gioco, il file o GameFiles, 1 che la lettura non è riuscita. Per vederlo,
scrivi `echo $LASTEXITCODE` in PowerShell, oppure `echo $?` su macOS e Linux.
