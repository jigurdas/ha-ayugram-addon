#!/usr/bin/env python3
import hashlib
import http.client
import json
import os
import re
import subprocess
import sys
import tempfile
import urllib.parse
import urllib.request
from datetime import datetime

BUILD_FILE_PATTERNS = [
    '.github/workflows/build-ayugram.yml',
    'scripts/',
    'patches/',
]

UPSTREAM_OWNER = os.environ.get('UPSTREAM_OWNER', 'AyuGram')
UPSTREAM_REPO = os.environ.get('UPSTREAM_REPO', 'AyuGramDesktop')
REPO = os.environ.get('GITHUB_REPOSITORY')
TOKEN = os.environ.get('GITHUB_TOKEN')
EVENT_NAME = os.environ.get('GITHUB_EVENT_NAME', '')
SHA = os.environ.get('GITHUB_SHA', '')
EVENT_BEFORE = os.environ.get('GITHUB_EVENT_BEFORE', '')
API_BASE = 'https://api.github.com'

if not REPO or not TOKEN:
    print('ERROR: GITHUB_REPOSITORY and GITHUB_TOKEN must be provided', file=sys.stderr)
    sys.exit(1)


def run_command(command, check=True, capture_output=False):
    result = subprocess.run(command, shell=True, check=check, capture_output=capture_output, text=True)
    return result.stdout.strip() if capture_output else None


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
    request = urllib.request.Request(url, data=body, method=method, headers=headers)
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


def get_changed_files():
    if EVENT_NAME != 'push':
        return []
    if not EVENT_BEFORE or re.fullmatch(r'0{40}', EVENT_BEFORE):
        commit_range = f'{SHA}^..{SHA}'
    else:
        commit_range = f'{EVENT_BEFORE}..{SHA}'
    try:
        output = run_command(f'git diff --name-only {commit_range}', capture_output=True)
    except subprocess.CalledProcessError:
        return []
    return [line.strip() for line in output.splitlines() if line.strip()]


def file_changes_touch_build_inputs(changed_files):
    for path in changed_files:
        if path == BUILD_FILE_PATTERNS[0]:
            return True
        if any(path.startswith(prefix) for prefix in BUILD_FILE_PATTERNS[1:]):
            return True
    return False


def compute_build_inputs_hash():
    matches = []
    for pattern in BUILD_FILE_PATTERNS:
        if pattern.endswith('/'):
            for root, _, files in os.walk(pattern[:-1]):
                for name in sorted(files):
                    matches.append(os.path.join(root, name))
        elif os.path.exists(pattern):
            matches.append(pattern)
    hasher = hashlib.sha256()
    for path in sorted(matches):
        with open(path, 'rb') as f:
            hasher.update(path.encode('utf-8'))
            hasher.update(b'\0')
            hasher.update(f.read())
            hasher.update(b'\0')
    return hasher.hexdigest()


def get_upstream_release():
    return gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/releases/latest')


def get_commit_for_tag(tag_name):
    tag_ref = gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/git/ref/tags/{urllib.parse.quote(tag_name, safe="")}')
    obj = tag_ref.get('object', {})
    if obj.get('type') == 'tag':
        tag_obj = gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/git/tags/{obj["sha"]}')
        return tag_obj.get('object', {}).get('sha')
    return obj.get('sha')


def get_local_release(tag_name):
    try:
        return gh_api(f'/repos/{REPO}/releases/tags/{urllib.parse.quote(tag_name, safe="")}')
    except SystemExit:
        return None
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise


def build_ayugram():
    if os.path.exists('tdesktop'):
        run_command('rm -rf tdesktop')
    run_command('git clone --recursive https://github.com/AyuGram/AyuGramDesktop.git tdesktop')
    run_command('sudo chown -R $(id -u):$(id -g) tdesktop')
    run_command('mkdir -p tdesktop/out')
    run_command('chmod -R 777 tdesktop/out')
    docker_cmd = (
        'docker run --rm '
        '-u $(id -u):$(id -g) '
        f'-v "{os.getcwd()}/tdesktop:/usr/src/tdesktop" '
        'ghcr.io/telegramdesktop/tdesktop/centos_env:latest '
        '/usr/src/tdesktop/Telegram/build/docker/centos_env/build.sh '
        f'-D TDESKTOP_API_ID={os.environ["TDESKTOP_API_ID"]} '
        f'-D TDESKTOP_API_HASH={os.environ["TDESKTOP_API_HASH"]}'
    )
    run_command(docker_cmd)
    binary = os.path.join('tdesktop', 'out', 'Release', 'AyuGram')
    if not os.path.isfile(binary):
        print(f'ERROR: AyuGram binary not found at {binary}', file=sys.stderr)
        sys.exit(1)
    return binary


def sha256_file(path):
    digest = hashlib.sha256()
    with open(path, 'rb') as fh:
        for chunk in iter(lambda: fh.read(8192), b''):
            digest.update(chunk)
    return digest.hexdigest()


def upload_asset(release, asset_name, file_path, content_type):
    upload_url = release['upload_url'].split('{')[0] + '?name=' + urllib.parse.quote(asset_name, safe='')
    headers = {
        'Content-Type': content_type,
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'ayugram-addon-ci',
    }
    with open(file_path, 'rb') as fh:
        request = urllib.request.Request(upload_url, data=fh.read(), headers=headers, method='POST')
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode('utf-8'))


def delete_existing_assets(release, asset_names):
    assets = release.get('assets', [])
    for asset in assets:
        if asset.get('name') in asset_names:
            del_url = f"/repos/{REPO}/releases/assets/{asset['id']}"
            request = urllib.request.Request(API_BASE + del_url, method='DELETE', headers={
                'Authorization': f'Bearer {TOKEN}',
                'User-Agent': 'ayugram-addon-ci',
            })
            try:
                with urllib.request.urlopen(request):
                    pass
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise


def create_or_update_release(tag_name, name, body, existing_release=None):
    if existing_release is None:
        data = {
            'tag_name': tag_name,
            'name': name,
            'body': body,
            'draft': False,
            'prerelease': False,
        }
        return gh_api(f'/repos/{REPO}/releases', method='POST', data=data)
    release_id = existing_release['id']
    data = {
        'name': name,
        'body': body,
        'prerelease': False,
    }
    return gh_api(f'/repos/{REPO}/releases/{release_id}', method='PATCH', data=data)


def main():
    changed_files = get_changed_files()
    build_related_changed = file_changes_touch_build_inputs(changed_files)
    print(f'Build-related repo files changed: {build_related_changed}')

    upstream_release = get_upstream_release()
    upstream_tag = upstream_release['tag_name']
    upstream_version = upstream_tag.lstrip('v')
    upstream_commit = get_commit_for_tag(upstream_tag)
    release_tag = f'AyuGram-{upstream_version}'
    current_release = get_local_release(release_tag)
    metadata_asset_name = 'metadata.json'
    binary_asset_name = 'AyuGram'
    build_inputs_hash = compute_build_inputs_hash()

    need_build = False
    if build_related_changed:
        print('Build-related files changed; AyuGram build will be refreshed if needed.')
        need_build = True

    if current_release is None:
        print(f'No release found for tag {release_tag}; the AyuGram binary will be built and published.')
        need_build = True
    else:
        asset_map = {asset['name']: asset for asset in current_release.get('assets', [])}
        if metadata_asset_name not in asset_map or binary_asset_name not in asset_map:
            print('Expected release assets are missing; AyuGram build will be refreshed.')
            need_build = True
        else:
            metadata_path = os.path.join(tempfile.gettempdir(), 'ayugram_metadata.json')
            gh_download(asset_map[metadata_asset_name]['browser_download_url'], metadata_path)
            with open(metadata_path, 'r', encoding='utf-8') as fh:
                metadata = json.load(fh)

            if metadata.get('version') != upstream_version:
                print(f"Metadata version mismatch: {metadata.get('version')} != {upstream_version}")
                need_build = True
            if metadata.get('tag') != upstream_tag:
                print(f"Metadata tag mismatch: {metadata.get('tag')} != {upstream_tag}")
                need_build = True
            if metadata.get('commit') != upstream_commit:
                print(f"Metadata commit mismatch: {metadata.get('commit')} != {upstream_commit}")
                need_build = True
            if metadata.get('build_inputs_hash') != build_inputs_hash:
                print('Metadata build_inputs_hash mismatch; release asset is not up to date with build scripts.')
                need_build = True

            if not need_build:
                binary_path = os.path.join(tempfile.gettempdir(), 'AyuGram_binary')
                gh_download(asset_map[binary_asset_name]['browser_download_url'], binary_path)
                actual_sha256 = sha256_file(binary_path)
                if metadata.get('sha256') != actual_sha256:
                    print(f"Binary SHA256 mismatch: {metadata.get('sha256')} != {actual_sha256}")
                    need_build = True

    if not need_build:
        print('AyuGram release asset is up to date; no build required.')
        return

    binary_path = build_ayugram()
    binary_sha256 = sha256_file(binary_path)
    metadata = {
        'version': upstream_version,
        'tag': upstream_tag,
        'commit': upstream_commit,
        'sha256': binary_sha256,
        'build_inputs_hash': build_inputs_hash,
        'built_at': datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
    }
    metadata_path = os.path.join(tempfile.gettempdir(), 'ayugram_metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as fh:
        json.dump(metadata, fh, indent=2)
        fh.write('\n')

    release_body = (
        f'AyuGram binary built from upstream release {upstream_tag} (commit {upstream_commit}).\n'
        f'Metadata checksum: {binary_sha256}.'
    )

    release = create_or_update_release(release_tag, release_tag, release_body, existing_release=current_release)
    delete_existing_assets(release, [binary_asset_name, metadata_asset_name])
    upload_asset(release, binary_asset_name, binary_path, 'application/octet-stream')
    upload_asset(release, metadata_asset_name, metadata_path, 'application/json')
    print(f'Published GitHub Release {release_tag} with AyuGram binary and metadata.')


if __name__ == '__main__':
    main()
