#!/usr/bin/env bash
set -euo pipefail
umask 077
IFS= read -r registry
IFS= read -r registry_user
IFS= read -r registry_password
IFS= read -r image_tag
[[ "$registry" =~ ^[a-z0-9.-]+\.azurecr\.io$ ]]
[[ "$image_tag" =~ ^[0-9a-f]{40}$ ]]
cd "$HOME/voting-app-deploy"
printf '%s\n' "$registry_password" | sudo docker login "$registry" -u "$registry_user" --password-stdin
unset registry_password
printf 'ACR_LOGIN_SERVER=%s\nIMAGE_TAG=%s\n' "$registry" "$image_tag" > .env
sudo docker compose pull
sudo docker compose up -d --no-build --remove-orphans --wait --wait-timeout 240
sudo docker compose ps
curl --fail --silent --show-error http://127.0.0.1:5000/ > /dev/null
curl --fail --silent --show-error http://127.0.0.1:5001/ > /dev/null
# Limit cleanup to dangling images built by this lab, preserving other projects.
sudo docker image prune -f --filter label=io.kostiuk.lab=6
printf 'Deployment verified for commit %s\n' "$image_tag"
