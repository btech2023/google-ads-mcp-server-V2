# Secret Detection and Removal Instructions

This document provides instructions for completing the secret detection and removal process.

## 1. Delete .env Files

Since we cannot delete these files through the API, please manually delete the `.env` file that contains real credentials:

- `/.env`

You can do this with:

```bash
rm .env
```

## 2. Amend the Current Commit

To update the commit without creating a new one:

```bash
# Add all the changes
git add .

# Amend the previous commit
git commit --amend --no-edit

# Force push to update the remote repository
git push -f origin main
```

## 3. Rotate Your Credentials

Since your credentials were exposed in the Git history, you should:

1. Go to the Google Cloud Console
2. Create new OAuth 2.0 credentials
3. Update your local .env files with the new credentials (but don't commit them)
4. In Google Ads, regenerate your developer token if possible

## 4. Run Secret Detection

Use the included script to check for any remaining secrets:

```bash
python scripts/check_for_secrets.py
```

## 5. Install Pre-commit Hooks

To prevent future secret leaks, install and use the pre-commit hooks:

```bash
pip install pre-commit
pre-commit install
```

## 6. Long-term Security Measures

1. **Enable GitHub Secret Scanning** in your repository settings
2. **Use environment variables** exclusively for credentials, never hardcode them
3. **Follow the sensitive documentation template** in the `templates` directory
4. **Consider a secrets manager** like HashiCorp Vault or AWS Secrets Manager
5. **Regularly audit** for secrets using the provided script

## Additional Notes

- All sensitive documentation should use the template in `templates/sensitive-doc-template.md`
- The enhanced `.gitignore` now excludes a wider range of potential secret-containing files
- The GitHub Actions workflow is safe as it uses repository secrets

# Security Instructions for Google Ads MCP Server

This document provides instructions for maintaining a secure development environment and handling credentials properly.

## Environment Variables and Credentials

1. **Never commit credentials** to the repository
2. **Always use .env files** for local development
3. **Keep .env files in .gitignore**
4. **Use example files with placeholders** for documentation

## Setting Up Your Environment

1. Copy the `.env.example` file to `.env` and add your actual credentials:
   ```bash
   cp .env.example .env
   # Edit .env with your real credentials
   ```


## Preventing Credential Leaks

We've implemented several safeguards:

1. **Enhanced .gitignore**: Prevents committing .env files and other sensitive patterns
2. **Pre-commit hooks**: Run `pip install pre-commit && pre-commit install` to set up hooks that detect secrets before commits
3. **Secret scanning script**: Run `python scripts/check_for_secrets.py` to scan for potential secrets

## What To Do If Credentials Are Leaked

If credentials are accidentally committed or leaked:

1. **Invalidate and rotate credentials immediately**
   - Reset OAuth client credentials in Google Cloud Console
   - Reset developer token in Google Ads
   - Generate new refresh tokens

2. **Remove from Git history**
   - For minor leaks, use `git filter-branch` or BFG Repo Cleaner
   - For major leaks, consider creating a fresh repository

## Best Practices

1. **Use environment variables** exclusively for credentials
2. **Follow documentation templates** when writing about authentication
3. **Run secret scans regularly** before committing code
4. **Consider a secrets manager** for production deployment

## Additional Resources

- [Google Ads API - Secure Your Credentials](https://developers.google.com/google-ads/api/docs/productionize/secure-credentials)
- [GitHub - Removing Sensitive Data](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) 
