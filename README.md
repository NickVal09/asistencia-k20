# Sistema de Control de Asistencia K20 (ZKTeco)

Sistema web profesional para la gestión, consulta rápida, auditoría y exportación de marcaciones biométricas históricas del reloj **ZKTeco K20**.

---

## 📋 Resumen del Proyecto y Contexto Biométrico

- **Dispositivo configurado:** ZKTeco K20
- **Plataforma / Firmware:** ZLM60_TFT
- **Dirección IP del reloj:** `192.168.10.69` (Puerto: `4370`)
- **Biblioteca de enlace:** `pyzk`
- **Total de marcaciones históricas procesadas:** 48 601 registros
- **Detección de anomalías temporales:** 37 registros identificados con fechas futuras (años 2029, 2033 y 2119).
- **Trabajadores identificados:** 232 identificadores únicos (`user_id`) en marcaciones; **289 colaboradores** en el padrón importado desde `Colaboradores Export.xls`.
- **Nombres y departamentos:** 209 colaboradores con nombre real; 80 registros del archivo fuente repiten el código en la columna `Name` y se muestran como `Sin nombre registrado`.
- **Tiempo de carga inicial:** ~9.5 segundos para 48 601 filas con deduplicación criptográfica O(1).
- **Tiempo de re-ejecución:** ~1.0 segundo (idempotente: 0 registros duplicados insertados).

---

## 🛠️ Stack Tecnológico

### Backend
- **Python:** 3.12
- **Framework Web:** FastAPI
- **ORM / Base de Datos:** SQLAlchemy 2.0 + PyMySQL + Cryptography
- **Validación y Configuración:** Pydantic 2.x + Pydantic-Settings
- **Procesamiento y Exportación:** Pandas + OpenPyXL
- **Control de Versiones de BD:** Alembic (Migraciones automáticas)
- **Servidor ASGI:** Uvicorn

### Frontend
- **Framework:** Vue 3 (Composition API `<script setup>`)
- **Bundler:** Vite
- **Lenguaje:** JavaScript
- **Enrutamiento:** Vue Router 4
- **Cliente HTTP:** Axios (con interceptores y baseURL configurado)
- **Estilos:** Tailwind CSS v3

### Base de Datos
- **Motor:** MySQL 8.4 (administrado por Laragon)
- **Base de datos:** `asistencia_k20` (Charset: `utf8mb4`, Collation: `utf8mb4_unicode_ci`)

---

## 🏛️ Arquitectura del Sistema

```
asistencia-k20/
├── backend/
│   ├── alembic/                    # Migraciones de esquema
│   │   ├── versions/
│   │   ├── env.py                  # Verificación estricta de base de datos
│   │   └── script.py.mako
│   ├── app/
│   │   ├── api/
│   │   │   └── v1/
│   │   │       ├── endpoints/
│   │   │       │   ├── dashboard.py     # KPIs, punches y fechas sospechosas
│   │   │       │   ├── marcaciones.py   # Consulta paginada con filtros
│   │   │       │   ├── trabajadores.py  # Padrón de 232 trabajadores
│   │   │       │   ├── export.py        # Streaming de Excel (.xlsx) y CSV
│   │   │       │   ├── importacion.py   # Ingesta idempotente con token
│   │   │       │   └── dispositivos.py  # Estado y preparación Fase 2 K20
│   │   │       └── api.py               # Agregador de rutas v1
│   │   ├── core/
│   │   │   ├── config.py           # Variables de entorno y settings
│   │   │   ├── database.py         # SQLAlchemy engine y SessionLocal
│   │   │   └── security.py         # Control de acceso y token
│   │   ├── models/
│   │   │   ├── dispositivo.py      # Modelo Dispositivo
│   │   │   ├── trabajador.py       # Modelo Trabajador (user_id texto)
│   │   │   ├── ejecucion.py        # Auditoría de importaciones
│   │   │   └── marcacion.py        # Modelo Marcacion con índices
│   │   ├── schemas/                # Esquemas Pydantic
│   │   └── services/
│   │       ├── dashboard_service.py # Agregaciones SQL rápidas
│   │       ├── marcacion_service.py # Paginación y filtrado dinámico
│   │       ├── import_service.py    # Deduplicación SHA-256 e ingesta
│   │       ├── colaborador_import_service.py # Padrón XLS (AC No. ↔ user_id)
│   │       ├── export_service.py    # Formateo Excel y CSV UTF-8 BOM
│   │       └── biometrico_service.py# Arquitectura lista para Fase 2
│   ├── main.py                     # Instancia FastAPI y Lifespan
│   ├── alembic.ini
│   ├── requirements.txt
│   ├── .env.example
│   ├── .env
│   ├── test_system.py              # Suite de pruebas automatizadas
│   └── test_colaboradores.py       # Pruebas del padrón y la relación con marcaciones
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── common/             # StatCard, Modal, Toast, LoadingSpinner
│   │   │   └── layout/             # Sidebar, Navbar con reloj en vivo
│   │   ├── views/
│   │   │   ├── DashboardView.vue   # Métricas, alertas y gráficos
│   │   │   ├── MarcacionesView.vue # Tabla con filtros y paginación
│   │   │   ├── TrabajadoresView.vue# Directorio de trabajadores
│   │   │   ├── ExportacionesView.vue# Centro de descargas
│   │   │   └── DispositivoView.vue # Configuración K20 e historial
│   │   ├── router/                 # Vue Router
│   │   ├── services/api.js         # Cliente Axios
│   │   ├── App.vue                 # Layout raíz con modales globales
│   │   ├── main.js
│   │   └── style.css               # Tailwind CSS
│   ├── index.html
│   ├── vite.config.js
│   ├── tailwind.config.js
│   └── package.json
├── datos/
│   ├── registros_k20.csv           # Archivo original (48 601 registros)
│   └── Colaboradores Export.xls    # Padrón de 289 colaboradores (ZLM60_TFT)
├── iniciar_backend.bat             # Servicio unico (web + API) con doble clic
├── iniciar_frontend.bat            # Solo desarrollo: Vite con recarga en caliente (5174)
├── iniciar_sistema.ps1             # Inicia/reutiliza el servicio y abre el navegador
├── detener_sistema.ps1             # Detiene el servicio
├── servicio_k20.ps1                # Lo ejecuta la tarea de arranque automatico
├── instalar_autostart.ps1          # Arranque automatico al iniciar sesion
├── quitar_autostart.ps1            # Quita el arranque automatico
├── Dockerfile                      # Imagen unica (web + API) para Dokploy
├── docker-compose.yml              # App + MySQL para despliegue
├── .dockerignore
└── .gitignore
```

---

## 🔒 Principios de Integridad y Deduplicación de Datos

1. **Estrategia de Deduplicación Criptográfica:**
   - No se asume que el campo `uid` identifique universalmente una marcación (los dispositivos biométricos reinician el `uid` tras formateos o sobreescritura de buffer circular).
   - Se implementa un hash único `SHA-256(dispositivo_id_user_id_timestamp_status_punch)` indexado de forma única en MySQL.
   - Permite re-ejecutar importaciones repetidamente sin duplicar registros y detectando colisiones.

2. **Preservación de `user_id`:**
   - Se almacena como `VARCHAR(50)` para evitar la pérdida de ceros a la izquierda en identificadores de trabajadores.

3. **No Interpretación Arbitraria de Códigos:**
   - Los campos `status` y `punch` se almacenan en sus valores numéricos originales (0, 1, 4, 5). No se fuerza la etiqueta "Entrada" o "Salida" sin confirmación formal de las políticas de la institución.

4. **Identificación de Fechas Sospechosas:**
   - Los 37 registros con fechas en el futuro (años 2029, 2033 y 2119) se conservan intactos en la base de datos sin corregirlos ni eliminarlos. Se marcan con la bandera `fecha_sospechosa = True` y su motivo respectivo para permitir auditorías y filtros de exclusión para nómina.

---

## 👥 Padrón de Colaboradores (nombres y departamentos)

El archivo `datos/Colaboradores Export.xls` (formato BIFF8 / Excel antiguo, leído con `xlrd` y codificación `cp1252`) contiene 289 colaboradores. Se relaciona con las marcaciones usando **`AC No.` ↔ `marcaciones.user_id`**, conservando los identificadores como texto y los ceros iniciales.

- **Endpoint:** `POST /api/v1/importar/colaboradores` (protegido con `X-API-Key`).
- **UI:** botón *Importar Colaboradores* dentro del modal de sincronización del frontend.
- **Idempotente:** re-ejecutar el importador no crea duplicados ni altera marcaciones.
- **Trazabilidad:** cada ejecución se registra en `ejecuciones_sincronizacion` con procesados, creados, actualizados, omitidos, nombres no disponibles, códigos sin coincidencia y errores.
- **Exportaciones y consultas:** las columnas *Nombre del Trabajador* y *Departamento* se incorporan a los endpoints de marcaciones, al CSV y al Excel. Si no existe un trabajador asociado se muestra el código original junto a `Sin nombre registrado`.

> **Nota de calidad de datos:** 80 de los 289 registros del Excel traen el propio código en la columna `Name` (por ejemplo, AC No. `104` con Name `104`). El importador los trata como *nombre no disponible* en lugar de mostrar un número como nombre de la persona; el departamento de todos los registros del archivo es `OUR COMPANY`.

> **Copia de seguridad previa:** `backend/backups/backup_asistencia_k20_pre_colaboradores.sql` (generada antes de importar el padrón).

---

## ↕️ Ordenamiento de las tablas

Todas las columnas de **Marcaciones** y de **Trabajadores** son ordenables haciendo clic en su encabezado. El primer clic aplica un sentido y el segundo lo invierte (indicador `▲` ascendente / `▼` descendente):

- **Marcaciones:** `# ID`, `UID Orig.`, `ID Trabajador`, `Nombre`, `Departamento`, `Fecha y Hora`, `Status`, `Punch Original` y `Anomalía`.
- **Trabajadores:** `ID Trabajador`, `Nombre`, `Departamento`, `Total Marcaciones`, `Primer Registro`, `Último Registro` y `Estado`.

El orden se resuelve en MySQL (no en el navegador), por lo que se aplica a **todas** las filas y no solo a la página visible. Los nombres y departamentos vacíos se muestran siempre al final, y se usa `id` como desempate para que la paginación sea estable (sin filas repetidas ni omitidas).

La API acepta `order_by` y `order_dir` (`asc`/`desc`) tanto en `/api/v1/marcaciones` y `/api/v1/trabajadores` como en las exportaciones `/api/v1/export/csv` y `/api/v1/export/excel`, de modo que el archivo descargado sale exactamente en el orden que ves en pantalla.

---

## 🚀 Guía de Instalación y Ejecución en Windows (Laragon)

### 1. Requisitos Previos
- MySQL 8.x en ejecución desde Laragon (puerto 3306).
- Python 3.12 instalado.
- Node.js (v18+) y npm instalados.

### 2. Configuración de Base de Datos
La base de datos `asistencia_k20` se crea automáticamente con:
```sql
CREATE DATABASE IF NOT EXISTS asistencia_k20 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. Configuración del Backend (.env)
Verifica que `backend/.env` contenga tus credenciales locales:
```env
MYSQL_SERVER=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=
MYSQL_DB=asistencia_k20
ZK_DEVICE_IP=192.168.10.69
ZK_DEVICE_PORT=4370
API_ACCESS_TOKEN=k20-access-token-dev
```

### 4. Ejecución en Windows

La aplicación es **un solo servicio**: el mismo proceso sirve la web compilada y la API en el puerto **5173**. No necesitas Node ni una segunda ventana.

#### Uso normal
```powershell
.\iniciar_sistema.ps1     # inicia (o reutiliza) el servicio y abre el navegador
.\detener_sistema.ps1     # lo detiene
```
También puedes iniciarlo sin scripts con doble clic en `iniciar_backend.bat`, o directamente:
```powershell
cd backend
.\venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 5173
```

#### Que arranque solo con Windows (recomendado)
Ejecuta **una sola vez**:
```powershell
.\instalar_autostart.ps1
```
Crea la tarea programada `AsistenciaK20`, que al iniciar sesión levanta el servicio en segundo plano. Desde entonces solo abres `http://127.0.0.1:5173` y funciona, sin ejecutar nada más. El registro queda en `backend\logs\servidor.log`.
```powershell
.\quitar_autostart.ps1    # desinstala el arranque automático
```

> Cerrar el navegador no detiene nada: puedes cerrar y volver a abrir la pestaña cuando quieras. El servicio se reinicia solo si falla y la interfaz muestra un estado de error con botón **Reintentar** en lugar de quedarse “Cargando…”.

#### Desarrollo (recarga en caliente)
Con el servicio principal activo en 5173:
```powershell
.\iniciar_frontend.bat    # Vite en http://127.0.0.1:5174 (proxy /api -> 5173)
```
Los cambios del frontend requieren `npm run build` para reflejarse en el puerto 5173. Los cambios del backend requieren reiniciar `iniciar_sistema.ps1`.

### 5. Acceso a la Aplicación
- **Interfaz Web:** `http://127.0.0.1:5173`
- **API y Swagger:** `http://127.0.0.1:5173/api/v1/docs`
- **Healthcheck:** `http://127.0.0.1:5173/health`

---

## ☁️ Despliegue en Dokploy (sin scripts de inicio/apagado)

El proyecto incluye `Dockerfile` y `docker-compose.yml`. En el servidor no se ejecuta `iniciar_sistema.ps1` ni `detener_sistema.ps1`: el contenedor arranca solo y se reinicia automáticamente (`restart: unless-stopped`).

1. Sube el proyecto a un repositorio Git (GitHub/GitLab).
2. En Dokploy crea una **Application** con *Build Type = Dockerfile* (o un **Compose** apuntando a `docker-compose.yml`).
3. Expón el puerto **5173** (es el mismo de la web y la API) y configura el dominio.
4. Define las variables de entorno: `MYSQL_SERVER`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DB`, `SECRET_KEY`, `API_ACCESS_TOKEN`, `ZK_DEVICE_IP`, `ZK_DEVICE_PORT`.
5. Deploy. Dokploy construye la web, la sirve junto a la API y la mantiene activa.

Con `docker-compose.yml` se incluye además un MySQL 8 con volumen persistente, así que un solo `docker compose up -d --build` deja todo funcionando. Para usar una base externa, elimina el servicio `db` y apunta `MYSQL_SERVER` a tu servidor.

> `datos/` y `backend/.env` están excluidos de la imagen (contienen información personal y credenciales). El padrón ya importado vive en la base de datos; si necesitas reimportarlo en el servidor, monta el archivo como volumen y usa el endpoint de importación.

---

## 🔐 Acceso y sincronización con el K20 (Fase 2)

### Autenticación

Todos los endpoints de datos personales y sincronización requieren autenticación.
El frontend muestra una pantalla de inicio de sesión; el token Bearer se guarda
en el navegador y se envía en cada petición. Para automatización use
`X-API-Key: <API_ACCESS_TOKEN>`.

Credenciales de administrador (en `backend/.env`):

```env
ADMIN_USER=admin
# Desarrollo: contraseña en claro
ADMIN_PASSWORD=k20-admin-dev
# Producción: hash (genere con: python scripts/generar_password_hash.py)
ADMIN_PASSWORD_HASH=
```

### Sincronización manual con el K20

Botón **"Sincronizar con K20"** (distinto de "Sincronizar CSV"). Descarga
completa de marcaciones por `pyzk` (solo lectura, ~40-50 s), con
deduplicación por hash SHA-256. La tarea corre en un hilo en segundo plano del
servidor: sobrevive al cierre del navegador. El panel muestra leídas, nuevas,
duplicadas y errores; también hay un botón **"Probar conexión"** (solo lectura,
no descarga).

Estado real del dispositivo: **Configurado / Conexión comprobada / Sin conexión**,
basado en la última conexión exitosa o el último error, nunca solo en la IP.

### Sincronización automática (desactivada por defecto)

```powershell
# Activar en backend/.env:
SYNC_AUTOMATICA_ENABLED=True
SYNC_INTERVALO_MINUTOS=10
```

Iniciar/detener el daemon en Windows:

```powershell
.\\iniciar_sync_auto.ps1          # (agregue -Force si no activó la variable)
.\\detener_sync_auto.ps1
```

Arranque automático con Windows (opcional, solo tras activar la variable):

```powershell
# Tarea programada independiente
accion = New-ScheduledTaskAction -Execute "powershell.exe" -Argument "-NoProfile -WindowStyle Hidden -File `"$PWD\\backend\\scripts\\sync_auto.py`"" ...
```

En Proxmox/Dokploy, el servicio `sync` del `docker-compose.yml` está bajo el
perfil `sync` y no arranca por defecto:

```bash
docker compose --profile sync up -d
```

El daemon usa APScheduler (`max_instances=1`, `coalesce=True`) y
`GET_LOCK('k20_sync')` en MySQL para evitar ejecuciones duplicadas entre
procesos. Si el reloj está desconectado, se registra el error y se reintenta
en la siguiente ejecución sin borrar datos.

### Seguridad

- No hay permiso implícito por venir de `localhost`.
- Sin token de desarrollo en el frontend.
- MySQL y el puerto 4370 no se exponen a Internet.
- La sincronización y los datos personales exigen autorización real del servidor.

---

## 🧪 Pruebas Realizadas y Resultados Verificados

El archivo de pruebas `backend/test_system.py` fue ejecutado exitosamente con los siguientes resultados reales:

| Prueba | Resultado Esperado | Resultado Obtenido | Estado |
|---|---|---|---|
| Ingesta inicial CSV | 48 601 registros | 48 601 registros en 9.57s | ✅ APROBADO |
| Trabajadores únicos | 232 trabajadores | 232 identificados | ✅ APROBADO |
| Fechas sospechosas | 37 anomalías | 37 detectadas (2029, 2033, 2119) | ✅ APROBADO |
| Idempotencia (2da pasada) | 0 nuevos / 48 601 duplicados | 0 nuevos / 48 601 omitidos en 1.05s | ✅ APROBADO |
| Filtro por Punch 0 | 16 139 registros | 16 139 registros | ✅ APROBADO |
| Exportación Excel (.xlsx) | Archivo binario con estilos | 7 373 bytes generados | ✅ APROBADO |
| Exportación CSV (UTF-8 BOM) | Archivo compatible con Excel ES | 3 191 bytes generados | ✅ APROBADO |
| Importación padrón .xls | 289 colaboradores procesados / 0 errores | 232 actualizados + 57 creados, 0 códigos sin coincidencia | ✅ APROBADO |
| Idempotencia del padrón | 0 creados / 0 actualizados en 2da pasada | 289 omitidos, marcaciones intactas (48 601) | ✅ APROBADO |
| Relación Marcación → Trabajador | Nombre visible en consultas y exportaciones | 209 con nombre real, 80 sin nombre disponible | ✅ APROBADO |
| Endpoints HTTP REST | Código 200 OK en todas las rutas | 200 OK verificado | ✅ APROBADO |

