#!/bin/bash
# Script to apply Cloud Monitoring dashboard and alerting policies
# Usage: ./apply-monitoring.sh PROJECT_ID NOTIFICATION_CHANNEL_ID

set -e

# Check if required arguments are provided
if [ "$#" -lt 1 ]; then
    echo "Usage: $0 PROJECT_ID [NOTIFICATION_CHANNEL_ID]"
    exit 1
fi

PROJECT_ID=$1
NOTIFICATION_CHANNEL_ID=${2:-""}
ENV=${3:-"dev"}

# Directory containing this script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Applying monitoring configurations for project: $PROJECT_ID"
echo "Using environment: $ENV"

# Create or update dashboard
echo "Creating/updating dashboard..."
TEMP_DASHBOARD_FILE=$(mktemp)
cat "$SCRIPT_DIR/dashboard-definition.json" | sed "s/\"namespace_name\"=\"dev\"/\"namespace_name\"=\"$ENV\"/g" > "$TEMP_DASHBOARD_FILE"
gcloud monitoring dashboards create --project="$PROJECT_ID" --config-from-file="$TEMP_DASHBOARD_FILE"
rm "$TEMP_DASHBOARD_FILE"
echo "Dashboard applied successfully"

# Update notification channel in alerting policies if provided
if [ -n "$NOTIFICATION_CHANNEL_ID" ]; then
    echo "Configuring notification channel: $NOTIFICATION_CHANNEL_ID"
    TEMP_ALERTS_FILE=$(mktemp)
    
    # Replace project ID, channel ID and environment in the alerting policies
    sed "s|YOUR_PROJECT_ID|$PROJECT_ID|g; s|YOUR_CHANNEL_ID|$NOTIFICATION_CHANNEL_ID|g; s|namespace_name=\"dev\"|namespace_name=\"$ENV\"|g" "$SCRIPT_DIR/alerting-policies.yaml" > "$TEMP_ALERTS_FILE"
    
    # Split the YAML file into separate policy files and apply each one
    echo "Applying alerting policies..."
    csplit -f "$TEMP_ALERTS_FILE." "$TEMP_ALERTS_FILE" "/^---$/" "{*}" >/dev/null
    
    for policy_file in "$TEMP_ALERTS_FILE".??; do
        if [ -s "$policy_file" ]; then
            echo "Applying policy from $policy_file"
            gcloud alpha monitoring policies create --project="$PROJECT_ID" --policy-from-file="$policy_file" || echo "Warning: Failed to apply policy"
        fi
    done
    
    # Clean up temporary files
    rm -f "$TEMP_ALERTS_FILE"*
else
    echo "Skipping alerting policies as no notification channel was provided"
    echo "To apply alerting policies, run again with: $0 $PROJECT_ID YOUR_NOTIFICATION_CHANNEL_ID"
fi

# Create a local backup of the applied configuration
BACKUP_DIR="$SCRIPT_DIR/applied-configs/$(date +%Y-%m-%d-%H-%M-%S)"
mkdir -p "$BACKUP_DIR"
cp "$SCRIPT_DIR/dashboard-definition.json" "$BACKUP_DIR/dashboard-definition.json"
cp "$SCRIPT_DIR/alerting-policies.yaml" "$BACKUP_DIR/alerting-policies.yaml"
echo "Configuration backed up to $BACKUP_DIR"

echo "Done! Monitoring configuration has been applied."
echo "To view the dashboard, visit: https://console.cloud.google.com/monitoring/dashboards?project=$PROJECT_ID"
echo "To view the alerting policies, visit: https://console.cloud.google.com/monitoring/alerting?project=$PROJECT_ID" 