#!/usr/bin/env python3
"""
Script to introspect the Cway GraphQL API schema and save it to a file.
"""
import asyncio
import json
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.infrastructure.graphql_client import CwayGraphQLClient
from config.settings import settings


async def introspect_schema():
    """Perform full GraphQL schema introspection."""
    
    introspection_query = """
    query IntrospectionQuery {
      __schema {
        queryType { name }
        mutationType { name }
        subscriptionType { name }
        types {
          ...FullType
        }
        directives {
          name
          description
          locations
          args {
            ...InputValue
          }
        }
      }
    }

    fragment FullType on __Type {
      kind
      name
      description
      fields(includeDeprecated: true) {
        name
        description
        args {
          ...InputValue
        }
        type {
          ...TypeRef
        }
        isDeprecated
        deprecationReason
      }
      inputFields {
        ...InputValue
      }
      interfaces {
        ...TypeRef
      }
      enumValues(includeDeprecated: true) {
        name
        description
        isDeprecated
        deprecationReason
      }
      possibleTypes {
        ...TypeRef
      }
    }

    fragment InputValue on __InputValue {
      name
      description
      type { ...TypeRef }
      defaultValue
    }

    fragment TypeRef on __Type {
      kind
      name
      ofType {
        kind
        name
        ofType {
          kind
          name
          ofType {
            kind
            name
            ofType {
              kind
              name
              ofType {
                kind
                name
                ofType {
                  kind
                  name
                  ofType {
                    kind
                    name
                  }
                }
              }
            }
          }
        }
      }
    }
    """
    
    print(f"🔍 Introspecting GraphQL schema at {settings.cway_api_url}")
    print(f"🔑 Using API token: {settings.cway_api_token[:10]}...")
    
    client = CwayGraphQLClient(settings.cway_api_url, settings.cway_api_token)
    
    try:
        async with client:
            print("✅ Connected to GraphQL API")
            result = await client.execute_query(introspection_query)
            
            # Save full introspection result
            output_dir = Path(__file__).parent.parent / "docs"
            output_dir.mkdir(exist_ok=True)
            
            full_schema_path = output_dir / "graphql_schema_full.json"
            with open(full_schema_path, "w") as f:
                json.dump(result, f, indent=2)
            print(f"💾 Saved full schema to: {full_schema_path}")
            
            # Extract and save readable schema documentation
            schema = result.get("__schema", {})
            
            # Build readable documentation
            doc = {
                "query_type": schema.get("queryType", {}).get("name"),
                "mutation_type": schema.get("mutationType", {}).get("name"),
                "subscription_type": schema.get("subscriptionType", {}).get("name"),
                "queries": [],
                "mutations": [],
                "types": []
            }
            
            # Extract queries and mutations
            for type_info in schema.get("types", []):
                type_name = type_info.get("name")
                
                if type_name == schema.get("queryType", {}).get("name"):
                    for field in type_info.get("fields", []):
                        doc["queries"].append({
                            "name": field["name"],
                            "description": field.get("description"),
                            "args": [
                                {
                                    "name": arg["name"],
                                    "type": _format_type(arg["type"]),
                                    "description": arg.get("description")
                                }
                                for arg in field.get("args", [])
                            ],
                            "return_type": _format_type(field["type"])
                        })
                
                elif type_name == schema.get("mutationType", {}).get("name"):
                    for field in type_info.get("fields", []):
                        doc["mutations"].append({
                            "name": field["name"],
                            "description": field.get("description"),
                            "args": [
                                {
                                    "name": arg["name"],
                                    "type": _format_type(arg["type"]),
                                    "description": arg.get("description")
                                }
                                for arg in field.get("args", [])
                            ],
                            "return_type": _format_type(field["type"])
                        })
                
                # Save interesting types (exclude introspection types)
                elif not type_name.startswith("__"):
                    if type_info.get("kind") in ["OBJECT", "INPUT_OBJECT", "ENUM"]:
                        type_doc = {
                            "name": type_name,
                            "kind": type_info["kind"],
                            "description": type_info.get("description")
                        }
                        
                        if type_info["kind"] == "OBJECT":
                            type_doc["fields"] = [
                                {
                                    "name": f["name"],
                                    "type": _format_type(f["type"]),
                                    "description": f.get("description")
                                }
                                for f in type_info.get("fields", [])
                            ]
                        elif type_info["kind"] == "INPUT_OBJECT":
                            type_doc["input_fields"] = [
                                {
                                    "name": f["name"],
                                    "type": _format_type(f["type"]),
                                    "description": f.get("description")
                                }
                                for f in type_info.get("inputFields", [])
                            ]
                        elif type_info["kind"] == "ENUM":
                            type_doc["values"] = [
                                {
                                    "name": v["name"],
                                    "description": v.get("description")
                                }
                                for v in type_info.get("enumValues", [])
                            ]
                        
                        doc["types"].append(type_doc)
            
            # Save readable documentation
            doc_path = output_dir / "graphql_schema_readable.json"
            with open(doc_path, "w") as f:
                json.dump(doc, f, indent=2)
            print(f"📖 Saved readable schema to: {doc_path}")
            
            # Print summary
            print("\n📊 Schema Summary:")
            print(f"   Queries: {len(doc['queries'])}")
            print(f"   Mutations: {len(doc['mutations'])}")
            print(f"   Types: {len(doc['types'])}")
            
            if doc['queries']:
                print("\n🔍 Available Queries:")
                for q in doc['queries'][:10]:  # Show first 10
                    print(f"   - {q['name']}: {q.get('description', 'No description')}")
                if len(doc['queries']) > 10:
                    print(f"   ... and {len(doc['queries']) - 10} more")
            
            if doc['mutations']:
                print("\n✏️  Available Mutations:")
                for m in doc['mutations'][:10]:  # Show first 10
                    print(f"   - {m['name']}: {m.get('description', 'No description')}")
                if len(doc['mutations']) > 10:
                    print(f"   ... and {len(doc['mutations']) - 10} more")
            
    except Exception as e:
        print(f"❌ Error during introspection: {e}")
        raise


def _format_type(type_info):
    """Format a GraphQL type for readable output."""
    if not type_info:
        return "Unknown"
    
    kind = type_info.get("kind")
    name = type_info.get("name")
    of_type = type_info.get("ofType")
    
    if kind == "NON_NULL":
        return f"{_format_type(of_type)}!"
    elif kind == "LIST":
        return f"[{_format_type(of_type)}]"
    else:
        return name or "Unknown"


if __name__ == "__main__":
    asyncio.run(introspect_schema())
