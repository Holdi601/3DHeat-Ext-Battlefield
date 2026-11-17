---
title: "Startseite"
nav_order: 1
lang: "de"
source: index.md
source_hash: "42fa7cbbd4cd"
nav_exclude: true
search_exclude: true
permalink: /de/
---
# 3DHeat Battlefield {#dheat-battlefield}

**Was ist das?** Dieses Werkzeug macht aus einem Battlefield-6-Level, gelesen aus **deiner
eigenen Installation**, ein 3D-Level für den [3DHeat](https://github.com/Holdi601/3DHeat)-Viewer
([Dokumentation](https://holdi601.github.io/3DHeat/)): ein Modell der Karte, über das du
fliegen kannst. Dazu gehören der Boden und jedes Gebäude, jeden Felsen, Baum und Zaun, die
das Level platziert, auf Wunsch mit ihren Farben und den Flächen, auf denen Soldaten gehen
können.

**Warum nutzt man das?** Damit die Hitze aus deinen Battlefield-6-Partien den Boden und die
Gebäude darunter hat, in den Koordinaten des Spiels: ohne Platzieren oder Skalieren im Viewer.

**Beispiel:** `heat3d-battlefield-maps level <level> -o level.glb` -> `level.glb`, ein paar
hundert MB für ein ganzes Level. (*Frostbite* ist die Engine, mit der Battlefield gemacht ist.)

## Schnellstart {#quick-start}

Du brauchst Windows, Python 3.10 oder neuer (im Installer "Add python.exe to PATH"
ankreuzen), das installierte Spiel und etwa 130 MB Platz je Level; Git ist nicht nötig.
Neu auf der Kommandozeile? Lies zuerst [Bevor du anfängst](before-you-start.md).

```bash
python -m pip install https://github.com/Holdi601/3DHeat-Ext-Battlefield/archive/refs/tags/v0.2.0.zip
heat3d-battlefield-maps levels --game "C:\Program Files\EA Games\Battlefield 4"                 # seine Levels
heat3d-battlefield-maps level MP_Prison --game "C:\Program Files\EA Games\Battlefield 4" -o levels
heat3d-battlefield-maps level all --game "C:\Program Files\EA Games\Battlefield 1" -o levels\bf1
heat3d-battlefield-maps levels                                                                   # Battlefield 6, findet es selbst
heat3d-battlefield-maps level <level> -o levels --textures --ground-texture                       # ein Battlefield-6-Level, mit Farbe
```

Battlefield 4 und 1 brauchen ihren Ordner mit `--game` (die EA-App installiert sie
unter `C:\Program Files\EA Games\`, Steam unter `...\steamapps\common\`).
`levels` beginnt mit einer Zeile wie `34 multiplayer levels in <Ordner>` und listet je
Zeile ein Level; `level` endet mit `-> levels\MP_Prison.glb (133 MB, 37 s)`. Ein Level
aus Battlefield 4 oder 1 dauert 20 bis 60 Sekunden, ein großes ein paar Minuten; `all`
schreibt jedes Mehrspieler-Level, zusammen etwa 4 bis 5 GB.

Dann öffne die `.glb` im [3DHeat-Viewer](https://github.com/Holdi601/3DHeat#quick-start):
herunterladen (**Code -> Download ZIP**, entpacken), `start.bat` doppelklicken (es bietet
an, Node.js zu installieren, wenn es fehlt, und öffnet `http://127.0.0.1:5273`), dann
**Hintergrund / Level -> 3D-Modell...** und die Datei wählen
([Level laden](https://holdi601.github.io/3DHeat/levels.html)). Das Level bleibt auf
deinem Rechner.

Wenn ein neues Release erscheint, sagt das Werkzeug es beim Start und bietet an, sich
selbst zu aktualisieren.

Jeder Spiele-Leser ist ein eigenes kleines Projekt mit eigener Lizenzdatei, eigenen Releases und eigenem Issue-Tracker. So lässt er sich für sich allein installieren, aktualisieren und pflegen - oder auf Wunsch eines Rechteinhabers zurückziehen -, ohne dass der Viewer oder die anderen Werkzeuge davon berührt werden.

## Seiten {#pages}

| Seite | Was sie behandelt |
|---|---|
| [Bevor du anfängst](before-you-start.md) | Python, GameFiles, ein Terminal, ein erster Lauf |
| [Battlefield-6-Level: levels und level](level-battlefield.md) | die Levels auflisten, jede Option eines Exports, seine Teile, die zu erwartenden Größen |
| [Level aus Battlefield 4 und Battlefield 1](level-battlefield-older.md) | die Mehrspieler-Level der beiden älteren Spiele aus einem angegebenen Ordner: Optionen, Teile, wie der Viewer sie zuordnet, wie sie gelesen werden |
| [Eine Datei erkennen: identify](identify.md) | ob eine Datei eine Frostbite-Inhaltstabelle ist und was sie enthält |
| [Frostbite](reader-frostbite.md) | wie Tabellen, Bundles, Meshes, Gelände und Texturen gelesen werden und wie jedes geprüft wurde |
| [Bedingungen und Lizenz](terms.md) | EAs Spiel, Oodle, die Quellen, ein Projekt für sich |
| [Befehlsreferenz](../cli-reference.md) | jede Option, aus dem Code erzeugt |
| [Diese Doku pflegen](maintaining.md) | die Checkliste für jedes Release |

## Verwandt {#related}

- Der 3DHeat-Viewer: [github.com/Holdi601/3DHeat](https://github.com/Holdi601/3DHeat),
  Dokumentation unter [holdi601.github.io/3DHeat](https://holdi601.github.io/3DHeat/).
- [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/): die Leser der
  Spiel-Engine und der glTF-Schreiber, auf denen dieses Werkzeug aufbaut; seine `levels`,
  `level` und `identify` starten dieses Werkzeug, wenn es installiert ist.

## Die 3DHeat-Werkzeuge {#the-3dheat-tools}

| Werkzeug | Was es tut | Code | Doku |
|---|---|---|---|
| 3DHeat-Viewer | zeigt die Daten: Heatmaps, Rennanalyse, Match-Auswertung | [3DHeat](https://github.com/Holdi601/3DHeat) | [Doku](https://holdi601.github.io/3DHeat/) |
| GameFiles | Levels und Strecken aus den eigenen Dateien eines Spiels | [3DHeat-GameFiles](https://github.com/Holdi601/3DHeat-GameFiles) | [Doku](https://holdi601.github.io/3DHeat-GameFiles/) |
| GameCapture | Rundentelemetrie und Levels, aus Gameplay-Videos rekonstruiert | [3DHeat-GameCapture](https://github.com/Holdi601/3DHeat-GameCapture) | [Doku](https://holdi601.github.io/3DHeat-GameCapture/) |
| Unreal Exporter | ein Unreal-Editor-Plugin: ein Level als eine `.glb` | [3DHeat-UnrealExporter](https://github.com/Holdi601/3DHeat-UnrealExporter) | [Doku](https://holdi601.github.io/3DHeat-UnrealExporter/) |
| CS2 | Counter-Strike-2-Demos und Karten | [3DHeat-CS2](https://github.com/Holdi601/3DHeat-CS2) | [Doku](https://holdi601.github.io/3DHeat-CS2/) |
| Watcher | zeichnet auf, was Spiele veröffentlichen, während du spielst | [3DHeat-Watcher](https://github.com/Holdi601/3DHeat-Watcher) | [Doku](https://holdi601.github.io/3DHeat-Watcher/) |
| Ext-WarThunder | War-Thunder-Replays | [3DHeat-Ext-WarThunder](https://github.com/Holdi601/3DHeat-Ext-WarThunder) | [Doku](https://holdi601.github.io/3DHeat-Ext-WarThunder/) |
| Ext-WoT | World-of-Tanks-Replays | [3DHeat-Ext-WoT](https://github.com/Holdi601/3DHeat-Ext-WoT) | [Doku](https://holdi601.github.io/3DHeat-Ext-WoT/) |
| Ext-WoWs | World-of-Warships-Replays | [3DHeat-Ext-WoWs](https://github.com/Holdi601/3DHeat-Ext-WoWs) | [Doku](https://holdi601.github.io/3DHeat-Ext-WoWs/) |
| Ext-Squad | Squad-Serverdemos | [3DHeat-Ext-Squad](https://github.com/Holdi601/3DHeat-Ext-Squad) | [Doku](https://holdi601.github.io/3DHeat-Ext-Squad/) |
| Ext-DCS | DCS-World-Karten als 3D-Levels | [3DHeat-Ext-DCS](https://github.com/Holdi601/3DHeat-Ext-DCS) | [Doku](https://holdi601.github.io/3DHeat-Ext-DCS/) |
| Ext-IL2 | IL-2-Sturmovik-Karten als 3D-Levels | [3DHeat-Ext-IL2](https://github.com/Holdi601/3DHeat-Ext-IL2) | [Doku](https://holdi601.github.io/3DHeat-Ext-IL2/) |
| Ext-Dota | die Dota-2-Karte als 3D-Level | [3DHeat-Ext-Dota](https://github.com/Holdi601/3DHeat-Ext-Dota) | [Doku](https://holdi601.github.io/3DHeat-Ext-Dota/) |
| Ext-DotaReplay | Dota-2-Replays als Tabellen | [3DHeat-Ext-DotaReplay](https://github.com/Holdi601/3DHeat-Ext-DotaReplay) | [Doku](https://holdi601.github.io/3DHeat-Ext-DotaReplay/) |
| Ext-Riot | League-of-Legends- und VALORANT-Replays | [3DHeat-Ext-Riot](https://github.com/Holdi601/3DHeat-Ext-Riot) | [Doku](https://holdi601.github.io/3DHeat-Ext-Riot/) |
| Ext-Forza | Forza-Horizon-Strecken und -Autos | [3DHeat-Ext-Forza](https://github.com/Holdi601/3DHeat-Ext-Forza) | [Doku](https://holdi601.github.io/3DHeat-Ext-Forza/) |
| Ext-Battlefield | Battlefield-6-Levels als 3D-Levels | [3DHeat-Ext-Battlefield](https://github.com/Holdi601/3DHeat-Ext-Battlefield) | [Doku](https://holdi601.github.io/3DHeat-Ext-Battlefield/) |
| Ext-BeamNG | BeamNG.drive-Strecken rund um deine Runden | [3DHeat-Ext-BeamNG](https://github.com/Holdi601/3DHeat-Ext-BeamNG) | [Doku](https://holdi601.github.io/3DHeat-Ext-BeamNG/) |
| Ext-ACRally | Assetto-Corsa-Rally-Etappen rund um deine Runden | [3DHeat-Ext-ACRally](https://github.com/Holdi601/3DHeat-Ext-ACRally) | [Doku](https://holdi601.github.io/3DHeat-Ext-ACRally/) |
| Ext-Reforger | Arma-Reforger-Welten als 3D-Levels | [3DHeat-Ext-Reforger](https://github.com/Holdi601/3DHeat-Ext-Reforger) | [Doku](https://holdi601.github.io/3DHeat-Ext-Reforger/) |
| Ext-R6 | Rainbow-Six-Siege-Match-Replays | [3DHeat-Ext-R6](https://github.com/Holdi601/3DHeat-Ext-R6) | [Doku](https://holdi601.github.io/3DHeat-Ext-R6/) |
