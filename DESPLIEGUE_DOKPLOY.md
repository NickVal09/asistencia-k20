# Desplegar en Dokploy (sin terminal)

## Lo primero: no uses `127.0.0.1` para probar Dokploy

| URL | Qué es | Depende de |
|-----|--------|------------|
| `http://127.0.0.1:5173` | El servicio en **esta PC** (Windows) | La tarea `AsistenciaK20` / `iniciar_sistema.ps1` |
| `https://tu-dominio.com` | El servicio en **Dokploy** | El contenedor Docker en el servidor |

Si cierras la ventana del terminal y se cae `127.0.0.1:5173`, eso **no tiene
relación con Dokploy**: es el servicio local de Windows. En Dokploy no hay
terminal: el contenedor arranca solo y se reinicia automáticamente.

`127.0.0.1` **siempre** significa "esta computadora". Desde tu PC nunca vas a
llegar a Dokploy por `127.0.0.1`; usa el dominio que configures en Dokploy o la
IP del servidor con el puerto publicado.

---

## Acceso por IP y puerto (sin dominio)

Dokploy **no publica** el puerto del contenedor por sí solo. El "Container Port"
de la pestaña **Domains** solo sirve para que Traefik enrute un dominio; no abre
`IP:puerto`. Por eso `http://192.168.10.62:5173` da `ERR_CONNECTION_REFUSED`
aunque la aplicación esté corriendo.

Para abrirla directamente por IP y puerto:

1. Application → pestaña **Advanced** → sección **Ports** → **Add Port**.
2. Rellena:

   | Campo | Valor |
   |-------|-------|
   | Published Port | `5173` |
   | Target Port | `5173` |
   | Protocol | `TCP` |

3. **Save** y luego **Redeploy** (los cambios de puertos se aplican al recrear
   el contenedor).
4. Abre `http://192.168.10.62:5173`.

> Nota: el "Published Port" es el puerto del *host* (el 192.168.10.62). Si otro
> servicio ya usa el 5173 en ese servidor, usa otro, por ejemplo `8080` →
> Target `5173`, y abre `http://192.168.10.62:8080`.

### Si quieres usar dominio

Los dominios de Dokploy pasan por **Traefik**, que escucha en los puertos
**80** y **443**. Si esos puertos están cerrados (firewall o Traefik detenido),
ningún dominio funcionará. Compruébalo desde otra PC de la red:

```powershell
Test-NetConnection 192.168.10.62 -Port 80
Test-NetConnection 192.168.10.62 -Port 443
```

Si dan `False`, revisa en el servidor:

```bash
docker ps | grep traefik
sudo ufw status
```

Mientras tanto, usa el acceso por IP:puerto de la sección anterior.

---

## Configuración del servicio en Dokploy

### Application (recomendado)

| Campo | Valor |
|-------|-------|
| Repository | `NickVal09/asistencia-k20` |
| Branch | `main` |
| **Build Type** | **Dockerfile** ← NO uses Nixpacks |
| Dockerfile Path | `Dockerfile` |
| Docker Context Path | `.` |
| **Container Port** (Domains) | **5173** |
| Auto Deploy | activado (opcional) |

> Si dejas **Nixpacks** (el valor por defecto), Dokploy intenta compilar el
> proyecto como una app Node/Python suelta, no encuentra la configuración y el
> build falla (por eso aparecen errores tipo "Node 18"). Este proyecto **debe**
> compilarse con el `Dockerfile`, que ya compila Vue y arranca FastAPI.

### Variables de entorno

```env
ENVIRONMENT=production
MYSQL_SERVER=<host de MySQL>
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=<password de MySQL>
MYSQL_DB=asistencia_k20
SECRET_KEY=<cadena larga y aleatoria>
API_ACCESS_TOKEN=<cadena larga y aleatoria>
ADMIN_USER=admin
ADMIN_PASSWORD=
ADMIN_PASSWORD_HASH=<hash generado>
ZK_DEVICE_IP=192.168.10.69
ZK_DEVICE_PORT=4370
ZK_DEVICE_PLATFORM=ZLM60_TFT
ZK_DEVICE_NAME=ZKTeco K20
SYNC_AUTOMATICA_ENABLED=False
```

- `MYSQL_SERVER`: si usas el MySQL del `docker-compose.yml`, es `db`.
  Si usas un MySQL externo, pon su host/IP (nunca `127.0.0.1` dentro del
  contenedor: ahí `127.0.0.1` es el propio contenedor).
- `ADMIN_PASSWORD_HASH` se genera así:

```powershell
cd backend
.\venv\Scripts\python.exe scripts\generar_password_hash.py "MiClaveSegura"
```

### Compose (alternativa con MySQL incluido)

1. Crear servicio → **Compose** → archivo `docker-compose.yml`.
2. Dominio → **Container Port: 5173**.
3. Deploy. Dokploy levanta `db` + `app`.

---

## Qué hace el contenedor al arrancar

`entrypoint.sh`:

1. Espera a MySQL (60 s). Si no aparece, **arranca igual** para que la web
   muestre el error en vez de quedar caída.
2. Crea la base de datos si no existe.
3. Aplica `alembic upgrade head`.
4. Arranca `uvicorn` en `0.0.0.0:5173` (o el puerto de `PORT`/`APP_PORT`).

No ejecuta ningún `.bat`, `.ps1` ni necesita terminal.

---

## Verificación después del deploy

1. `https://tu-dominio.com/health`

   ```json
   {"status":"ok","environment":"production","frontend":true}
   ```

   - `frontend: false` → falló la compilación de Vue (revisa el build log).

   Y para comprobar la base de datos: `https://tu-dominio.com/health/db`

   ```json
   {"database": true}
   ```

   Si devuelve `false`, revisa `MYSQL_SERVER`, `MYSQL_USER`, `MYSQL_PASSWORD`
   y `MYSQL_DB`.

2. `https://tu-dominio.com/` → debe mostrar **la pantalla de login**.
3. `https://tu-dominio.com/api/v1/marcaciones?per_page=1` → debe responder
   `401 Autenticación requerida`. Si devuelve datos, la imagen desplegada es
   antigua (haz "Redeploy" con rebuild).
4. Inicia sesión con `ADMIN_USER` / la contraseña que definiste.
5. Dispositivo → **Probar conexión** (solo funciona si el servidor de Dokploy
   está en la misma red que `192.168.10.69`).

---

## Si el build falla

Abre el **build log** del deployment en Dokploy y busca la primera línea con
`ERROR`. Causas típicas:

| Mensaje | Causa | Solución |
|---------|-------|----------|
| `Could not read package.json` / `npm ERR!` en la raíz | Build Type = Nixpacks | Cambiar a **Dockerfile** |
| `npm ci` falla por lockfile | `package-lock.json` desincronizado | Ya está corregido en el repo |
| `Cannot connect to the Docker daemon` | El servidor Dokploy no tiene Docker | Revisar instalación de Dokploy |
| `no space left on device` | Disco lleno | `docker system prune -af` en el servidor |

Si la página carga pero sale error 502/504, revisa que el **Container Port**
del dominio sea `5173` y que el contenedor esté `healthy`.
