# Laboratory 6 — Костюк Артем, КН-42

The fork uses two workflows: PR validation and main-branch delivery to Azure Container Registry / vm-linux-it-01.

## PR gate

The required checks are `Linters & Static Analysis`, `Dependencies, Unit Tests & Artifact Build`, and `Docker Build (Dry-Run) & Trivy Security Scan`. Python tests mock Redis; Node syntax checks use the files actually present in this repository; the .NET release artifact is retained for three days. Hadolint covers the Dockerfiles, Bandit checks Python, and the C# compiler runs built-in analyzers. Trivy scans repository dependencies and each of the three built images; JSON/text reports remain available for seven days, including failed runs.

Baseline commit `7fec82f` kept upstream versions and passed informational scanning in Actions run `41524683430`. Hard-gate commit `a25469c` failed in run `41525241948` on real fixable critical vulnerabilities. The final policy blocks any fixable CRITICAL finding in the filesystem or any of the three application images. Hadolint blocks warnings and errors across all three Dockerfiles. Archived reports explicitly include both HIGH and CRITICAL findings, including unfixed ones, and do not inherit the gate's exit code. No CVE ignore list is used.

## Remediation and non-root runtime

The maintained runtime images are Python `3.13.18-slim-trixie`, Node `24.22.2-trixie-slim`, and .NET `10.0.14-noble` (SDK `10.0.403-noble`). Python dependencies are fully pinned, Node has an updated npm lock, and Worker has a NuGet lock used in locked restore mode. CI uses Python 3.13, Node 24 and .NET 10.

The baseline lock's `proxy-addr` 2.0.7 (`CVE-2026-90711`) is updated to 2.0.8. The old result image's npm-bundled `tar` is removed with unused package-manager tooling from the runtime stage; npm remains available in the dependency-build stage. Replacing Node 18 / .NET 7 base images also replaces their old Debian libraries. Upgrading the Worker dependencies removes the vulnerable transitive `System.Drawing.Common` 5.0.0 (`CVE-2021-24112`). `express-rate-limit` 8.7.3 supports the Result request limiter. Image-level findings must be verified by the subsequent Actions run.

Vote runs as `appuser` with UID 10001 and listens on port 8080, published as `5000:8080`. Its healthcheck uses Python's standard library, and Result's uses Node's HTTP library, so neither image needs curl. Deployment prints the actual Vote UID, published endpoint and internal HTTP status, and fails if the Vote process runs as UID 0. Worker also uses the non-root `app` account supplied by Microsoft's runtime image.

## Delivery

Configure the six repository secrets specified in the assignment: `ACR_LOGIN_SERVER`, `ACR_USERNAME`, `ACR_PASSWORD`, `VM_HOST`, `VM_USERNAME`, `VM_SSH_KEY`. The public SSH host key in `.github/deploy_known_hosts` was checked against the existing trusted VM connection; it is not a secret. Verify any replacement host key out-of-band before changing that file.

On push to main, the first job builds all three services and pushes both commit-SHA tags and the convenience `latest` tags. The second job copies the Compose file and deployment script over verified SSH, supplies ACR credentials through encrypted stdin, and deploys the exact commit-SHA images with `--no-build`. It waits for healthy services and checks both HTTP endpoints. Passwords and SSH private keys are never included in image build arguments, command-line arguments, source code, or the deployed `.env` file. The `.env` file contains only the registry address and image commit SHA. Docker's local credential store remains on the lab VM as required by the ACR login exercise.

The deployment uses `~/voting-app-deploy`, whose named PostgreSQL volume is separate from the previous lab. Compose has no `build` entries or source-code bind mounts. Ports 5000 and 5001 expose the application; Redis and PostgreSQL are only on the private Compose network. Use `sudo docker compose down` in the deployment directory to stop containers while preserving the named database volume. Deallocate the VM in Azure after completing verification.
