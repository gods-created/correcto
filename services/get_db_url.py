from typing import Optional

def get_db_url(tenant: str) -> Optional[str]:
    import configs

    return configs.TENANTS.get(tenant, {}).get('db_url')
