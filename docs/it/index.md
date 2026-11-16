---
title: Home
nav_order: 1
lang: "it"
source: index.md
source_hash: "52e652b3dd93"
nav_exclude: true
search_exclude: true
permalink: /it/
---
# 3DHeat Battlefield {#dheat-battlefield}

**Che cos'è?** Questo strumento trasforma un livello di Battlefield 6, letto dalla **tua installazione**,
in un livello 3D - un modello della mappa sopra cui puoi volare - per il visualizzatore
[3DHeat](https://github.com/Holdi601/3DHeat) ([documentazione](https://holdi601.github.io/3DHeat/)): il suolo, ogni
edificio, roccia, albero e recinzione che il livello colloca, a richiesta con i loro colori
e le superfici su cui possono camminare i soldati.

**Perché usarlo?** Perché il calore delle tue partite di Battlefield 6 abbia sotto di sé il suolo e
gli edifici, nelle coordinate del gioco: niente da posizionare o ridimensionare nel visualizzatore.

**Esempio:** `heat3d-battlefield-maps level <level> -o level.glb` -> `level.glb`,
qualche centinaio di MB per un livello intero. (*Frostbite* è il motore con cui è fatto
Battlefield.)

## Avvio rapido {#quick-start}

Non hai mai usato la riga di comando? Leggi prima [Prima di iniziare](before-you-start.md).
Ti servono Python 3.10 o successivo, [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/)
(la libreria con cui lo strumento legge) e Battlefield 6 installato. Esegui questi comandi nella
cartella in cui hai clonato o decompresso lo strumento:

```bash
python -m pip install -e .                                  # installs heat3d-battlefield-maps, and GameFiles with it
heat3d-battlefield-maps levels                              # where the game is, and its levels
heat3d-battlefield-maps level <level> -o level.glb          # one level, flat colours
heat3d-battlefield-maps level <level> -o level.glb --textures --ground-texture   # with colour
```

`levels` inizia con una riga come `<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6`
e stampa un livello per riga; `level` termina con `-> level.glb (<n> MB)`. Poi
carica `level.glb` nel pannello **Sfondo / livello** del visualizzatore
([caricare un livello](https://holdi601.github.io/3DHeat/levels.html)).

Il livello è costruito a partire dai file del gioco: resta **sul tuo computer**, per
guardarlo, non per condividerlo o pubblicarlo ([Termini](terms.md)).

## Pagine {#pages}

| Pagina | Cosa contiene |
|---|---|
| [Prima di iniziare](before-you-start.md) | Python, GameFiles, un terminale, una prima esecuzione |
| [Livelli di Battlefield 6: levels e level](level-battlefield.md) | elencare i livelli, ogni opzione di un'esportazione, le sue parti, le dimensioni da aspettarsi |
| [Identificare un file: identify](identify.md) | se un file è un indice Frostbite, e che cosa contiene |
| [Frostbite](reader-frostbite.md) | come vengono letti indici, bundle, mesh, terreno e texture, e come ciascuno è stato verificato |
| [Termini e licenza](terms.md) | il gioco di EA, Oodle, le fonti, perché questo è un pacchetto separato |
| [Riferimento dei comandi](../cli-reference.md) | ogni opzione, generata dal codice |
| [Manutenzione di queste pagine](maintaining.md) | la checklist di rilascio |

## Collegamenti {#related}

- Il visualizzatore 3DHeat: [github.com/Holdi601/3DHeat](https://github.com/Holdi601/3DHeat),
  documentazione su [holdi601.github.io/3DHeat](https://holdi601.github.io/3DHeat/).
- [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/): i lettori del motore e lo
  scrittore glTF su cui si basa questo strumento; i suoi `levels`, `level` e
  `identify` eseguono questo strumento quando è installato.

## Gli strumenti 3DHeat {#the-3dheat-tools}

| Strumento | Cosa fa | Codice | Documentazione |
|---|---|---|---|
| Visualizzatore 3DHeat | mostra i dati: mappe di calore, analisi di gara, revisione delle partite | [3DHeat](https://github.com/Holdi601/3DHeat) | [docs](https://holdi601.github.io/3DHeat/) |
| GameFiles | livelli e percorsi dai file propri di un gioco | [3DHeat-GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) | [docs](https://holdi601.github.io/3DHeat-GameFiles/) |
| GameCapture | telemetria dei giri, e livelli ricostruiti dai video di gioco | [3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) | [docs](https://holdi601.github.io/3DHeat-GameCapture/) |
| Unreal Exporter | un plugin per Unreal Editor: un livello come un unico `.glb` | [3DHeat-UnrealExporter](https://github.com/Holdi601/3DHeat-UnrealExporter) | [docs](https://holdi601.github.io/3DHeat-UnrealExporter/) |
| CS2 | demo e mappe di Counter-Strike 2 | [3DHeat-CS2](https://github.com/Holdi601/3DHeat-CS2) | [docs](https://holdi601.github.io/3DHeat-CS2/) |
| Watcher | registra ciò che i giochi pubblicano mentre giochi | [3DHeat-Watcher](https://github.com/Holdi601/3DHeat-Watcher) | [docs](https://holdi601.github.io/3DHeat-Watcher/) |
| Ext-WarThunder | replay di War Thunder | [3DHeat-Ext-WarThunder](https://github.com/Holdi601/3DHeat-Ext-WarThunder) | [docs](https://holdi601.github.io/3DHeat-Ext-WarThunder/) |
| Ext-WoT | replay di World of Tanks | [3DHeat-Ext-WoT](https://github.com/Holdi601/3DHeat-Ext-WoT) | [docs](https://holdi601.github.io/3DHeat-Ext-WoT/) |
| Ext-WoWs | replay di World of Warships | [3DHeat-Ext-WoWs](https://github.com/Holdi601/3DHeat-Ext-WoWs) | [docs](https://holdi601.github.io/3DHeat-Ext-WoWs/) |
| Ext-Squad | demo dei server di Squad | [3DHeat-Ext-Squad](https://github.com/Holdi601/3DHeat-Ext-Squad) | [docs](https://holdi601.github.io/3DHeat-Ext-Squad/) |
| Ext-DCS | mappe di DCS World come livelli 3D | [3DHeat-Ext-DCS](https://github.com/Holdi601/3DHeat-Ext-DCS) | [docs](https://holdi601.github.io/3DHeat-Ext-DCS/) |
| Ext-IL2 | mappe di IL-2 Sturmovik come livelli 3D | [3DHeat-Ext-IL2](https://github.com/Holdi601/3DHeat-Ext-IL2) | [docs](https://holdi601.github.io/3DHeat-Ext-IL2/) |
| Ext-Dota | la mappa di Dota 2 come livello 3D | [3DHeat-Ext-Dota](https://github.com/Holdi601/3DHeat-Ext-Dota) | [docs](https://holdi601.github.io/3DHeat-Ext-Dota/) |
| Ext-DotaReplay | replay di Dota 2 come tabelle | [3DHeat-Ext-DotaReplay](https://github.com/Holdi601/3DHeat-Ext-DotaReplay) | [docs](https://holdi601.github.io/3DHeat-Ext-DotaReplay/) |
| Ext-Riot | replay di League of Legends e VALORANT | [3DHeat-Ext-Riot](https://github.com/Holdi601/3DHeat-Ext-Riot) | [docs](https://holdi601.github.io/3DHeat-Ext-Riot/) |
| Ext-Forza | percorsi e auto di Forza Horizon | [3DHeat-Ext-Forza](https://github.com/Holdi601/3DHeat-Ext-Forza) | [docs](https://holdi601.github.io/3DHeat-Ext-Forza/) |
| Ext-Battlefield | livelli di Battlefield 6 come livelli 3D | [3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield) | [docs](https://holdi601.github.io/3DHeat-Ext-Battlefield/) |
| Ext-BeamNG | percorsi di BeamNG.drive intorno ai tuoi giri | [3DHeat-Ext-BeamNG](https://github.com/Holdi601/3DHeat-Ext-BeamNG) | [docs](https://holdi601.github.io/3DHeat-Ext-BeamNG/) |
| Ext-ACRally | tappe di Assetto Corsa Rally intorno ai tuoi giri | [3DHeat-Ext-ACRally](https://github.com/Holdi601/3DHeat-Ext-ACRally) | [docs](https://holdi601.github.io/3DHeat-Ext-ACRally/) |
| Ext-Reforger | mondi di Arma Reforger come livelli 3D | [3DHeat-Ext-Reforger](https://github.com/Holdi601/3DHeat-Ext-Reforger) | [docs](https://holdi601.github.io/3DHeat-Ext-Reforger/) |
| Ext-R6 | replay di partite di Rainbow Six Siege | [3DHeat-Ext-R6](https://github.com/Holdi601/3DHeat-Ext-R6) | [docs](https://holdi601.github.io/3DHeat-Ext-R6/) |
