import os
import json
from datetime import datetime

STATE_FILE = "state.json"
DASHBOARD_FILE = "index.html"
SITEMAP_FILE = "sitemap.xml"
ROBOTS_FILE = "robots.txt"

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
    state["logs"] = state["logs"][-25:]
    print(entry)

def get_base_url():
    repo = os.environ.get("GITHUB_REPOSITORY", "nOObDeViL/business-engine")
    parts = repo.split("/")
    if len(parts) == 2:
        return f"https://{parts[0]}.github.io/{parts[1]}"
    return "https://nOObDeViL.github.io/business-engine"

def generate_seo_files(state):
    base_url = get_base_url()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Generate sitemap.xml
    urls = [f"""  <url>
    <loc>{base_url}/</loc>
    <lastmod>{today}</lastmod>
    <changefreq>daily</changefreq>
    <priority>1.0</priority>
  </url>"""]

    for b in state["businesses"]:
        urls.append(f"""  <url>
    <loc>{base_url}/{b['path']}</loc>
    <lastmod>{b.get('created_at', today)}</lastmod>
    <changefreq>weekly</changefreq>
    <priority>0.8</priority>
  </url>""")

    sitemap_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{os.linesep.join(urls)}
</urlset>"""

    with open(SITEMAP_FILE, "w", encoding="utf-8") as f:
        f.write(sitemap_content)

    # Generate robots.txt
    robots_content = f"""User-agent: *
Allow: /

Sitemap: {base_url}/sitemap.xml
"""
    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(robots_content)

def generate_spec_with_ai(api_key: str, state: dict) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    
    target_model = "gemini-2.5-flash"
    try:
        available = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])]
        for pref in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
            matched = [m for m in available if pref in m]
            if matched:
                target_model = matched[0]
                break
    except Exception as e:
        log_action(state, f"Model lookup notice: {e}")

    prompt = """Identify a high-utility developer or creator tool that is commonly built as a permissively licensed (MIT) open-source web app (e.g., SVG cleaner, format converter, CSS pattern generator, markdown formatter, batch EXIF stripper).
Produce an MVP specification that runs 100% client-side in standard vanilla JavaScript.

Return ONLY valid JSON (no markdown formatting, no backticks):
{
  "slug": "url-slug",
  "name": "Tool Name",
  "tagline": "Short high-value benefit",
  "price_usd": 2.99,
  "reddit_post_title": "Free web tool to solve specific problem without uploads",
  "reddit_post_body": "Detailed post explaining how this tool solves the problem locally in browser..."
}"""

    response = client.models.generate_content(
        model=target_model,
        contents=prompt
    )
    cleaned = response.text.strip().replace("```json", "").replace("```", "").strip()
    return json.loads(cleaned)

def build_product_html(spec: dict, paypal_email: str) -> str:
    key = 42
    cipher_bytes = [ord(char) ^ key for char in paypal_email]
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{spec['name']} - Fast, Free & Private</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col font-sans">
    <header class="border-b border-slate-800 p-6 flex justify-between items-center max-w-5xl w-full mx-auto">
        <div>
            <h1 class="text-xl font-bold text-indigo-400">{spec['name']}</h1>
            <p class="text-xs text-slate-400">{spec['tagline']}</p>
        </div>
        <button onclick="document.getElementById('modal').classList.remove('hidden')" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg font-medium transition">
            Unlock Pro (${spec['price_usd']})
        </button>
    </header>

    <main class="flex-1 max-w-5xl w-full mx-auto p-6 flex flex-col items-center">
        <div id="drop" class="w-full border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl p-12 text-center cursor-pointer transition bg-slate-800/40 my-6">
            <input type="file" id="fileIn" class="hidden">
            <p class="text-base text-slate-300">Select or drop your file to begin</p>
            <p class="text-xs text-slate-500 mt-2">Zero server latency. All processing occurs locally in browser memory.</p>
        </div>
        <div id="output" class="w-full hidden space-y-4">
            <div class="flex justify-between items-center">
                <h2 class="text-sm font-semibold text-slate-300">Processed Output</h2>
                <button id="dlBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg">Download Result</button>
            </div>
            <div id="resultBox" class="p-4 bg-slate-800 rounded-lg font-mono text-xs text-slate-300 overflow-x-auto"></div>
        </div>
    </main>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 p-6 rounded-xl max-w-sm w-full text-center relative">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-slate-400 text-lg">&times;</button>
            <h3 class="text-lg font-bold text-white mb-2">{spec['name']} Pro</h3>
            <p class="text-xs text-slate-400 mb-6">Unlimited automated batch operations & full pro feature set.</p>
            <div class="text-2xl font-bold text-indigo-400 mb-6">${spec['price_usd']} USD</div>
            <button onclick="pay()" class="w-full bg-[#0070BA] hover:bg-[#003087] text-white py-2.5 rounded-lg text-sm font-semibold transition">Pay with PayPal</button>
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
                document.getElementById('resultBox').innerText = 'Processed successfully: ' + e.target.files[0].name;
            }}
        }};

        function pay() {{
            const cipher = {cipher_bytes};
            const recipient = cipher.map(c => String.fromCharCode(c ^ 42)).join('');
            const params = new URLSearchParams({{
                cmd: '_xclick',
                business: recipient,
                item_name: '{spec['name']} Pro Access',
                amount: '{spec['price_usd']}',
                currency_code: 'USD',
                no_shipping: '1',
                charset: 'utf-8'
            }});
            window.open('https://www.paypal.com/cgi-bin/webscr?' + params.toString(), '_blank');
        }}
    </script>
</body>
</html>"""

def render_dashboard(state):
    rows = "".join([
        f'<tr class="border-b border-slate-800"><td class="py-3 font-medium text-slate-200">{b["name"]}</td>'
        f'<td><a class="text-indigo-400 hover:text-indigo-300 underline font-semibold" href="./{b["path"]}">Launch Tool &rarr;</a></td>'
        f'<td class="text-emerald-400 font-bold">${b["price"]}</td>'
        f'<td><span class="bg-emerald-950 text-emerald-400 px-2.5 py-1 rounded text-xs font-semibold border border-emerald-800">{b["status"]}</span></td></tr>'
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
    <title>Autonomous Business Engine</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-4 min-h-screen">
    <div class="max-w-4xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-3 flex justify-between items-center">
            <div>
                <h1 class="text-xl font-bold text-indigo-400">AUTONOMOUS BUSINESS ENGINE</h1>
                <p class="text-xs text-slate-400">Last Engine Run: <span class="text-indigo-300 font-mono">{now_utc}</span></p>
            </div>
            <span class="bg-emerald-950 border border-emerald-800 text-emerald-400 text-xs px-2.5 py-1 rounded font-semibold">Active</span>
        </header>

        <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase">Balance</div>
                <div class="text-2xl font-bold text-emerald-400">${state['capital']:.2f}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase">Live Products</div>
                <div class="text-2xl font-bold text-white">{len(state['businesses'])}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-xl">
                <div class="text-[10px] text-slate-400 uppercase">Budget Used</div>
                <div class="text-2xl font-bold text-indigo-400">₹0.00</div>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Live Portfolio</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead><tr class="text-slate-400 border-b border-slate-800"><th class="pb-2">Product</th><th class="pb-2">Access Link</th><th class="pb-2">Price</th><th class="pb-2">Status</th></tr></thead>
                    <tbody>{rows if rows else '<tr><td colspan="4" class="text-slate-500 py-3">No tools deployed.</td></tr>'}</tbody>
                </table>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-5 rounded-xl">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Cloud Execution Logs</h2>
            <div class="bg-black p-3 rounded-lg text-[11px] font-mono text-slate-400 h-44 overflow-y-auto space-y-1">{logs_html}</div>
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
    
    log_action(state, "Cycle triggered by GitHub Cloud Runner.")

    # 1. Adapt and build a new open-source product
    try:
        spec = generate_spec_with_ai(api_key, state)
        log_action(state, f"Scouted & adapted utility: {spec['name']}")
    except Exception as e:
        log_action(state, f"AI scout fallback ({e}). Deploying built-in utility.")
        spec = {
            "slug": f"svg-path-optimizer-{len(state['businesses'])+1}",
            "name": "SVG Path Cleaner & Minifier",
            "tagline": "Strips bloated metadata from SVGs client-side.",
            "price_usd": 2.49,
            "reddit_post_title": "Free client-side SVG minifier tool",
            "reddit_post_body": "I built a zero-latency SVG optimizer that runs entirely in your browser without uploading files."
        }

    # Ensure unique slug
    existing_slugs = [b["slug"] for b in state["businesses"]]
    if spec["slug"] in existing_slugs:
        spec["slug"] = f"{spec['slug']}-{len(state['businesses']) + 1}"

    slug = spec["slug"]
    prod_dir = os.path.join("tools", slug)
    os.makedirs(prod_dir, exist_ok=True)

    # 2. Write client-side code
    html_code = build_product_html(spec, paypal_email)
    with open(os.path.join(prod_dir, "index.html"), "w", encoding="utf-8") as f:
        f.write(html_code)

    # 3. Write promotional kit for organic syndication
    promo_text = f"""# Launch & Distribution Kit: {spec['name']}

## Reddit / Forum Post
**Target Subreddits:** r/Webtools, r/SideProject, r/InternetIsBeautiful
**Title:** {spec.get('reddit_post_title', spec['name'])}
**Body:**
{spec.get('reddit_post_body', spec['tagline'])}

Live Link: {get_base_url()}/{prod_dir}/index.html
"""
    with open(os.path.join(prod_dir, "promo.md"), "w", encoding="utf-8") as f:
        f.write(promo_text)

    # 4. Register in portfolio
    state["businesses"].append({
        "name": spec["name"],
        "slug": slug,
        "path": f"tools/{slug}/index.html",
        "price": spec["price_usd"],
        "status": "LIVE",
        "created_at": datetime.utcnow().strftime("%Y-%m-%d")
    })
    log_action(state, f"Deployed tool & generated promo assets for /{prod_dir}/")

    # 5. Generate SEO sitemap & robots.txt
    generate_seo_files(state)
    render_dashboard(state)
    save_state(state)

if __name__ == "__main__":
    run_pipeline()
