"""
Punto de entrada: lanzador con autodiagnóstico.

Valida el entorno y los componentes de cálculo antes de dejar el servidor
web corriendo. Ejecución (desde la carpeta que contiene valoriza_app y
motor_calculo):

    python valoriza_app
"""

import os
import sys

# La app importa el paquete hermano motor_calculo, que vive en la carpeta
# padre; se agrega esa carpeta al path para poder ejecutar `python valoriza_app`.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

SEPARADOR = "-" * 60


def verificar_entorno_python():
    """Informa la versión del intérprete que ejecuta la aplicación."""
    print(f"[OK] Entorno Python detectado: {sys.version.split()[0]}")


def verificar_motor_calculo():
    """Ejecuta una cubicación real de humo con el motor de cálculo."""
    try:
        from motor_calculo import cubicacion_revestimiento_canal
        c = cubicacion_revestimiento_canal(largo=10, base=1, altura=1,
                                           espesor=0.1, talud=0)
        if c.hormigon <= 0:
            print("[ERROR] El motor de calculo devolvio una cubicacion vacia.")
            sys.exit(1)
        print(f"[OK] Motor de calculo operativo: cubicacion de prueba = {c.hormigon:.2f} m3 de hormigon.")
    except Exception as error:
        print(f"[ERROR] Fallo el motor de calculo: {error}")
        sys.exit(1)


def verificar_precios():
    """Verifica que la tabla de precios sea legible y tenga registros."""
    try:
        from valorizacion import cargar_precios
        precios = cargar_precios()
        if not precios:
            print("[ERROR] La tabla de precios esta vacia.")
            sys.exit(1)
        print(f"[OK] Tabla de precios cargada: {len(precios)} precios unitarios.")
    except Exception as error:
        print(f"[ERROR] Fallo la lectura de precios.csv: {error}")
        sys.exit(1)


def verificar_valorizacion():
    """Valoriza una obra de prueba de punta a punta (cubicación + precios)."""
    try:
        from valorizacion import valorizar
        resultado = valorizar("canoa", {"largo": 24, "base": 1, "altura": 1})
        total = resultado["resumen"]["total"]["clp"]
        if total <= 0:
            print("[ERROR] La valorizacion de prueba dio total cero.")
            sys.exit(1)
        print(f"[OK] Valorizacion de prueba exitosa: total ${total:,} CLP.")
    except Exception as error:
        print(f"[ERROR] Fallo la valorizacion de prueba: {error}")
        sys.exit(1)


def determinar_puerto():
    """Puerto: usa $PORT si existe (Render, Railway, etc.), si no el por defecto."""
    import os
    from servidor import PUERTO_POR_DEFECTO
    puerto_env = os.environ.get("PORT")
    if puerto_env:
        try:
            return int(puerto_env)
        except ValueError:
            print(f"[ERROR] PORT inválido '{puerto_env}'. Se usará {PUERTO_POR_DEFECTO}.")
    if len(sys.argv) > 1:
        try:
            return int(sys.argv[1])
        except ValueError:
            print(f"[ERROR] Puerto inválido '{sys.argv[1]}'. Se usará {PUERTO_POR_DEFECTO}.")
    return PUERTO_POR_DEFECTO

def main():
    print(SEPARADOR)
    print("Valorizacion de Obras de Riego (CNR) - Motor Python + Vue")
    print("Autodiagnostico de arranque")
    print(SEPARADOR)

    verificar_entorno_python()
    verificar_motor_calculo()
    verificar_precios()
    verificar_valorizacion()

    print(SEPARADOR)
    from servidor import iniciar_servidor
    iniciar_servidor(determinar_puerto())


if __name__ == "__main__":
    main()
