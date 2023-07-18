from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

SQLALCHEMY_DATABASE_URL = "postgresql://admin:aOXmJA2HnSHFnEeTME3scoDUbVPChmIP@dpg-ciqph3enqql4qa2vr340-a.frankfurt-postgres.render.com/reservations_czwi"

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()
