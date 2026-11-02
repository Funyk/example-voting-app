# Laboratory 6 — Костюк Артем, КН-42

The fork uses two workflows: PR validation and main-branch delivery to Azure Container Registry / vm-linux-it-01.

## PR gate

The required checks are `Linters & Static Analysis`, `Dependencies, Unit Tests & Artifact Build`, and `Docker Build (Dry-Run) & Trivy Security Scan`. Python tests mock Redis; Node syntax checks use the files actually present in this repository; the .NET release artifact is retained for three days. Hadolint covers the Dockerfiles, Bandit checks Python, and the C# compiler runs built-in analyzers. Trivy scans repository dependencies and each of the three built images; JSON/text reports remain available for seven days, including failed runs.

The initial commit intentionally keeps upstream image/dependency versions and uses informational scanning. The next step is to enable a fixable-CRITICAL hard gate, record its real findings, then remediate them. No CVE is suppressed in this baseline.

## Delivery

Configure the six repository secrets specified in the assignment: `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`, `VM_HOST`, `VM_USERNAME`, `VM_SSH_KEY`. The public SSH host key in `.github/deploy_known_hosts` was checked against the existing trusted VM connection; it is not a secret. Verify any replacement host key out-of-band before changing that file.

On push to main, the first job builds all three services and pushes both immutable commit-SHA tags and the convenience `latest` tags. The second job copies the Compose file and deployment script over verified SSH, supplies ACR credentials through encrypted stdin, and deploys the exact commit-SHA images with `--no-build`. It waits for healthy services and checks both HTTP endpoints. Passwords and SSH private keys are never included in image build arguments, command-line arguments, source code, or the deployed `.env` file. The `.env` file contains only the registry address and image commit SHA. Docker's local credential store remains on the lab VM as required by the ACR login exercise.

The deployment uses `~/voting-app-deploy`, whose named PostgreSQL volume is separate from the previous lab. Compose has no `build` entries or source-code bind mounts. Ports 5000 and 5001 expose the application; Redis and PostgreSQL are only on the private Compose network. Use `sudo docker compose down` in the deployment directory to stop containers while preserving the named database volume. Deallocate the VM in Azure after completing verification.
