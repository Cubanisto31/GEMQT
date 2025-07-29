import asyncio
import typer
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

from src.config import ExperimentConfig
from src.database import initialize_database
from src.runner import ExperimentRunner

app = typer.Typer()

@app.command()
def run(
    config_path: Path = typer.Option("src/config.yaml", "--config", "-c", exists=True),
    queries_file: Optional[Path] = typer.Option(None, "--queries", "-q", exists=True, help="Fichier externe contenant les requêtes (Excel ou CSV)")
):
    try:
        config = ExperimentConfig.from_yaml(str(config_path), queries_file=queries_file)
        db_path = Path(config.database_url.replace("sqlite:///", ""))
        db_path.parent.mkdir(parents=True, exist_ok=True)
        initialize_database(config.database_url)
        runner = ExperimentRunner(config)
        asyncio.run(runner.run())
    except Exception as e:
        typer.secho(f"Erreur: {e}", fg=typer.colors.RED)
        raise typer.Exit(code=1)

if __name__ == "__main__":
    app()