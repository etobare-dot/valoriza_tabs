# valoriza_obras

Sistema de cubicación y valorización de obras de riego (CNR), migrado desde
la macro Excel "Anexo 9-5 Desarrollo informático" a Python. Construido
íntegramente con la biblioteca estándar de Python y Vue.js 3 local: sin
`pip install`, sin Node.js, sin conexión a internet.

## Contenido

| Carpeta | Descripción |
|---|---|
| [motor_calculo/](motor_calculo/) | Núcleo de cálculo: hidráulica (Manning, altura crítica), parámetros de diseño y cubicaciones de 11 tipologías de obra. Con suite de tests. |
| [valoriza_app/](valoriza_app/) | Aplicación web: API JSON sobre `http.server` + interfaz Vue 3 para cubicar y valorizar obras con tabla de precios editable. |

## Uso rápido

```bash
python3 valoriza_app        # levanta la aplicación en http://localhost:8000
```

Instrucciones completas, y la guía de qué puede modificar la CNR (precios,
valor UF, tablas estándar, tipologías), en [valoriza_app/README.md](valoriza_app/README.md).

## Tests del motor de cálculo

```bash
python3 -m unittest discover -s motor_calculo
```
