from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy import String, Index, ForeignKey
from datetime import datetime
from typing import List
from json import loads

class Base(DeclarativeBase):
    pass

class Tenant(Base):
    __tablename__ = 'tenants'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    domain: Mapped[str] = mapped_column(String(12), nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now())

    __table_args__ = (
        Index('domain_idx', 'domain'),
    )

# python tenant

class PythonTenantBase(DeclarativeBase):
    pass

class Admin(PythonTenantBase):
    __tablename__ = 'admins'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    password: Mapped[str] = mapped_column(String(150), nullable=False)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now())

    __table_args__ = (
        Index('email_idx', 'email'),
        Index('email_&_password_idx', 'email', 'password')
    )

    def to_json(self) -> dict:
        return {
            'id': self.id,
            'email': self.email,
            'password': self.password,
            'created_at': self.created_at.strftime('%d.%m.%Y, %H:%M')
        }

class User(PythonTenantBase):
    __tablename__ = 'users'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    fullname: Mapped[str] = mapped_column(String(150), nullable=False, unique=False)
    email: Mapped[str] = mapped_column(String(150), nullable=False, unique=True)
    solutions: Mapped[List['Solution']] = relationship(
        back_populates='user', cascade='all, delete-orphan'
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now())

    __table_args__ = (
        Index('email_idx', 'email'),
    )

    def to_json(self) -> dict:
        return {
            'id': self.id,
            'fullname': self.fullname,
            'email': self.email,
            'solutions': [solution.to_json() for solution in self.solutions],
            'created_at': self.created_at.strftime('%d.%m.%Y, %H:%M')
        }

class Solution(PythonTenantBase):
    __tablename__ = 'solutions'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    filename: Mapped[str] = mapped_column(String(150), nullable=False, unique=False)
    mark: Mapped[float] = mapped_column(nullable=True, default=0.0)
    checked: Mapped[bool] = mapped_column(nullable=False, default=False)
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id', ondelete='SET NULL'), nullable=True)
    task_id: Mapped[int] = mapped_column(ForeignKey('tasks.id', ondelete='SET NULL'), nullable=True)
    user: Mapped['User'] = relationship(back_populates='solutions', passive_deletes=True)
    task: Mapped['Task'] = relationship(back_populates='solutions', passive_deletes=True)
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now())

    __table_args__ = (
        Index('user_id_idx', 'user_id'),
        Index('task_id_idx', 'task_id'),
    )

    def to_json(self) -> dict:
        return {
            'id': self.id,
            'filename': self.filename,
            'mark': self.mark,
            'checked': self.checked,
            'user_id': self.user_id,
            'task_id': self.task_id,
            'task': self.task.to_json() if self.task else None,
            'created_at': self.created_at.strftime('%d.%m.%Y, %H:%M')
        }

class Task(PythonTenantBase):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(autoincrement=True, primary_key=True)
    task_description: Mapped[str] = mapped_column(String(256), nullable=False, unique=True)
    tags: Mapped[str] = mapped_column(String(256), nullable=False, default='[]')
    return_values: Mapped[str] = mapped_column(String(256), nullable=False, default='[]')
    solutions: Mapped[List['Solution']] = relationship(
        back_populates='task', cascade='all, delete-orphan'
    )
    created_at: Mapped[datetime] = mapped_column(nullable=False, default=lambda: datetime.now())

    __table_args__ = (
        Index('tags_idx', 'tags'),
    )

    def to_json(self) -> dict:
        return { 
            'id': self.id,
            'task_description': self.task_description,
            'tags': loads(self.tags),
            'return_values': loads(self.return_values),
            'created_at': self.created_at.strftime('%d.%m.%Y, %H:%M')
        }
    
# end python tenant

# alembic init alembic
# alembic revision --autogenerate -m "Added tenants table" 
# alembic upgrade head