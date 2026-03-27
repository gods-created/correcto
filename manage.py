from click import group, option
from typing import Optional
from core.management.commands.create_tasks import create_tasks as create_tasks_command

@group()
def cli() -> None:
    pass 

@cli.command('create_tasks')
@option('--filename', type=str, default=None)
def create_tasks(filename: Optional[str] = None) -> None:
    if not filename:
        return 
    
    create_tasks_command(filename)

if __name__ == '__main__':
    cli()