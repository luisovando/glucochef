> Detalla en esta sección los prompts principales utilizados durante la creación del proyecto, que justifiquen el uso de asistentes de código en todas las fases del ciclo de vida del desarrollo. Esperamos un máximo de 3 por sección, principalmente los de creación inicial o  los de corrección o adición de funcionalidades que consideres más relevantes.
Puedes añadir adicionalmente la conversación completa como link o archivo adjunto si así lo consideras


## Índice

1. [Descripción general del producto](#1-descripción-general-del-producto)
2. [Arquitectura del sistema](#2-arquitectura-del-sistema)
3. [Modelo de datos](#3-modelo-de-datos)
4. [Especificación de la API](#4-especificación-de-la-api)
5. [Historias de usuario](#5-historias-de-usuario)
6. [Tickets de trabajo](#6-tickets-de-trabajo)
7. [Pull requests](#7-pull-requests)

---

## 1. Descripción general del producto

**Prompt 1:**
Estoy desarrollando una aplicación que ayuda a pacientes diabéticos a planificar comidas personalizadas (basadas en sus gustos y necesidades alimenticias) y dar seguimiento a sus estudios de laboratorio, con recomendaciones de IA basadas en su perfil glucémico.

Estoy buscando el MVP de este proyecto, para esto necesito:

1. Un análisis de la competencia, tablas de features, que falta, que sobra.
2. Lee threads de reddit y otras redes sociales, reviews de apps existentes en app store y google play. Busca los patrones de queja mas repetidos.
3. Revisa artículos académicos sobre la efectividad de apps de diabetes.

**Prompt 2:**
Sintetizalo como un requerimiento que alguien a alto nivel (CEO, Cliente) entregaría a un CPO.

Entregamelo en formato Markdown con una estructura clara y organizada.

**Prompt 3:**

---

## 2. Arquitectura del Sistema

### **2.1. Diagrama de arquitectura:**

**Prompt 1:**
Crea la skill glucochef-c4-architecture con niveles Context y Container requeridos, Component opcional; usa Mermaid como lenguaje de diagrama; incluye convenciones, diagramas completos con nodos PHI marcados, tabla de decisiones por nivel, y sección de anti-patrones.

**Prompt 2:**

**Prompt 3:**

### **2.2. Descripción de componentes principales:**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.3. Descripción de alto nivel del proyecto y estructura de ficheros**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.4. Infraestructura y despliegue**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.5. Seguridad**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

### **2.6. Tests**

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 3. Modelo de Datos

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 4. Especificación de la API

**Prompt 1:**

- **Context**: Phase 5 (PHI encryption + audit logging) is complete. All backend tests pass. The `NutritionalProfile` model and its child tables (`medications`, `allergies`, `intolerances`, `dietary_preferences`) exist, and `RejectedIngredient` is implemented. The `AuditAction` enum currently contains `read`, `write`, and `delete`.
- **Prompt**:
  > Execute `@glucochef-phase-executor Phase 6 / AI4-43`. Implement `POST /onboarding` so that it accepts diabetes type, medications, allergies, intolerances, rejected foods, and cultural preferences, persists a `NutritionalProfile`, is protected by `get_current_patient`, and writes audit entries. Follow TDD Red→Green for each acceptance criterion: authenticated POST returns 201 with the profile id; unauthenticated POST returns 401; posting twice for the same patient updates the existing profile instead of duplicating it.
- **Output**: `backend/app/schemas/onboarding.py`, `backend/app/api/routes/onboarding.py`, registration in `backend/app/main.py`, `backend/tests/test_onboarding.py`, and Alembic migration `e3d89e75cb1c` adding the `consent` value to the `audit_action` enum.
- **Design notes**:
  - Explicit consent is enforced by a Pydantic validator on `OnboardingRequest.consent` and recorded on the `Patient` record.
  - The endpoint writes two audit entries (`write onboarding`, `consent`) in the same transaction as the profile upsert.
  - Related child rows are replaced explicitly via `delete(...).where(...)` to avoid triggering lazy loads inside the async test client.

**Prompt 2:**

**Prompt 3:**

---

### 5. Historias de Usuario

**Prompt 1:**
Necesito un PRD optimizado para agentes de IA (Cursor/Claude Code) para Glucochef.

Estructura el PRD en fases secuenciales donde cada fase:

1. Tenga dependencias explícitas de fases anteriores
2. Incluya criterios de aceptación verificables
3. Defina explícitamente qué NO debe cambiar
4. Sea completable en 5-15 minutos por un agente

Incluye también una sección "Non-goals" con lo que está fuera de alcance.

Generalo como un archivo markdown en Ingles dentro de docs/glucochef-prd.md 

**Prompt 2:**
Evalúa las user stories generadas contra los criterios INVEST y sugiere mejoras si es que existen.

**Prompt 3:**

---

### 6. Tickets de Trabajo

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**

---

### 7. Pull Requests

**Prompt 1:**

**Prompt 2:**

**Prompt 3:**
