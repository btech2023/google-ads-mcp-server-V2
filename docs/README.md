# Google Ads MCP Server Documentation

## Project Documentation

- [Project Management Rules](../.cursor/rules/project-management-rules.mdc) - Core project organization guidelines
- [Changelog System](./changelog-system.md) - Documentation of the automated changelog system

## Modularization Process

- [Modularization Tracker](./modularization-tracker.md) - Tracking system for files that exceed the line threshold
- [Modularization Meeting Template](./modularization-meeting-template.md) - Template for status meeting modularization reviews
- [Monthly Changelog Review](./monthly-changelog-review.md) - Template for monthly system effectiveness reviews

## Templates

- [Error Template](./error-template.md) - Template for documenting significant errors
- [Solution Template](./solution-template.md) - Template for documenting error solutions

## Usage

### Changelog System

```powershell
# Generate a changelog manually
.\scripts\generate-changelog.ps1

# Reinstall the Git hook if needed
.\scripts\generate-changelog.ps1 -InstallGitHook
```

### Modularization Process

1. Review the latest changelog in `logs\change-logs\`
2. Discuss modularization candidates in status meetings using the template
3. Update the modularization tracker with decisions and assignments
4. Complete modularization work as scheduled
5. Conduct a monthly review of the system effectiveness

### Optional Error/Solution Logging

For significant issues:
1. Document the error using the error template
2. Save to `logs\error-logs\` with the naming convention `ERROR-[PREFIX][NUM]-YYYY-MM-DD-[ShortDescription].md`
3. When resolved, document the solution using the solution template
4. Save to `logs\solution-logs\` with the naming convention `SOLUTION-[PREFIX][NUM]-YYYY-MM-DD-[ShortDescription].md`

## Directory Structure

- **api/** - API specifications and documentation
  - [Visualization Data Format Specification](api/visualization-data-format-spec.md) - Detailed specification for JSON data formats required for visualizing Google Ads KPI data

- **project-docs/** - Project-related documentation
  - Planning documents, requirements, and other project materials

- **[Security Instructions](SECURITY_INSTRUCTIONS.md)** - Security guidelines and instructions for the project

## External Documentation

Additional documentation can be found in the following locations:

- **[README.md](../README.md)** - Project overview and main documentation
- **[project-planning/](../project-planning/)** - Detailed project planning documents
- **[monitoring/README.md](../monitoring/README.md)** - Monitoring documentation
- **[google_ads_mcp_server/visualization/claude_artifacts_example.md](../google_ads_mcp_server/visualization/claude_artifacts_example.md)** - Examples of Claude Artifacts visualization 