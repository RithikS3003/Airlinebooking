from fastapi import FastAPI, APIRouter, Depends, HTTPException
from sqlalchemy import text
from starlette.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from pydantic import BaseModel
from typing import Optional, List
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from datetime import datetime
import pytz
# Create FastAPI app instance
app = FastAPI()

# CORS middleware setup
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Continue with the rest of the code
router = APIRouter()

# Database setup
DATABASE_URL = "postgresql+asyncpg://postgres:1234@localhost:5432/postgres"
engine = create_async_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(bind=engine, class_=AsyncSession, autocommit=False, autoflush=False)

# Model Base
Base = declarative_base()

# Database dependency
async def get_db():
    async with SessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

#BaseModel Class User
class AirlinebookCreate(BaseModel):

    Name: str
    password: str
    phno: str
    details: str
    AadharNo: str
    Validate: bool
    from_place: str
    To_place: str

class AirlinebookResponseData(BaseModel):
    passenger_id: str
    Name: str
    password: str
    phno: str
    details: str
    AadharNo: str
    Validate: bool
    from_place: str
    To_place: str

class AirlinebookResponse(BaseModel):
    message: str
    data: List[AirlinebookResponseData]

#BaseModel Class Admin
class Airline_AdminCreate(BaseModel):
    Airplane_no: int  # Add this line
    Airplane_name: str
    Airplane_pilotName: str
    Airplane_ticketcost: int
    airplane_from_place: str
    airplane_to_place: str
    airplane_datetime: datetime  # Use datetime instead of str
    Admin_id: str


class Airline_AdminResponseData(BaseModel):
    Airplane_no: int
    Airplane_name: str
    Airplane_pilotName: str
    Airplane_ticketcost: int
    airplane_from_place: str
    airplane_to_place: str
    airplane_datetime: datetime
    Admin_id: str

class Airline_AdminResponse(BaseModel):
    message: str
    data : List[Airline_AdminResponseData]

#Available in Airplanes:


#Generate User Passenger Id
async def generate_passenger_id(db: AsyncSession) -> str:
    query = text("SELECT passenger_id FROM aerobooking ORDER BY passenger_id DESC LIMIT 1")
    result = await db.execute(query)
    pass_id = result.scalar()

    if pass_id is not None:
        prefix, num_part = pass_id.split('_')
        new_id_number = int(num_part) + 1
        return f"{prefix}_{new_id_number:04d}"
    else:
        return "Passenger_0001"

#CRUD Functions in FastAPI
@app.get("/Airline", response_model=AirlinebookResponse)
async def get_details(db: AsyncSession = Depends(get_db)):
    try:
        query = text("SELECT passenger_id, name, password, phno, details, AadharNo, Validate,from_place, To_place FROM aerobooking ORDER BY passenger_id ASC ")
        result = await db.execute(query)
        rows = result.fetchall()
        return AirlinebookResponse(
            message="success",
            data=[
                AirlinebookResponseData(
                    passenger_id=row[0],
                    Name=row[1],
                    password=row[2],
                    phno=row[3],
                    details=row[4],
                    AadharNo=row[5],
                    Validate=bool(row[6]),
                    from_place=row[7],
                    To_place=row[8]
                ) for row in rows
            ]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.get("/Airline/{name}/{password}", response_model=AirlinebookResponse)
async def passenger_get(name:str ,password: str, db: AsyncSession = Depends(get_db)):
    try:

        query = text("SELECT passenger_id, name,password,phno,details,Aadharno,validate, from_place, To_place FROM aerobooking WHERE name = :name and password = :password")
        result = await db.execute(query, {"name": name,"password":password})
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Passenger not found.")

        return AirlinebookResponse(
            message="success",
            data=[AirlinebookResponseData(
                    passenger_id=row[0],
                    Name=row[1],
                    password=row[2],
                    phno=row[3],
                    details=row[4],
                    AadharNo=row[5],
                    Validate=bool(row[6]),
                    from_place=row[7],
                    To_place=row[8]
                ) for row in rows
            ]
        )
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@app.post("/AirLineBooking", response_model=AirlinebookResponse)
async def create_details(passenger_create: AirlinebookCreate, db: AsyncSession = Depends(get_db)):
    try:
        new_passenger_id = await generate_passenger_id(db)
        create_query = text(
            "INSERT INTO aerobooking(passenger_id, name, password, phno, details, AadharNo, Validate, from_place, To_place) "
            "VALUES (:passenger_id, :name, :password, :phno, :details, :AadharNo, :Validate, :from_place, :To_place)"
        )
        await db.execute(create_query, {
            'passenger_id': new_passenger_id,
            'name': passenger_create.Name,
            'password': passenger_create.password,
            'phno': passenger_create.phno,
            'details': passenger_create.details,
            'AadharNo': passenger_create.AadharNo,
            'Validate': passenger_create.Validate,
            'from_place':passenger_create.from_place,
            'To_place':passenger_create.To_place
        })
        await db.commit()

        return AirlinebookResponse(
            message="Passenger details added successfully",
            data=[AirlinebookResponseData(
                passenger_id=new_passenger_id,
                Name=passenger_create.Name,
                password=passenger_create.password,
                phno=passenger_create.phno,
                details=passenger_create.details,
                AadharNo=passenger_create.AadharNo,
                Validate=passenger_create.Validate,
                from_place=passenger_create.from_place,  # Include this
                To_place=passenger_create.To_place  # Include this
            )]
        )

    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Passenger creation failed due to duplicate or invalid data.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")





#--------------------------------------Admin----------------------------------------------------------------------------


@app.get("/AirlineAdmin/{Admin_id}", response_model=Airline_AdminResponse)
async def admin_get(Admin_id: str, db: AsyncSession = Depends(get_db)):
    try:
        # Validation query
        admin_validate = text("SELECT Admin_id FROM airplane WHERE Admin_id = :Admin_id")
        admin_result = await db.execute(admin_validate, {"Admin_id": Admin_id})
        correct_admin = admin_result.fetchone()

        if not correct_admin:
            raise HTTPException(status_code=404, detail="Invalid Admin_id!")

        # Main query to fetch admin details
        query = text("""
            SELECT Admin_id, Airplane_no, Airplane_name, Airplane_pilotName, airplane_ticketcost,airplane_from_place,airplane_to_place, airplane_datetime 
            FROM airplane 
            WHERE Admin_id = :Admin_id
        """)
        result = await db.execute(query, {"Admin_id": Admin_id})
        rows = result.fetchall()

        if not rows:
            raise HTTPException(status_code=404, detail="Admin not found.")

        # Constructing response data
        return Airline_AdminResponse(
            message="success",
            data=[
                Airline_AdminResponseData(
                    Airplane_no=row[0],
                    Airplane_name=row[1],
                    Airplane_pilotName=row[2],
                    Airplane_ticketcost=row[3],
                    airplane_from_place=row[4],
                    airplane_to_place=row[5],
                    airplane_datetime=row[6],
                    Admin_id=row[7],
                ) for row in rows
            ]
        )

    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.post("/AirLineAdmin", response_model=Airline_AdminResponse)
async def create_details(Admin_create: Airline_AdminCreate, db: AsyncSession = Depends(get_db)):
    try:
        # Make datetime naive
        naive_datetime = Admin_create.airplane_datetime.replace(tzinfo=None)

        create_query = text(
            "INSERT INTO airplane (airplane_no, airplane_name, airplane_pilotName, airplane_ticketcost, airplane_from_place, airplane_to_place, airplane_datetime, admin_id) "
            "VALUES (:Airplane_no, :Airplane_name, :Airplane_pilotName, :Airplane_ticketcost, :airplane_from_place, :airplane_to_place, :airplane_datetime, :Admin_id)"
        )
        await db.execute(create_query, {
            'Airplane_no': Admin_create.Airplane_no,
            'Airplane_name': Admin_create.Airplane_name,
            'Airplane_pilotName': Admin_create.Airplane_pilotName,
            'Airplane_ticketcost': Admin_create.Airplane_ticketcost,
            'airplane_from_place': Admin_create.airplane_from_place,
            'airplane_to_place': Admin_create.airplane_to_place,
            'airplane_datetime': naive_datetime,  # Use naive datetime
            'Admin_id': Admin_create.Admin_id,
        })
        await db.commit()

        return Airline_AdminResponse(
            message="Admin airplane details added successfully",
            data=[Airline_AdminResponseData(
                Airplane_no=Admin_create.Airplane_no,
                Airplane_name=Admin_create.Airplane_name,
                Airplane_pilotName=Admin_create.Airplane_pilotName,
                Airplane_ticketcost=Admin_create.Airplane_ticketcost,
                airplane_from_place=Admin_create.airplane_from_place,
                airplane_to_place=Admin_create.airplane_to_place,
                airplane_datetime=naive_datetime,  # Use naive datetime
                Admin_id=Admin_create.Admin_id,
            )]
        )
    except IntegrityError:
        await db.rollback()
        raise HTTPException(status_code=400, detail="Admin creation failed due to duplicate or invalid data.")
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

