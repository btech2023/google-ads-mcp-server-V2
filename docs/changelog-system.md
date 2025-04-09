# Changelog System Documentation

## Overview

The Google Ads MCP Server project uses an automated changelog system to track changes, monitor file sizes, and identify candidates for modularization. This system helps maintain code quality and provides transparency into project evolution.

## Features

- **Automated Change Tracking**: Records files that are modified, added, or deleted
- **Code Metrics**: Tracks lines added and removed
- **Modularization Monitoring**: Identifies files exceeding 300 lines that are candidates for breaking down
- **Git Integration**: Automatically generates changelogs after each commit via Git hook

## Directory Structure

```
logs/
├── change-logs/        # Generated changelog files
├── error-logs/         # Documentation of encountered errors
└── solution-logs/      # Documentation of solutions to errors
```

## Using the Changelog System

### Viewing Changelogs

Changelogs are generated daily in the `logs/change-logs/` directory with filenames following the pattern `changes-YYYY-MM-DD.md`.

### Modularization Review Process

1. **Identification**: Files exceeding 300 lines are automatically flagged as modularization candidates
2. **Review**: Discuss flagged files during status meetings to determine refactoring priority
3. **Assignment**: Assign modularization tasks to team members
4. **Implementation**: Break down large files into smaller, more focused modules
5. **Verification**: The changelog system will verify that the file size has been reduced in subsequent reports

### Error Logging (Optional)

When encountering significant errors:

1. Create a file in `logs/error-logs/` with the format `ERROR-[PREFIX][NUM]-YYYY-MM-DD-[ShortDescription].md`
2. Document the context, problem, error details, and root causes

### Solution Logging (Optional)

When resolving documented errors:

1. Create a file in `logs/solution-logs/` with the format `SOLUTION-[PREFIX][NUM]-YYYY-MM-DD-[ShortDescription].md`
2. Reference the error log it resolves
3. Document the solution implemented, verification steps, and preventative measures

## Manual Operations

### Generate Changelog Manually

```powershell
.\scripts\generate-changelog.ps1
```

### Install Git Hook (Already Done)

If you need to reinstall the Git hook:

```powershell
.\scripts\generate-changelog.ps1 -InstallGitHook
```

## Best Practices

1. **Regular Review**: Check the latest changelog before status meetings
2. **Prioritize Largest Files**: Focus on files that significantly exceed the threshold (>500 lines)
3. **Document Decisions**: When deciding not to modularize a large file, document the reasoning
4. **Progressive Implementation**: Address modularization issues gradually rather than all at once

## Note on Project Management Rules

This system implements a simplified version of the project management rules defined in `.cursor/rules/project-managment-rules.mdc`, adapted to work with the current project structure. The primary focus is on monitoring file sizes and encouraging modularization, with optional error and solution logging for significant issues. 