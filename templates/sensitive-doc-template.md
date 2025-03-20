# Sensitive Documentation Template

**Date: YYYY-MM-DD**

## ⚠️ IMPORTANT: CREDENTIAL SECURITY NOTICE ⚠️

This document may reference API credentials, tokens, or other sensitive information.

**ALWAYS follow these guidelines:**

1. **NEVER** include real credentials in documentation
2. **ALWAYS** use placeholder values like `your_token_here` or `XXXXXXXXXX`
3. **NEVER** commit this document with real values to version control

## Authentication Configuration

### Environment Variables Template

```
# Authentication Variables
CLIENT_ID=your_client_id_here
CLIENT_SECRET=your_client_secret_here
REFRESH_TOKEN=your_refresh_token_here
DEVELOPER_TOKEN=your_developer_token_here

# Account IDs
PRIMARY_ACCOUNT_ID=XXXXXXXXXX
SECONDARY_ACCOUNT_ID=XXXXXXXXXX
```

### Authentication Code Example

```python
# Example code with placeholders
auth_client = Client(
    client_id="your_client_id_here",
    client_secret="your_client_secret_here",
    refresh_token="your_refresh_token_here",
    customer_id="XXXXXXXXXX"
)
```

## Implementation Details

[Describe implementation details here without including real credentials]

## Testing

[Include testing details without real credentials]

---

*Note: Replace all placeholders with your actual values only in secure environments and never commit real values.*
