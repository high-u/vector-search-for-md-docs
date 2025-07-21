import typer

from .utilities.config import load_config
from .interfaces.database.connection import create_database_connection
from .interfaces.database.schema import initialize_database
from .interfaces.filesystem.validation import validate_directory_path
from .core.tools.management import add_tool


app = typer.Typer()
tool_app = typer.Typer()
app.add_typer(tool_app, name="tool")


def create_dependencies(config_path: str = "config.toml"):
    """Create dependencies"""
    config = load_config(config_path)
    db_conn = create_database_connection(config["database"]["path"])
    initialize_database(db_conn)
    return {
        "config": config,
        "db_conn": db_conn,
        "validate_directory": validate_directory_path
    }


@tool_app.command("add")
def tool_add(
    name: str = typer.Option(..., "--name", "-n", help="Tool name"),
    description: str = typer.Option(..., "--description", "-d", help="Tool description"),
    source: str = typer.Option(..., "--source", "-s", help="Source directory"),
    config_path: str = typer.Option("config.toml", "--config", help="Configuration file path")
):
    """Add a new tool"""
    deps = create_dependencies(config_path)
    
    with deps["db_conn"] as db_conn:
        tool_id = add_tool(
            db_conn=db_conn,
            name=name,
            description=description,
            source_directory=source,
            validate_directory=deps["validate_directory"]
        )
    
    typer.echo(f"Tool '{name}' added successfully with ID: {tool_id}")


if __name__ == "__main__":
    app()