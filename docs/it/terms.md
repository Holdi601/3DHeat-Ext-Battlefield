---
title: "Termini e licenza"
nav_order: 8
lang: "it"
source: terms.md
source_hash: "50d8b31139d6"
nav_exclude: true
search_exclude: true
---
# Termini e licenza {#terms-and-licence}

## Il gioco di EA {#eas-game}

Battlefield 6 e i suoi livelli appartengono a Electronic Arts. 3DHeat Battlefield non è affiliato
a Electronic Arts né da essa approvato. Battlefield e i nomi e marchi correlati appartengono ai
rispettivi proprietari.

Questo strumento non include nulla del gioco e non scarica nulla: niente risorse del gioco, niente
codice del gioco, nessuna DLL. Legge i file della copia **che hai** installato, sul tuo computer, al
di fuori del gioco. Non modifica nulla nel gioco, non gira insieme ad esso e non comunica con nessun
server.

Il livello che scrive resta sul tuo computer: conserva i file `.glb` esportati, e le texture al loro
interno, per la tua analisi, e non pubblicare, condividere né vendere livelli, modelli o texture
esportati. Il file `.gitignore` del repository tiene fuori dal controllo di versione i file di gioco
e le esportazioni, per tipo di file.

Ogni lettore di gioco è un piccolo progetto a sé, con il proprio file di licenza, le proprie release e il proprio issue tracker: può essere installato, aggiornato, mantenuto - o ritirato su richiesta di un titolare dei diritti - da solo, senza toccare il visualizzatore o gli altri strumenti.

Titolari dei diritti: aprite una issue su [github.com/Holdi601/3DHeat-Ext-Battlefield/issues](https://github.com/Holdi601/3DHeat-Ext-Battlefield/issues) - rispondiamo rapidamente e rimuoviamo qualsiasi cosa su richiesta.

## Nessuna parte cifrata viene aperta {#nothing-encrypted-is-opened}

- **Nessuna chiave: nessuna fornita, nessuna recuperata.** Nulla cerca una chiave in un eseguibile,
  e nulla legge la memoria di un altro processo.
- **Nemmeno l'offuscamento è implementato.** Gli indici Frostbite offuscati con XOR vengono
  riconosciuti e rifiutati, perché nessun file a disposizione usa quella forma e non ci sarebbe
  nulla con cui verificare un'implementazione.
- **I file cifrati restano chiusi.** Il file system iniziale di Battlefield 6, che contiene la libreria di tipi
  del gioco, è cifrato e non viene letto. L'esportazione del livello lavora sui file non cifrati, e
  ricava dai dati i due tipi di cui ha bisogno.
- **Nulla si inietta in un processo di gioco.** Lo strumento legge solo file su disco.

## Oodle si trova, non è incluso {#oodle-is-found-not-bundled}

Parte dei dati del gioco è compressa con Oodle. Oodle (RAD Game Tools, ora Epic)
è proprietario e non esiste una build ridistribuibile. `oo2core_*.dll` è concesso in licenza al
prodotto che lo distribuisce. Questo strumento quindi non lo include mai: il `oodle.py` di 3DHeat
GameFiles carica una libreria già presente sulla macchina - quella che il gioco distribuisce, oppure la copia
a cui punta `HEAT3D_OODLE` - invece di portarne una con sé. Vedi
[Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## Il formato in sé {#the-format-itself}

I `.toc`, i bundle, le partizioni EBX, le MeshSet e il terreno di Frostbite non sono documentati. I lettori qui sono stati ricavati dai file dello stesso
Battlefield 6. Descrizioni pubbliche di versioni più vecchie di Frostbite (gli strumenti di modding Frosty, una
nota sul formato di Need for Speed Heat, un intervento alla GDC) hanno fornito nomi di campi e una mappa di
cosa cercare. Non è stato preso codice da nessuna di esse; ogni offset è stato misurato sui file
(le fonti e le loro licenze:
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md)).

## Licenza e fonti {#licence-and-sources}

MIT ([`LICENSE`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSE)):
usalo, modificalo, distribuiscilo, a fini commerciali o meno. Si basa su
[3DHeat GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) (MIT) e richiede
numpy (BSD-3-Clause), Pillow (MIT-CMU), lz4 e zstandard (BSD-3-Clause); i test richiedono pytest
(MIT). Vedi
[`LICENSES.md`](https://github.com/Holdi601/3DHeat-Ext-Battlefield/blob/main/LICENSES.md).
