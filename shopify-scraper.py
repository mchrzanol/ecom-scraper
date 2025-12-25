import json
import csv
import requests
import argparse
import time
import random
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs, urlencode, urlunparse

# anti-bot and proxy settings
USER_AGENTS = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:109.0) Gecko/20100101 Firefox/119.0',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15'
]

def get_random_headers():
    return {
        'User-Agent': random.choice(USER_AGENTS),
        'Accept': 'application/json, text/javascript, */*; q=0.01',
        'Accept-Language': 'pl-PL,pl;q=0.9,en-US;q=0.8,en;q=0.7'
    }

def load_proxies(file_path, silent=False):
    try:
        with open(file_path, 'r') as f:
            proxies = [line.strip() for line in f if line.strip()]
        if not silent:
            print(f"[i] Loaded {len(proxies)} proxy servers.")
        return proxies
    except FileNotFoundError:
        if not silent:
            print("[i] Not found any proxy - running on local IP.")
        return []

def get_request(url, proxy_list):
    retries = 3
    for _ in range(retries):
        headers = get_random_headers()
        proxy_dict = {}
        
        if proxy_list:
            proxy_url = random.choice(proxy_list)
            proxy_dict = {'http': proxy_url, 'https': proxy_url}

        try:
            r = requests.get(url, headers=headers, proxies=proxy_dict, timeout=10)
            if r.status_code == 200:
                return r
            elif r.status_code == 429: # Too Many Requests
                time.sleep(5)
            elif r.status_code == 403: # Bot detected
                pass # Try again with different proxy/user-agent
        except Exception:
            pass # Silently ignore and retry
            
    return None # Failed after retries

def check_availability_via_js(product_handle, base_url, proxy_list):
    """
    PLAN B: Accesses the .js endpoint of a specific product.
    This bypasses hiding inventory states on collective lists.
    Returns: (is_available, variants_array)
    """
    js_url = f"{base_url}/products/{product_handle}.js"
    r = get_request(js_url, proxy_list)
    
    if not r: return False, [] # Failed to fetch, assume unavailable

    try:
        data = r.json()
        variants = data.get('variants', [])
        # Extract variant info with title and availability
        variant_list = [
            {
                'title': v.get('title', ''),
                'available': v.get('available', False)
            }
            for v in variants
        ]
        is_available = any(v.get('available') for v in variants)
        return is_available, variant_list
    except:
        return False, []

def clean_html(raw_html):
    if not raw_html: return ""
    return BeautifulSoup(raw_html, 'html.parser').get_text(separator=' ').strip()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-t', '--target', dest='website_url', type=str, required=True, help='url link')
    parser.add_argument('-p', '--proxies', dest='proxy_file', type=str, default='proxies.txt', help='proxy file path')
    parser.add_argument('-o', '--output', dest='output_file', type=str, help='output file name prefix')
    parser.add_argument('-s', '--silent', action='store_true', help='silent mode, minimal output')
    args = parser.parse_args()

    base_url = args.website_url.rstrip('/')
    list_url = base_url + '/products.json'

    output_file_name = args.output_file if args.output_file else args.website_url.replace('https://', '').replace('http://', '').split('.')[0]
    
    proxies = load_proxies(args.proxy_file, args.silent)
    all_products = []

    page = 1
    if not args.silent:
        print(f"\n[🚀] STARTING SCRAPER: {base_url}")
        print("[i] Strategy: JSON -> JS Fallback -> Proxy Rotation")

    while True:
        if not args.silent:
            print(f"\n--- Processing page {page} ---")
        
        # Fetch product list (JSON)
        r = get_request(f"{list_url}?page={page}", proxies)
        
        if not r:
            if not args.silent:
                print("[!] Error fetching product list. Stopping.")
            break
            
        data = r.json()
        products = data.get('products', [])

        if not products:
            if not args.silent:
                print("[i] No more products. Done.")
            break

        for p in products:
            try:
                # 1. Basic data
                name = p['title']
                handle = p['handle']
                product_url = f"{base_url}/products/{handle}"
                
                variants = p.get('variants', [])
                if not variants: continue
                
                first_variant = variants[0]

                # 2. AVAILABILITY CHECK (Hybrid Strategy)
                is_available = False
                variant_list = []
                
                # STEP A: Check quick JSON list
                # Look at available OR inventory states/policy
                qty = first_variant.get('inventory_quantity', 0)
                policy = first_variant.get('inventory_policy', 'deny')
                
                # Do we have an explicit available flag?
                json_explicit_avail = any(v.get('available') for v in variants) if 'available' in first_variant else None
                
                if json_explicit_avail is True:
                    is_available = True
                    # Extract variants from JSON
                    variant_list = [
                        {
                            'title': v.get('title', ''),
                            'available': v.get('available', False)
                        }
                        for v in variants
                    ]
                elif qty > 0 or policy == 'continue':
                    is_available = True
                    # Extract variants from JSON (may not have 'available' field)
                    variant_list = [
                        {
                            'title': v.get('title', ''),
                            'available': (v.get('inventory_quantity', 0) > 0 or v.get('inventory_policy') == 'continue')
                        }
                        for v in variants
                    ]
                else:
                    # STEP B: If JSON list is silent/unclear -> query the .js endpoint
                    # We only do this if Step A gave False/No data, to avoid unnecessary calls
                    # print(f"   ...querying .js for {name}") # Optional log
                    is_available, variant_list = check_availability_via_js(handle, base_url, proxies)

                # 3. Rest of data
                price = float(first_variant.get('price', 0))
                compare = first_variant.get('compare_at_price')
                old_price = float(compare) if compare else price
                
                images = [img['src'] for img in p.get('images', [])]
                # main_image = images[0] if images else ""
                
                desc = clean_html(p.get('body_html', ''))

                # Data object
                item = {
                    'external_id': p['id'],# unique product shopify ID
                    'name': name,
                    'price': price,
                    'original_price': old_price,
                    'is_discounted': old_price > price,
                    'is_sold_out': is_available,
                    'buy_link': product_url, # utm applied later if needed
                    'images': images,
                    'variants': variant_list,
                    'description': desc, # short description
                    'scraped_at': time.strftime('%Y-%m-%d %H:%M:%S')
                }
                
                all_products.append(item)
                
                if not args.silent:
                    icon = "✅" if is_available else "❌"
                    print(f"   {icon} {name} | {price} PLN")

            except Exception as e:
                if not args.silent:
                    print(f"   [!] Error processing product: {e}")
                continue

        page += 1
        # Random delay between pages
        sleep_time = random.uniform(1.0, 3.0)
        if not args.silent:
            print(f"[zzz] Waiting {sleep_time:.1f}s...")
        time.sleep(sleep_time)
    
    # 1. Save to JSON
    with open(output_file_name + '.json', 'w', encoding='utf-8') as f:
        json.dump(all_products, f, ensure_ascii=False, indent=4)
    if not args.silent:
        print(f"\n[OK] Saved {len(all_products)} products to {output_file_name}.json")

    # 2. Save to CSV
    if all_products:
        keys = all_products[0].keys()
        with open(output_file_name + '.csv', 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(all_products)
    if not args.silent:
        print(f"[OK] Saved {len(all_products)} products to {output_file_name}.csv")