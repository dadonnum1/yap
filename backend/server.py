from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
import bcrypt
from jose import JWTError, jwt
import hashlib
from emergentintegrations.llm.chat import LlmChat, UserMessage

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ['DB_NAME']]

# JWT settings
JWT_SECRET = os.environ.get('JWT_SECRET', 'yapping_jwt_secret_key_2025')
JWT_ALGORITHM = os.environ.get('JWT_ALGORITHM', 'HS256')
JWT_EXPIRATION_HOURS = int(os.environ.get('JWT_EXPIRATION_HOURS', '24'))

# LLM settings
EMERGENT_LLM_KEY = os.environ.get('EMERGENT_LLM_KEY')

# Create the main app
app = FastAPI(title="Yapping API", description="API for generating tweets about crypto projects")
api_router = APIRouter(prefix="/api")

# Security will be instantiated per request

# Models
class User(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    email: EmailStr
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class UserCreate(BaseModel):
    email: EmailStr
    password: str

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    is_active: bool

class Company(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    twitter_handle: str  # @company format
    company_name: str
    description: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class CompanyCreate(BaseModel):
    twitter_handle: str
    company_name: str
    description: Optional[str] = None

class CompanyResponse(BaseModel):
    id: str
    twitter_handle: str
    company_name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool

class Tweet(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    company_id: str
    content: str
    content_hash: str
    generated_at: datetime = Field(default_factory=datetime.utcnow)
    copied_at: Optional[datetime] = None

class TweetResponse(BaseModel):
    id: str
    company_id: str
    content: str
    generated_at: datetime
    copied_at: Optional[datetime]
    company_name: str
    twitter_handle: str

class TweetGenerate(BaseModel):
    company_id: str
    count: Optional[int] = 1

class Token(BaseModel):
    access_token: str
    token_type: str

# Utility functions
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode('utf-8'), hashed.encode('utf-8'))

def create_access_token(data: dict):
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

def hash_content(content: str) -> str:
    return hashlib.md5(content.encode()).hexdigest()

async def get_current_user(authorization: str = Header(None)) -> dict:
    """Dependency to get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated"
        )
    
    token = authorization.split(" ")[1]
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Query user from database
    user = await db.users.find_one({"id": user_id, "is_active": True})
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    return user

async def generate_tweet_content(company_name: str, twitter_handle: str, description: str = "") -> str:
    """Generate positive tweet content about a company using LLM"""
    try:
        # Create system message for positive tweet generation
        system_message = f"""You are a crypto enthusiast and content creator specializing in writing engaging, positive tweets about blockchain and crypto projects.

Generate a short, positive, and engaging tweet (under 280 characters) about {company_name} ({twitter_handle}). 

Guidelines:
- Be genuinely positive and enthusiastic
- Include recent developments, technology highlights, or community achievements
- Make it sound authentic, not overly promotional
- MUST include the {twitter_handle} mention for airdrop credit
- Use relevant crypto/blockchain hashtags
- Keep it under 280 characters
- Sound like an excited community member, not a marketing bot

{f"Additional context: {description}" if description else ""}

Generate ONE tweet only, no explanations or alternatives."""

        # Initialize LLM chat
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"tweet_gen_{uuid.uuid4()}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")

        # Create user message
        user_message = UserMessage(
            text=f"Generate a positive, engaging tweet about {company_name} {twitter_handle}. Include the @mention and keep it under 280 characters."
        )

        # Send message and get response
        response = await chat.send_message(user_message)
        
        # Clean up the response
        tweet_content = response.strip()
        
        # Ensure twitter handle is included
        if twitter_handle not in tweet_content:
            tweet_content = f"{tweet_content} {twitter_handle}"
        
        # Truncate if too long
        if len(tweet_content) > 280:
            tweet_content = tweet_content[:277] + "..."
            
        return tweet_content
        
    except Exception as e:
        logging.error(f"Error generating tweet content: {str(e)}")
        # Fallback tweet
        return f"Amazing developments happening at {twitter_handle}! The future of blockchain is looking bright 🚀 #crypto #blockchain #web3"

# Auth Routes
@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserCreate):
    # Check if user already exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = hash_password(user_data.password)
    user = User(
        email=user_data.email,
        password_hash=hashed_password
    )
    
    await db.users.insert_one(user.dict())
    return UserResponse(**user.dict())

@api_router.post("/auth/login", response_model=Token)
async def login(user_data: UserLogin):
    # Find user
    user = await db.users.find_one({"email": user_data.email, "is_active": True})
    if not user or not verify_password(user_data.password, user["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user["id"]})
    return Token(access_token=access_token, token_type="bearer")

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# Company Routes
@api_router.post("/companies", response_model=CompanyResponse)
async def create_company(company_data: CompanyCreate, current_user: dict = Depends(get_current_user)):
    # Ensure twitter handle starts with @
    twitter_handle = company_data.twitter_handle
    if not twitter_handle.startswith('@'):
        twitter_handle = '@' + twitter_handle
    
    # Check if company already exists for this user
    existing_company = await db.companies.find_one({
        "user_id": current_user["id"],
        "twitter_handle": twitter_handle,
        "is_active": True
    })
    if existing_company:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Company already exists in your list"
        )
    
    # Create new company
    company = Company(
        user_id=current_user["id"],
        twitter_handle=twitter_handle,
        company_name=company_data.company_name,
        description=company_data.description
    )
    
    await db.companies.insert_one(company.dict())
    return CompanyResponse(**company.dict())

@api_router.get("/companies", response_model=List[CompanyResponse])
async def get_companies(current_user: dict = Depends(get_current_user)):
    companies = await db.companies.find({
        "user_id": current_user["id"],
        "is_active": True
    }).to_list(1000)
    return [CompanyResponse(**company) for company in companies]

@api_router.delete("/companies/{company_id}")
async def delete_company(company_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.companies.update_one(
        {"id": company_id, "user_id": current_user["id"]},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    return {"message": "Company removed successfully"}

# Tweet Generation Routes
@api_router.post("/tweets/generate", response_model=List[TweetResponse])
async def generate_tweets(tweet_data: TweetGenerate, current_user: dict = Depends(get_current_user)):
    # Get company
    company = await db.companies.find_one({
        "id": tweet_data.company_id,
        "user_id": current_user["id"],
        "is_active": True
    })
    if not company:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Company not found"
        )
    
    generated_tweets = []
    for _ in range(min(tweet_data.count, 5)):  # Limit to 5 tweets per request
        # Generate tweet content
        content = await generate_tweet_content(
            company["company_name"],
            company["twitter_handle"],
            company.get("description", "")
        )
        
        content_hash = hash_content(content)
        
        # Check if this exact tweet was already generated
        existing_tweet = await db.tweets.find_one({
            "user_id": current_user["id"],
            "content_hash": content_hash
        })
        
        if not existing_tweet:
            # Create new tweet
            tweet = Tweet(
                user_id=current_user["id"],
                company_id=tweet_data.company_id,
                content=content,
                content_hash=content_hash
            )
            
            await db.tweets.insert_one(tweet.dict())
            
            tweet_response = TweetResponse(
                **tweet.dict(),
                company_name=company["company_name"],
                twitter_handle=company["twitter_handle"]
            )
            generated_tweets.append(tweet_response)
    
    if not generated_tweets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No new tweets could be generated (all duplicates)"
        )
    
    return generated_tweets

@api_router.post("/tweets/generate-daily")
async def generate_daily_tweets(current_user: dict = Depends(get_current_user)):
    """Generate daily tweets for all user's companies"""
    companies = await db.companies.find({
        "user_id": current_user["id"],
        "is_active": True
    }).to_list(1000)
    
    if not companies:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No companies found. Add some companies first!"
        )
    
    all_tweets = []
    
    for company in companies:
        # Generate 1 tweet per company daily
        content = await generate_tweet_content(
            company["company_name"],
            company["twitter_handle"],
            company.get("description", "")
        )
        
        content_hash = hash_content(content)
        
        # Check if this exact tweet was already generated today
        today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        existing_tweet = await db.tweets.find_one({
            "user_id": current_user["id"],
            "company_id": company["id"],
            "generated_at": {"$gte": today},
            "content_hash": content_hash
        })
        
        if not existing_tweet:
            # Create new tweet
            tweet = Tweet(
                user_id=current_user["id"],
                company_id=company["id"],
                content=content,
                content_hash=content_hash
            )
            
            await db.tweets.insert_one(tweet.dict())
            
            tweet_response = TweetResponse(
                **tweet.dict(),
                company_name=company["company_name"],
                twitter_handle=company["twitter_handle"]
            )
            all_tweets.append(tweet_response)
    
    return {
        "message": f"Generated {len(all_tweets)} new tweets",
        "tweets": all_tweets
    }

@api_router.get("/tweets", response_model=List[TweetResponse])
async def get_tweets(current_user: dict = Depends(get_current_user)):
    # Get tweets with company information
    pipeline = [
        {"$match": {"user_id": current_user["id"]}},
        {"$lookup": {
            "from": "companies",
            "localField": "company_id",
            "foreignField": "id",
            "as": "company"
        }},
        {"$unwind": "$company"},
        {"$sort": {"generated_at": -1}},
        {"$limit": 100}
    ]
    
    tweets = await db.tweets.aggregate(pipeline).to_list(100)
    
    return [
        TweetResponse(
            id=tweet["id"],
            company_id=tweet["company_id"],
            content=tweet["content"],
            generated_at=tweet["generated_at"],
            copied_at=tweet.get("copied_at"),
            company_name=tweet["company"]["company_name"],
            twitter_handle=tweet["company"]["twitter_handle"]
        )
        for tweet in tweets
    ]

@api_router.post("/tweets/{tweet_id}/mark-copied")
async def mark_tweet_copied(tweet_id: str, current_user: dict = Depends(get_current_user)):
    result = await db.tweets.update_one(
        {"id": tweet_id, "user_id": current_user["id"]},
        {"$set": {"copied_at": datetime.utcnow()}}
    )
    if result.matched_count == 0:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tweet not found"
        )
    return {"message": "Tweet marked as copied"}

# Health check
@api_router.get("/")
async def root():
    return {"message": "Yapping API is running! Ready to generate tweets for airdrop hunting! 🚀"}

# Debug endpoints removed

# Include router
app.include_router(api_router)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()