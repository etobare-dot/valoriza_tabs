"""
Servidor HTTP de la aplicación de valorización.

Construido solo con la biblioteca estándar (http.server, socketserver, json):
  - Sirve los archivos estáticos de la carpeta (index.html, vue.global.js).
  - GET  /api/tipologias      → tipologías disponibles y sus formularios.
  - GET  /api/vectores-precio → vectores de precio disponibles en precios.csv.
  - POST /api/valorizar       → {tipologia, parametros, porcentajes, vector_precio} → presupuesto.
"""

import json
import http.server
import socketserver
import os

from valorizacion import listar_tipologias, listar_vectores_precio, valorizar, PREFIJO_VECTOR_PRECIO

DIRECTORIO_BASE = os.path.dirname(os.path.abspath(__file__))
PUERTO_POR_DEFECTO = 8000


class ManejadorPeticiones(http.server.SimpleHTTPRequestHandler):
    """Archivos estáticos + las rutas de la API JSON."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=DIRECTORIO_BASE, **kwargs)

    def do_GET(self):
        if self.path == "/api/tipologias":
            self._responder_json(200, listar_tipologias())
        elif self.path == "/api/vectores-precio":
            self._responder_json(200, listar_vectores_precio())
        else:
            super().do_GET()

    def do_POST(self):
        if self.path != "/api/valorizar":
            self.send_error(404, "Ruta no encontrada")
            return
        try:
            largo = int(self.headers.get("Content-Length", 0))
            datos = json.loads(self.rfile.read(largo))
            resultado = valorizar(
                datos.get("tipologia", ""),
                datos.get("parametros", {}),
                datos.get("porcentajes"),
                datos.get("vector_precio") or PREFIJO_VECTOR_PRECIO,
            )
            self._responder_json(200, resultado)
        except (ValueError, KeyError) as error:
            self._responder_json(400, {"error": str(error)})
        except Exception as error:  # error inesperado: no botar el servidor
            self._responder_json(500, {"error": f"Error interno: {error}"})

    def _responder_json(self, estado, datos):
        cuerpo = json.dumps(datos, ensure_ascii=False).encode("utf-8")
        self.send_response(estado)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(cuerpo)))
        self.end_headers()
        self.wfile.write(cuerpo)

    def log_message(self, formato, *args):
        print("[servidor] %s - %s" % (self.address_string(), formato % args))


def iniciar_servidor(puerto=PUERTO_POR_DEFECTO):
    """Levanta el servidor HTTP multihilo en el puerto indicado."""
    socketserver.ThreadingTCPServer.allow_reuse_address = True
    with socketserver.ThreadingTCPServer(("0.0.0.0", puerto), ManejadorPeticiones) as httpd:
        print(f"[OK] Servidor HTTP inicializado en el puerto {puerto}.")
        print(f"[INFO] Todo en orden. Servidor corriendo en http://localhost:{puerto}")
        print("[INFO] Presiona Ctrl+C para detener el servidor.")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n[INFO] Deteniendo servidor...")
            httpd.shutdown()
