# webenum.py

## Usage Examples

- [Basic Usage](#basic-usage)
- [Combined Enumeration](#combined-enumeration)
- [Parameter Discovery](#parameter-discovery)
- [Wordlist Sizes](#wordlist-sizes)
- [Custom Extensions](#custom-extensions)

### Basic Usage

```bash
# Run vhost enumeration
python webenum.py --vhost example.com -t http://example.com

# Run standard web enumeration
python webenum.py --web -t http://example.com

# Run API endpoint enumeration
python webenum.py --api -t http://example.com
```

### Combined Enumeration

```bash
# The web and api enumeration will be performed for the target provided with -t and for 
# every discovered vhost
python webenum.py --vhost example.com --web --api -t http://example.com
```

### Parameter Discovery

Use `--param-discovery` to run parameter discovery on found pages

⚠️ Parameter discovery requires to provide either `--web` or `--api` (or both). Running parameter discovery on a specific page is not yet supported.

```bash
python webenum.py --web --param-discovery -t http://example.com

python webenum.py --api --param-discovery -t http://example.com

python webenum.py --web --api --param-discovery -t http://example.com
```

### Wordlist Sizes

Run more in-depth enumeration specifying wordlists size with `--medium`, `--web-size`, `--api-size` and `--vhost-size`

```bash
# Use 'medium' wordlists globally (default is small)
python webenum.py --web --api --vhost example.com --medium -t http://example.com

# Specific sizes for --web and --api while --vhost uses the global --medium
python webenum.py --web --web-size medium --api --api-size small --vhost example.com --medium -t http://example.com

# Specific size for --vhost while --web and --api use the program global default (small)
python webenum.py --web --api --vhost example.com --vhost-size large -t http://example.com
```

### Custom Extensions

The program performs some basic extensions inference based on server response but additional extensions can be provided with `--extensions`

```bash
# Comma separated list of extensions
python webenum.py -t https://example.com --web --extensions php,asp,aspx
```