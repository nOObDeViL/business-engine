import os
import json
import uuid
from datetime import datetime
from google import genai

STATE_FILE = "state.json"
DASHBOARD_FILE = "index.html"

def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"capital": 0.0, "revenue": 0.0, "businesses": [], "logs": []}

def save_state(state):
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

def log_action(state, msg):
    timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")
    entry = f"[{timestamp}] {msg}"
    state["logs"].append(entry)
    state["logs"] = state["logs"][-20:]
    print(entry)

def run_pipeline():
    state = load_state()
    api_key = os.environ.get("GOOGLE_API_KEY")
    paypal_email = os.environ.get("PAYPAL_RECEIVER_EMAIL", "ccprakash67@gmail.com")
    
    if not api_key:
        log_action(state, "FATAL: Missing GOOGLE_API_KEY secret.")
        save_state(state)
        return

    log_action(state, "Cycle triggered by GitHub Cloud Runner.")

    key = 42
    cipher_bytes = [ord(char) ^ key for char in paypal_email]

    prompt = """
    Generate an MVP spec for a 100% client-side web utility (HTML5/Canvas/Vanilla JS, $0 compute) for creators or developers.
    Return clean JSON only (no markdown formatting, no backticks):
    {
      "slug": "url-slug",
      "name": "Tool Name",
      "tagline": "Short description",
      "price_usd": 2.50
    }
    """
    
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        
        cleaned_text = response.text.strip().replace("```json", "").replace("```", "").strip()
        spec = json.loads(cleaned_text)
        
        slug = spec["slug"]
        prod_dir = os.path.join("tools", slug)
        os.makedirs(prod_dir, exist_ok=True)

        product_html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{spec['name']}</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-900 text-white min-h-screen flex flex-col items-center justify-center p-6">
    <div class="max-w-xl w-full bg-slate-800 p-8 rounded-2xl border border-slate-700 text-center shadow-xl">
        <h1 class="text-2xl font-bold text-indigo-400 mb-2">{spec['name']}</h1>
        <p class="text-sm text-slate-300 mb-6">{spec['tagline']}</p>
        <div class="p-6 border-2 border-dashed border-slate-600 rounded-xl mb-6">
            <input type="file" id="up" class="text-xs text-slate-400">
        </div>
        <button onclick="checkout()" class="w-full bg-[#0070BA] hover:bg-[#003087] py-3 rounded-xl font-semibold shadow-md transition">
            Unlock Pro (${spec['price_usd']})
        </button>
    </div>
    <script>
        function checkout() {{
            const cipher = {cipher_bytes};
            const key = {key};
            const recipient = cipher.map(c => String.fromCharCode(c ^ key)).join('');
            const form = document.createElement('form');
            form.method = 'post';
            form.action = 'https://www.paypal.com/cgi-bin/webscr';
            form.target = '_blank';
            const fields = {{
                'cmd': '_xclick',
                'business': recipient,
                'item_name': '{spec['name']} Pro Unlock',
                'amount': '{spec['price_usd']}',
                'currency_code': 'USD',
                'no_shipping': '1'
            }};
            for (const [k, v] of Object.entries(fields)) {{
                const input = document.createElement('input');
                input.type = 'hidden';
                input.name = k;
                input.value = v;
                form.appendChild(input);
            }}
            document.body.appendChild(form);
            form.submit();
            document.body.removeChild(form);
        }}
    </script>
</body>
</html>"""
        with open(os.path.join(prod_dir, "index.html"), "w", encoding="utf-8") as f:
            f.write(product_html)

        state["businesses"].append({
            "name": spec["name"],
            "slug": slug,
            "path": f"tools/{slug}/",
            "price": spec["price_usd"],
            "status": "LIVE",
            "created_at": datetime.utcnow().strftime("%Y-%m-%d")
        })
        log_action(state, f"Successfully built and deployed '{spec['name']}'.")

    except Exception as e:
        log_action(state, f"Generation error: {str(e)}")

    render_dashboard(state)
    save_state(state)

def render_dashboard(state):
    rows = "".join([
        f'<tr class="border-b border-slate-800"><td class="py-2">{b["name"]}</td>'
        f'<td><a class="text-indigo-400 underline" href="./{b["path"]}">View Tool</a></td>'
        f'<td class="text-emerald-400 font-bold">${b["price"]}</td>'
        f'<td><span class="bg-emerald-950 text-emerald-400 px-2 py-0.5 rounded text-xs">{b["status"]}</span></td></tr>'
        for b in state["businesses"]
    ])
    logs_html = "".join([f'<div class="py-0.5">{log}</div>' for log in reversed(state["logs"])])

    html = f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Autonomous Engine Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-slate-950 text-slate-100 font-sans p-4 min-h-screen">
    <div class="max-w-4xl mx-auto space-y-6">
        <header class="border-b border-slate-800 pb-3">
            <h1 class="text-xl font-bold text-indigo-400">AUTONOMOUS BUSINESS ENGINE</h1>
            <p class="text-xs text-slate-400">Host: GitHub Cloud Actions (100% Free)</p>
        </header>
        <div class="grid grid-cols-3 gap-3 text-center">
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                <div class="text-[10px] text-slate-400 uppercase">Balance</div>
                <div class="text-2xl font-bold text-emerald-400">${state['capital']:.2f}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                <div class="text-[10px] text-slate-400 uppercase">Live Products</div>
                <div class="text-2xl font-bold text-white">{len(state['businesses'])}</div>
            </div>
            <div class="bg-slate-900 border border-slate-800 p-3 rounded-lg">
                <div class="text-[10px] text-slate-400 uppercase">Budget Used</div>
                <div class="text-2xl font-bold text-indigo-400">₹0.00</div>
            </div>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <h2 class="text-xs font-bold text-slate-300 uppercase mb-3">Live Portfolio</h2>
            <table class="w-full text-left text-xs">
                <thead><tr class="text-slate-400 border-b border-slate-800"><th>Name</th><th>Link</th><th>Price</th><th>Status</th></tr></thead>
                <tbody>{rows if rows else '<tr><td colspan="4" class="text-slate-500 py-2">No tools built yet.</td></tr>'}</tbody>
            </table>
        </div>
        <div class="bg-slate-900 border border-slate-800 p-4 rounded-lg">
            <h2 class="text-xs font-bold text-slate-300 uppercase mb-2">Cloud Execution Logs</h2>
            <div class="bg-black p-3 rounded text-[11px] font-mono text-slate-400 h-40 overflow-y-auto">{logs_html}</div>
        </div>
    </div>
</body>
</html>"""
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

if __name__ == "__main__":
    run_pipeline()
