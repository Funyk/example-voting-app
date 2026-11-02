#!/usr/bin/env bash
set -euo pipefail
# Secrets arrive through the Actions environment, never through command arguments.
[[ "$VM_HOST" =~ ^[a-zA-Z0-9.-]+$ ]]
[[ "$VM_USERNAME" =~ ^[a-z_][a-z0-9_-]*$ ]]
key_file=$(mktemp)
trap 'rm -f "$key_file"' EXIT
chmod 600 "$key_file"
printf '%s\n' "$VM_SSH_KEY" > "$key_file"
unset VM_SSH_KEY
ssh_options=(-i "$key_file" -o IdentitiesOnly=yes -o BatchMode=yes
  -o StrictHostKeyChecking=yes -o UserKnownHostsFile=.github/deploy_known_hosts
  -o ConnectTimeout=30 -o ServerAliveInterval=30)
remote="$VM_USERNAME@$VM_HOST"
ssh "${ssh_options[@]}" "$remote" 'mkdir -p "$HOME/voting-app-deploy"'
scp "${ssh_options[@]}" docker-compose.yml .github/scripts/deploy-remote.sh "$remote:voting-app-deploy/"
# Newline-delimited values go over encrypted SSH stdin. The remote script has no tracing.
printf '%s\n' "$ACR_LOGIN_SERVER" "$ACR_USERNAME" "$ACR_PASSWORD" "$GITHUB_SHA" |
  ssh "${ssh_options[@]}" "$remote" 'bash "$HOME/voting-app-deploy/deploy-remote.sh"'
