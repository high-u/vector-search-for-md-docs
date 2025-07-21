import typer
from pathlib import Path
from typing import Optional

from .utilities.config import load_config
from .interfaces.database.connection import create_database_connection
from .interfaces.database.schema import initialize_database
from .core.tools.management import add_tool


app = typer.Typer()
tool_app = typer.Typer()
app.add_typer(tool_app, name="tool")


def create_dependencies(config_path: str = "config.toml"):
    """依存関係を作成する"""
    config = load_config(config_path)
    db_conn = create_database_connection(config["database"]["path"])
    initialize_database(db_conn)
    return {
        "config": config,
        "db_conn": db_conn
    }


@tool_app.command("add")
def tool_add(
    name: str = typer.Option(..., "--name", "-n", help="ツール名"),
    description: str = typer.Option(..., "--description", "-d", help="ツールの説明"),
    source: str = typer.Option(..., "--source", "-s", help="ソースディレクトリ"),
    config_path: str = typer.Option("config.toml", "--config", help="設定ファイルのパス")
):
    """新しいツールを追加する"""
    try:
        deps = create_dependencies(config_path)
        
        # ソースディレクトリを絶対パスに変換
        source_path = Path(source).resolve()
        
        with deps["db_conn"] as db_conn:
            tool_id = add_tool(
                db_conn=db_conn,
                name=name,
                description=description,
                source_directory=str(source_path)
            )
        
        typer.echo(f"Tool '{name}' added successfully with ID: {tool_id}")
        
    except FileNotFoundError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except ValueError as e:
        typer.echo(f"Error: {e}", err=True)
        raise typer.Exit(1)
    except Exception as e:
        typer.echo(f"Unexpected error: {e}", err=True)
        raise typer.Exit(1)


if __name__ == "__main__":
    app()