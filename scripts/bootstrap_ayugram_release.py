#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import re
import sys
import tempfile
import urllib.error
import urllib.parse
import urllib.request
import zipfile
from datetime import datetime

REPO = os.environ.get('GITHUB_REPOSITORY')
TOKEN = os.environ.get('GITHUB_TOKEN')
UPSTREAM_OWNER = os.environ.get('UPSTREAM_OWNER', 'AyuGram')
UPSTREAM_REPO = os.environ.get('UPSTREAM_REPO', 'AyuGramDesktop')
API_BASE = 'https://api.github.com'
BUILD_FILE_PATTERNS = [
    '.github/workflows/build-ayugram.yml',
    'patches/',
    'scripts/ayugram_release.py',
]


def gh_api(path, method='GET', data=None, extra_headers=None):
    url = API_BASE + path
    headers = {
        'Accept': 'application/vnd.github+json',
        'User-Agent': 'ayugram-addon-bootstrap',
    }
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
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
        if exc.code == 404:
            raise
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
        'User-Agent': 'ayugram-addon-bootstrap',
    }
    if TOKEN:
        headers['Authorization'] = f'Bearer {TOKEN}'
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


def load_local_metadata():
    metadata_path = os.path.join(os.getcwd(), 'metadata.json')
    if not os.path.isfile(metadata_path):
        return None
    try:
        with open(metadata_path, 'r', encoding='utf-8') as fh:
            return json.load(fh)
    except (OSError, json.JSONDecodeError):
        return None


def normalize_tag(tag):
    return tag if tag.startswith('v') else f'v{tag}'


def parse_semver(tag):
    match = re.match(r'v?(\d+)\.(\d+)\.(\d+)', tag)
    if not match:
        return None
    return tuple(int(x) for x in match.groups())


def find_embedded_version(binary_path):
    with open(binary_path, 'rb') as fh:
        data = fh.read(16 * 1024 * 1024)
    try:
        text = data.decode('latin1', errors='ignore')
    except Exception:
        return None
    version_match = re.search(r'AyuGram.{0,120}?(v\d+\.\d+\.\d+)', text, flags=re.IGNORECASE)
    if version_match:
        return normalize_tag(version_match.group(1))
    candidates = sorted({m.group(0) for m in re.finditer(r'v\d+\.\d+\.\d+', text)})
    semvers = [tag for tag in candidates if parse_semver(tag)]
    if semvers:
        return semvers[-1]
    return None


def locate_ayugram_binary(path):
    if os.path.isdir(path):
        print(f'ERROR: Expected a file, not a directory: {path}', file=sys.stderr)
        sys.exit(1)
    if os.path.isfile(path) and zipfile.is_zipfile(path):
        with zipfile.ZipFile(path, 'r') as zf:
            candidates = [name for name in zf.namelist() if os.path.basename(name) == 'AyuGram' and not name.endswith('/')]
            if not candidates:
                print(f'ERROR: No AyuGram executable found in archive: {path}', file=sys.stderr)
                sys.exit(1)
            target = candidates[0]
            extracted_dir = tempfile.mkdtemp(prefix='ayugram-bootstrap-')
            extracted_path = os.path.join(extracted_dir, os.path.basename(target))
            with open(extracted_path, 'wb') as out_f:
                out_f.write(zf.read(target))
            os.chmod(extracted_path, 0o755)
            return extracted_path
    if os.path.isfile(path):
        return path
    print(f'ERROR: Binary file not found: {path}', file=sys.stderr)
    sys.exit(1)


def get_upstream_latest_release():
    return gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/releases/latest')


def get_commit_for_tag(tag_name):
    encoded = urllib.parse.quote(tag_name, safe='')
    tag_ref = gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/git/ref/tags/{encoded}')
    obj = tag_ref.get('object', {})
    if obj.get('type') == 'tag':
        tag_obj = gh_api(f'/repos/{UPSTREAM_OWNER}/{UPSTREAM_REPO}/git/tags/{obj['sha']}')
        return tag_obj.get('object', {}).get('sha')
    return obj.get('sha')


def get_repo_release_by_tag(tag_name):
    try:
        return gh_api(f'/repos/{REPO}/releases/tags/{urllib.parse.quote(tag_name, safe="")}')
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
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


def delete_existing_assets(release, asset_names):
    for asset in release.get('assets', []):
        if asset.get('name') in asset_names:
            delete_url = f"/repos/{REPO}/releases/assets/{asset['id']}"
            request = urllib.request.Request(API_BASE + delete_url, method='DELETE', headers={
                'Authorization': f'Bearer {TOKEN}',
                'User-Agent': 'ayugram-addon-bootstrap',
            })
            try:
                with urllib.request.urlopen(request):
                    pass
            except urllib.error.HTTPError as exc:
                if exc.code != 404:
                    raise


def upload_asset(release, asset_name, file_path, content_type):
    upload_url = release['upload_url'].split('{')[0] + '?name=' + urllib.parse.quote(asset_name, safe='')
    headers = {
        'Content-Type': content_type,
        'Authorization': f'Bearer {TOKEN}',
        'User-Agent': 'ayugram-addon-bootstrap',
    }
    with open(file_path, 'rb') as fh:
        request = urllib.request.Request(upload_url, data=fh.read(), headers=headers, method='POST')
        with urllib.request.urlopen(request) as response:
            return json.loads(response.read().decode('utf-8'))


def main():
    parser = argparse.ArgumentParser(description='Bootstrap the initial AyuGram GitHub Release with an existing compiled binary or archive.')
    parser.add_argument('--binary-path', required=True, help='Path to the existing compiled AyuGram binary or ZIP archive')
    parser.add_argument('--upstream-tag', help='Optional upstream AyuGram release tag. Only used as a fallback.')
    parser.add_argument('--force', action='store_true', help='Replace existing release assets if the release already exists.')
    args = parser.parse_args()

    if not REPO:
        print('ERROR: GITHUB_REPOSITORY must be provided', file=sys.stderr)
        sys.exit(1)

    binary_path = locate_ayugram_binary(args.binary_path)
    sha256 = sha256_file(binary_path)

    metadata = load_local_metadata()
    version = None
    upstream_tag = None

    if metadata and metadata.get('sha256') == sha256 and metadata.get('version') and metadata.get('tag'):
        version = metadata['version']
        upstream_tag = normalize_tag(metadata['tag'])
        print(f'Using existing metadata.json for upstream tag {upstream_tag}.')
    else:
        embedded = find_embedded_version(binary_path)
        if embedded:
            upstream_tag = normalize_tag(embedded)
            version = embedded.lstrip('v')
            print(f'Detected upstream tag {upstream_tag} from embedded AyuGram binary.')

    if version is None or upstream_tag is None:
        if args.upstream_tag:
            upstream_tag = normalize_tag(args.upstream_tag)
            version = upstream_tag.lstrip('v')
            print(f'Falling back to explicit upstream tag {upstream_tag}.')
        else:
            try:
                upstream_release = get_upstream_latest_release()
                upstream_tag = upstream_release['tag_name']
                version = upstream_tag.lstrip('v')
                print(f'Using latest upstream release tag {upstream_tag} from GitHub API.')
            except urllib.error.HTTPError:
                print('ERROR: Could not determine upstream AyuGram tag from metadata, binary, or GitHub API.', file=sys.stderr)
                sys.exit(1)

    release_tag = f'AyuGram-{version}'
    upstream_commit = get_commit_for_tag(upstream_tag)
    if not upstream_commit:
        print(f'ERROR: Could not determine commit SHA for upstream tag {upstream_tag}', file=sys.stderr)
        sys.exit(1)

    metadata_payload = {
        'version': version,
        'tag': upstream_tag,
        'commit': upstream_commit,
        'sha256': sha256,
        'build_inputs_hash': compute_build_inputs_hash(),
        'built_at': datetime.utcnow().replace(microsecond=0).isoformat() + 'Z',
    }

    metadata_path = os.path.join(os.getcwd(), 'metadata.json')
    with open(metadata_path, 'w', encoding='utf-8') as fh:
        json.dump(metadata_payload, fh, indent=2)
        fh.write('\n')

    if not TOKEN:
        print('Generated metadata.json and resolved binary information, but GITHUB_TOKEN is required to upload the release.')
        print('Run this command once authentication is available:')
        print(f'GITHUB_TOKEN=... GITHUB_REPOSITORY={REPO} python3 scripts/bootstrap_ayugram_release.py --binary-path {args.binary_path}')
        sys.exit(0)

    existing_release = get_repo_release_by_tag(release_tag)
    release_body = f'Bootstrap AyuGram release for upstream tag {upstream_tag}.'
    if existing_release is None:
        release = create_or_update_release(release_tag, release_tag, release_body)
    else:
        release = create_or_update_release(release_tag, release_tag, release_body, existing_release=existing_release)

    delete_existing_assets(release, ['AyuGram', 'metadata.json'])
    upload_asset(release, 'AyuGram', binary_path, 'application/octet-stream')
    upload_asset(release, 'metadata.json', metadata_path, 'application/json')

    print(f'Bootstrap release {release_tag} created or updated with binary and metadata.')
    print('Next runs will reuse this release asset until upstream AyuGram changes.')


if __name__ == '__main__':
    main()
