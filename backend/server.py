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

# Admin Models
class Admin(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    username: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    is_active: bool = True

class AdminLogin(BaseModel):
    username: str
    password: str

class AdminResponse(BaseModel):
    id: str
    username: str
    created_at: datetime
    is_active: bool

class SystemStats(BaseModel):
    total_users: int
    total_companies: int
    total_tweets: int
    active_users: int
    tweets_today: int

class UserWithStats(BaseModel):
    id: str
    email: str
    created_at: datetime
    is_active: bool
    company_count: int
    tweet_count: int
    last_tweet: Optional[datetime] = None

class CompanyWithUser(BaseModel):
    id: str
    twitter_handle: str
    company_name: str
    description: Optional[str]
    created_at: datetime
    is_active: bool
    user_email: str
    tweet_count: int

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

bearer = HTTPBearer()

async def get_current_user(token: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """Dependency to get current user from JWT token"""
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
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

async def get_current_admin(token: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    """Dependency to get current admin from JWT token"""
    try:
        payload = jwt.decode(token.credentials, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        admin_id: str = payload.get("sub")
        is_admin: bool = payload.get("is_admin", False)
        
        if admin_id is None or not is_admin:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Admin access required"
            )
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials"
        )
    
    # Query admin from database
    admin = await db.admins.find_one({"id": admin_id, "is_active": True})
    if admin is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Admin access required"
        )
    
    return admin

def create_admin_token(admin_id: str):
    """Create JWT token with admin privileges"""
    to_encode = {"sub": admin_id, "is_admin": True}
    expire = datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return encoded_jwt

import random
import re
from difflib import SequenceMatcher

def calculate_similarity(text1: str, text2: str) -> float:
    """Calculate similarity between two texts (0.0 to 1.0)"""
    return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()

async def check_tweet_uniqueness(new_tweet: str, company_id: str, min_similarity: float = 0.7) -> bool:
    """Check if tweet is sufficiently unique compared to existing tweets"""
    # Get all existing tweets for this company
    existing_tweets = await db.tweets.find({"company_id": company_id}).to_list(1000)
    
    # Also check against tweets from other companies to ensure global uniqueness
    all_tweets = await db.tweets.find({}).to_list(5000)  # Check last 5000 tweets
    
    for tweet in all_tweets:
        similarity = calculate_similarity(new_tweet, tweet["content"])
        if similarity > min_similarity:
            return False  # Too similar, not unique enough
    
    return True

async def generate_human_like_tweet(company_name: str, twitter_handle: str, description: str = "", attempt: int = 1) -> str:
    """Generate human-like tweet that passes AI detection"""
    
    # Different writing styles for variety
    styles = [
        "excited_community_member",
        "casual_investor", 
        "tech_enthusiast",
        "long_term_holder",
        "defi_user"
    ]
    
    # Different prompt approaches for uniqueness
    style = random.choice(styles)
    
    if style == "excited_community_member":
        system_message = f"""You're an excited crypto community member who genuinely loves {company_name}. Write like a real person on Twitter - use natural language, maybe some slang, and show real enthusiasm. You're not a marketer, just a fan sharing your thoughts.

Write a tweet about {company_name} that feels completely natural and human. Include {twitter_handle} naturally in your message.

Make it sound like something you'd actually say to friends, not a corporate announcement. Use casual language, maybe throw in some crypto slang. Keep it under 280 chars."""

    elif style == "casual_investor":
        system_message = f"""You're a casual crypto investor sharing your genuine thoughts about {company_name}. Write like you're talking to other investors in a Discord or Twitter space.

Share why you're bullish on {company_name} ({twitter_handle}) but keep it conversational and real. Use the kind of language actual crypto investors use - natural, sometimes imperfect, but authentic.

No corporate speak - just honest investor perspective. Under 280 characters."""

    elif style == "tech_enthusiast":
        system_message = f"""You're a tech-savvy person who appreciates the technical aspects of {company_name}. Write about what impresses you technically, but in a way that shows you really understand and use the product.

Mention {twitter_handle} naturally while discussing something specific you like about their tech or recent updates. Sound like someone who actually uses crypto products, not someone reading a script.

Keep it authentic and under 280 chars."""

    elif style == "long_term_holder":
        system_message = f"""You're someone who has been following {company_name} for a while and believes in the long-term vision. Share your perspective as someone who has seen the project evolve.

Include {twitter_handle} while talking about what keeps you excited about the project long-term. Write like you're sharing with other long-term believers.

Make it personal and genuine, under 280 characters."""

    else:  # defi_user
        system_message = f"""You're an active DeFi user who has had good experiences with {company_name}'s products. Write about your actual user experience in a natural way.

Mention {twitter_handle} while sharing something specific about using their platform or tools. Sound like someone who actually interacts with DeFi protocols regularly.

Keep it real and conversational, under 280 characters."""

    # Add randomness and human imperfections
    human_touches = [
        "Maybe add a small typo or informal contraction",
        "Use casual punctuation - maybe skip some periods or use multiple exclamation marks", 
        "Include some crypto Twitter slang naturally",
        "Maybe start with 'ngl' or 'tbh' or similar casual phrase",
        "Could use 'fr' (for real) or 'lowkey' naturally"
    ]
    
    human_touch = random.choice(human_touches)
    system_message += f"\n\nHuman touch: {human_touch}"
    
    try:
        # Initialize LLM chat with unique session
        chat = LlmChat(
            api_key=EMERGENT_LLM_KEY,
            session_id=f"human_tweet_{uuid.uuid4()}_{attempt}",
            system_message=system_message
        ).with_model("openai", "gpt-4o-mini")

        # Varied user prompts for more uniqueness
        prompts = [
            f"Write a natural, human tweet about {company_name} {twitter_handle}",
            f"Share your genuine thoughts on {company_name} {twitter_handle} like you're talking to friends",
            f"Create an authentic tweet about why you like {company_name} {twitter_handle}",
            f"Write something real about your experience with {company_name} {twitter_handle}",
            f"Share what excites you about {company_name} {twitter_handle} in a casual way"
        ]
        
        user_message = UserMessage(text=random.choice(prompts))
        response = await chat.send_message(user_message)
        
        # Clean up response
        tweet_content = response.strip()
        
        # Ensure twitter handle is included
        if twitter_handle not in tweet_content:
            # Add it naturally at the end if missing
            connectors = [" ", " - ", " 🚀 ", " 💪 ", " 🔥 "]
            tweet_content = f"{tweet_content}{random.choice(connectors)}{twitter_handle}"
        
        # Truncate if too long
        if len(tweet_content) > 280:
            tweet_content = tweet_content[:277] + "..."
            
        return tweet_content
        
    except Exception as e:
        logging.error(f"Error generating human-like tweet: {str(e)}")
        # Fallback with randomization
        fallbacks = [
            f"honestly {twitter_handle} keeps delivering 🔥 love what they're building",
            f"ngl {twitter_handle} has been one of my best crypto discoveries this year 💪",
            f"been using {twitter_handle} for months now and it just keeps getting better fr",
            f"lowkey {twitter_handle} is undervalued rn... their tech is actually insane 🚀",
            f"tbh {twitter_handle} community is something else. bullish long term 📈"
        ]
        return random.choice(fallbacks)

async def generate_tweet_content(company_name: str, twitter_handle: str, description: str = "") -> str:
    """Generate completely unique, human-like tweet content with AI detection evasion"""
    
    max_attempts = 10
    attempt = 1
    
    while attempt <= max_attempts:
        # Generate human-like tweet
        tweet_content = await generate_human_like_tweet(company_name, twitter_handle, description, attempt)
        
        # Check for uniqueness - we need to get company_id first
        # For now, we'll do a basic global uniqueness check
        is_unique = await check_global_tweet_uniqueness(tweet_content)
        
        if is_unique:
            logging.info(f"Generated unique tweet on attempt {attempt}")
            return tweet_content
        
        logging.info(f"Tweet not unique enough, attempt {attempt}/{max_attempts}")
        attempt += 1
    
    # If all attempts failed, create a highly randomized fallback
    random_elements = [
        ["honestly", "ngl", "tbh", "lowkey", "fr tho"],
        ["keeps delivering", "been crushing it", "going hard", "building different", "hitting different"],
        ["🔥", "💪", "🚀", "📈", "⚡"],
        ["love to see it", "here for it", "bullish af", "can't sleep on this", "this is it"],
        ["#crypto", "#blockchain", "#web3", "#defi", ""]
    ]
    
    elements = [random.choice(group) for group in random_elements]
    fallback = f"{elements[0]} {twitter_handle} {elements[1]} {elements[2]} {elements[3]} {elements[4]}".strip()
    
    return fallback

async def check_global_tweet_uniqueness(tweet_content: str) -> bool:
    """Check if tweet is unique across all generated tweets"""
    # Check against all existing tweets
    all_tweets = await db.tweets.find({}).to_list(10000)  # Check last 10k tweets
    
    for existing_tweet in all_tweets:
        similarity = calculate_similarity(tweet_content, existing_tweet["content"])
        if similarity > 0.6:  # If more than 60% similar, reject
            return False
    
    return True

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

# Admin Routes
@api_router.post("/admin/login", response_model=Token)
async def admin_login(admin_data: AdminLogin):
    # Find admin
    admin = await db.admins.find_one({"username": admin_data.username, "is_active": True})
    if not admin or not verify_password(admin_data.password, admin["password_hash"]):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create admin access token
    access_token = create_admin_token(admin["id"])
    return Token(access_token=access_token, token_type="bearer")

@api_router.get("/admin/me", response_model=AdminResponse)
async def get_admin_me(current_admin: dict = Depends(get_current_admin)):
    return AdminResponse(**current_admin)

@api_router.get("/admin/stats", response_model=SystemStats)
async def get_system_stats(current_admin: dict = Depends(get_current_admin)):
    # Get system statistics
    total_users = await db.users.count_documents({"is_active": True})
    total_companies = await db.companies.count_documents({"is_active": True})
    total_tweets = await db.tweets.count_documents({})
    active_users = await db.users.count_documents({"is_active": True})
    
    # Tweets created today
    today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    tweets_today = await db.tweets.count_documents({"generated_at": {"$gte": today}})
    
    return SystemStats(
        total_users=total_users,
        total_companies=total_companies,
        total_tweets=total_tweets,
        active_users=active_users,
        tweets_today=tweets_today
    )

@api_router.get("/admin/users", response_model=List[UserWithStats])
async def get_all_users(current_admin: dict = Depends(get_current_admin)):
    # Aggregation pipeline to get users with stats
    pipeline = [
        {"$match": {}},
        {"$lookup": {
            "from": "companies",
            "let": {"user_id": "$id"},
            "pipeline": [
                {"$match": {"$expr": {"$and": [
                    {"$eq": ["$user_id", "$$user_id"]},
                    {"$eq": ["$is_active", True]}
                ]}}}
            ],
            "as": "companies"
        }},
        {"$lookup": {
            "from": "tweets",
            "let": {"user_id": "$id"},
            "pipeline": [
                {"$match": {"$expr": {"$eq": ["$user_id", "$$user_id"]}}},
                {"$sort": {"generated_at": -1}},
                {"$limit": 1}
            ],
            "as": "last_tweet"
        }},
        {"$addFields": {
            "company_count": {"$size": "$companies"},
            "tweet_count": {"$size": {"$ifNull": [
                {"$lookup": {
                    "from": "tweets",
                    "localField": "id",
                    "foreignField": "user_id",
                    "as": "all_tweets"
                }}, []
            ]}},
            "last_tweet": {"$arrayElemAt": ["$last_tweet.generated_at", 0]}
        }},
        {"$project": {
            "password_hash": 0,
            "companies": 0,
            "all_tweets": 0
        }}
    ]
    
    users = await db.users.aggregate(pipeline).to_list(1000)
    
    result = []
    for user in users:
        # Count tweets for this user
        tweet_count = await db.tweets.count_documents({"user_id": user["id"]})
        
        result.append(UserWithStats(
            id=user["id"],
            email=user["email"],
            created_at=user["created_at"],
            is_active=user["is_active"],
            company_count=user.get("company_count", 0),
            tweet_count=tweet_count,
            last_tweet=user.get("last_tweet")
        ))
    
    return result

@api_router.get("/admin/companies", response_model=List[CompanyWithUser])
async def get_all_companies(current_admin: dict = Depends(get_current_admin)):
    # Aggregation pipeline to get companies with user info
    pipeline = [
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$unwind": "$user"},
        {"$sort": {"created_at": -1}}
    ]
    
    companies = await db.companies.aggregate(pipeline).to_list(1000)
    
    result = []
    for company in companies:
        # Count tweets for this company
        tweet_count = await db.tweets.count_documents({"company_id": company["id"]})
        
        result.append(CompanyWithUser(
            id=company["id"],
            twitter_handle=company["twitter_handle"],
            company_name=company["company_name"],
            description=company.get("description"),
            created_at=company["created_at"],
            is_active=company["is_active"],
            user_email=company["user"]["email"],
            tweet_count=tweet_count
        ))
    
    return result

@api_router.get("/admin/tweets")
async def get_all_tweets(current_admin: dict = Depends(get_current_admin)):
    # Get all tweets with user and company information
    pipeline = [
        {"$lookup": {
            "from": "companies",
            "localField": "company_id",
            "foreignField": "id",
            "as": "company"
        }},
        {"$lookup": {
            "from": "users",
            "localField": "user_id",
            "foreignField": "id",
            "as": "user"
        }},
        {"$unwind": "$company"},
        {"$unwind": "$user"},
        {"$sort": {"generated_at": -1}},
        {"$limit": 200}
    ]
    
    tweets = await db.tweets.aggregate(pipeline).to_list(200)
    
    return [
        {
            "id": tweet["id"],
            "content": tweet["content"],
            "generated_at": tweet["generated_at"],
            "copied_at": tweet.get("copied_at"),
            "company_name": tweet["company"]["company_name"],
            "twitter_handle": tweet["company"]["twitter_handle"],
            "user_email": tweet["user"]["email"]
        }
        for tweet in tweets
    ]

@api_router.post("/admin/users/{user_id}/toggle")
async def toggle_user_status(user_id: str, current_admin: dict = Depends(get_current_admin)):
    user = await db.users.find_one({"id": user_id})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    new_status = not user["is_active"]
    await db.users.update_one(
        {"id": user_id},
        {"$set": {"is_active": new_status}}
    )
    
    return {"message": f"User {'activated' if new_status else 'deactivated'} successfully"}

@api_router.delete("/admin/companies/{company_id}")
async def admin_delete_company(company_id: str, current_admin: dict = Depends(get_current_admin)):
    result = await db.companies.update_one(
        {"id": company_id},
        {"$set": {"is_active": False}}
    )
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Company not found")
    
    return {"message": "Company deactivated successfully"}

@api_router.post("/admin/setup")
async def setup_admin():
    """One-time setup endpoint to create default admin"""
    # Check if admin already exists
    existing_admin = await db.admins.find_one({})
    if existing_admin:
        raise HTTPException(status_code=400, detail="Admin already exists")
    
    # Create default admin
    admin = Admin(
        username="admin",
        password_hash=hash_password("admin123")
    )
    
    await db.admins.insert_one(admin.dict())
    
    return {"message": "Admin created successfully", "username": "admin", "password": "admin123"}

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