import tempfile
import os
import shutil
import subprocess
import sys
import ctypes
import tarfile
import urllib.request
import json


def get_docker_token(image_name):
    # You need to get an auth token, but you don't need a username/password
    # Say your image is busybox/latest, you would make a GET request to this
    # URL: https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/busybox:pull

    url = f"https://auth.docker.io/token?service=registry.docker.io&scope=repository:library/{
        image_name}:pull"

    res = urllib.request.urlopen(url)
    res_json = json.loads(res.read().decode())

    return res_json["token"]


def build_docker_headers(token):
    """Generate the docker headers for requests"""

    return {
        "Accept": "application/vnd.docker.distribution.manifest.v2+json",
        "Authorization": f"Bearer {token}",
    }


def get_docker_image_manifest(headers, image_name):
    """retrieve the image manifest from docker hub"""
    manifest_url = (
        f"https://registry.hub.docker.com/v2/library/{
            image_name}/manifests/latest"
    )

    request = urllib.request.Request(
        manifest_url,
        headers=headers,
    )

    res = urllib.request.urlopen(request)
    res_json = json.loads(res.read().decode())

    return res_json


def get_image_layers(headers: dict, image: str, layers) -> str:
    """download the layers and extract the files"""
    dir_path = tempfile.mkdtemp()

    # loop the layers to pull down each manifest
    for layer in layers:
        url = f"https://registry.hub.docker.com/v2/library/{
            image}/blobs/{layer['digest']}"

        sys.stderr.write(url)
        request = urllib.request.Request(url, headers=headers)
        res = urllib.request.urlopen(request)

        tmp_file = os.path.join(dir_path, "manifest.tar")

        with open(tmp_file, "wb") as f:
            shutil.copyfileobj(res, f)

        with tarfile.open(tmp_file) as tar:
            tar.extractall(dir_path)

    os.remove(tmp_file)

    return dir_path


def main():

    image = sys.argv[2]
    command = sys.argv[3]
    args = sys.argv[4:]

    # get token from Docker auth server by making GET req using image from args
    token = get_docker_token(image_name=image)
    # create header for docker calls
    headers = build_docker_headers(token)
    # get image manifest for specified image from Docker Hub
    manifest = get_docker_image_manifest(headers, image)
    # Download layers from manifest file and put result a tarfile (call it manifest.tar)
    dir_path = get_image_layers(headers, image, manifest["layers"])

    completed_process = subprocess.run(
        ["unshare", "-fpu", "chroot", dir_path, command, *args], capture_output=True
    )
    sys.stderr.write(completed_process.stderr.decode("utf-8"))
    sys.stdout.write(completed_process.stdout.decode("utf-8"))

    sys.exit(completed_process.returncode)


if __name__ == "__main__":
    main()
