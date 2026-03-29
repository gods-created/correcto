from models import PythonTenantBase
from configs import TENANTS
from loguru import logger
from sqlalchemy.orm import Session, registry
from sqlalchemy import create_engine, delete
from sqlalchemy.exc import IntegrityError, InterfaceError, DatabaseError

TENANT_MODELS = {
    'python': PythonTenantBase
}

def delete_all_rows(tenant: str) -> None:
    try:
        db_url = TENANTS.get(tenant, {}).get('db_url')
        if db_url is None:
            raise ValueError(f'DB didn\'t find for tenant with name \'{tenant}\'')
        
        base_model = TENANT_MODELS.get(tenant)
        if not base_model:
            raise ValueError(f'Base model didn\'t find for tenant with name \'{tenant}\'')

        session = None
        try:
            session = Session(
                bind=create_engine(
                    url=db_url,
                    echo=False
                )
            )
            
            mapper_registry = base_model.registry

            for mapper in mapper_registry.mappers:
                cls = mapper.class_

                stmt = delete(cls).where(cls.id > 0)
                session.execute(stmt)

            session.commit()

        except (IntegrityError, InterfaceError, DatabaseError) as e:
            err_derscription = str(e)
            if 'UNIQUE constraint failed' in err_derscription:
                err_derscription = 'The similar row is already existing.'

            if 'NOT NULL constraint failed' in err_derscription:
                err_derscription = 'Constraint for operation due to invalid field.'
               
            err_derscription += ' No row didn\'t add to table.'
            raise Exception(err_derscription)
        
        finally:
            if session:
                session.close()

    except ValueError as e:
        logger.error(str(e))

    except Exception as e:
        logger.error(str(e))
