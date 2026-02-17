#!/usr/bin/env python3

# Copyright 2025 Frank Sommers
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Generate paper background images using Novita's FLUX 2 Dev model.

Generates realistic paper texture backgrounds (1152x1536, US Letter 3:4 aspect ratio)
for use as document overlays. Images are saved to the backgrounds/ directory
with sequential numbering.
"""

import os
import re
import random
import sys
import time

import click
import requests
from dotenv import load_dotenv

load_dotenv()

NOVITA_API_KEY = os.getenv('NOVITA_API_KEY')
FLUX_ENDPOINT = 'https://api.novita.ai/v3/async/flux-2-dev'
TASK_RESULT_ENDPOINT = 'https://api.novita.ai/v3/async/task-result'

DEFAULT_PROMPT = (
    "realistic scanned white office paper texture, clean business document background, "
    "subtle paper grain, very faint creases, mostly white with slight beige tint, "
    "no text, no writing, blank paper sheet, high resolution texture"
)

IMG_WIDTH = 1152
IMG_HEIGHT = 1536

MAX_RETRIES = 3
RETRY_DELAY = 5
POLL_INTERVAL = 3
POLL_TIMEOUT = 120


def get_next_index(output_dir, prefix):
    """Scan existing files to determine the next available index."""
    pattern = re.compile(rf'^{re.escape(prefix)}_(\d+)\.png$')
    max_index = 0
    if os.path.isdir(output_dir):
        for filename in os.listdir(output_dir):
            match = pattern.match(filename)
            if match:
                max_index = max(max_index, int(match.group(1)))
    return max_index + 1


def get_auth_headers():
    return {
        'Authorization': f'Bearer {NOVITA_API_KEY}',
        'Content-Type': 'application/json',
    }


def submit_generation(prompt, seed):
    """Submit an image generation task to Novita FLUX 2 Dev, with retries."""
    payload = {
        'prompt': prompt,
        'size': f'{IMG_WIDTH}*{IMG_HEIGHT}',
        'seed': seed,
    }
    for attempt in range(1, MAX_RETRIES + 1):
        response = requests.post(FLUX_ENDPOINT, json=payload, headers=get_auth_headers(), timeout=60)
        if response.status_code == 500 and attempt < MAX_RETRIES:
            delay = RETRY_DELAY * attempt
            click.echo(f"⚠️  Server error (attempt {attempt}/{MAX_RETRIES}), retrying in {delay}s...")
            time.sleep(delay)
            continue
        response.raise_for_status()
        return response.json()['task_id']


def poll_for_result(task_id):
    """Poll the task result endpoint until the image is ready."""
    start = time.time()
    while time.time() - start < POLL_TIMEOUT:
        response = requests.get(
            TASK_RESULT_ENDPOINT,
            params={'task_id': task_id},
            headers=get_auth_headers(),
            timeout=30,
        )
        response.raise_for_status()
        data = response.json()
        status = data.get('task', {}).get('status', '')
        if status == 'TASK_STATUS_SUCCEED':
            return data['images'][0]['image_url']
        if status == 'TASK_STATUS_FAILED':
            reason = data.get('task', {}).get('reason', 'unknown')
            raise RuntimeError(f"Task failed: {reason}")
        time.sleep(POLL_INTERVAL)
    raise TimeoutError(f"Task {task_id} did not complete within {POLL_TIMEOUT}s")


def download_image(url, filepath):
    """Download an image from a presigned URL and save it."""
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    with open(filepath, 'wb') as f:
        f.write(response.content)


@click.command()
@click.option('--count', '-c', type=int, default=4, help='Number of images to generate (default: 4)')
@click.option('--prompt', '-p', default=DEFAULT_PROMPT, help='Custom prompt for image generation')
@click.option('--output-dir', '-o', default='backgrounds', help='Output directory (default: backgrounds)')
@click.option('--prefix', '-n', default='paper_bg', help='Filename prefix (default: paper_bg)')
@click.option('--seed', '-S', type=int, default=None, help='Starting seed for reproducibility (default: random)')
def generate_backgrounds(count, prompt, output_dir, prefix, seed):
    """Generate paper background images using Novita FLUX 2 Dev."""

    if not NOVITA_API_KEY:
        click.echo("❌ NOVITA_API_KEY not found in environment. Set it in your .env file.")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)
    next_index = get_next_index(output_dir, prefix)

    if seed is None:
        seed = random.randint(0, 2**31 - 1)

    click.echo(f"🎨 Generating {count} background image(s) with FLUX 2 Dev")
    click.echo(f"📁 Output: {output_dir}/{prefix}_*.png")
    click.echo(f"🌱 Starting seed: {seed}")
    click.echo(f"📐 Dimensions: {IMG_WIDTH}x{IMG_HEIGHT}")
    click.echo(f"💬 Prompt: {prompt[:80]}{'...' if len(prompt) > 80 else ''}")
    click.echo("-" * 50)

    for i in range(count):
        index = next_index + i
        current_seed = seed + i
        filename = f"{prefix}_{index}.png"
        filepath = os.path.join(output_dir, filename)

        click.echo(f"\n🖼️  [{i + 1}/{count}] Generating {filename} (seed: {current_seed})...")

        try:
            task_id = submit_generation(prompt, current_seed)
            click.echo(f"⏳ Task submitted ({task_id[:12]}...), waiting for result...")
            image_url = poll_for_result(task_id)
            click.echo(f"⬇️  Downloading...")
            download_image(image_url, filepath)
            click.echo(f"✅ Saved {filepath}")
        except requests.exceptions.HTTPError as e:
            click.echo(f"❌ API error: {e}")
            click.echo(f"   Response: {e.response.text[:200] if e.response is not None else 'No response'}")
            sys.exit(1)
        except (RuntimeError, TimeoutError) as e:
            click.echo(f"❌ {e}")
            sys.exit(1)
        except Exception as e:
            click.echo(f"❌ Error: {e}")
            sys.exit(1)

    click.echo(f"\n✅ Successfully generated {count} background image(s)!")


if __name__ == '__main__':
    generate_backgrounds()
