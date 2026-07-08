# Scientific OS: Hardware Constraints & Runtime Realities

Dieser Audit-Bericht konsolidiert die kritischen architektonischen Herausforderungen beim Übergang von einer abstrakten Compiler-Ebene (Scientific Compiler) zu einer physikalischen Laufzeit-Ebene (Anti-Gravity Bridge). Die Integration lokaler High-Performance-Modelle (wie Gemma 4 via Ollama) und rechenintensiver 3D-Pipelines (Meshroom, Blender) erfordert strikte Ressourcengrenzen und deterministische Sicherheitsnetze.

## 1. JIT-Guarding vs. Statische Kostenmodelle
Der Scientific Compiler operiert auf Basis von ASTs und DAGs (Directed Acyclic Graphs).
- **Das Problem:** Statische Laufzeit- oder Speicherschätzungen für Prozesse wie Photogrammetrie (Meshroom) oder Raytracing (Blender Cycles) sind bei heterogenen Datensätzen unmöglich.
- **Die Lösung (JIT-Guarding):** Die Anti-Gravity Bridge darf Compiler-Pläne nicht blind ausführen. Sie muss eine *Just-in-Time* (JIT) Validierung durchführen. Wenn der Compiler Node A an GPU 0 delegiert, muss die Bridge unmittelbar vor Ausführung prüfen, ob der geforderte VRAM tatsächlich frei ist, und andernfalls das Scheduling anpassen.

## 2. VRAM Time-Sharing & Local LLM Isolation
Die Nutzung lokaler LLMs (z.B. Gemma 4) für Function Calling oder Agenten-Schleifen konkurriert direkt mit der 3D-Pipeline.
- **Das Problem:** Ein geladenes Gemma 4 (GGUF/QAT) blockiert signifikante Teile des VRAMs. Startet zeitgleich ein Meshroom-SfM-Prozess, kollabiert das System mit einem Out-of-Memory (OOM) Fehler oder drosselt über den Unified Memory hart.
- **Die Lösung:** Die Bridge agiert als strikter Ressourchen-Manager. Local LLMs dürfen nicht als "Always-On"-Dienste laufen. Die Bridge muss aggressives VRAM Time-Sharing erzwingen: Modelle via API entladen, bevor GPU-intensive 3D-Jobs gestartet werden, und erst danach für die Auswertung neu laden.

## 3. Logische vs. Empirische Provenance
Das Zusammenführen von Compiler- und Bridge-Metadaten in einem gemeinsamen Provenance-Manifest ist essenziell für die Auditierung, darf aber keine falschen Reproduzierbarkeitsversprechen machen.
- **Das Problem:** Bitweiser Determinismus ist bei GPU-Floating-Point-Operationen (cuDNN, Blender Cycles) oder stochastischen LLM-Outputs de facto unmöglich, selbst bei identischen Seeds und Hashes.
- **Die Lösung:** Das System muss streng zwischen *Logischer Provenance* (welche Befehle und Parameter wurden übergeben) und *Empirischer Drift* (Hardware-Temperaturen, Thread-Scheduling, Treiber-Versionen) unterscheiden. Das Manifest dokumentiert den Prozess, garantiert aber keine mathematisch identischen Binär-Artefakte.

## 4. Strikte LLM-Output Validierung
LLMs können als intelligente Parser eingesetzt werden, ihre Outputs bleiben jedoch probabilistisch.
- **Das Problem:** Ein stochastisch generierter Parameter-Block (z.B. ein Blender-Python-Snippet oder Meshroom-CLI-Flags) kann durch minimale Syntaxfehler die gesamte Pipeline zum Absturz bringen.
- **Die Lösung:** Der Compiler/die Bridge darf LLM-Outputs niemals direkt ("raw") ausführen. Jeder Payload muss durch eine harte, deterministische Pydantic-/JSON-Schema-Validierung laufen. Schlägt diese fehl, wird nicht endlos reflektiert (Kosten- und Zeit-Faktor), sondern ein deterministischer Fallback ausgelöst.

## Fazit für die Architektur
Die Rollentrennung muss kompromisslos sein:
1. **Compiler:** Hardware-agnostisch. Erzeugt rein logische, typgeprüfte AST/DAGs.
2. **Bridge:** Die physische Sandbox. Sie verwaltet den VRAM, validiert Ressourcen JIT, steuert den Ollama-Lifecycle und kapselt die Adapter-Ausführung.
