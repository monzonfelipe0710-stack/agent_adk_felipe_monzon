# Asistente de IA para modelos locales — Google ADK

Agente desarrollado con Python y Google Agent Development Kit (ADK) para ayudar a estudiar y preparar la ejecución local de modelos de lenguaje. Está basado en los contenidos de **Fundamentos de Agentes de Inteligencia Artificial** y **Cuantización e Inferencia Local de LLMs**.

No es solamente un chatbot: el modelo decide cuándo utilizar herramientas Python para buscar información, consultar una base de conocimiento y estimar memoria de modelos.

## Funcionalidades y herramientas

El agente dispone de cuatro herramientas con responsabilidades diferentes:

1. **`buscar_en_web`**: realiza búsquedas web con DuckDuckGo (paquete `ddgs`). Devuelve resultados con título, URL y resumen. Valida la consulta y la cantidad de resultados.
2. **`consultar_base_conocimiento`**: busca conceptos en una base local incluida en `knowledge_base.json`. Permite responder preguntas sobre agentes, ADK, cuantización, GGUF, Ollama, precisión y memoria sin inventar datos.
3. **`estimar_memoria_modelo`**: calcula la memoria teórica de los pesos según cantidad de parámetros y precisión (FP32, FP16, BF16, INT8 o INT4). Informa que el consumo real será mayor por contexto, activaciones y overhead.
4. **`comparar_precisiones`**: compara varias precisiones para una misma cantidad de parámetros e informa ahorro aproximado respecto de FP16.

El agente puede combinar herramientas. Por ejemplo, puede consultar la base local para explicar Q4_K_M y luego buscar información actualizada en la web si el usuario lo solicita.

## Arquitectura

```
Usuario
  |
  v
Google ADK Agent (LiteLLM + Ollama)
  |
  +--> buscar_en_web ------------------> DuckDuckGo
  +--> consultar_base_conocimiento ----> knowledge_base.json
  +--> estimar_memoria_modelo ---------> cálculo Python
  +--> comparar_precisiones -----------> cálculo Python
  |
  v
Respuesta basada en los resultados de las herramientas
```

## Requisitos

- Python 3.10 o superior.
- [Ollama](https://ollama.com/) instalado y ejecutándose.
- Un modelo disponible en Ollama. El valor predeterminado es `qwen3.5:4b`; se puede cambiar mediante la variable `OLLAMA_MODEL`.
- Conexión a Internet para la herramienta de búsqueda web.
- `uv` recomendado para crear el entorno e instalar dependencias.

> El modelo se ejecuta a través de Ollama y LiteLLM. La disponibilidad del modelo depende de la biblioteca de modelos y del hardware del equipo. La estimación de memoria de la herramienta calcula solamente los pesos, no garantiza que un modelo entre en la RAM/VRAM disponible.

## Instalación en Windows

Clonar el repositorio:

```powershell
git clone https://github.com/monzonfelipe0710-stack/agent_adk_felipe_monzon.git
cd agent_adk_felipe_monzon
```

Crear y activar un entorno virtual:

```powershell
uv venv
.\\.venv\\Scripts\\activate
```

Instalar dependencias:

```powershell
uv pip install -r requirements.txt
```

Instalar y ejecutar Ollama. Luego descargar el modelo:

```powershell
ollama pull qwen3.5:4b
ollama list
```

Copiar la configuración de ejemplo:

```powershell
Copy-Item .env.example .env
```

Si se utiliza otro modelo, editar `.env` y establecer su nombre exacto en `OLLAMA_MODEL`. Por ejemplo, para un modelo ya descargado llamado `gemma4:31b-cloud`, usar `ollama_chat/gemma4:31b-cloud` como identificador interno de LiteLLM mediante `OLLAMA_MODEL=gemma4:31b-cloud`. El equipo debe tener acceso al modelo indicado.

## Instalación en Linux / macOS

```bash
git clone https://github.com/monzonfelipe0710-stack/agent_adk_felipe_monzon.git
cd agent_adk_felipe_monzon
uv venv
source .venv/bin/activate
uv pip install -r requirements.txt
cp .env.example .env
ollama pull qwen3.5:4b
```

## Ejecución de la interfaz web

Desde la carpeta que contiene el paquete `agent_adk_felipe_monzon`, ejecutar:

```bash
adk web
```

Abrir [http://localhost:8000](http://localhost:8000) en el navegador y seleccionar el agente `agent_adk_felipe_monzon`.

También se puede probar desde la terminal:

```bash
adk run agent_adk_felipe_monzon
```

## Ejemplos para probar las herramientas

- **Base de conocimiento:** "¿Qué diferencia hay entre FP16 y BF16?"
- **Estimación:** "¿Cuánta memoria ocupan los pesos de un modelo de 7 mil millones de parámetros en FP16?"
- **Comparación:** "Compará FP16, INT8 e INT4 para un modelo de 7B."
- **Búsqueda web:** "Buscá información actualizada sobre las novedades de Ollama."
- **Uso combinado:** "Explicame qué es GGUF según la base local y buscá documentación oficial para ampliar."

Para comprobar la selección de herramientas, realizar preguntas de cada tipo y observar en la interfaz de ADK los eventos de ejecución de herramientas y sus resultados.

## Validaciones y manejo de errores

- Las consultas vacías o demasiado largas se rechazan con un mensaje claro.
- La cantidad de resultados de búsqueda se limita a un rango válido.
- Las precisiones y cantidades de parámetros se validan antes de calcular.
- Si una búsqueda no devuelve resultados, la herramienta informa que no encontró coincidencias.
- Los errores de conexión de DuckDuckGo y las excepciones se devuelven como mensajes controlados, sin interrumpir la conversación.
- Si el modelo no está disponible, revisar que Ollama esté iniciado, que el modelo esté descargado y que `OLLAMA_MODEL` coincida con el nombre local.

## Estructura del proyecto

```
agent_adk_felipe_monzon/
├── agent_adk_felipe_monzon/
│   ├── __init__.py
│   ├── agent.py
│   ├── tools.py
│   └── knowledge_base.json
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

## Modelo utilizado

Google ADK coordina el agente y las herramientas. LiteLLM permite conectar ADK con Ollama mediante el identificador `ollama_chat/<nombre-del-modelo>`. Por defecto se configura `qwen3.5:4b`, pero puede cambiarse sin modificar el código.

## Alcance

La estimación de memoria es teórica: parámetros × bits por parámetro ÷ 8. No incluye caché KV, contexto, activaciones, buffers ni overhead del runtime. Los resultados web dependen del servicio de búsqueda y de la conexión a Internet. La base local es editable y puede ampliarse agregando entradas a `knowledge_base.json`.

## Autor

Felipe Monzón
