# Cloud Run Readiness Status

**WICHTIGER HINWEIS:**
`sandbox_limited: true`
*Der Deployment-Status wird nur vorbereitend dokumentiert.*

## Aktuelle Phase: Vorbereitung
Das Projekt bereitet Cloud Run aktuell **nur vor**, es wird **nicht** deployt.

Zu prüfende/relevante Dateien für die Bereitstellung:
- `Dockerfile.cloudrun`
- `cloudrun-service.yaml`
- `requirements-lock.txt`

## Provider und Umgebung
- **Cloud LLM:** Gemini (als Cloud Provider gelistet)
- **Lokales LLM:** Ollama bleibt strikt lokal-only.
- **Secrets:** Es gibt Secret Manager Hinweise. Keine Secrets im Klartext ablegen!

Es finden keine Cloud-Deployments durch Jules statt.
