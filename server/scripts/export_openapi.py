#!/usr/bin/env python3
"""
Export OpenAPI specification for ChatGPT GPT custom actions.

This script extracts the OpenAPI spec from the FastAPI app and saves it to a JSON file
that can be uploaded to ChatGPT GPT actions configuration.
"""

import sys
import json
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.presentation.rest_api import app


def export_openapi_spec(output_file: str = "openapi.json"):
    """Export OpenAPI specification to a JSON file."""
    
    # Get OpenAPI schema from FastAPI app
    openapi_schema = app.openapi()
    
    # Add authentication details for ChatGPT
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "Enter your Cway API token"
        }
    }
    
    # Apply security to all operations
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add server information
    openapi_schema["servers"] = [
        {
            "url": "http://localhost:8000",
            "description": "Local development server"
        },
        {
            "url": "https://your-api-domain.com",
            "description": "Production server (update with your actual URL)"
        }
    ]
    
    # Write to file
    output_path = Path(__file__).parent.parent / output_file
    with open(output_path, "w") as f:
        json.dump(openapi_schema, f, indent=2)
    
    print(f"✅ OpenAPI specification exported to: {output_path}")
    print("\n📋 To use with ChatGPT GPT:")
    print("1. Go to https://chat.openai.com/gpts/editor")
    print("2. Create a new GPT or edit existing one")
    print("3. Go to 'Actions' section")
    print("4. Click 'Import from file' or paste the JSON content")
    print(f"5. Upload the file: {output_path}")
    print("6. Configure authentication with your Cway API token")
    print("\n🔑 Authentication:")
    print("- Type: Bearer")
    print("- Token: Your CWAY_API_TOKEN from .env file")
    
    return output_path


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Export OpenAPI spec for ChatGPT GPT integration"
    )
    parser.add_argument(
        "-o", "--output",
        default="openapi.json",
        help="Output file name (default: openapi.json)"
    )
    
    args = parser.parse_args()
    export_openapi_spec(args.output)
