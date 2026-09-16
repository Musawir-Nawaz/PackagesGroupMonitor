import time

import requests

APIFY_BASE_URL = "https://api.apify.com/v2"
TERMINAL_RUN_STATUSES = {"SUCCEEDED", "FAILED", "ABORTED", "TIMED-OUT"}


class ApifyClientError(Exception):
    pass


class ApifyClient:
    """Thin wrapper around the Apify REST API.

    Starts a run and polls it (start -> poll -> fetch dataset) rather than
    using the run-sync-get-dataset-items shortcut, because that endpoint
    has a hard 300s SERVER-SIDE cap (confirmed against Apify's own API
    docs) — a slower actor (e.g. a broad Reddit search) gets cut off no
    matter how high a client-side timeout is set, since Apify itself stops
    waiting at 300s. Async start+poll has no such ceiling; `timeout` below
    bounds our own patience instead (see incident: two Reddit runs each
    burned ~5 minutes and a small real charge for zero results before this
    was switched over).

    Uses `requests`, not `httpx`, deliberately — under uvicorn on Windows,
    blocking httpx calls made from FastAPI's request threadpool
    intermittently raised "OSError: [Errno 22] Invalid argument" (a
    Proactor-event-loop/IOCP interaction), reproducible even with
    asyncio.WindowsSelectorEventLoopPolicy set. requests has no
    asyncio/event-loop coupling at all, so it doesn't share that failure
    mode; confirmed stable across repeated real Apify calls where httpx
    failed intermittently on the very same calls.
    """

    def __init__(self, token: str, timeout: float = 600.0, poll_interval: float = 5.0):
        if not token:
            raise ApifyClientError("APIFY_API_TOKEN is not set")
        self.token = token
        self.timeout = timeout
        self.poll_interval = poll_interval
        # Token goes in the Authorization header, not a `?token=` query
        # param — Apify's own recommended approach, and the only one that
        # doesn't end up verbatim in the client's exception message (which
        # for a URL-based error can include the full request URL) if a
        # call fails. That message propagates as-is through run_collection
        # -> the /api/collection/run 502 response -> the Platforms page's
        # error banner, so a query-param token would otherwise be shown in
        # plaintext in the browser on every failed run.
        self._headers = {"Authorization": f"Bearer {self.token}"}

    def run_actor_sync(
        self, actor_id: str, run_input: dict, max_total_charge_usd: float | None = None
    ) -> list[dict]:
        if not actor_id:
            raise ApifyClientError("Actor ID is not configured")

        # The REST API needs "~" between owner and actor name, not the "/"
        # used in Store page URLs (e.g. "harvestapi/linkedin-post-search"
        # -> "harvestapi~linkedin-post-search") — a literal "/" gets parsed
        # as extra path segments and 404s.
        api_actor_id = actor_id.replace("/", "~")
        deadline = time.monotonic() + self.timeout

        try:
            run = self._start_run(api_actor_id, run_input, max_total_charge_usd)
            run = self._wait_for_finish(run, deadline)

            if run["status"] != "SUCCEEDED":
                raise ApifyClientError(f"Apify actor run ended with status {run['status']}")

            return self._fetch_dataset_items(run["defaultDatasetId"])
        except requests.exceptions.HTTPError as exc:
            raise ApifyClientError(
                f"Apify actor run failed: {exc.response.status_code} {exc.response.reason}"
            ) from exc
        except requests.exceptions.RequestException as exc:
            raise ApifyClientError(f"Apify actor run failed: {type(exc).__name__}") from exc

    def _start_run(self, api_actor_id: str, run_input: dict, max_total_charge_usd: float | None) -> dict:
        url = f"{APIFY_BASE_URL}/acts/{api_actor_id}/runs"
        params = {"waitForFinish": 60}  # lets Apify hold the connection open for fast actors, skipping polling entirely
        if max_total_charge_usd:
            # Hard per-run spend cap enforced by Apify itself (pay-per-event
            # actors) — a real safety net, not just a documented intent, so
            # a wrong maxItems/maxPosts value in any collector can't run up
            # an unexpectedly large bill (see incident: two untested
            # LinkedIn runs burned the whole $5 free monthly credit before
            # this was wired in).
            params["maxTotalChargeUsd"] = max_total_charge_usd

        response = requests.post(url, params=params, json=run_input, headers=self._headers, timeout=90.0)
        response.raise_for_status()
        return response.json()["data"]

    def _wait_for_finish(self, run: dict, deadline: float) -> dict:
        run_id = run["id"]
        status_url = f"{APIFY_BASE_URL}/actor-runs/{run_id}"

        while run["status"] not in TERMINAL_RUN_STATUSES:
            if time.monotonic() >= deadline:
                # Giving up waiting must not mean giving up on the spend —
                # the run keeps executing (and billing) on Apify's side
                # otherwise. Discovered live: two abandoned Reddit runs
                # kept running unsupervised for 10+ and 30+ minutes after
                # our client stopped polling, together costing ~$0.75
                # before being caught and aborted by hand.
                self._abort_run(run_id)
                raise ApifyClientError(
                    f"Apify actor run timed out after {self.timeout:.0f}s and was aborted "
                    f"(was still {run['status']})"
                )
            time.sleep(self.poll_interval)
            response = requests.get(status_url, headers=self._headers, timeout=30.0)
            response.raise_for_status()
            run = response.json()["data"]

        return run

    def _abort_run(self, run_id: str) -> None:
        url = f"{APIFY_BASE_URL}/actor-runs/{run_id}/abort"
        try:
            requests.post(url, headers=self._headers, timeout=30.0)
        except requests.exceptions.RequestException:
            pass  # best-effort — the timeout error still surfaces either way

    def _fetch_dataset_items(self, dataset_id: str) -> list[dict]:
        url = f"{APIFY_BASE_URL}/datasets/{dataset_id}/items"
        response = requests.get(url, headers=self._headers, timeout=60.0)
        response.raise_for_status()
        return response.json()
