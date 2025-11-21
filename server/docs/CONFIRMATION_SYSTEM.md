# Confirmation System for Destructive Operations

This document describes the confirmation system implemented to prevent accidental execution of destructive operations in the Cway MCP Server.

## Overview

The confirmation system uses a two-step process to ensure that destructive operations (like deleting or closing projects) require explicit confirmation before execution:

1. **Prepare Step**: Preview the operation and receive a time-limited confirmation token
2. **Confirm Step**: Execute the operation using the confirmation token

## Architecture

### Components

- **ConfirmationService** (`src/application/services/confirmation_service.py`): Core service that generates and validates confirmation tokens
- **MCP Tools**: Six tools for prepare/confirm operations
  - `prepare_close_projects` / `confirm_close_projects`
  - `prepare_delete_projects` / `confirm_delete_projects`
  - `prepare_delete_user` / `confirm_delete_user`

### Security Features

- **HMAC-style signatures**: Tokens are cryptographically signed to prevent tampering
- **Time-limited tokens**: Default 5-minute expiration to prevent stale confirmations
- **One-time use**: Tokens cannot be reused after validation
- **Action validation**: Tokens are bound to specific actions (delete vs. close)
- **Automatic cleanup**: Used tokens are automatically cleaned up after 1 hour

## Usage Examples

### Closing Projects (Reversible)

#### Step 1: Prepare
```python
# AI calls prepare_close_projects
result = await call_tool("prepare_close_projects", {
    "project_ids": ["proj-123", "proj-456"],
    "force": False
})

# Response includes:
# {
#   "action": "preview",
#   "operation": "close",
#   "items": [...],  # Project details
#   "warnings": [
#     "Will close 2 project(s)",
#     "Artworks must be complete or approved to close",
#     "This action can be reversed using reopen_projects"
#   ],
#   "confirmation_token": "eyJ...|abc123...",
#   "token_expires_at": "2025-11-21T00:05:00Z",
#   "next_step": "To proceed, call confirm_close_projects with the confirmation_token"
# }
```

#### Step 2: Confirm
```python
# AI confirms after user review
result = await call_tool("confirm_close_projects", {
    "confirmation_token": "eyJ...|abc123..."
})

# Response:
# {
#   "success": True,
#   "action": "closed",
#   "closed_count": 2,
#   "project_ids": ["proj-123", "proj-456"],
#   "message": "Successfully closed 2 project(s)"
# }
```

### Deleting Projects (Irreversible - Extra Warnings)

#### Step 1: Prepare
```python
# AI calls prepare_delete_projects
result = await call_tool("prepare_delete_projects", {
    "project_ids": ["proj-789"],
    "force": False
})

# Response includes strong warnings:
# {
#   "warnings": [
#     "⚠️ DESTRUCTIVE ACTION: Will permanently delete 1 project(s)",
#     "🚨 THIS ACTION CANNOT BE UNDONE",
#     "Projects must be empty (no artworks) to delete",
#     "All associated artworks and data will be permanently lost"
#   ]
# }
```

#### Step 2: Confirm
```python
# AI confirms with token
result = await call_tool("confirm_delete_projects", {
    "confirmation_token": "eyJ...|def456..."
})
```

### Deleting Users (Irreversible - SSO Detection)

#### Step 1: Prepare
```python
# AI calls prepare_delete_user
result = await call_tool("prepare_delete_user", {
    "username": "john.doe"
})

# Response includes user details and warnings:
# {
#   "action": "preview",
#   "operation": "delete",
#   "items": [{
#     "username": "john.doe",
#     "name": "John Doe",
#     "email": "john.doe@example.com",
#     "enabled": true,
#     "is_sso": false
#   }],
#   "warnings": [
#     "⚠️ DESTRUCTIVE ACTION: Will permanently delete user 'john.doe'",
#     "🚨 THIS ACTION CANNOT BE UNDONE",
#     "User email: john.doe@example.com",
#     "All user data and associations will be permanently lost",
#     "User will lose access to all projects and artworks"
#   ]
# }
```

#### Step 2: Confirm
```python
# AI confirms with token
result = await call_tool("confirm_delete_user", {
    "confirmation_token": "eyJ...|ghi789..."
})

# Response:
# {
#   "success": True,
#   "action": "deleted",
#   "username": "john.doe",
#   "message": "User 'john.doe' deleted successfully"
# }
```

**Note**: If the user is an SSO user, an additional warning is included:
- "⚠️ This is an SSO user - deletion may affect external authentication"

## Token Format

Tokens consist of two parts separated by a pipe (`|`):

```
{payload_json}|{signature}
```

Example:
```
{"action":"delete_projects","data":{"project_ids":["proj-1"]},"expires_at":1700000000.0,"issued_at":1699999700.0,"nonce":"a1b2c3d4"}|e4f5a6b7c8d9...
```

### Payload Structure

```json
{
  "action": "delete_projects",           // Action type
  "data": {                              // Action-specific data
    "project_ids": ["proj-1", "proj-2"],
    "force": true
  },
  "expires_at": 1700000000.0,           // Unix timestamp
  "issued_at": 1699999700.0,            // Unix timestamp
  "nonce": "a1b2c3d4"                   // Prevents replay attacks
}
```

## Error Handling

### Common Error Scenarios

1. **Token Expired**
   ```json
   {
     "success": false,
     "message": "Confirmation failed: Token has expired"
   }
   ```
   **Solution**: Call the prepare tool again to get a new token

2. **Token Already Used**
   ```json
   {
     "success": false,
     "message": "Confirmation failed: Token has already been used"
   }
   ```
   **Solution**: Request a new confirmation token

3. **Invalid Token Signature**
   ```json
   {
     "success": false,
     "message": "Confirmation failed: Invalid token signature"
   }
   ```
   **Solution**: Ensure token wasn't tampered with; request new token

4. **Action Mismatch**
   ```json
   {
     "success": false,
     "message": "Invalid token: wrong action type"
   }
   ```
   **Solution**: Use the correct confirm tool for the prepare tool used

## AI Integration Guidelines

### When AI Should Ask for Confirmation

The AI should **always** use the two-step confirmation process for:
- Deleting projects (`prepare_delete_projects` → `confirm_delete_projects`)
- Closing projects (`prepare_close_projects` → `confirm_close_projects`)
- Deleting users (`prepare_delete_user` → `confirm_delete_user`)

### AI Behavior Pattern

1. **User requests destructive action**
   - AI calls `prepare_*` tool
   - AI shows user the preview with warnings
   - AI waits for explicit user confirmation

2. **User confirms**
   - AI calls `confirm_*` tool with the token
   - AI reports the result to user

3. **Token expires**
   - AI detects expiration error
   - AI asks user if they still want to proceed
   - If yes, start over with new `prepare_*` call

### Example AI Flow

```
User: "Delete project ABC123"

AI: [calls prepare_delete_projects]
AI: "I found the following project to delete:
     - ABC123: 'Marketing Campaign' (Status: active, 5 artworks)
     
     ⚠️ WARNING: This is a destructive action that cannot be undone.
     All 5 artworks and associated data will be permanently lost.
     
     Do you want to proceed with deletion?"

User: "Yes, delete it"

AI: [calls confirm_delete_projects with token]
AI: "✓ Project 'Marketing Campaign' has been permanently deleted."
```

## Configuration

### Token Expiration Time

Default: 5 minutes

To change:
```python
confirmation_service = ConfirmationService(
    secret_key="your-secret-key",
    default_expiry_minutes=10  # 10 minutes
)
```

### Secret Key

The service generates a random secret key by default. For production, you can provide a consistent key:

```python
# In settings or environment
CONFIRMATION_SECRET_KEY=your-secure-random-key-here

# In code
confirmation_service = ConfirmationService(
    secret_key=settings.confirmation_secret_key
)
```

## Testing

### Unit Tests

Run confirmation service tests:
```bash
cd server
python -m pytest tests/unit/test_confirmation_service.py -v
```

### Manual Testing

Test the full flow:
```bash
cd server
python -c "
from src.application.services.confirmation_service import ConfirmationService

service = ConfirmationService()

# Generate token
token_info = service.generate_token(
    action='delete_projects',
    data={'project_ids': ['test-1', 'test-2']}
)

print('Token:', token_info['token'])
print('Expires:', token_info['expires_at'])

# Validate token
validated = service.validate_token(token_info['token'])
print('Validated:', validated)
"
```

## Extending to Other Operations

To add confirmation to other destructive operations:

1. **Create prepare tool** in `tool_definitions.py`:
   ```python
   Tool(
       name="prepare_delete_users",
       description="Preview users before deletion...",
       inputSchema={...}
   )
   ```

2. **Create confirm tool**:
   ```python
   Tool(
       name="confirm_delete_users",
       description="Execute user deletion after confirmation...",
       inputSchema={...}
   )
   ```

3. **Implement handlers** in `cway_mcp_server.py`:
   ```python
   elif name == "prepare_delete_users":
       # Fetch user details
       users = [...]
       warnings = [...]
       
       # Generate token
       token_info = self.confirmation_service.generate_token(
           action="delete_users",
           data={"user_ids": user_ids}
       )
       
       return self.confirmation_service.create_preview_response(
           action="delete",
           items=users,
           item_type="users",
           warnings=warnings,
           token_info=token_info
       )
   
   elif name == "confirm_delete_users":
       # Validate and execute
       validated = self.confirmation_service.validate_token(token)
       # ... execute deletion
   ```

## Security Considerations

1. **Token Storage**: Tokens are never stored in database - only in memory
2. **Token Transmission**: Tokens are passed through MCP protocol (secure channel)
3. **Replay Prevention**: Nonces and one-time use prevent replay attacks
4. **Expiration**: Short expiration times limit attack window
5. **Signature Verification**: PBKDF2 HMAC ensures token integrity

## Troubleshooting

### Issue: Tokens expiring too quickly
**Solution**: Increase `default_expiry_minutes` in service initialization

### Issue: "Token has already been used" when retrying
**Solution**: This is expected - request a new token by calling prepare tool again

### Issue: Token validation fails after server restart
**Solution**: In-memory tokens are lost on restart - this is by design for security

## Future Enhancements

Potential improvements:
- [ ] Add audit logging for all confirmation attempts
- [ ] Support for bulk operations with selective confirmation
- [ ] Configurable expiration times per operation type
- [ ] Admin override capability for emergency operations
- [ ] Integration with user permission levels
