#!/usr/bin/env python3
"""
Additional test for style clone feature with different examples
"""

import asyncio
import aiohttp
import json

BACKEND_URL = "https://yapping-saas.preview.emergentagent.com/api"

async def test_different_style_clones():
    """Test style clone with different example tweets"""
    
    # Login first
    async with aiohttp.ClientSession() as session:
        # Login
        login_payload = {
            "email": "testuser@example.com",
            "password": "testpassword123"
        }
        
        async with session.post(f"{BACKEND_URL}/auth/login", json=login_payload) as response:
            if response.status != 200:
                print("❌ Login failed")
                return
            
            data = await response.json()
            auth_token = data.get("access_token")
            headers = {"Authorization": f"Bearer {auth_token}"}
        
        # Get companies
        async with session.get(f"{BACKEND_URL}/companies", headers=headers) as response:
            if response.status != 200:
                print("❌ Failed to get companies")
                return
            
            companies = await response.json()
            if not companies:
                print("❌ No companies found")
                return
            
            company_id = companies[0]["id"]
            print(f"✅ Using company: {companies[0]['company_name']} ({companies[0]['twitter_handle']})")
        
        # Test different style examples
        test_examples = [
            {
                "name": "Excited Discovery",
                "tweet": "Just discovered this amazing DeFi protocol! 🚀 The yields are incredible! #DeFi #crypto"
            },
            {
                "name": "Technical Analysis", 
                "tweet": "The tokenomics on this project are actually solid. Low supply, strong utility, and real adoption. This could be big."
            },
            {
                "name": "Community Hype",
                "tweet": "LFG! 🔥 This community is absolutely insane! The energy here is unmatched! To the moon! 🌙 #crypto #bullish"
            },
            {
                "name": "Casual Observation",
                "tweet": "Been watching this project for months. Finally decided to ape in. The team delivers consistently."
            }
        ]
        
        print("\n🧪 Testing Style Clone with Different Examples:")
        print("=" * 60)
        
        for i, example in enumerate(test_examples, 1):
            payload = {
                "company_id": company_id,
                "example_tweet": example["tweet"],
                "generation_type": "style_clone"
            }
            
            async with session.post(f"{BACKEND_URL}/tweets/custom", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    print(f"\n{i}. {example['name']}:")
                    print(f"   Original: {example['tweet']}")
                    print(f"   Generated: {data.get('content')}")
                    print(f"   ✅ Success")
                else:
                    error_text = await response.text()
                    print(f"\n{i}. {example['name']}:")
                    print(f"   ❌ Failed: {error_text}")

if __name__ == "__main__":
    asyncio.run(test_different_style_clones())