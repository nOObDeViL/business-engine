import os
import json
import urllib.request
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
    return {
        "capital": 0.0,
        "revenue": 0.0,
        "businesses": [],
        "logs": [],
        "indexing_status": "Pending Initial Crawl",
        "total_page_views": 0
    }

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

def update_seo_and_ping(state):
    base_url = get_base_url()
    today = datetime.utcnow().strftime("%Y-%m-%d")

    # Generate Sitemap
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

    with open(ROBOTS_FILE, "w", encoding="utf-8") as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base_url}/sitemap.xml\n")

    # Automated Ping to Search Engines
    sitemap_url = f"{base_url}/sitemap.xml"
    try:
        urllib.request.urlopen(f"https://www.bing.com/ping?sitemap={sitemap_url}", timeout=5)
        state["indexing_status"] = f"Pings Submitted ({today})"
        log_action(state, "Sitemap successfully broadcasted to search crawlers.")
    except Exception:
        state["indexing_status"] = f"Sitemap Updated ({today})"

def generate_tool_spec(api_key: str, state: dict) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)

    # Alternate between brand new tool vs mobile mutation
    should_mutate = len(state["businesses"]) > 0 and len(state["businesses"]) % 2 == 1
    
    if should_mutate:
        parent = state["businesses"][0]
        prompt = f"""You are the Mutation Engine. Create a specialized MOBILE-FIRST variant of our product '{parent['name']}'.
Target: Smartphone/tablet touch interfaces, 9:16 vertical video formats (TikTok/Shorts/Reels), or instant mobile image cropping.
Strict Rule: Price MUST be between $0.99 and $1.49.
Return ONLY valid JSON:
{{
  "slug": "{parent['slug']}-mobile-9x16",
  "name": "{parent['name']} (9:16 Mobile & Shorts Edition)",
  "tagline": "Format comic panels directly into 9:16 vertical video stories on mobile.",
  "price_usd": 0.99,
  "is_mutation": true
}}"""
    else:
        prompt = """Generate a high-utility, client-side web utility (HTML5/Canvas) for developers or digital creators.
Strict Rule: Price MUST be between $0.99 and $1.49.
Return ONLY valid JSON:
{
  "slug": "unique-slug-name",
  "name": "Punchy Tool Name",
  "tagline": "1-sentence benefit statement",
  "price_usd": 0.99,
  "is_mutation": false
}"""

    target_model = "gemini-2.5-flash"
    try:
        available = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])]
        for pref in ["gemini-2.5-flash", "gemini-1.5-flash", "gemini-pro"]:
            m = next((m for m in available if pref in m), None)
            if m:
                target_model = m
                break
    except Exception:
        pass

    response = client.models.generate_content(model=target_model, contents=prompt)
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
    <title>{spec['name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/jszip/3.10.1/jszip.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/FileSaver.js/2.0.5/FileSaver.min.js"></script>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen flex flex-col font-sans">
    <header class="border-b border-slate-800 p-4 flex justify-between items-center max-w-4xl w-full mx-auto">
        <div>
            <h1 class="text-lg font-bold text-indigo-400">{spec['name']}</h1>
            <p class="text-xs text-slate-400">{spec['tagline']}</p>
        </div>
        <button onclick="document.getElementById('modal').classList.remove('hidden')" class="bg-emerald-600 hover:bg-emerald-500 text-white text-xs px-3.5 py-2 rounded-lg font-bold shadow-md transition">
            Unlock Pro (${spec['price_usd']})
        </button>
    </header>

    <main class="flex-1 max-w-4xl w-full mx-auto p-4 flex flex-col items-center">
        <div id="drop" class="w-full border-2 border-dashed border-slate-700 hover:border-indigo-500 rounded-2xl p-8 text-center cursor-pointer transition bg-slate-800/40 my-4">
            <input type="file" id="fileIn" accept="image/*" class="hidden">
            <p class="text-sm text-slate-300">Tap to upload image file</p>
            <p class="text-[11px] text-slate-500 mt-1">Processed 100% locally in browser memory. No files sent to servers.</p>
        </div>
        <div id="output" class="w-full hidden space-y-4">
            <div class="flex justify-between items-center">
                <span class="text-xs font-semibold text-slate-300">Generated Panels</span>
                <button id="dlBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-3 py-1.5 rounded-lg">Download All (ZIP)</button>
            </div>
            <div id="panels" class="grid grid-cols-2 md:grid-cols-3 gap-3"></div>
        </div>
    </main>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 p-6 rounded-xl max-w-xs w-full text-center relative shadow-2xl">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-slate-400 text-lg">&times;</button>
            <h3 class="text-base font-bold text-white mb-1">{spec['name']} Pro</h3>
            <p class="text-xs text-slate-400 mb-4">Unlimited batch processing and zero compression output.</p>
            <div class="text-3xl font-black text-emerald-400 mb-5">${spec['price_usd']} <span class="text-xs text-slate-400 font-normal">USD</span></div>
            <button onclick="pay()" class="w-full bg-[#0070BA] hover:bg-[#003087] text-white py-2.5 rounded-lg text-xs font-bold transition">Pay with PayPal</button>
        </div>
    </div>

    <script>
        const fileIn = document.getElementById('fileIn');
        const drop = document.getElementById('drop');
        drop.onclick = () => fileIn.click();
        fileIn.onchange = (e) => {{ if (e.target.files.length) handle(e.target.files[0]); }};

        let slices = [];
        function handle(file) {{
            const img = new Image();
            img.onload = () => {{
                document.getElementById('output').classList.remove('hidden');
                drop.classList.add('hidden');
                const container = document.getElementById('panels');
                container.innerHTML = '';
                slices = [];
                const targetW = 1080, targetH = 1920; // 9:16 mobile vertical format
                const sliceH = img.width * (targetH / targetW);
                const count = Math.min(Math.ceil(img.height / sliceH), 8);
                for(let i = 0; i < count; i++) {{
                    const canvas = document.createElement('canvas');
                    canvas.width = targetW; canvas.height = targetH;
                    const ctx = canvas.getContext('2d');
                    ctx.fillStyle = "#0f172a";
                    ctx.fillRect(0,0,targetW,targetH);
                    const sy = i * sliceH;
                    const sh = Math.min(sliceH, img.height - sy);
                    const dh = (sh / sliceH) * targetH;
                    ctx.drawImage(img, 0, sy, img.width, sh, 0, (targetH - dh)/2, targetW, dh);
                    slices.push(canvas);
                    const thumb = document.createElement('img');
                    thumb.src = canvas.toDataURL();
                    thumb.className = "rounded border border-slate-700 w-full";
                    container.appendChild(thumb);
                }}
            }};
            img.src = URL.createObjectURL(file);
        }}

        document.getElementById('dlBtn').onclick = () => {{
            const zip = new JSZip();
            slices.forEach((c, idx) => zip.file(`panel_${{idx+1}}.png`, c.toDataURL().split(',')[1], {{base64: true}}));
            zip.generateAsync({{type:'blob'}}).then(b => saveAs(b, 'panels_mobile.zip'));
        }};

        function pay() {{
            const cipher = {cipher_bytes};
            const recipient = cipher.map(c => String.fromCharCode(c ^ 42)).join('');
            const params = new URLSearchParams({{
                cmd: '_xclick',
                business: recipient,
                item_name: '{spec['name']} Pro Unlock',
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
        f'<td><a class="text-indigo-400 hover:text-indigo-300 underline text-xs font-semibold" href="./{b["path"]}">View Tool</a></td>'
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
            <div class="text-right">
                <span class="text-[10px] bg-slate-900 border border-slate-700 text-slate-300 px-2.5 py-1 rounded font-mono">
                    Search Engine Status: {state.get('indexing_status', 'Active')}
                </span>
            </div>
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
                <div class="text-[10px] text-slate-400 uppercase font-bold">Pricing Model</div>
                <div class="text-2xl font-black text-indigo-400 font-mono">$0.99</div>
            </div>
        </div>

        <div class="bg-slate-900 border border-slate-800 p-4 rounded-xl">
            <h2 class="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">Live Products & Mutations</h2>
            <div class="overflow-x-auto">
                <table class="w-full text-left text-xs">
                    <thead><tr class="text-slate-400 border-b border-slate-800"><th class="pb-2">Tool</th><th class="pb-2">Link</th><th class="pb-2">Price</th><th class="pb-2">Status</th></tr></thead>
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
    
    log_action(state, "Cycle triggered by GitHub Actions.")

    try:
        spec = generate_tool_spec(api_key, state)
        log_action(state, f"Generated spec: '{spec['name']}' at ${spec['price_usd']}")
    except Exception as e:
        log_action(state, f"Fallback generator engaged: {e}")
        spec = {
            "slug": f"comic-slicer-mobile-9x16-{len(state['businesses'])+1}",
            "name": "Webtoon 9:16 Shorts Slicer",
            "tagline": "Converts comic strips into 9:16 vertical frames for TikTok and Shorts.",
            "price_usd": 0.99
        }

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
    log_action(state, f"Deployed tool to /{prod_dir}/")

    update_seo_and_ping(state)
    render_dashboard(state)
    save_state(state)

if __name__ == "__main__":
    run_pipeline()
