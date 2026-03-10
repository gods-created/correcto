from routers import python_routers

TENANTS = {
    'python': {
        'routers': python_routers,
        'db_url': 'sqlite:///databases/python.sqlite'
    }
}