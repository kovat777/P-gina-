# P-gina-

## Skills de Instagram para Claude

Instaladas en `.claude/skills/`, a partir de [postzen-dev/instagram-agent-skill](https://github.com/postzen-dev/instagram-agent-skill) (licencia MIT, ver `.claude/skills/LICENSE-postzen`).
Se cargan solas en cualquier sesión de Claude Code que abra este repositorio.

| Comando | Para qué sirve |
| --- | --- |
| `/ig-reel` | Guion de reel: 3 ganchos con puntaje, texto en pantalla y tiempos |
| `/ig-viral` | Qué reels funcionan en tu nicho y por qué |
| `/ig-caption` | Escribe y revisa la descripción (lo que se ve antes de "… más") |
| `/ig-carousel` | Carrusel: portada, textos y archivos 1080x1350 |
| `/ig-story` | Secuencia de historias y embudo a DM |
| `/ig-profile` | Nota de tu perfil sobre 100 y cómo mejorarlo |
| `/ig-plan` | Plan de la semana |
| `/ig-human` | Quita el "tono IA" de los textos |
| `/ig-comment` | Comentarios en posts de otros |
| `/ig-reply` | Respuestas a tus comentarios |
| `/ig-dm` | Mensajes directos y propuestas de colaboración |
| `/ig-repurpose` | Convierte un video/podcast en una semana de contenido |
| `/ig-audit` | Revisa qué posts te funcionaron mejor |
| `/ig-publish` | Publica en Instagram (necesita PostZen conectado) |

### Antes de empezar
1. Llena `templates/voice.md` con tu forma de hablar (todas las skills lo leen).
2. Para publicar automáticamente: el archivo `.mcp.json` registra el servidor de PostZen.
   En Claude Code en tu computadora ejecuta `/mcp` → `postzen` → Authenticate.
   Tu cuenta de Instagram debe ser de Empresa o Creador. Plan gratis: 20 publicaciones/mes.

## Videos
Sube reels a la carpeta `videos/` para analizarlos.
