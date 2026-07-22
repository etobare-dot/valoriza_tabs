# valoriza_app — Valorización de Obras de Riego

Aplicación web para cubicar y valorizar obras de riego según tipología. Reemplaza el flujo de la macro Excel "Anexo 9-5 Desarrollo informático": el usuario selecciona una tipología de obra, ingresa sus dimensiones y la aplicación calcula las cantidades de obra (cubicación) y el presupuesto completo (partidas con precios unitarios, gastos generales, utilidades, imprevistos e IVA), expresado en pesos chilenos y en UF.

El backend usa exclusivamente la **biblioteca estándar de Python** (sin `pip install`) y la interfaz está construida con **Vue.js 3 servido localmente** (sin Node.js, sin conexión a internet). Los cálculos de ingeniería provienen del paquete `motor_calculo`, migrado desde las macros VBA originales.

## Requisitos

- Python 3.x instalado.
- La carpeta `valoriza_app` y la carpeta `motor_calculo` deben estar **juntas en el mismo directorio** (la aplicación importa el motor de cálculo desde la carpeta hermana):

```
valoriza_obras/
├── motor_calculo/      ← motor de cálculo (hidráulica y cubicaciones)
└── valoriza_app/       ← esta aplicación
```

> **Importante:** no se requieren entornos virtuales ni instalación de paquetes. Cero dependencias externas.

## Ejecución

1. Abrir una terminal (CMD, PowerShell o Terminal).
2. Navegar hasta el directorio que contiene ambas carpetas:

```bash
cd ruta/a/valoriza_obras
```

3. Ejecutar la aplicación pasando la carpeta como argumento al intérprete:

```bash
python valoriza_app
```

(en macOS/Linux usar `python3 valoriza_app`; para otro puerto: `python valoriza_app 8080`)

4. La consola mostrará el autodiagnóstico de arranque y la URL de acceso:

```
------------------------------------------------------------
Valorizacion de Obras de Riego (CNR) - Motor Python + Vue
Autodiagnostico de arranque
------------------------------------------------------------
[OK] Entorno Python detectado: 3.13.3
[OK] Motor de calculo operativo: cubicacion de prueba = 3.20 m3 de hormigon.
[OK] Tabla de precios cargada: 18 precios unitarios.
[OK] Valorizacion de prueba exitosa: total $16,074,522 CLP.
------------------------------------------------------------
[OK] Servidor HTTP inicializado en el puerto 8000.
[INFO] Todo en orden. Servidor corriendo en http://localhost:8000
```

Si alguna validación falla, el proceso se detiene con un mensaje `[ERROR]` antes de levantar el servidor.

5. Abrir el navegador en **http://localhost:8000**.

Para detener la aplicación: `Ctrl+C` en la terminal.

## Uso de la interfaz

1. **Seleccionar la tipología de obra** en el desplegable (revestimiento de canal, disipador de energía, desarenador, marco partidor, compuerta, cajón de hormigón, canoa, sifón, reja de sifón, túnel con shotcrete).
2. **Ingresar las dimensiones** de la obra. El formulario se adapta a cada tipología y precarga valores de referencia. Todas las unidades están indicadas (m, m³/s).
3. Ajustar si es necesario los **parámetros del presupuesto**: gastos generales (8%), utilidades (15%), imprevistos (1%) e IVA (19%).
4. Presionar **"Cubicar y valorizar"**.

El panel derecho muestra:

- **Datos calculados** intermedios cuando aplica (ej.: altura normal por Manning y espesor de revestimiento en la tipología de canal; largo de decantación en el desarenador; cajón estándar seleccionado).
- **Tabla de partidas**: código, descripción, unidad, cantidad cubicada, precio unitario y subtotales en pesos y UF.
- **Resumen del presupuesto**: costo directo, gastos generales, utilidades, imprevistos, costo total neto, IVA y total con IVA, en pesos y UF.

## Elementos que la CNR puede modificar

### 1. Precios unitarios — `precios.csv` (sin tocar código)

Es el archivo principal de mantención. Cada fila es un precio unitario:

```csv
codigo,descripcion,unidad,precio_clp
MT003,Hormigon estructural G25,m3,189220
MT011,Enfierradura (acero de refuerzo),kg,3959
...
```

- **Actualizar un precio**: editar la columna `precio_clp` (entero, en pesos). Se puede editar con Excel guardando como CSV, o con cualquier editor de texto.
- **No cambiar los códigos** (`MTxxx`): son los que vinculan cada partida con las cubicaciones. Los códigos replican la codificación de la planilla original.
- Los precios incluidos son **referenciales** (tomados del presupuesto de la obra Bellavista Bajo donde existían; el resto son provisorios y deben ser validados por la CNR).

Los cambios se aplican al siguiente cálculo, sin reiniciar el servidor.

### 2. Valor de la UF y parámetros globales — `valorizacion.py` (constantes al inicio del archivo)

```python
UF_CLP = 39841.72          # valor de la UF usado para convertir a UF
PENDIENTE_CANAL = 0.001    # pendiente longitudinal del modelo hidráulico (m/m)
MANNING_HORMIGON = 0.018   # rugosidad de Manning del hormigón
PORCENTAJES_DEFECTO = {...}  # GG, utilidades, imprevistos e IVA por defecto
```

### 3. Tabla de cajones estándar — `valorizacion.py` (`CAJONES_ESTANDAR`)

Lista de cajones prefabricados disponibles como tuplas `(base, alto, espesor)` en metros. Es una **tabla referencial de muestra**: debe reemplazarse por la tabla real "CajonM" del libro Excel original. La aplicación selecciona automáticamente el cajón que cubre las dimensiones del canal ingresadas.

### 4. Valores por defecto de los formularios — `valorizacion.py` (registro `TIPOLOGIAS`)

Cada tipología declara sus campos con etiqueta, unidad y valor por defecto:

```python
_campo("caudal", "Caudal de diseno", "m3/s", 0.67),
```

Cambiar el último argumento modifica el valor precargado en el formulario web (el formulario se genera automáticamente desde esta declaración).

### 5. Agregar una tipología nueva — `valorizacion.py`

1. Escribir la función de cubicación en `motor_calculo/cubicaciones.py` (o reutilizar una existente).
2. Escribir una función `_mi_tipologia(p)` en `valorizacion.py` que devuelva la lista de `(codigo_precio, cantidad)` y los datos informativos.
3. Registrarla en el diccionario `TIPOLOGIAS` con su título y campos.

No hay que tocar el frontend: la interfaz lee las tipologías desde la API y construye el formulario sola.

### 6. Fórmulas de cubicación — `motor_calculo/`

Las fórmulas de ingeniería (volúmenes de hormigón, cuantías de acero, espesores, movimiento de tierras, hidráulica de Manning) están en el paquete `motor_calculo`, documentadas función por función con referencia a la macro VBA de origen. Cualquier ajuste de criterio de cubicación se hace ahí, y queda cubierto por la suite de tests:

```bash
python -m unittest discover -s motor_calculo
```

## Qué NO cubre esta versión

- La tipología **portal de túnel** está migrada en el motor de cálculo pero no expuesta en la interfaz: requiere la tabla real de arcos tipo ("Arco") del libro Excel.
- La **compuerta metálica** se valoriza como 1 unidad de precio fijo (código MT042); la planilla original la seleccionaba por dimensiones desde una tabla de compuertas estándar.
- Exportación a PDF/Excel del presupuesto (la interfaz permite imprimir la página con el navegador).

## Arquitectura (referencia rápida)

```
valoriza_app/
├── __main__.py       # punto de entrada: autodiagnóstico + arranque del servidor
├── servidor.py       # http.server: archivos estáticos + API JSON
│                     #   GET  /api/tipologias  → formularios disponibles
│                     #   POST /api/valorizar   → cubicación + presupuesto
├── valorizacion.py   # une motor_calculo con precios.csv (registro TIPOLOGIAS)
├── precios.csv       # tabla de precios unitarios (editable por la CNR)
├── index.html        # interfaz Vue 3 (formulario dinámico + presupuesto)
└── vue.global.js     # Vue 3 producción, servido localmente
```
