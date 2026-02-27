#!/usr/bin/env python3
"""Test Skywork API connection"""
import asyncio
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment
PROJECT_ROOT = Path(__file__).parent
load_dotenv(PROJECT_ROOT / ".env")

from src.skywork.client import call_skywork_tool

async def test_skywork():
    """Test Skywork API connection"""
    secret_id = os.getenv("SKYWORK_SECRET_ID")
    secret_key = os.getenv("SKYWORK_SECRET_KEY")

    print(f"Testing with Secret ID: {secret_id[:20]}...")
    print(f"Testing with Secret Key: {secret_key[:20]}...")

    # Simple test
    try:
        result = await call_skywork_tool(
            tool_name="gen_doc",
            query="Hello World",
            use_network="false",
            secret_id=secret_id,
            secret_key=secret_key
        )
        print(f"Result: {result[:200]}...")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    asyncio.run(test_skywork())
