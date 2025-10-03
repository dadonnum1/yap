#!/usr/bin/env python3
"""
Backend API Testing Script for Yapping SaaS
Tests the custom tweet clone feature and other backend functionality
"""

import asyncio
import aiohttp
import json
import os
from datetime import datetime

# Get backend URL from environment
BACKEND_URL = "https://yapping-saas.preview.emergentagent.com/api"

class BackendTester:
    def __init__(self):
        self.session = None
        self.auth_token = None
        self.test_user_email = "testuser@example.com"
        self.test_user_password = "testpassword123"
        self.test_results = []
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
    
    def log_result(self, test_name, success, message, details=None):
        """Log test result"""
        result = {
            "test": test_name,
            "success": success,
            "message": message,
            "timestamp": datetime.now().isoformat(),
            "details": details or {}
        }
        self.test_results.append(result)
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name} - {message}")
        if details and not success:
            print(f"   Details: {details}")
    
    async def register_test_user(self):
        """Register a test user for authentication"""
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/register", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.log_result("User Registration", True, "Test user registered successfully", {"user_id": data.get("id")})
                    return True
                elif response.status == 400:
                    # User might already exist, try to login
                    return await self.login_test_user()
                else:
                    error_text = await response.text()
                    self.log_result("User Registration", False, f"Registration failed with status {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("User Registration", False, f"Registration error: {str(e)}")
            return False
    
    async def login_test_user(self):
        """Login test user and get auth token"""
        try:
            payload = {
                "email": self.test_user_email,
                "password": self.test_user_password
            }
            
            async with self.session.post(f"{BACKEND_URL}/auth/login", json=payload) as response:
                if response.status == 200:
                    data = await response.json()
                    self.auth_token = data.get("access_token")
                    self.log_result("User Login", True, "Login successful", {"token_type": data.get("token_type")})
                    return True
                else:
                    error_text = await response.text()
                    self.log_result("User Login", False, f"Login failed with status {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("User Login", False, f"Login error: {str(e)}")
            return False
    
    async def create_test_company(self):
        """Create a test company for tweet generation"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "twitter_handle": "@ethereum",
                "company_name": "Ethereum",
                "description": "Leading blockchain platform for smart contracts and DeFi"
            }
            
            async with self.session.post(f"{BACKEND_URL}/companies", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    company_id = data.get("id")
                    self.log_result("Company Creation", True, "Test company created successfully", {"company_id": company_id, "name": data.get("company_name")})
                    return company_id
                elif response.status == 400:
                    # Company might already exist, get existing companies
                    return await self.get_existing_company()
                else:
                    error_text = await response.text()
                    self.log_result("Company Creation", False, f"Company creation failed with status {response.status}", {"error": error_text})
                    return None
                    
        except Exception as e:
            self.log_result("Company Creation", False, f"Company creation error: {str(e)}")
            return None
    
    async def get_existing_company(self):
        """Get existing company ID"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.get(f"{BACKEND_URL}/companies", headers=headers) as response:
                if response.status == 200:
                    companies = await response.json()
                    if companies:
                        company_id = companies[0]["id"]
                        self.log_result("Get Existing Company", True, "Retrieved existing company", {"company_id": company_id, "name": companies[0].get("company_name")})
                        return company_id
                    else:
                        self.log_result("Get Existing Company", False, "No companies found")
                        return None
                else:
                    error_text = await response.text()
                    self.log_result("Get Existing Company", False, f"Failed to get companies with status {response.status}", {"error": error_text})
                    return None
                    
        except Exception as e:
            self.log_result("Get Existing Company", False, f"Get companies error: {str(e)}")
            return None
    
    async def test_custom_tweet_style_clone(self, company_id):
        """Test the custom tweet style clone feature"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "company_id": company_id,
                "example_tweet": "Just discovered this amazing DeFi protocol! 🚀 The yields are incredible! #DeFi #crypto",
                "generation_type": "style_clone"
            }
            
            async with self.session.post(f"{BACKEND_URL}/tweets/custom", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tweet_content = data.get("content", "")
                    generation_type = data.get("generation_type", "")
                    source_input = data.get("source_input", "")
                    
                    # Verify the response structure
                    success = all([
                        tweet_content,
                        generation_type == "style_clone",
                        source_input == payload["example_tweet"],
                        data.get("company_name"),
                        data.get("twitter_handle")
                    ])
                    
                    if success:
                        self.log_result("Custom Tweet Style Clone", True, "Style clone tweet generated successfully", {
                            "original_tweet": payload["example_tweet"],
                            "generated_tweet": tweet_content,
                            "generation_type": generation_type,
                            "company": data.get("company_name"),
                            "handle": data.get("twitter_handle")
                        })
                    else:
                        self.log_result("Custom Tweet Style Clone", False, "Response missing required fields", {"response": data})
                    
                    return success
                else:
                    error_text = await response.text()
                    self.log_result("Custom Tweet Style Clone", False, f"Style clone failed with status {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Custom Tweet Style Clone", False, f"Style clone error: {str(e)}")
            return False
    
    async def test_custom_tweet_idea_generation(self, company_id):
        """Test the custom tweet idea generation feature"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "company_id": company_id,
                "custom_idea": "Talk about the recent network upgrades and improved scalability",
                "generation_type": "idea"
            }
            
            async with self.session.post(f"{BACKEND_URL}/tweets/custom", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    tweet_content = data.get("content", "")
                    generation_type = data.get("generation_type", "")
                    
                    success = all([
                        tweet_content,
                        generation_type == "idea",
                        data.get("company_name"),
                        data.get("twitter_handle")
                    ])
                    
                    if success:
                        self.log_result("Custom Tweet Idea Generation", True, "Idea-based tweet generated successfully", {
                            "idea": payload["custom_idea"],
                            "generated_tweet": tweet_content,
                            "generation_type": generation_type
                        })
                    else:
                        self.log_result("Custom Tweet Idea Generation", False, "Response missing required fields", {"response": data})
                    
                    return success
                else:
                    error_text = await response.text()
                    self.log_result("Custom Tweet Idea Generation", False, f"Idea generation failed with status {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Custom Tweet Idea Generation", False, f"Idea generation error: {str(e)}")
            return False
    
    async def test_analyze_style_endpoint_removed(self):
        """Test that the analyze-style endpoint was properly removed"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            async with self.session.post(f"{BACKEND_URL}/tweets/analyze-style", json={"tweet": "test"}, headers=headers) as response:
                if response.status == 404:
                    self.log_result("Analyze Style Endpoint Removal", True, "Analyze-style endpoint properly removed (404 response)")
                    return True
                else:
                    self.log_result("Analyze Style Endpoint Removal", False, f"Analyze-style endpoint still exists (status {response.status})")
                    return False
                    
        except Exception as e:
            # Connection errors or other exceptions might indicate the endpoint doesn't exist
            if "404" in str(e) or "Not Found" in str(e):
                self.log_result("Analyze Style Endpoint Removal", True, "Analyze-style endpoint properly removed")
                return True
            else:
                self.log_result("Analyze Style Endpoint Removal", False, f"Error testing analyze-style endpoint: {str(e)}")
                return False
    
    async def test_invalid_generation_type(self, company_id):
        """Test error handling for invalid generation type"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "company_id": company_id,
                "example_tweet": "Test tweet",
                "generation_type": "invalid_type"
            }
            
            async with self.session.post(f"{BACKEND_URL}/tweets/custom", json=payload, headers=headers) as response:
                if response.status == 400:
                    self.log_result("Invalid Generation Type", True, "Properly rejected invalid generation type")
                    return True
                else:
                    self.log_result("Invalid Generation Type", False, f"Should have rejected invalid type but got status {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Invalid Generation Type", False, f"Error testing invalid generation type: {str(e)}")
            return False
    
    async def test_missing_required_fields(self, company_id):
        """Test error handling for missing required fields"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test missing example_tweet for style_clone
            payload = {
                "company_id": company_id,
                "generation_type": "style_clone"
                # Missing example_tweet
            }
            
            async with self.session.post(f"{BACKEND_URL}/tweets/custom", json=payload, headers=headers) as response:
                if response.status == 400:
                    self.log_result("Missing Required Fields", True, "Properly rejected missing example_tweet for style_clone")
                    return True
                else:
                    self.log_result("Missing Required Fields", False, f"Should have rejected missing fields but got status {response.status}")
                    return False
                    
        except Exception as e:
            self.log_result("Missing Required Fields", False, f"Error testing missing fields: {str(e)}")
            return False
    
    async def test_regular_tweet_generation(self, company_id):
        """Test regular tweet generation still works"""
        try:
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            payload = {
                "company_id": company_id,
                "count": 1
            }
            
            async with self.session.post(f"{BACKEND_URL}/tweets/generate", json=payload, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    if data and len(data) > 0:
                        tweet = data[0]
                        self.log_result("Regular Tweet Generation", True, "Regular tweet generation works", {
                            "tweet_content": tweet.get("content"),
                            "company": tweet.get("company_name")
                        })
                        return True
                    else:
                        self.log_result("Regular Tweet Generation", False, "No tweets generated")
                        return False
                else:
                    error_text = await response.text()
                    self.log_result("Regular Tweet Generation", False, f"Regular generation failed with status {response.status}", {"error": error_text})
                    return False
                    
        except Exception as e:
            self.log_result("Regular Tweet Generation", False, f"Regular generation error: {str(e)}")
            return False
    
    async def run_all_tests(self):
        """Run all backend tests"""
        print("🚀 Starting Backend API Tests for Custom Tweet Clone Feature")
        print("=" * 60)
        
        # Setup authentication
        if not await self.register_test_user():
            if not await self.login_test_user():
                print("❌ Authentication failed - cannot continue tests")
                return
        
        # Get or create test company
        company_id = await self.create_test_company()
        if not company_id:
            print("❌ Company setup failed - cannot continue tests")
            return
        
        # Run core tests
        await self.test_custom_tweet_style_clone(company_id)
        await self.test_custom_tweet_idea_generation(company_id)
        await self.test_analyze_style_endpoint_removed()
        await self.test_invalid_generation_type(company_id)
        await self.test_missing_required_fields(company_id)
        await self.test_regular_tweet_generation(company_id)
        
        # Print summary
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)
        
        passed = sum(1 for result in self.test_results if result["success"])
        total = len(self.test_results)
        
        print(f"Total Tests: {total}")
        print(f"Passed: {passed}")
        print(f"Failed: {total - passed}")
        print(f"Success Rate: {(passed/total)*100:.1f}%")
        
        if total - passed > 0:
            print("\n❌ FAILED TESTS:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")
        
        return self.test_results

async def main():
    """Main test runner"""
    async with BackendTester() as tester:
        results = await tester.run_all_tests()
        
        # Save results to file
        with open("/app/test_results_backend.json", "w") as f:
            json.dump(results, f, indent=2, default=str)
        
        print(f"\n📁 Detailed results saved to: /app/test_results_backend.json")

if __name__ == "__main__":
    asyncio.run(main())