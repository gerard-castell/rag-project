Este es el roadmap detallado para ir de "Cero" a "Senior RAG Engineer". El enfoque es construir un sistema local **contenierizado (Docker)** que sea idéntico a una arquitectura de producción en nube, permitiendo un despliegue futuro sin reescribir código.

Utilizaremos **"Iteraciones Ágiles" (Sprints)**. No intentes hacerlo todo a la vez. Cada sprint debe terminar con un contenedor funcional.

---

### Arquitectura de Referencia (Stack Local para Prod)

Antes de empezar, define tu `docker-compose.yml`. Este será tu entorno de "Producción Simulado":

1. **API Service (Tú código):** Python 3.11+, FastAPI, LangGraph.
2. **Vector DB:** **Qdrant**. (Estándar de mercado actual por performance (Rust), filtrado de metadatos y API amigable. Alternativa: Weaviate).
3. **Observabilidad:** **Arize Phoenix** (open source y local). Es vital para visualizar las trazas de LangGraph y los retrievals.
4. **Cache:** **Redis**. Para caché semántica y persistencia de memoria de hilos (checkpoints).

---

### Sprint 1: La Base Sólida (ETL & Ingesta "No-Naive")

*Objetivo: Entender que la calidad del RAG depende en un 70% de cómo limpias y guardas los datos.*

**Conceptos a aprender:**

* **Embeddings:** Qué son y por qué `text-embedding-3-small` (OpenAI) o `bge-m3` (Open Source/Local) son estándares.
* **Vector Database:** Colecciones, Payloads (metadatos) y Puntos.

**Tareas Técnicas:**

1. **Pipeline de Ingesta (ETL):** Crea un script Python (separado de la API) que lea PDFs/Markdowns.
* *Nivel Senior:* No uses `Unstructured` genérico. Usa **LlamaParse** (excelente para tablas complejas) o implementa una limpieza manual con Regex. La basura en el texto = alucinación.


2. **Chunking Semántico (No por caracteres):**
* Implementa `RecursiveCharacterTextSplitter` de LangChain como base.
* *Mejora:* Añade un "Rolling Window" (solapamiento) para no cortar frases a la mitad.
* **Metadata Enrichment:** A cada chunk, añádele metadatos: `{ "source": "doc1.pdf", "page": 3, "section_title": "Garantías" }`. Esto es crucial para el filtrado posterior.


3. **Indexado:** Sube los vectores a Qdrant corriendo en Docker.

**Resultado entregable:** Un script que ingesta documentos y un Dashboard de Qdrant donde puedes ver tus vectores y metadatos.

---

### Sprint 2: Retrieval Avanzado (Búsqueda Híbrida)

*Objetivo: Solucionar el problema de "El usuario buscó un ID exacto y el modelo vectorial falló".*

**Conceptos a aprender:**

* **Dense retrieval:** Búsqueda por significado (Vectores).
* **Sparse retrieval (BM25/Splade):** Búsqueda por palabras clave exactas.
* **Reciprocal Rank Fusion (RRF):** Cómo combinar ambos resultados.

**Tareas Técnicas:**

1. **Configurar Hybrid Search en Qdrant:** Habilita vectores densos y vectores *sparse* en la misma colección.
2. **FastAPI Endpoint:** Crea una ruta `/search` (no chat todavía).
3. **Implementación:**
* Tu código debe convertir la query del usuario en Vector (Embedding) Y en Sparse Vector (BM25).
* Lanza la búsqueda híbrida a Qdrant.


4. **Evaluación manual:** Busca un término muy técnico (ej: "Error 504") y una pregunta conceptual (ej: "¿Cómo funciona el sistema?"). La búsqueda híbrida debe traer los documentos correctos para ambos casos.

**Resultado entregable:** Una API que devuelve JSONs con los fragmentos de texto más relevantes, ordenados por score híbrido.

---

### Sprint 3: Reranking & Context Assembly

*Objetivo: "Precision is King". Pasar de traer 20 documentos mediocres a 5 excelentes.*

**Conceptos a aprender:**

* **Lost in the Middle:** Los LLMs ignoran información si está en medio de un contexto muy largo.
* **Cross-Encoders:** Modelos que leen (Query + Documento) y puntúan la relevancia real. Son lentos pero precisos.

**Tareas Técnicas:**

1. **Retrieval Amplio:** Configura el paso anterior para traer 25 documentos (High Recall).
2. **Implementar Reranker:**
* Integra `bge-reranker-v2-m3` (local, pesado) o Cohere Rerank (API, estándar de industria).
* Pasa los 25 docs por el Reranker.
* Quédate con el Top 5.


3. **Generación (V1):** Envía esos 5 docs + la query al LLM con un Prompt de Sistema estricto: *"Responde solo usando el contexto proporcionado"*.Revi

**Resultado entregable:** Un endpoint `/chat` simple que responde con alta precisión.

---

### Sprint 4: Arquitectura de Agente con LangGraph

*Objetivo: Manejar flujos complejos, bucles y correcciones. El verdadero "Seniority".*

**Conceptos a aprender:**

* **Grafos de Estado:** Nodos, aristas y estado compartido.
* **Conditional Edges:** Decidir el siguiente paso basado en el output del LLM.

**Tareas Técnicas (El Core del Proyecto):**
Diseña un grafo en LangGraph con estos nodos:

1. **Nodo `Retrieve`:** Ejecuta la búsqueda híbrida.
2. **Nodo `Grade`:** Un LLM ligero (ej. GPT-4o-mini o Llama-3-8b) evalúa si los documentos recuperados son relevantes para la pregunta.
* *Si NO son relevantes:* Pasa a un nodo `Rewrite Query` (transforma la pregunta) y vuelve a buscar.
* *Si SI son relevantes:* Pasa al nodo `Generate`.


3. **Nodo `Generate`:** Genera la respuesta final.
4. **Checkpointer:** Usa Redis o Postgres para guardar el `thread_id` y mantener la conversación en memoria.

**Resultado entregable:** Un sistema que se "auto-corrige". Si preguntas algo raro, verás en los logs que el sistema intenta buscar dos veces con términos distintos.

---

### Sprint 5: Evaluación "Eval-Driven" (RAGAS)

*Objetivo: Métricas cuantitativas para poner en tu CV/Portfolio.*

**Conceptos a aprender:**

* **Golden Dataset:** Pares de Pregunta/Respuesta ideal creados por humanos (o generados sintéticamente).
* **Métricas:** Faithfulness, Answer Relevance, Context Recall.

**Tareas Técnicas:**

1. **Generación de Test Set:** Usa un LLM para generar 20 preguntas basadas en tus documentos de prueba.
2. **Integración de RAGAS:**
* Crea un script que corra tu pipeline de RAG sobre esas 20 preguntas.
* Usa RAGAS para comparar la respuesta de tu sistema vs la respuesta ideal.


3. **CI/CD (Simulado):** Configura que si la métrica de "Faithfulness" baja del 0.8, el "despliegue" (el script) falle.

**Resultado entregable:** Un informe HTML o Markdown generado automáticamente con las métricas de tu RAG.

---

### Sprint 6: Optimización de Producción

*Objetivo: Latencia y Coste.*

**Tareas Técnicas:**

1. **Async Streaming:** Asegura que tu endpoint de FastAPI use `StreamingResponse` para enviar tokens al frontend en tiempo real.
2. **Semantic Cache:** Antes de llamar a LangGraph, consulta en Redis si esa pregunta (o una semánticamente idéntica) ya se hizo. Si es así, devuelve la respuesta guardada.

---

### Resumen del Proyecto para Portfolio

Al final tendrás un repositorio con esta estructura (muy valorada profesionalmente):

```text
/src
  /app (FastAPI)
  /graph (LangGraph Logic)
  /etl (Ingestion Pipelines)
  /evals (RAGAS scripts)
/infra
  docker-compose.yml (Qdrant, Redis, Phoenix)
README.md (Con diagrama de arquitectura y métricas de evaluación)

```

Este camino te obliga a tocar: Ingesta sucia, Vectores, Grafos de control, Evaluación y Optimización. Exactamente lo que un Senior debe dominar.