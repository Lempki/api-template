#!/usr/bin/env bash
# Starts the service's image and waits until it answers /health, as CI's smoke test does.
# Usage: .github/smoke-test.sh <image>
# A build passes even when the service inside the image cannot start, which this catches.
set -euo pipefail
image=$1
container="smoke-test-$$"

cleanup() {
    docker rm -f "$container" >/dev/null 2>&1 || true
}
trap cleanup EXIT

# The service refuses to start without a secret of at least 16 characters.
docker run -d --name "$container" -e API_SECRET=smoke-test-secret-0123456789 "$image" >/dev/null
for _ in $(seq 45); do
    if docker exec "$container" python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=4)" 2>/dev/null; then
        echo "The service started and answered /health."
        exit 0
    fi
    if [ "$(docker inspect -f '{{.State.Running}}' "$container")" != "true" ]; then
        break
    fi
    sleep 2
done
docker logs "$container"
echo "::error::The service did not answer /health within 90 seconds."
exit 1
