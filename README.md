# Shopify Scraper

A Python tool for scraping product data from Shopify-based e-commerce stores. This scraper extracts product information including prices, availability, images, and descriptions, and exports the data to JSON and CSV formats.

## Features

- 🔍 **Smart Availability Detection**: Uses hybrid strategy (JSON API + .js endpoint fallback) to accurately determine product availability
- 🛡️ **Anti-Bot Protection**: Rotating user agents and optional proxy support to avoid detection
- 📊 **Multiple Export Formats**: Saves data in both JSON and CSV formats
- 🔄 **Automatic Retry Logic**: Handles rate limiting and failed requests intelligently
- 🎯 **Accurate Pricing**: Captures both current and original prices to identify discounts

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
```bash
python3 -m venv venv
source venv/bin/activate  # On macOS/Linux
# or
venv\Scripts\activate  # On Windows
```

3. Install dependencies:
```bash
python3 -m pip install -r requirements.txt
```

## Usage

### Basic Usage

```bash
python3 shopify-scraper.py -t https://example-store.com
```

### With Proxies

```bash
python3 shopify-scraper.py -t https://example-store.com -p proxies.txt
```

### Custom Output Name

```bash
python3 shopify-scraper.py -t https://example-store.com -o my_products
```

### Silent Mode

```bash
python3 shopify-scraper.py -t https://example-store.com -s
```

## Command-Line Arguments

| Argument | Short | Description | Required | Default |
|----------|-------|-------------|----------|---------|
| `--target` | `-t` | Target Shopify store URL | Yes | - |
| `--proxies` | `-p` | Path to proxy file (one proxy per line) | No | `proxies.txt` |
| `--output` | `-o` | Output file name prefix | No | Extracted from URL |
| `--silent` | `-s` | Silent mode (minimal output) | No | False |

## Proxy File Format

If using proxies, create a `proxies.txt` file with one proxy per line:

```
http://user:pass@proxy1.com:8080
http://user:pass@proxy2.com:8080
https://proxy3.com:8080
```

## Output

The scraper generates two files:

- `{output_name}.json` - Detailed product data in JSON format
- `{output_name}.csv` - Tabular data in CSV format

### Output Fields

Each product includes:
- `external_id` - Shopify product ID
- `name` - Product name
- `price` - Current price
- `original_price` - Original/compare-at price
- `is_discounted` - Boolean indicating if product is on sale
- `is_sold_out` - Boolean indicating availability
- `buy_link` - Direct product URL
- `images` - Array of image URLs
- `description` - Product description (truncated to 500 chars)
- `scraped_at` - Timestamp of when data was collected

## How It Works

1. **Fetches product list** from the store's `/products.json` endpoint
2. **Checks availability** using a hybrid approach:
   - First checks the JSON API response
   - Falls back to individual product `.js` endpoints for accurate availability
3. **Rotates user agents** and proxies (if provided) to avoid detection
4. **Handles pagination** automatically, processing all pages
5. **Exports results** to both JSON and CSV formats

## Example

```bash
python3 shopify-scraper.py -t https://flavamadeit.com
```

Output:
```
[🚀] STARTING SCRAPER: https://flavamadeit.com
[i] Not found any proxy - running on local IP.

--- Processing page 1 ---
   ✅ Product Name 1 | 99.99 PLN
   ❌ Product Name 2 | 149.99 PLN
   ✅ Product Name 3 | 79.99 PLN
...

[OK] Saved 45 products to flavamadeit.json
[OK] Saved 45 products to flavamadeit.csv
```

## Notes

- The scraper respects rate limits and includes delays between requests
- Some stores may have additional anti-bot measures that could block scraping
- Use proxies responsibly and in compliance with the target website's terms of service
- This tool is for educational and research purposes

## License

This project is provided as-is for educational purposes.

Read me created by copilot:)
