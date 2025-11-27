# db_config.py
from sqlalchemy import create_engine, Column, Integer, String, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DATABASE_URL = "sqlite:///./app.db"  # change if you use another DB

engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    password = Column(String, nullable=False)
    role = Column(String, default="user")

    # Explicitly tell SQLAlchemy which FK to use
    incidents = relationship(
        "Incident",
        back_populates="requester",
        foreign_keys="Incident.requester_id"
    )
    memberships = relationship("GroupMembership", back_populates="user")

# Groups
class Group(Base):
    __tablename__ = "groups"
    id = Column(Integer, primary_key=True)
    name = Column(String, unique=True, nullable=False)

    memberships = relationship("GroupMembership", back_populates="group")
    incidents = relationship("Incident", back_populates="assigned_group")

class GroupMembership(Base):
    __tablename__ = "group_memberships"
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    is_active = Column(Boolean, default=True)

    user = relationship("User", back_populates="memberships")
    group = relationship("Group", back_populates="memberships")

# Incidents
class Incident(Base):
    __tablename__ = "incidents"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    description = Column(Text)
    status = Column(String, default="open")
    requester_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    assigned_group_id = Column(Integer, ForeignKey("groups.id"), nullable=False)
    assigned_to_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)

    created_at = Column(DateTime(timezone=True))
    updated_at = Column(DateTime(timezone=True))
    closed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    requester = relationship(
        "User",
        foreign_keys=[requester_id],
        back_populates="incidents"
    )
    assigned_group = relationship("Group", back_populates="incidents")
    assigned_to = relationship("User", foreign_keys=[assigned_to_user_id])
    journals = relationship("IncidentJournal", back_populates="incident", cascade="all, delete-orphan")

# Journals
class IncidentJournal(Base):
    __tablename__ = "incident_journals"
    id = Column(Integer, primary_key=True)
    incident_id = Column(Integer, ForeignKey("incidents.id"), nullable=False)
    author_user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    comment = Column(Text, nullable=False)
    status = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True))

    incident = relationship("Incident", back_populates="journals")
    author = relationship("User")
