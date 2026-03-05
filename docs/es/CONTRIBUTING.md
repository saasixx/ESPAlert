# Contribuir a ESPAlert

> 🇪🇸 **Español** | [🇬🇧 English](../../CONTRIBUTING.md)

¡Gracias por tu interés en contribuir a **ESPAlert**! Este documento explica el flujo
de trabajo, las convenciones del proyecto y cómo enviar tus cambios de forma eficiente.

---

## Tabla de contenidos

- [Código de conducta](#código-de-conducta)
- [Primeros pasos](#primeros-pasos)
- [Entorno de desarrollo](#entorno-de-desarrollo)
- [Flujo de trabajo con Git](#flujo-de-trabajo-con-git)
- [Convenciones de código](#convenciones-de-código)
- [Tests](#tests)
- [Pull Requests](#pull-requests)
- [Reportar bugs](#reportar-bugs)
- [Solicitar funcionalidades](#solicitar-funcionalidades)

---

## Código de conducta

Este proyecto se rige por el [Código de Conducta](../../CODE_OF_CONDUCT.md).
Al participar, te comprometes a respetar sus normas.

## Primeros pasos

1. Haz **fork** del repositorio.
2. Clona tu fork:
   ```bash
   git clone https://github.com/<tu-usuario>/ESPAlert.git
   cd ESPAlert
   ```
3. Crea una rama descriptiva:
   ```bash
   git checkout -b feat/mi-nueva-funcionalidad
   ```

## Entorno de desarrollo

### Opción A — Docker (recomendada)

```bash
cp .env.example .env          # Ajusta los valores si es necesario
docker compose up --build      # Levanta toda la pila
```

- **Frontend**: http://localhost:3000
- **API + Docs**: http://localhost:8000/docs

### Opción B — Local (sin Docker para el frontend)

```bash
# Levanta solo los servicios de infraestructura
docker compose up db redis api worker beat -d

# Instala dependencias del frontend
npm install
npm run dev
```

### Requisitos

| Herramienta | Versión mínima |
|------------|----------------|
| Node.js    | 20 LTS         |
| Python     | 3.12           |
| Docker     | 24+            |
| npm        | 10+            |

## Flujo de trabajo con Git

Utilizamos [Conventional Commits](https://www.conventionalcommits.org/es/):

```
<tipo>(<alcance>): <descripción breve>

[cuerpo opcional]

[pie de página opcional]
```

### Tipos permitidos

| Tipo       | Cuándo usarlo                              |
|------------|-------------------------------------------|
| `feat`     | Nueva funcionalidad                       |
| `fix`      | Corrección de bug                         |
| `docs`     | Solo documentación                        |
| `style`    | Formato (sin cambios lógicos)             |
| `refactor` | Refactorización sin cambio funcional      |
| `test`     | Añadir o corregir tests                   |
| `chore`    | Tareas de mantenimiento (CI, deps, etc.)  |
| `perf`     | Mejora de rendimiento                     |

### Ejemplos

```
feat(mapa): añadir capa de incendios forestales
fix(api): corregir filtro de eventos por radio GPS
docs(readme): actualizar instrucciones de instalación
```

## Convenciones de código

### Python (Backend — `apps/api/`)

- **Linter**: [Ruff](https://docs.astral.sh/ruff/) con las reglas por defecto.
- **Formato**: Ruff format (compatible con Black).
- **Docstrings**: En inglés, estilo Google.
- **Tipos**: Usar type hints en todas las funciones públicas.

```bash
# Ejecutar linter
pip install ruff
ruff check apps/api/
ruff format apps/api/
```

### TypeScript/React (Frontend — `apps/web/`)

- **Linter**: ESLint con la config de Next.js.
- **Formato**: Prettier (configurado vía ESLint).
- **Componentes**: Functional components con hooks.
- **Nombrado**: PascalCase para componentes, camelCase para hooks y utilidades.

```bash
npm run lint
```

### Idioma del código

- **Interfaz de usuario**: Español (principal), inglés disponible vía i18n.
- **Código fuente** (variables, funciones, clases): En **inglés**.
- **Comentarios y docstrings**: En **inglés**.
- **Commits y PRs**: Se prefiere inglés, se acepta español.

## Tests

### Backend

```bash
cd apps/api
pip install -r requirements.txt pytest httpx
pytest -v
```

### Frontend

```bash
npm run turbo lint --filter=web
npm run turbo build --filter=web
```

## Pull Requests

1. Asegúrate de que tu rama está actualizada con `main`.
2. Verifica que los tests pasan localmente.
3. Escribe una descripción clara del cambio.
4. Referencia el issue relacionado (si aplica): `Closes #123`.
5. Solicita revisión de al menos un maintainer.

### Checklist para el PR

- [ ] Mi código sigue las convenciones del proyecto.
- [ ] He añadido tests para los cambios (si aplica).
- [ ] La documentación está actualizada.
- [ ] Los commits siguen el formato Conventional Commits.
- [ ] He probado los cambios localmente con Docker.

## Reportar bugs

Usa la plantilla de [Bug Report](.github/ISSUE_TEMPLATE/bug_report.md) y proporciona:

1. **Descripción** clara del problema.
2. **Pasos para reproducir** el error.
3. **Comportamiento esperado** vs. **actual**.
4. **Entorno**: navegador, SO, versión de Docker.
5. **Capturas de pantalla** o logs relevantes.

## Solicitar funcionalidades

Usa la plantilla de [Feature Request](.github/ISSUE_TEMPLATE/feature_request.md) e incluye:

1. **Problema** que resuelve la funcionalidad.
2. **Solución propuesta** con el mayor detalle posible.
3. **Alternativas** que hayas considerado.
4. **Mockups o diagramas** si aplica.

---

> **¿Dudas?** Abre un [Discussion](../../discussions) en GitHub o contacta con los maintainers.

¡Gracias por hacer de ESPAlert un proyecto mejor! 🛡️
