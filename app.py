"""Punto de entrada de la aplicación (Hugging Face Spaces o ejecución local).

Ejecuta el script principal sin modificarlo: descarga los datos oficiales (DANE, NASA POWER),
estima el SpVAR y lanza la interfaz Gradio.
"""
import pathlib
import runpy

SCRIPT = pathlib.Path(__file__).with_name("spvar_colombia_agro_manufactura.py")
runpy.run_path(str(SCRIPT), run_name="__main__")
