#!/bin/bash
# Script to introspect Cway GraphQL API schema using Bearer token

# Load environment variables
if [ -f ../.env ]; then
    export $(cat ../.env | grep -v '^#' | xargs)
fi

if [ -z "$CWAY_API_TOKEN" ]; then
    echo "❌ Error: CWAY_API_TOKEN not set"
    echo "Please set it in .env file or export it"
    exit 1
fi

API_URL="${CWAY_API_URL:-https://app.cway.se/graphql}"

echo "🔍 Introspecting GraphQL schema at $API_URL"
echo "🔑 Using API token: ${CWAY_API_TOKEN:0:10}..."

# Full introspection query
INTROSPECTION_QUERY='{
  "query": "query IntrospectionQuery { __schema { queryType { name } mutationType { name } subscriptionType { name } types { ...FullType } directives { name description locations args { ...InputValue } } } } fragment FullType on __Type { kind name description fields(includeDeprecated: true) { name description args { ...InputValue } type { ...TypeRef } isDeprecated deprecationReason } inputFields { ...InputValue } interfaces { ...TypeRef } enumValues(includeDeprecated: true) { name description isDeprecated deprecationReason } possibleTypes { ...TypeRef } } fragment InputValue on __InputValue { name description type { ...TypeRef } defaultValue } fragment TypeRef on __Type { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name ofType { kind name } } } } } } } }"
}'

# Create docs directory if it doesn't exist
mkdir -p ../docs

# Execute introspection query
echo "📡 Sending introspection query..."
curl -X POST "$API_URL" \
  -H "Authorization: Bearer $CWAY_API_TOKEN" \
  -H "Content-Type: application/json" \
  -d "$INTROSPECTION_QUERY" \
  -o ../docs/graphql_schema_full.json \
  -w "\nHTTP Status: %{http_code}\n" \
  -s

if [ $? -eq 0 ]; then
    echo "✅ Schema introspection completed"
    echo "💾 Saved full schema to: docs/graphql_schema_full.json"
    
    # Parse and create readable version using Python
    python3 << 'PYTHON_SCRIPT'
import json
from pathlib import Path

# Read the introspection result
schema_file = Path("../docs/graphql_schema_full.json")
with open(schema_file) as f:
    result = json.load(f)

if "errors" in result:
    print(f"❌ GraphQL errors: {result['errors']}")
    exit(1)

schema = result.get("data", {}).get("__schema", {})

# Build readable documentation
doc = {
    "query_type": schema.get("queryType", {}).get("name") if schema.get("queryType") else None,
    "mutation_type": schema.get("mutationType", {}).get("name") if schema.get("mutationType") else None,
    "subscription_type": schema.get("subscriptionType", {}).get("name") if schema.get("subscriptionType") else None,
    "queries": [],
    "mutations": [],
    "types": []
}

def format_type(type_info):
    """Format a GraphQL type for readable output."""
    if not type_info:
        return "Unknown"
    
    kind = type_info.get("kind")
    name = type_info.get("name")
    of_type = type_info.get("ofType")
    
    if kind == "NON_NULL":
        return f"{format_type(of_type)}!"
    elif kind == "LIST":
        return f"[{format_type(of_type)}]"
    else:
        return name or "Unknown"

# Extract queries and mutations
for type_info in schema.get("types", []):
    type_name = type_info.get("name")
    
    if type_name == doc["query_type"]:
        for field in type_info.get("fields", []):
            doc["queries"].append({
                "name": field["name"],
                "description": field.get("description"),
                "args": [
                    {
                        "name": arg["name"],
                        "type": format_type(arg["type"]),
                        "description": arg.get("description")
                    }
                    for arg in field.get("args", [])
                ],
                "return_type": format_type(field["type"])
            })
    
    elif type_name == doc["mutation_type"]:
        for field in type_info.get("fields", []):
            doc["mutations"].append({
                "name": field["name"],
                "description": field.get("description"),
                "args": [
                    {
                        "name": arg["name"],
                        "type": format_type(arg["type"]),
                        "description": arg.get("description")
                    }
                    for arg in field.get("args", [])
                ],
                "return_type": format_type(field["type"])
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
                        "type": format_type(f["type"]),
                        "description": f.get("description")
                    }
                    for f in type_info.get("fields", [])
                ]
            elif type_info["kind"] == "INPUT_OBJECT":
                type_doc["input_fields"] = [
                    {
                        "name": f["name"],
                        "type": format_type(f["type"]),
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
doc_path = Path("../docs/graphql_schema_readable.json")
with open(doc_path, "w") as f:
    json.dump(doc, f, indent=2)

print(f"📖 Saved readable schema to: {doc_path}")

# Print summary
print(f"\n📊 Schema Summary:")
print(f"   Queries: {len(doc['queries'])}")
print(f"   Mutations: {len(doc['mutations'])}")
print(f"   Types: {len(doc['types'])}")

if doc['queries']:
    print(f"\n🔍 Available Queries:")
    for q in sorted(doc['queries'], key=lambda x: x['name'])[:15]:
        print(f"   - {q['name']}: {q.get('description', 'No description')}")
    if len(doc['queries']) > 15:
        print(f"   ... and {len(doc['queries']) - 15} more")

if doc['mutations']:
    print(f"\n✏️  Available Mutations:")
    for m in sorted(doc['mutations'], key=lambda x: x['name'])[:15]:
        print(f"   - {m['name']}: {m.get('description', 'No description')}")
    if len(doc['mutations']) > 15:
        print(f"   ... and {len(doc['mutations']) - 15} more")

PYTHON_SCRIPT

else
    echo "❌ Failed to introspect schema"
    exit 1
fi
