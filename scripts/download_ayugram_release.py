#!/usr/bin/env python3
import hashlib
import json
import os
import sys
import tempfile
import time
import urllib.error
import urllib.parse
import urllib.request

REPO = os.environ.get('GITHUB_REPOSITORY')
TOKEN = os.environ.get('GITHUB_TOKEN')
UPSTREAM_OWNER = os.environ.get('UPSTREAM_OWNER', 'AyuGram')
UPSTREAM_REPO = os.environ.get('UPSTREAM_REPO', 'AyuGramDesktop')
BUILD_WORKFLOW_FILE = os.environ.get('BUILD_WORKFLOW_FILE', 'build-ayugram.yml')
API_BASE = 'https://api.github.com'
BUILD_FILE_PATTERNS = [
    '.github/workflows/build-ayugram.yml',
    'patches/',
    'scripts/ayugram_release.py',
]

if not REPO or not TOKEN:
    print('ERROR: GITHUB_REPOSITORY and GITHUB_TOKEN must be provided', file=sys.stderr)
    sys.exit(1)


def gh_api(path, method='GET', data=None, extra_headers=None):
    url = API_BASE + path
    headers = {
        'Accept': 'application/vnd.github+json',
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'ayugram-addon-ci',
    }
    if extra_headers:
        headers.update(extra_headers)
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
        headers['Content-Type'] = 'application/json'
    request = urllib.request.Request(url, headers=headers, method=method, data=body)
    try:
        with urllib.request.urlopen(request) as response:
            payload = response.read()
            if payload:
                return json.loads(payload.decode('utf-8'))
            return {}
    except urllib.error.HTTPError as exc:
        payload = exc.read().decode('utf-8')
        try:
            details = json.loads(payload)
        except Exception:
            details = payload
        if exc.code == 404:
            raise exc
        print(f'GitHub API {method} {path} failed: {exc.code} {exc.reason}\n{details}', file=sys.stderr)
        sys.exit(1)


def gh_download(url, output_path):
    headers = {
        'Accept': 'application/octet-stream',
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'ayugram-addon-ci',
    }
    request = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(request) as response, open(output_path, 'wb') as out_f:
        out_f.write(response.read())


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(8192), b''):
            digest.update(chunk)
    return digest.hexdigest()


def compute_build_inputs_hash():
    matches = []
    for pattern in BUILD_FILE_PATTERNS:
        if pattern.endswith('/'):
            directory = pattern[:-1]
            if os.path.isdir(directory):
                for root, _, files in os.walk(directory):
                    for name in sorted(files):
                        matches.append(os.path.join(root, name))
        elif os.path.exists(pattern):
            matches.append(pattern)
    hasher = hashlib.sha256()
    for path in sorted(matches):
        with open(path, 'rb') as fh:
            hasher.update(path.encode('utf-8'))
            hasher.update(b'\0')
            hasher.update(fh.read())
            hasher.update(b'\0')
    return hasher.hexdigest()


def get_upstream_latest_release():
    return gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/releases/latest')


def get_repo_release_by_tag(tag_name):
    try:
        return gh_api(f'/repos/{REPO}/releases/tags/{urllib.parse.quote(tag_name, safe="")}')
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def get_active_build_run():
    response = gh_api(
        f"/repos/{REPO}/actions/workflows/{urllib.parse.quote(BUILD_WORKFLOW_FILE, safe='')}/runs?status=in_progress&per_page=10"
    )
    runs = response.get('workflow_runs', [])
    return runs[0] if runs else None


def get_latest_build_run():
    response = gh_api(
        f"/repos/{REPO}/actions/workflows/{urllib.parse.quote(BUILD_WORKFLOW_FILE, safe='')}/runs?per_page=10"
    )
    runs = response.get('workflow_runs', [])
    return runs[0] if runs else None


def wait_for_build_run(run_id, timeout_seconds=1800, interval_seconds=15):
    start = time.time()
    while time.time() - start < timeout_seconds:
        run = gh_api(f'/repos/{REPO}/actions/runs/{run_id}')
        status = run.get('status')
        if status == 'completed':
            return run
        time.sleep(interval_seconds)
    print(f'ERROR: Timed out waiting for build workflow run {run_id}', file=sys.stderr)
    sys.exit(1)


def release_asset_valid(release, upstream_tag, upstream_version, build_inputs_hash):
    assets = {asset['name']: asset for asset in release.get('assets', [])}
    if 'AyuGram' not in assets or 'metadata.json' not in assets:
        return False

    metadata_path = os.path.join(tempfile.gettempdir(), 'ayugram_metadata.json')
    binary_path = os.path.join(tempfile.gettempdir(), 'AyuGram_binary')
    gh_download(assets['metadata.json']['browser_download_url'], metadata_path)
    gh_download(assets['AyuGram']['browser_download_url'], binary_path)

    with open(metadata_path, 'r', encoding='utf-8') as fh:
        metadata = json.load(fh)

    if metadata.get('version') != upstream_version:
        return False
    if metadata.get('tag') != upstream_tag:
        return False
    if metadata.get('build_inputs_hash') != build_inputs_hash:
        return False
    if 'commit' not in metadata or not metadata['commit']:
        return False

    actual_sha256 = sha256_file(binary_path)
    if metadata.get('sha256') != actual_sha256:
        return False

    return True


def ensure_release_asset_available(target_release_tag, upstream_tag, upstream_version, build_inputs_hash):
    active_run = get_active_build_run()
    if active_run:
        print(f'Found active build workflow run {active_run["id"]}, waiting for completion...')
        completed = wait_for_build_run(active_run['id'])
        if completed.get('conclusion') != 'success':
            print('ERROR: Existing AyuGram build workflow failed.', file=sys.stderr)
            sys.exit(1)

    current_release = get_repo_release_by_tag(target_release_tag)
    if current_release and release_asset_valid(current_release, upstream_tag, upstream_version, build_inputs_hash):
        active_run = get_active_build_run()
        if active_run:
            print(f'Found build workflow run {active_run["id"]} after validation, waiting for completion...')
            completed = wait_for_build_run(active_run['id'])
            if completed.get('conclusion') != 'success':
                print('ERROR: Existing AyuGram build workflow failed.', file=sys.stderr)
                sys.exit(1)
            current_release = get_repo_release_by_tag(target_release_tag)
            if current_release and release_asset_valid(current_release, upstream_tag, upstream_version, build_inputs_hash):
                return current_release
        else:
            return current_release

    print('ERROR: Release asset is missing or invalid for target release {target_release_tag}.')
    print('Please create or refresh the release using scripts/bootstrap_ayugram_release.py or run the build-ayugram workflow.')
    sys.exit(1)


def download_assets(release, output_dir):
    assets = {asset['name']: asset for asset in release.get('assets', [])}
    binary_path = os.path.join(output_dir, 'AyuGram')
    metadata_path = os.path.join(output_dir, 'metadata.json')
    gh_download(assets['AyuGram']['browser_download_url'], binary_path)
    gh_download(assets['metadata.json']['browser_download_url'], metadata_path)
    return binary_path, metadata_path


def validate_downloaded_asset(binary_path, metadata_path, upstream_tag, upstream_version, build_inputs_hash):
    with open(metadata_path, 'r', encoding='utf-8') as fh:
        metadata = json.load(fh)

    if metadata.get('version') != upstream_version:
        return False
    if metadata.get('tag') != upstream_tag:
        return False
    if metadata.get('build_inputs_hash') != build_inputs_hash:
        return False
    if 'commit' not in metadata or not metadata['commit']:
        return False

    actual_sha256 = sha256_file(binary_path)
    if metadata.get('sha256') != actual_sha256:
        return False

    return True


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--output-dir', default='build')
    args = parser.parse_args()

    upstream_release = get_upstream_latest_release()
    upstream_tag = upstream_release['tag_name']
    upstream_version = upstream_tag.lstrip('v')
    target_release_tag = f'AyuGram-{upstream_version}'
    build_inputs_hash = compute_build_inputs_hash()

    current_release = ensure_release_asset_available(
        target_release_tag,
        upstream_tag,
        upstream_version,
        build_inputs_hash,
    )

    os.makedirs(args.output_dir, exist_ok=True)
    binary_path, metadata_path = download_assets(current_release, args.output_dir)

    if not validate_downloaded_asset(binary_path, metadata_path, upstream_tag, upstream_version, build_inputs_hash):
        print('ERROR: Downloaded AyuGram asset failed validation after build.', file=sys.stderr)
        sys.exit(1)

    print(f'Downloaded AyuGram asset from repository release {current_release.get("tag_name")} to {binary_path}')


if __name__ == '__main__':
    main()
