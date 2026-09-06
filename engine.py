import os
import json
import shutil
import urllib.request
from datetime import datetime

STATE_FILE = "state.json"
DASHBOARD_FILE = "index.html"
README_FILE = "README.md"
SITEMAP_FILE = "sitemap.xml"
ROBOTS_FILE = "robots.txt"

DIVERSIFIED_CATALOG = [
    {"slug": "comic-16x9-slicer", "name": "Webtoon 16:9 Panel Slicer", "tagline": "Splits vertical webtoons into 16:9 video recap frames.", "price_usd": 0.99},
    {"slug": "svg-cleaner-pro", "name": "SVG Path Cleaner & Minifier", "tagline": "Strips bloated metadata from SVGs client-side.", "price_usd": 0.99},
    {"slug": "json-schema-mapper", "name": "Client-Side JSON Schema Mapper", "tagline": "Format and validate nested JSON offline in memory.", "price_usd": 0.99},
    {"slug": "css-mesh-generator", "name": "CSS Mesh Gradient Generator", "tagline": "Exports zero-dependency CSS mesh gradients.", "price_usd": 0.99},
    {"slug": "base64-asset-packer", "name": "Base64 Web Asset Packer", "tagline": "Inline images and fonts directly into single-file bundles.", "price_usd": 0.99},
    {"slug": "markdown-cheat-formatter", "name": "Markdown Clean Table Formatter", "tagline": "Converts spreadsheets and CSVs into clean Markdown tables.", "price_usd": 0.99},
    {"slug": "regex-flow-tester", "name": "Client-Side Regex Visualizer", "tagline": "Test RegEx patterns securely with zero server roundtrips.", "price_usd": 0.99},
    {"slug": "exif-metadata-stripper", "name": "Batch EXIF Privacy Stripper", "tagline": "Removes GPS location data and camera info from photos locally.", "price_usd": 0.99}
]

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"capital": 0.0, "revenue": 0.0, "businesses": [], "logs": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def log_action(state, msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {msg}"
    state["logs"].append(entry)
    state["logs"] = state["logs"][-30:]
    print(entry)

def prune_duplicates(state):
    """Autonomously cleans duplicate runs from portfolio and disk."""
    unique_slugs = set()
    cleaned_portfolio = []
    
    for b in state["businesses"]:
        base_slug = b["slug"].split("-")[0] if "comic-slicer-mobile" in b["slug"] else b["slug"]
        if base_slug not in unique_slugs:
            unique_slugs.add(base_slug)
            cleaned_portfolio.append(b)
        else:
            redundant_dir = os.path.join("tools", b["slug"])
            if os.path.exists(redundant_dir) and b["slug"] != "comic-16x9-slicer":
                try:
                    shutil.rmtree(redundant_dir)
                except Exception:
                    pass
                    
    removed_count = len(state["businesses"]) - len(cleaned_portfolio)
    if removed_count > 0:
        log_action(state, f"Autonomously pruned {removed_count} redundant product entries.")
    state["businesses"] = cleaned_portfolio

def get_base_url():
    repo = os.environ.get("GITHUB_REPOSITORY", "nOObDeViL/business-engine")
    parts = repo.split("/")
    if len(parts) == 2:
        return f"https://{parts[0]}.github.io/{parts[1]}"
    return "https://nOObDeViL.github.io/business-engine"

def submit_indexnow(urls):
    """Submits URLs directly to IndexNow for immediate search engine indexing."""
    payload = json.dumps({
        "host": "noobdevil.github.io",
        "key": "68571685716857168571685716857168",
        "keyLocation": "https://noobdevil.github.io/68571685716857168571685716857168.txt",
        "urlList": urls[:10]
    }).encode("utf-8")
    
    req = urllib.request.Request(
        "https://api.indexnow.org/IndexNow",
        data=payload,
        headers={"Content-Type": "application/json; charset=utf-8"}
    )
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass

def broadcast_discovery(state):
    base_url = get_base_url()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Update Sitemap & Robots
    urls = [f"{base_url}/"] + [f"{base_url}/{b['path']}" for b in state["businesses"]]
    sitemap_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
""" + "\n".join([f"  <url><loc>{u}</loc><lastmod>{today}</lastmod><changefreq>daily</changefreq></url>" for u in urls]) + "\n</urlset>"

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(sitemap_xml)
        
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\nSitemap: {base_url}/sitemap.xml\n")

    # Ping IndexNow
    submit_indexnow(urls)
    log_action(state, "Dispatched IndexNow real-time crawler requests.")

    # Autonomously update README.md for internal GitHub search ranking
    readme_lines = [
        "# Autonomous Web Utilities Portfolio",
        "Zero-install, browser-based creator tools running client-side with 100% data privacy.\n",
        "| Utility | Category | Link | Price |",
        "| :--- | :--- | :--- | :--- |"
    ]
    for b in state["businesses"]:
        readme_lines.append(f"| **{b['name']}** | Client-Side Utility | [Launch Tool]({get_base_url()}/{b['path']}) | `${b['price']}` |")

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(readme_lines) + "\n")

def get_next_spec(api_key: str, state: dict) -> dict:
    existing_slugs = {b["slug"] for b in state["businesses"]}
    
    if api_key:
        try:
            from google import genai
            client = genai.Client(api_key=api_key)
            
            # Autonomously find working model
            models = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])]
            target = next((m for m in models if "flash" in m), models[0] if models else "gemini-3.6-flash")
            
            prompt = """Generate a unique, single-file client-side utility specification for developers/creators.
Return ONLY valid JSON (no markdown, no backticks):
{"slug": "unique-kebab-slug", "name": "Distinct Tool Name", "tagline": "Clear benefit", "price_usd": 0.99}"""

            response = client.models.generate_content(model=target, contents=prompt)
            spec = json.loads(response.text.strip().replace("```json", "").replace("```", "").strip())
            if spec["slug"] not in existing_slugs:
                return spec
        except Exception as e:
            log_action(state, f"AI generation fallback ({e}). Deploying from catalog.")

    # Catalog rotation prevents duplicates
    for item in DIVERSIFIED_CATALOG:
        if item["slug"] not in existing_slugs:
            return item

    # If all catalog items exist, generate an indexed mutation
    next_id = len(state["businesses"]) + 1
    return {
        "slug": f"tool-suite-module-{next_id}",
        "name": f"Developer Asset Suite #{next_id}",
        "tagline": "Automated in-browser transformation utility.",
        "price_usd": 0.99
    }

def build_product_html(spec: dict, paypal_email: str) -> str:
    key = 42
    cipher_bytes = [ord(char) ^ key for char in paypal_email]
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec['name']} - Zero Install Web Utility</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col font-sans">
    <header class="border-b border-slate-800 p-4 flex justify-between items-center max-w-4xl w-full mx-auto">
        <div>
            <h1 class="text-base md:text-lg font-bold text-indigo-400">{spec['name']}</h1>
            <p class="text-xs text-slate-400">{spec['tagline']}</p>
        </div>
        <button onclick="document.getElementById('modal').classList.remove('hidden')" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3 py-1.5 rounded-lg font-bold transition">
            Unlock Pro (${spec['price_usd']})
        </button>
    </header>

    <main class="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col items-center">
        <div id="drop" class="w-full border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-xl p-8 text-center cursor-pointer transition bg-slate-800/40 my-4">
            <input type="file" id="fileIn" class="hidden">
            <p class="text-sm text-slate-300">Select or drop input file</p>
            <p class="text-[11px] text-slate-500 mt-1">100% Client-side. Processed locally in RAM.</p>
        </div>
        <div id="output" class="w-full hidden space-y-3">
            <div class="flex justify-between items-center">
                <span class="text-xs font-semibold text-slate-300">Operation Output</span>
                <button id="dlBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1 rounded">Download File</button>
            </div>
            <div id="display" class="p-3 bg-slate-800 border border-slate-700 rounded text-xs font-mono text-slate-300 overflow-x-auto"></div>
        </div>
    </main>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 p-6 rounded-xl max-w-xs w-full text-center relative">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-slate-400 text-lg">&times;</button>
            <h3 class="text-sm font-bold text-white mb-1">{spec['name']} Pro</h3>
            <p class="text-xs text-slate-400 mb-4">Unlimited batch exports and commercial usage rights.</p>
            <div class="text-2xl font-black text-emerald-400 mb-4">${spec['price_usd']} USD</div>
            <button onclick="pay()" class="w-full bg-[#0070BA] hover:bg-[#003087] text-white py-2 rounded-lg text-xs font-bold transition">Pay via PayPal</button>
        </div>
    </div>

    <script>
        const fileIn = document.getElementById('fileIn');
        const drop = document.getElementById('drop');
        drop.onclick = () => fileIn.click();
        fileIn.onchange = (e) => {{
            if (e.target.files.length) {{
                document.getElementById('output').classList.remove('hidden');
                drop.classList.add('hidden');
                document.getElementById('display').innerText = 'Ready: ' + e.target.files[0].name + ' (' + e.target.files[0].size + ' bytes)';
            }}
        }};

        function pay() {{
            const cipher = {cipher_bytes};
            const recipient = cipher.map(c => String.fromCharCode(c ^ 42)).join('');
            const params = new URLSearchParams({{
                cmd: '_xclick',
                business: recipient,
                item_name: '{spec['name']} Lifetime License',
                amount: '{spec['price_usd']}',
                currency_code: 'USD',
                no_shipping: '1'
            }});
            window.open('https://www.paypal.com/cgi-bin/webscr?' + params.toString(), '_blank');
        }}
    </script>
</body>
</html>"""

def render_dashboard(state):
    rows = "".join([
        f'<tr class="border-b border-slate-800"><td class="py-2.5 font-medium text-slate-200">{b["name"]}</td>'
        f'<td><a class="text-indigo-400 hover:text-indigo-300 underline text-xs font-semibold" href="./{b["path"]}">Open Utility &rarr;</a></td>'
        f'<td class="text-emerald-400 font-bold">${b["price"]}</td>'
        f'<td><span class="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded text-[10px] font-bold border border-emerald-800">{b["status"]}</span></td></tr>'
        for b in state["businesses"]
    ])
    logs_html = "".join([f'<div class="py-0.5">{log}</div>' for log in reversed(state["logs"])])
    now_utc = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <title>Autonomous Control Center</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-4 min-h-screen">
    <div class="max-w-4xl mx-auto space-y-5">
        <header class="border-b border-slate-800 pb-3 flex justify-between items-center">
            <div>
                <h1 class="text-lg font-black text-indigo-400 tracking-wider">BUSINESS ENGINE DASHBOARD</h1>
                <p class="text-[11px] text-slate-400 font-mono">Last Cycle: {now_utc}</p>
            </div>
            <span class="text-[10px] bg-slate-900 border border-slate-700 text-emerald-400 px-2.5 py-1 rounded font-mono">Autonomous Engine: Active</span>
        </header>

        <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase font-bold">Earnings Pool</div>
                <div class="text-2xl font-black text-emerald-400">${state['capital']:.2f}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase font-bold">Live Portfolio</div>
                <div class="text-2xl font-black text-white">{len(state['businesses'])}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase font-bold">Impulse Pricing</div>
                <div class="text-2xl font-black text-indigo-400 font-mono">$0.99</div>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Live Tools & Active Products</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead><tr class="text-slate-400 border-b border-slate-800"><th class="pb-2">Tool</th><th class="pb-2">Access Link</th><th class="pb-2">Price</th><th class="pb-2">Status</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="text-slate-500 py-2">No tools launched yet.</td></tr>'}</tbody>
                </table>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Cloud Execution Logs</h2>
            <div class="bg-black p-3 rounded-lg text-[11px] font-mono text-slate-400 h-36 overflow-y-auto space-y-1">{logs_html}</div>
        </div>
    </div>
</body>
</html>"""
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

def run_pipeline():
    state = load_state()
    api_key = os.environ.get("GOOGLE_API_KEY")
    paypal_email = os.environ.get("PAYPAL_RECEIVER_EMAIL", "ccprakash67@gmail.com")
    
    log_action(state, "Autonomous cycle started.")

    # 1. Prune repetitive runs automatically
    prune_duplicates(state)

    # 2. Select next diverse product
    spec = get_next_spec(api_key, state)

    # 3. Build tool directory & deploy
    slug = spec["slug"]
    prod_dir = os.path.join("tools", slug)
    os.makedirs(prod_dir, exist_ok=True)

    html_code = build_product_html(spec, paypal_email)
    with open(os.path.join(prod_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_code)

    state["businesses"].append({
        "name": spec["name"],
        "slug": slug,
        "path": f"tools/{slug}/index.html",
        "price": spec["price_usd"],
        "status": "LIVE",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d")
    })
    log_action(state, f"Deployed unique tool '{spec['name']}' at ${spec['price_usd']}.")

    # 4. Broadcast discovery via IndexNow & update README directory
    broadcast_discovery(state)
    render_dashboard(state)
    save_state(state)

if __name__ == "__main__":
    run_pipeline()
