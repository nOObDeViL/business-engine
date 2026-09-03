import os
import json
from datetime import datetime

STATE_FILE = "state.json"
DASHBOARD_FILE = "index.html"

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

def get_builtin_product_spec():
    """Guaranteed zero-cost product blueprint (failsafe fallback)."""
    return {
        "slug": "comic-16x9-slicer",
        "name": "Webtoon & Manga 16:9 Panel Slicer",
        "tagline": "Slices vertical webtoons into 16:9 video recap assets directly in your browser.",
        "price_usd": 2.99
    }

def generate_spec_with_ai(api_key: str, state: dict) -> dict:
    from google import genai
    client = genai.Client(api_key=api_key)
    
    # 1. Discover models supported by this key
    target_model = "gemini-3.6-flash"
    try:
        available = [m.name for m in client.models.list() if "generateContent" in getattr(m, "supported_generation_methods", ["generateContent"])]
        # Match preferred models
        for pref in ["gemini-3.6-flash", "gemini-2.0-flash", "gemini-1.5-flash", "gemini-pro"]:
            matched = [m for m in available if pref in m]
            if matched:
                target_model = matched[0]
                break
    except Exception as e:
        log_action(state, f"Model auto-discovery notice: {e}")

    log_action(state, f"Contacting AI Model: {target_model}")
    
    prompt = """Generate an MVP spec for a 100% client-side web utility (HTML5/Canvas, zero compute costs) for creators.
Return ONLY valid JSON (no backticks, no markdown):
{"slug": "unique-url-slug", "name": "Tool Name", "tagline": "1-sentence benefit", "price_usd": 2.50}"""
    
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
    <title>{spec['name']}</title>
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
            <input type="file" id="fileIn" accept="image/*" class="hidden">
            <p class="text-base text-slate-300">Click or drop an image file here to process</p>
            <p class="text-xs text-slate-500 mt-2">100% Private. Processed locally in your browser with zero server uploads.</p>
        </div>
        <div id="output" class="w-full hidden space-y-4">
            <div class="flex justify-between items-center">
                <h2 class="text-sm font-semibold text-slate-300">Processed Output</h2>
                <button id="dlBtn" class="bg-indigo-600 hover:bg-indigo-500 text-white text-xs px-4 py-2 rounded-lg">Download Panels (ZIP)</button>
            </div>
            <div id="panels" class="grid grid-cols-1 md:grid-cols-2 gap-4"></div>
        </div>
    </main>

    <div id="modal" class="hidden fixed inset-0 bg-black/80 flex items-center justify-center p-4 z-50">
        <div class="bg-slate-800 border border-slate-700 p-6 rounded-xl max-w-sm w-full text-center relative">
            <button onclick="document.getElementById('modal').classList.add('hidden')" class="absolute top-3 right-3 text-slate-400 text-lg">&times;</button>
            <h3 class="text-lg font-bold text-white mb-2">{spec['name']} Pro</h3>
            <p class="text-xs text-slate-400 mb-6">Unlimited batch processing and 4K output exports.</p>
            <div class="text-2xl font-bold text-indigo-400 mb-6">${spec['price_usd']} USD</div>
            <button onclick="pay()" class="w-full bg-[#0070BA] hover:bg-[#003087] text-white py-2.5 rounded-lg text-sm font-semibold transition">Pay via PayPal</button>
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
                const targetW = 1920, targetH = 1080;
                const sliceH = img.width * (targetH / targetW);
                const count = Math.min(Math.ceil(img.height / sliceH), 6);
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
            zip.generateAsync({{type:'blob'}}).then(b => saveAs(b, 'panels.zip'));
        }};

        function pay() {{
            const cipher = {cipher_bytes};
            const recipient = cipher.map(c => String.fromCharCode(c ^ 42)).join('');
            const form = document.createElement('form');
            form.method = 'post';
            form.action = 'https://www.paypal.com/cgi-bin/webscr';
            form.target = '_blank';
            const f = {{
                'cmd': '_xclick',
                'business': recipient,
                'item_name': '{spec['name']} Pro Access',
                'amount': '{spec['price_usd']}',
                'currency_code': 'USD',
                'no_shipping': '1'
            }};
            for (const [k,v] of Object.entries(f)) {{
                const input = document.createElement('input');
                input.type = 'hidden'; input.name = k; input.value = v;
                form.appendChild(input);
            }}
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
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
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
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

    # Try AI generation first; fall back seamlessly if any error occurs
    spec = None
    if api_key:
        try:
            spec = generate_spec_with_ai(api_key, state)
            log_action(state, f"AI generated blueprint: {spec['name']}")
        except Exception as e:
            log_action(state, f"AI generation unavailable ({e}). Engaging built-in failsafe blueprint.")
            spec = get_builtin_product_spec()
    else:
        log_action(state, "No API key found. Engaging built-in failsafe blueprint.")
        spec = get_builtin_product_spec()

    # Prevent duplicate registrations of the same slug
    existing_slugs = [b["slug"] for b in state["businesses"]]
    if spec["slug"] in existing_slugs:
        spec["slug"] = f"{spec['slug']}-{len(state['businesses']) + 1}"

    # Build and deploy product
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
    log_action(state, f"Successfully built and deployed '{spec['name']}' to /{prod_dir}/")

    render_dashboard(state)
    save_state(state)

if __name__ == "__main__":
    run_pipeline()
