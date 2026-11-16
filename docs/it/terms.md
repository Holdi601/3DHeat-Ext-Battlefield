---
title: "Termini e licenza"
nav_order: 8
lang: "it"
source: terms.md
source_hash: "81e5e54e5585"
nav_exclude: true
search_exclude: true
---
# Termini e licenza {#terms-and-licence}

Questa pagina è una registrazione di ciò che dicono le licenze, non un parere legale.

## Il gioco di EA {#eas-game}

Battlefield 6 e i suoi livelli appartengono a Electronic Arts, che non approva questo
progetto. Questo strumento non include nulla del gioco e non scarica nulla: legge
i file della copia **che hai** installato, sul tuo computer, al di fuori del gioco. Non modifica nulla
nel gioco, non gira insieme ad esso e non comunica con nessun server.

Ciò a cui lo indirizzi resta sotto la tua responsabilità. I giochi hanno le proprie condizioni di licenza, e i
contratti di licenza (EULA) vietano comunemente il reverse engineering. Sono contratti applicabili, e
l'obbligo ricade su chi esegue lo strumento. Usarlo è una tua decisione, secondo i termini che hai
accettato per il gioco e per il negozio da cui lo hai acquistato (il Contratto Utente di EA, quello di Steam,
dell'app EA o di Epic).

Il livello che scrive è contenuto dell'editore del gioco: conserva i file `.glb` esportati, e
le texture al loro interno, per la tua analisi. Non pubblicare, condividere né vendere livelli,
modelli o texture esportati. Il file `.gitignore` del repository tiene fuori dal controllo di versione
i file di gioco e le esportazioni, per tipo di file.

Per questo è un pacchetto separato: se EA dovesse chiederne la rimozione, va via da solo,
e il visualizzatore, GameFiles e gli altri strumenti restano.

## Nessuna parte cifrata viene aperta {#nothing-encrypted-is-opened}

- **Nessuna chiave: nessuna fornita, nessuna recuperata.** Nulla cerca una chiave in un eseguibile,
  e nulla legge la memoria di un altro processo.
- **Nemmeno l'offuscamento è implementato.** Gli indici Frostbite offuscati con XOR tengono la chiave
  nel file stesso, quindi sono offuscamento e non un controllo di accesso. Vengono comunque riconosciuti e rifiutati,
  perché nessun file a disposizione usa quella forma e non ci sarebbe nulla con cui verificare un'implementazione.
- **I file cifrati restano chiusi.** Il file system iniziale di Battlefield 6, che contiene la libreria di tipi
  del gioco, è cifrato e non viene letto. L'esportazione del livello lavora sui file non cifrati, e
  ricava dai dati i due tipi di cui ha bisogno.
- **Nulla si inietta in un processo di gioco.** L'iniezione in un titolo con anti-cheat mette a rischio
  l'account di chi la esegue.

## Oodle si trova, non è incluso {#oodle-is-found-not-bundled}

Parte dei dati del gioco è compressa con Oodle. Oodle (RAD Game Tools, ora Epic)
è proprietario e non esiste una build ridistribuibile. `oo2core_*.dll` è concesso in licenza al
prodotto che lo distribuisce. Questo strumento quindi non lo include mai: il `oodle.py` di 3DHeat
GameFiles carica una libreria già presente sulla macchina - quella che il gioco distribuisce, oppure la copia
a cui punta `HEAT3D_OODLE` - invece di portarne una con sé. Vedi
[Oodle](https://holdi601.github.io/3DHeat-GameFiles/reader-oodle.html).

## Il formato in sé {#the-format-itself}

I `.toc`, i bundle, le partizioni EBX, le MeshSet e il terreno di Frostbite non sono documentati. Leggerli
è reverse engineering di un contenitore. I lettori qui sono stati ricavati dai file dello stesso
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
