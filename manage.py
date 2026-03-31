from click import group, option
from typing import Optional
from loguru import logger
from core.management.commands.create_tasks import create_tasks as create_tasks_command
from core.management.commands.delete_all_rows import delete_all_rows as delete_all_rows_command

@group()
def cli() -> None:
    pass 

@cli.command('create_tasks')
@option('--filename', type=str, default=None)
def create_tasks(filename: Optional[str] = None) -> None:
    if not filename:
        logger.info('Please, specify \'--filename\' option')
        return 
    
    create_tasks_command(filename)

@cli.command('delete_all_rows')
@option('--tenant', type=str, default=None)
def delete_all_rows(tenant: Optional[str] = None) -> None:
    if not tenant:
        logger.info('Please, specify \'--tenant\' option')
        return 
    
    delete_all_rows_command(tenant)

if __name__ == '__main__':
    cli()