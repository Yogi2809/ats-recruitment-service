import os
import re
import secrets
from dataclasses import dataclass

from argon2 import PasswordHasher
from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy import JSON, ForeignKey, Integer, String, create_engine, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, sessionmaker


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(320), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))


class WorkspaceRecord(Base):
    __tablename__ = "workspaces"

    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), primary_key=True)
    payload: Mapped[dict] = mapped_column(JSON, nullable=False)


@dataclass
class AuthStore:
    session_factory: sessionmaker[Session]
    signer: URLSafeTimedSerializer
    hasher: PasswordHasher

    def register(self, email: str, password: str) -> User | None:
        normalized = email.strip().lower()
        if not re.fullmatch(r"[^\s@]+@[^\s@]+\.[^\s@]+", normalized):
            raise ValueError("Enter a valid email address.")
        if len(password) < 12:
            raise ValueError("Password must have at least 12 characters.")
        with self.session_factory() as session:
            if session.scalar(select(User).where(User.email == normalized)):
                return None
            user = User(email=normalized, password_hash=self.hasher.hash(password))
            session.add(user)
            session.commit()
            session.refresh(user)
            return user

    def authenticate(self, email: str, password: str) -> User | None:
        with self.session_factory() as session:
            user = session.scalar(select(User).where(User.email == email.strip().lower()))
            if user is None:
                # Keep the expensive password check on both paths.
                try:
                    self.hasher.verify(self.hasher.hash("dummy-password-for-check"), password)
                except Exception:
                    pass
                return None
            try:
                return user if self.hasher.verify(user.password_hash, password) else None
            except Exception:
                return None

    def sign(self, user_id: int, keep_signed_in: bool) -> str:
        return self.signer.dumps({"id": user_id, "remember": keep_signed_in})

    def from_token(self, token: str | None) -> User | None:
        if not token:
            return None
        try:
            data = self.signer.loads(token, max_age=7 * 86400)
            if not data.get("remember"):
                self.signer.loads(token, max_age=86400)
        except (BadSignature, SignatureExpired):
            return None
        with self.session_factory() as session:
            return session.get(User, data["id"])


def create_auth_store(database_url: str | None, secret_key: str | None) -> AuthStore:
    url = database_url or os.getenv("DATABASE_URL", "sqlite:///./roletrace.db")
    if url.startswith("postgres://"):
        url = "postgresql+psycopg://" + url[len("postgres://") :]
    elif url.startswith("postgresql://"):
        url = "postgresql+psycopg://" + url[len("postgresql://") :]
    engine = create_engine(url, connect_args={"check_same_thread": False} if url.startswith("sqlite") else {})
    Base.metadata.create_all(engine)
    return AuthStore(
        session_factory=sessionmaker(engine, expire_on_commit=False),
        signer=URLSafeTimedSerializer(secret_key or os.getenv("SECRET_KEY") or secrets.token_urlsafe(32)),
        hasher=PasswordHasher(),
    )
