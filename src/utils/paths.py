# src/utils/paths.py
from pathlib import Path

def get_project_root():
    # En Jupyter, resolve() da la ruta correcta hasta /proyecto_final
    return Path(__file__).resolve().parents[2]

def get_model_dir():
    return get_project_root() / "models"

def get_processed_dir():
    return get_project_root() / "data" / "processed"
