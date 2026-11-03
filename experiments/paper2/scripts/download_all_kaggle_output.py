import os
import sys
import requests
import kaggle

kaggle.api.authenticate()
mod = sys.modules['kaggle.api.kaggle_api_extended']

target_dir = os.path.abspath("experiments/paper2/runs/kaggle_production_10m")
owner_slug = "brayanosinaka"
kernel_slug = "whot-ml-paper-2-ppo-training"

# Resume from the page token reported by the previous download
token = "eyJHY3NQYWdlVG9rZW4iOiIzNjUwMzc2NzEvb3V0cHV0L3dob3RfcHBvXzEwbS9wcG9fY2hlY2twb2ludF84NzUway5wdCJ9"

print(f"Fetching remaining pages for {owner_slug}/{kernel_slug}...")
page = 2
while True:
    with kaggle.api.build_kaggle_client() as client:
        req = mod.ApiListKernelSessionOutputRequest()
        req.user_name = owner_slug
        req.kernel_slug = kernel_slug
        if token:
            req.page_token = token
        resp = client.kernels.kernels_api_client.list_kernel_session_output(req)
        next_tok = resp.next_page_token

    print(f"Page {page}: {len(resp.files)} files. Next token: {next_tok}")
    for item in resp.files:
        outfile = os.path.join(target_dir, item.file_name)
        if os.path.exists(outfile) and os.path.getsize(outfile) > 0:
            continue
        os.makedirs(os.path.dirname(outfile), exist_ok=True)
        r = requests.get(item.url, stream=True)
        with open(outfile, 'wb') as f:
            f.write(r.content)
        print(f"  -> {item.file_name} ({len(r.content):,} bytes)")

    if not next_tok or next_tok == token:
        print("All pages fetched successfully!")
        break
    token = next_tok
    page += 1
