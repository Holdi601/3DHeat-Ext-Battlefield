---
title: "Startseite"
nav_order: 1
lang: "de"
source: index.md
source_hash: "52e652b3dd93"
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

Neu auf der Kommandozeile? Lies zuerst [Bevor du anfängst](before-you-start.md). Du brauchst
Python 3.10 oder neuer, [3DHeat GameFiles](https://holdi601.github.io/3DHeat-GameFiles/) (die
Bibliothek, mit der dieses Werkzeug liest) und ein installiertes Battlefield 6. Führe diese
Befehle in dem Ordner aus, den du geklont oder entpackt hast:

```bash
python -m pip install -e .                                  # installiert heat3d-battlefield-maps und GameFiles dazu
heat3d-battlefield-maps levels                              # wo das Spiel liegt, und seine Levels
heat3d-battlefield-maps level <level> -o level.glb          # ein Level, einfarbig
heat3d-battlefield-maps level <level> -o level.glb --textures --ground-texture   # mit Farbe
```

`levels` beginnt mit einer Zeile wie `<n> levels in D:\Games\Steam\steamapps\common\Battlefield 6`
und listet je Zeile ein Level; `level` endet mit `-> level.glb (<n> MB)`. Lade dann
`level.glb` im Bereich **Hintergrund / Level** des Viewers
([Level laden](https://holdi601.github.io/3DHeat/levels.html)).

Das Level wird aus den Dateien des Spiels gebaut und bleibt **auf deinem Rechner**: zum
Ansehen, nicht zum Teilen oder Veröffentlichen ([Bedingungen und Lizenz](terms.md)).

## Seiten {#pages}

| Seite | Was sie behandelt |
|---|---|
| [Bevor du anfängst](before-you-start.md) | Python, GameFiles, ein Terminal, ein erster Lauf |
| [Battlefield-6-Level: levels und level](level-battlefield.md) | die Levels auflisten, jede Option eines Exports, seine Teile, die zu erwartenden Größen |
| [Eine Datei erkennen: identify](identify.md) | ob eine Datei eine Frostbite-Inhaltstabelle ist und was sie enthält |
| [Frostbite](reader-frostbite.md) | wie Tabellen, Bundles, Meshes, Gelände und Texturen gelesen werden und wie jedes geprüft wurde |
| [Bedingungen und Lizenz](terms.md) | EAs Spiel, Oodle, die Quellen, warum dies ein eigenes Paket ist |
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
