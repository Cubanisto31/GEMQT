import asyncio
import typer
from pathlib import Path

from src.config import ExperimentConfig
from src.database import initialize_database
from src.runner import ExperimentRunner

app = typer.Typer()

@app.command()
def run(config_path: Path = typer.Option("src/config.yaml", "--config", "-c", exists=True)):
    try:
        config = ExperimentConfig.from_yaml(str(config_path))
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