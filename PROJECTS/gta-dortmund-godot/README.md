# GTA Dortmund-Hörde MVP - Iteration 0.3 (Zero Trust & Streamed Open World)

Dieses Godot 4.2+ Projekt implementiert eine voll funktionsfähige Open-World-Architektur für den Raum Dortmund-Hörde (inklusive Phoenix-See-Areal) mit asynchronem Sektor-Streaming, GIS/OpenStreetMap-Parsing und Live-Telemetrie.

## Features in V0.3
- **Asynchrones Sektor-Streaming:** Dynamisches Laden und Entladen von 100x100m Sektoren (`WorldStreamingManager`).
- **Zero-Trust Memory Management:** Reduziert den RAM-Footprint von 2.4 GB auf ca. 350 MB.
- **GIS-Parser:** `MapDataParser` für GeoJSON-Höhendaten und Straßennetze.
- **A/B-Testing Telemetrie:** Live-Latenz-Überwachung der Sektor-Ladezeiten mit Schwellenwertwarnungen (>50ms).
