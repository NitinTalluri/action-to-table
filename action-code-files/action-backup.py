#!/usr/bin/env python3
"""
Frontend-Backend API Mapping Script with Complete Table Analysis

This script analyzes the frontend TypeScript API files and backend Python route files
to create mapping between frontend API calls and backend endpoints, including the
database tables accessed by each endpoint.

Usage:
    uv run python action_to_table_complete.py
    uv run python action_to_table_complete.py --output mapping.json
    uv run python action_to_table_complete.py --format csv --output mapping.csv
"""
import re
import json
import argparse
import ast
import os
import glob
import builtins
from pathlib import Path
from typing import List, Optional, Dict, Set, Any
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class FrontendCall:
    file: str
    function_name: str
    method: str
    url_pattern: str
    line_number: int
    raw_code: str

@dataclass
class BackendRoute:
    file: str
    method: str
    route_pattern: str
    line_number: int
    function_name: str
    tags: List[str]
    raw_code: str
    tables: List[str]  # New field for database tables

@dataclass
class Mapping:
    frontend: FrontendCall
    backend: Optional[BackendRoute]

# Table analysis components from merged_route_analyzer_with_table_data.py
ROUTER_DECORATORS = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "delete": "DELETE",
    "patch": "PATCH",
    "options": "OPTIONS",
    "head": "HEAD",
}

SKIP_FUNCTIONS = {
    "ServiceException", "HTTPException", "SDPLifeCycle", "select", "text",
    "list", "any", "map", "max", "min", "Depends", "setattr"
}

BUILTIN_FUNCTIONS = {
    name for name in dir(builtins)
    if isinstance(getattr(builtins, name), type(abs))
}

SQL_KEYWORDS = {
    # Standard SQL keywords
    "select", "from", "where", "join", "inner", "left", "right", "full", "outer", "on",
    "insert", "into", "values", "update", "set", "delete", "create", "alter", "drop",
    "table", "view", "index", "and", "or", "not", "in", "is", "null", "like", "as",
    "group", "by", "order", "having", "limit", "offset", "union", "distinct", "case",
    "when", "then", "else", "end", "exists", "count", "sum", "avg", "min", "max", "for",
    "if", "with", "primary", "key", "foreign", "references", "constraint",
    # Common CTE/alias/utility words to filter
    "static", "deleted", "the", "super", "temp", "test", "backup", "current", "stg",
    "metrics", "cluster", "clusters", "details", "hdr", "info", "data", "snapshot",
    "report", "object", "json", "parquet", "thoughtspot", "contracts", "booking", "sub",
    "extension", "extensions", "input", "output", "row", "col", "column", "columns"
}

def collect_all_possible_table_names(root_dir="."):
    """Scan all .py files for __tablename__ = 'XXX' declarations."""
    table_names = set()
    tablename_pattern = re.compile(r'__tablename__\s*=\s*["\']([a-zA-Z0-9_]+)["\']')
    
    for dirpath, _, files in os.walk(root_dir):
        if '.venv' in dirpath or '__pycache__' in dirpath:
            continue
        for file in files:
            if file.endswith(".py"):
                path = os.path.join(dirpath, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        content = f.read()
                    for match in tablename_pattern.findall(content):
                        table_names.add(match.upper())
                except Exception:
                    continue
    return table_names

def extract_tables_from_sql(sql_text: str, known_tables: set = None) -> set:
    """Extract table names from SQL text."""
    tables = set()
    known_tables = known_tables or set()

    # Find CTE names
    cte_pattern = r"with\s+([a-zA-Z0-9_]+)\s+as\s*\("
    cte_names = set(re.findall(cte_pattern, sql_text, flags=re.IGNORECASE))
    chained_cte_pattern = r",\s*([a-zA-Z0-9_]+)\s+as\s*\("
    cte_names.update(re.findall(chained_cte_pattern, sql_text, flags=re.IGNORECASE))

    # Table extraction patterns
    patterns = [
        r'\bFROM\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
        r'\bJOIN\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
        r'\bUPDATE\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
        r'\bINSERT\s+INTO\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
        r'\bMERGE\s+INTO\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
        r'\bDELETE\s+FROM\s+([a-zA-Z0-9_]+)(?:\s|$|\)|,)',
    ]
    
    for pattern in patterns:
        for match in re.findall(pattern, sql_text, re.IGNORECASE):
            table_name = match.strip()
            if '.' in table_name:
                table_name = table_name.split('.')[-1]
            if table_name in known_tables or is_valid_table_candidate(table_name, cte_names):
                tables.add(table_name.upper())
    
    return tables

def is_valid_table_candidate(name: str, cte_names: set) -> bool:
    """Basic validation for table names."""
    if not name or len(name) < 3:
        return False
    
    if name in cte_names or name.lower() in SQL_KEYWORDS or name.isdigit():
        return False
    
    if name.isupper() or '_' in name or (name[0].isupper() and len(name) > 4):
        return True
    
    return False

class CompleteTableAnalyzer(ast.NodeVisitor):
    """Complete AST analyzer with deep function analysis from merged_route_analyzer_with_table_data.py"""
    
    def __init__(self, model_table_map=None, all_known_tables=None, all_function_definitions=None):
        self.router_prefix = ""
        self.routes_info = []
        self.flow_service_aliases = {"flow_service"}
        self.call_graph = defaultdict(set)
        self.defined_functions = set()
        self.current_function = None
        self.proc_calls = defaultdict(list)
        self.table_calls = defaultdict(set)
        self.current_route_info = None
        
        # Deep analysis capabilities
        self.function_definitions = all_function_definitions or {}
        self.analyzed_functions = set()
        self.service_methods = defaultdict(set)
        self.cross_file_functions = {}
        
        self.model_table_map = model_table_map or self._build_model_table_map()
        self.all_known_tables = set(all_known_tables) if all_known_tables else set()

    def _build_model_table_map(self) -> dict:
        """Build model-to-table mapping by scanning ORM files."""
        mapping = {}
        patterns = ["api/**/orm/**/*.py", "**/orm/**/*.py", "**/models/**/*.py"]
        for pattern in patterns:
            for file_path in glob.glob(pattern, recursive=True):
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    class_blocks = re.findall(
                        r'class\s+(\w+)[^\n]*:(.*?)(?=^class\s|\Z)',
                        content,
                        re.DOTALL | re.MULTILINE
                    )
                    for class_name, class_body in class_blocks:
                        match = re.search(r'__tablename__\s*=\s*["\']([^"\']+)["\']', class_body)
                        if match:
                            table_name = match.group(1)
                            mapping[class_name] = table_name.upper()
                except Exception:
                    continue
        return mapping

    def analyze_called_function(self, func_name: str, depth: int = 0) -> set:
        """Recursively analyze a called function to find its table usage"""
        if depth > 5 or func_name in self.analyzed_functions or func_name in SKIP_FUNCTIONS:
            return set()
        
        if func_name in BUILTIN_FUNCTIONS:
            return set()
            
        self.analyzed_functions.add(func_name)
        tables = set()
        
        # Look for function definition
        func_node = self.function_definitions.get(func_name)
        
        if func_node:
            # Save current context
            prev_function = self.current_function
            prev_route_info = self.current_route_info
            
            self.current_function = func_name
            self.current_route_info = None
            
            # Analyze the function body
            self.generic_visit(func_node)
            
            # Collect tables found in this function
            tables.update(self.table_calls.get(func_name, set()))
            
            # Recursively analyze called functions
            for called_func in self.call_graph.get(func_name, []):
                deep_tables = self.analyze_called_function(called_func, depth + 1)
                tables.update(deep_tables)
            
            # Restore context
            self.current_function = prev_function
            self.current_route_info = prev_route_info
        
        return tables

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call) and getattr(node.value.func, "id", None) == "APIRouter":
            for kw in node.value.keywords:
                if kw.arg == "prefix":
                    if isinstance(kw.value, ast.Constant):
                        self.router_prefix = kw.value.value
                    elif isinstance(kw.value, ast.Str):
                        self.router_prefix = kw.value.s
        self.generic_visit(node)

    def visit_With(self, node: ast.With):
        for item in node.items:
            if isinstance(item.context_expr, ast.Name) and item.context_expr.id == "flow_service":
                if isinstance(item.optional_vars, ast.Name):
                    self.flow_service_aliases.add(item.optional_vars.id)
        self.generic_visit(node)

    def visit_FunctionDef(self, node):
        func_name = node.name
        self.defined_functions.add(func_name)
        self.function_definitions[func_name] = node

        route_info = None
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call) and hasattr(decorator.func, "attr"):
                method_lower = decorator.func.attr.lower()
                if method_lower in ROUTER_DECORATORS:
                    path = "/"
                    if decorator.args:
                        arg0 = decorator.args[0]
                        if isinstance(arg0, ast.Constant):
                            path = arg0.value
                        elif isinstance(arg0, ast.Str):
                            path = arg0.s
                    full_path = self.router_prefix + path if self.router_prefix else path
                    route_info = {
                        "method": ROUTER_DECORATORS[method_lower],
                        "path": full_path,
                        "function": func_name,
                        "flow_calls": [],
                        "function_calls": [],
                        "stored_procedures": [],
                        "tables": [],
                        "call_hierarchy": [],
                        "category": "Backend, Frontend"
                    }
                    self.routes_info.append(route_info)
                    break
        
        prev_function = self.current_function
        prev_route_info = self.current_route_info
        self.current_function = func_name
        self.current_route_info = route_info
        self.generic_visit(node)
        self.current_function = prev_function
        self.current_route_info = prev_route_info

    def visit_AsyncFunctionDef(self, node):
        self.visit_FunctionDef(node)

    def visit_Call(self, node):
        if not self.current_function:
            self.generic_visit(node)
            return
        
        base_call_name = self.get_called_name(node.func)
        if base_call_name:
            if base_call_name in BUILTIN_FUNCTIONS or base_call_name in SKIP_FUNCTIONS:
                self.generic_visit(node)
                return
            
            # Track function calls
            self.call_graph[self.current_function].add(base_call_name)
            if self.current_route_info:
                self.current_route_info["function_calls"].append(base_call_name)
            
            # Handle flow service calls
            if isinstance(node.func, ast.Attribute):
                attr_name = node.func.attr
                base = node.func.value
                if isinstance(base, ast.Name) and base.id in self.flow_service_aliases:
                    if self.current_route_info:
                        self.current_route_info["flow_calls"].append(attr_name)
            
            # Handle stored procedures
            if base_call_name in [
                "run_stored_procedure", "run_v2_stored_procedure",
                "run_put_time_entries_stored_procedure", "make_stored_proc_statement"
            ]:
                if base_call_name == "run_put_time_entries_stored_procedure":
                    proc_name_val = "put_user_time_entries"
                    self.proc_calls[self.current_function].append(proc_name_val)
                    if self.current_route_info:
                        self.current_route_info["stored_procedures"].append(proc_name_val)
                
                for kw in node.keywords:
                    if kw.arg == "proc_name":
                        proc_name_val = self.extract_proc_name(kw.value)
                        if proc_name_val:
                            self.proc_calls[self.current_function].append(proc_name_val)
                            if self.current_route_info:
                                self.current_route_info["stored_procedures"].append(proc_name_val)
            
            # Detect database tables
            self.detect_database_tables(node)
        
        self.generic_visit(node)

    def detect_database_tables(self, node):
        """Enhanced database table detection with deep analysis"""
        if not self.current_function:
            return
        
        tables = set()
        
        if isinstance(node, ast.Call):
            func_name = self.get_called_name(node.func)
            
            # Check if function name maps to a table
            if func_name and func_name in self.model_table_map:
                table = self.model_table_map[func_name]
                tables.add(table.upper())
            
            # Enhanced: Check for service method calls
            if isinstance(node.func, ast.Attribute):
                attr_name = node.func.attr
                base = node.func.value
                
                # Pattern: service.method_name() or variable.method()
                if isinstance(base, ast.Name):
                    base_name = base.id
                    # Check if this is a service call
                    if 'service' in base_name.lower() or base_name in self.flow_service_aliases:
                        # This is a service method call - analyze it
                        service_method = f"{base_name}.{attr_name}"
                        if service_method in self.function_definitions:
                            service_tables = self.analyze_called_function(service_method)
                            tables.update(service_tables)
                
                # Pattern: SomeService().method_name()
                elif isinstance(base, ast.Call) and isinstance(base.func, ast.Name):
                    service_class = base.func.id
                    if 'service' in service_class.lower():
                        service_method = f"{service_class}.{attr_name}"
                        if service_method in self.function_definitions:
                            service_tables = self.analyze_called_function(service_method)
                            tables.update(service_tables)
            
            # Enhanced: Use comprehensive model reference extraction
            for arg in node.args:
                model_tables = self.extract_model_references(arg)
                tables.update(model_tables)
                
                # Also check for SQL strings
                if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                    sql_text = arg.value
                    if self.looks_like_sql(sql_text):
                        sql_tables = extract_tables_from_sql(sql_text, self.all_known_tables)
                        tables.update(sql_tables)
            
            # Check keyword arguments
            for kw in getattr(node, 'keywords', []):
                model_tables = self.extract_model_references(kw.value)
                tables.update(model_tables)
                
                if isinstance(kw.value, ast.Constant) and isinstance(kw.value.value, str):
                    sql_text = kw.value.value
                    if self.looks_like_sql(sql_text):
                        sql_tables = extract_tables_from_sql(sql_text, self.all_known_tables)
                        tables.update(sql_tables)
        
        # Store found tables
        for table in tables:
            if table and (table in self.all_known_tables or self.is_likely_real_table(table)):
                self.table_calls[self.current_function].add(table.upper())
                if self.current_route_info and table.upper() not in self.current_route_info["tables"]:
                    self.current_route_info["tables"].append(table.upper())

    def extract_model_references(self, node) -> set:
        """Recursively extract model class references from any AST node"""
        tables = set()
        
        if isinstance(node, ast.Name) and node.id in self.model_table_map:
            table = self.model_table_map[node.id]
            tables.add(table.upper())
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name) and node.value.id in self.model_table_map:
                table = self.model_table_map[node.value.id]
                tables.add(table.upper())
            tables.update(self.extract_model_references(node.value))
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in self.model_table_map:
                table = self.model_table_map[node.func.id]
                tables.add(table.upper())
            for arg in node.args:
                tables.update(self.extract_model_references(arg))
            for kw in node.keywords:
                tables.update(self.extract_model_references(kw.value))
        elif isinstance(node, (ast.List, ast.Tuple, ast.Set)):
            for elt in node.elts:
                tables.update(self.extract_model_references(elt))
        elif isinstance(node, ast.Dict):
            for key, value in zip(node.keys, node.values):
                if key:
                    tables.update(self.extract_model_references(key))
                tables.update(self.extract_model_references(value))
        elif hasattr(node, '__dict__'):
            # For any other node type, recursively check all attributes
            for attr_name, attr_value in node.__dict__.items():
                if isinstance(attr_value, list):
                    for item in attr_value:
                        if isinstance(item, ast.AST):
                            tables.update(self.extract_model_references(item))
                elif isinstance(attr_value, ast.AST):
                    tables.update(self.extract_model_references(attr_value))
        
        return tables

    def looks_like_sql(self, text: str) -> bool:
        """Check if a string looks like SQL"""
        if not text or len(text) < 10:
            return False
        
        text_upper = text.upper()
        sql_keywords = ['SELECT', 'FROM', 'INSERT', 'UPDATE', 'DELETE', 'WITH', 'JOIN', 'WHERE', 'CREATE', 'ALTER', 'DROP']
        keyword_count = sum(1 for keyword in sql_keywords if keyword in text_upper)
        
        if keyword_count >= 2:
            return True
        
        # Check for SQL-like patterns
        sql_patterns = [
            r'\bSELECT\s+.*\bFROM\b',
            r'\bINSERT\s+INTO\b',
            r'\bUPDATE\s+.*\bSET\b',
            r'\bDELETE\s+FROM\b',
            r'\bWITH\s+\w+\s+AS\s*\(',
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, text_upper):
                return True
        
        return False

    def is_likely_real_table(self, name: str) -> bool:
        """Check if a name is likely a real table"""
        if not name or len(name) < 3:
            return False
        
        if name.lower() in SQL_KEYWORDS:
            return False
        
        if (name.isupper() and ('_' in name or len(name) > 5)) or \
           ('_' in name and any(c.isupper() for c in name)):
            return True
        
        return False

    def get_called_name(self, node):
        """Get the name of a called function"""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Call):
            return self.get_called_name(node.func)
        elif isinstance(node, ast.Attribute):
            return node.attr
        return None

    def extract_proc_name(self, node):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        elif isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Attribute):
            return self.get_full_attribute_name(node)
        return None

    def get_full_attribute_name(self, node):
        parts = []
        while isinstance(node, ast.Attribute):
            parts.append(node.attr)
            node = node.value
        if isinstance(node, ast.Name):
            parts.append(node.id)
        parts.reverse()
        return ".".join(parts)

    def visit_Constant(self, node):
        """Visit string constants that might contain SQL"""
        if isinstance(node.value, str) and self.current_function:
            sql_text = node.value
            if self.looks_like_sql(sql_text):
                tables = extract_tables_from_sql(sql_text, self.all_known_tables)
                for table in tables:
                    if self.is_likely_real_table(table):
                        self.table_calls[self.current_function].add(table.upper())
                        if self.current_route_info and table.upper() not in self.current_route_info["tables"]:
                            self.current_route_info["tables"].append(table.upper())
        self.generic_visit(node)

    def visit_Str(self, node):  # For older Python versions
        """Handle string literals in older AST format"""
        if self.current_function:
            sql_text = node.s
            if self.looks_like_sql(sql_text):
                tables = extract_tables_from_sql(sql_text, self.all_known_tables)
                for table in tables:
                    if self.is_likely_real_table(table):
                        self.table_calls[self.current_function].add(table.upper())
                        if self.current_route_info and table.upper() not in self.current_route_info["tables"]:
                            self.current_route_info["tables"].append(table.upper())
        self.generic_visit(node)

class CompleteFrontendAnalyzer:
    """Complete frontend analyzer with all patterns from frontend_backend_api_mapping.py"""
    
    def __init__(self, frontend_path: str):
        self.src_path = Path(frontend_path) / "src"
        
    def extract_frontend_calls(self) -> List[FrontendCall]:
        calls = []
        if not self.src_path.exists():
            return calls
        
        # Search all .ts and .tsx files
        for ext in ["*.ts", "*.tsx"]:
            for file_path in self.src_path.rglob(ext):
                if file_path.name in ["utils.ts", "vite-env.d.ts"]:
                    continue
                calls.extend(self._parse_file(file_path))
        return calls
    
    def _parse_file(self, file_path: Path) -> List[FrontendCall]:
        try:
            lines = file_path.read_text(encoding='utf-8').split('\n')
        except:
            return []
        
        calls = []
        current_function = None
        found_lines = set()  
        
        for i, line in enumerate(lines, 1):
            # Function tracking - COMPLETE patterns from original
            if 'export' in line:
                func_patterns = [
                    r'export\s+(?:const|async\s+function|function)\s+(\w+)',
                    r'export\s+const\s+(\w+)\s*=\s*async',
                    r'export\s+async\s+function\s+(\w+)',
                    r'export\s+function\s+(\w+)',
                ]
                for pattern in func_patterns:
                    func_match = re.search(pattern, line)
                    if func_match:
                        current_function = func_match.group(1)
                        break
            
            # Track arrow functions and const declarations
            elif re.search(r'const\s+\w+\s*=\s*async', line) and not current_function:
                func_match = re.search(r'const\s+(\w+)\s*=\s*async', line)
                if func_match:
                    current_function = func_match.group(1)
            
            # Primary API call detection - COMPLETE patterns from original
            if ('client.' in line or 'tsClient.' in line) and i not in found_lines:
                api_patterns = [
                    r'(?:client|tsClient)\.(get|post|put|patch|delete)',
                    r'await\s+(?:client|tsClient)\.(get|post|put|patch|delete)',
                    r'return\s+(?:await\s+)?(?:client|tsClient)\.(get|post|put|patch|delete)',
                    r'const\s+\w+\s*=\s*(?:await\s+)?(?:client|tsClient)\.(get|post|put|patch|delete)',
                    r'=\s*(?:await\s+)?(?:client|tsClient)\.(get|post|put|patch|delete)',
                    r'\.then\(\s*(?:await\s+)?(?:client|tsClient)\.(get|post|put|patch|delete)',  
                    r'Promise\.all\([^)]*(?:client|tsClient)\.(get|post|put|patch|delete)', 
                ]
                
                for pattern in api_patterns:
                    api_match = re.search(pattern, line)
                    if api_match:
                        method = api_match.group(1).upper()
                        url = self._extract_url(line, lines, i-1)
                        if url:
                            calls.append(FrontendCall(
                                file=file_path.name,
                                function_name=current_function or "unknown",
                                method=method,
                                url_pattern=url,
                                line_number=i,
                                raw_code=line.strip()
                            ))
                            found_lines.add(i)
                        break
            
            # Fallback patterns - COMPLETE from original
            if ('client' in line or 'tsClient' in line) and i not in found_lines:
                fallback_patterns = [
                    r'(client|tsClient)\.(\w+)',  
                    r'(client|tsClient)\s*\[\s*["\'](\w+)["\']\s*\]',  
                ]
                
                for pattern in fallback_patterns:
                    fallback_match = re.search(pattern, line)
                    if fallback_match:
                        method_name = fallback_match.group(2)
                        if method_name.lower() in ['get', 'post', 'put', 'patch', 'delete']:
                            method = method_name.upper()
                            url = self._extract_url_aggressive(line, lines, i-1)
                            if url:
                                calls.append(FrontendCall(
                                    file=file_path.name,
                                    function_name=current_function or "unknown",
                                    method=method,
                                    url_pattern=url,
                                    line_number=i,
                                    raw_code=line.strip()
                                ))
                                found_lines.add(i)
                            break
        
        return calls
    
    def _extract_url(self, line: str, all_lines: List[str], line_idx: int) -> str:
        # COMPLETE URL extraction from original
        if 'blob' in line.lower() or 'responseType:' in line:
            return ""
        
        # URL patterns - COMPLETE from original
        patterns = [
            r'[`"](\$\{[^}]+\}[^`"]*)[`"]',  # Template strings
            r'[`"\']([/\w\-{}$\.]+[^`"\']*)[`"\']',  # Regular strings
            r'url\s*[=:]\s*[`"\'](.*?)[`"\']',  # url = "..." or url: "..."
            r'endpoint\s*[=:]\s*[`"\'](.*?)[`"\']',  # endpoint = "..."
            r'[`"\'](/api/[^`"\']*)[`"\']',  # Any /api/ path
            r'[`"\'](\$\{V2_WORKFLOW_URL\}[^`"\']*)[`"\']',  # Workflow URLs
            r'formData\.append\([^,]+,\s*[`"\'](.*?)[`"\']',  # FormData URLs
            r'path\s*[=:]\s*[`"\'](.*?)[`"\']',  # path = "..."
            r'route\s*[=:]\s*[`"\'](.*?)[`"\']',  # route = "..."
        ]
        
        # Search current line and next lines 
        for i in range(line_idx, min(line_idx + 30, len(all_lines))):
            current_line = all_lines[i]
            
            # Skip comments and empty lines
            if current_line.strip().startswith('//') or not current_line.strip():
                continue
                
            for pattern in patterns:
                match = re.search(pattern, current_line)
                if match:
                    url = match.group(1)
                    if url and (url.startswith('/') or '${' in url or 'api' in url or 'workflow' in url.lower()):
                        normalized = self._normalize_url(url)
                        if normalized and len(normalized) > 3:
                            return normalized
        
        # Variable detection - COMPLETE from original
        var_patterns = [
            r'(?:client|tsClient)\.\w+(?:<[^>]*>)?\s*\(\s*(\w+)',
            r'(?:client|tsClient)\.\w+\s*\(\s*(\w+)',
            r'(?:client|tsClient)\.\w+\s*\(\s*`([^`]+)`',
            r'(?:client|tsClient)\.\w+\s*\(\s*"([^"]+)"',
            r'(?:client|tsClient)\.\w+\s*\(\s*\'([^\']+)\'',
        ]
        
        for pattern in var_patterns:
            var_match = re.search(pattern, line)
            if var_match:
                var_name = var_match.group(1)
                excluded = ['data', 'body', 'payload', 'params', 'formData', 'config', 'options', 'headers', 'rest', 'args']
                if var_name not in excluded:
                    for j in range(max(0, line_idx - 80), line_idx):
                        search_line = all_lines[j]
                        var_def_patterns = [
                            f'(?:const|let|var)\\s+{var_name}\\s*=\\s*[`"\'](.*?)[`"\']',
                            f'{var_name}\\s*=\\s*[`"\'](.*?)[`"\']',
                            f'\\b{var_name}\\s*=\\s*`([^`]+)`',
                            f'\\b{var_name}\\s*:\\s*[`"\'](.*?)[`"\']', 
                        ]
                        for var_def_pattern in var_def_patterns:
                            var_def = re.search(var_def_pattern, search_line)
                            if var_def:
                                found_url = self._normalize_url(var_def.group(1))
                                if found_url:
                                    return found_url
                break
        
        return ""
    
    def _extract_url_aggressive(self, line: str, all_lines: List[str], line_idx: int) -> str:
        """Ultra-aggressive URL extraction for edge cases - COMPLETE from original"""
        
        if 'blob' in line.lower() or 'responseType:' in line:
            return ""
        
        # More patterns for edge cases - COMPLETE from original
        aggressive_patterns = [
            r'[`"](\$\{[^}]+\}[^`"]*)[`"]',
            r'[`"\']([/\w\-{}$\.]+[^`"\']*)[`"\']',
            r'[`"\'](\/[^`"\']*)[`"\']',  # Any path starting with /
            r'[`"\']([^`"\']*api[^`"\']*)[`"\']',  # Any string containing 'api'
            r'[`"\']([^`"\']*workflow[^`"\']*)[`"\']',  # Any string containing 'workflow'
            r'[`"\']([^`"\']*\$\{[^}]+\}[^`"\']*)[`"\']',  # Any template string
        ]
        
        # Search wider range - up to 40 lines
        for i in range(line_idx, min(line_idx + 40, len(all_lines))):
            current_line = all_lines[i]
            
            if current_line.strip().startswith('//') or not current_line.strip():
                continue
                
            for pattern in aggressive_patterns:
                match = re.search(pattern, current_line)
                if match:
                    url = match.group(1)
                    if url and len(url) > 2:  
                        normalized = self._normalize_url(url)
                        if normalized and len(normalized) > 3 and ('api' in normalized or normalized.startswith('/')):
                            return normalized
        
        return ""
    
    def _normalize_url(self, url: str) -> str:
        if not url:
            return ""
        
        # Replace template variables - COMPLETE from original
        url = url.replace('${V2_URL}', '/api/v2')
        url = url.replace('${V2_WORKFLOW_URL}', '/api/v2/workflows')
        
        # Handle complex interpolations
        url = re.sub(r'\$\{[\w.]+\.(\w+)\}', r'{\1}', url)
        url = re.sub(r'\$\{(\w+)\}', lambda m: '{' + self._camel_to_snake(m.group(1)) + '}', url)
        
        # Remove query parameters
        url = re.sub(r'\?.*$', '', url)
        
        return url.strip()
    
    @staticmethod
    def _camel_to_snake(name: str) -> str:
        name = re.sub('(.)([A-Z][a-z]+)', r'\1_\2', name)
        return re.sub('([a-z0-9])([A-Z])', r'\1_\2', name).lower()

class CompleteBackendAnalyzer:
    """Complete backend analyzer with deep table analysis"""
    
    def __init__(self, backend_path: str):
        self.routers_path = Path(backend_path) / "api" / "v2" / "routers"
        self.backend_path = Path(backend_path)
        
        # Initialize table analysis components
        self.all_known_tables = collect_all_possible_table_names(str(self.backend_path))
        print(f"Found {len(self.all_known_tables)} known tables")
        
        # Collect all function definitions for deep analysis
        self.all_function_definitions = self._collect_all_function_definitions()
        print(f"Collected {len(self.all_function_definitions)} function definitions")
        
    def _collect_all_function_definitions(self) -> Dict[str, Any]:
        """Collect all function definitions across all Python files"""
        all_function_definitions = {}
        
        for root, _, files in os.walk(str(self.backend_path)):
            if '.venv' in root or '__pycache__' in root:
                continue
            for file in files:
                if file.endswith(".py"):
                    full_path = os.path.join(root, file)
                    try:
                        with open(full_path, "r", encoding="utf-8") as f:
                            source = f.read()
                        tree = ast.parse(source, filename=full_path)
                        
                        # Extract function definitions (including class methods)
                        for node in ast.walk(tree):
                            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                all_function_definitions[node.name] = node
                            elif isinstance(node, ast.ClassDef):
                                # Extract class methods
                                for class_node in node.body:
                                    if isinstance(class_node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                                        method_name = f"{node.name}.{class_node.name}"
                                        all_function_definitions[method_name] = class_node
                    except Exception:
                        continue
        
        return all_function_definitions
        
    def extract_backend_routes(self) -> List[BackendRoute]:
        if not self.routers_path.exists():
            return []
        
        routes = []
        for file_path in self.routers_path.rglob("*.py"):
            if file_path.name != "__init__.py":
                routes.extend(self._parse_file(file_path))
        return routes
    
    def _parse_file(self, file_path: Path) -> List[BackendRoute]:
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                source = f.read()
            
            # Parse with COMPLETE AST analyzer for table analysis
            tree = ast.parse(source, filename=str(file_path))
            table_analyzer = CompleteTableAnalyzer(
                all_known_tables=self.all_known_tables,
                all_function_definitions=self.all_function_definitions
            )
            table_analyzer.visit(tree)
            
        except Exception as e:
            print(f"Error parsing {file_path}: {e}")
            return []
        
        routes = []
        rel_path = file_path.relative_to(self.routers_path)
        base_prefix = self._get_prefix(rel_path)
        
        # Parse route decorators
        lines = source.split('\n')
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            if line.startswith('@router.'):
                decorator_lines = [line]
                j = i + 1
                while j < len(lines) and ')' not in ''.join(decorator_lines):
                    decorator_lines.append(lines[j].strip())
                    j += 1
                
                full_decorator = ' '.join(decorator_lines)
                route_match = re.search(r'@router\.(get|post|put|patch|delete)\s*\(\s*["\']([^"\']*)["\']', full_decorator, re.IGNORECASE)
                
                if route_match:
                    method = route_match.group(1).upper()
                    route = route_match.group(2)
                    func_name = self._get_function_name(lines, j)
                    full_route = base_prefix + route if route else base_prefix
                    
                    # Get tables for this function with DEEP ANALYSIS
                    all_tables = set(table_analyzer.table_calls.get(func_name, set()))
                    
                    # Reset analyzed functions for each route to ensure complete analysis
                    table_analyzer.analyzed_functions = set()
                    
                    # Analyze each called function deeply
                    for called_func in table_analyzer.call_graph.get(func_name, []):
                        # Add tables from direct calls
                        all_tables.update(table_analyzer.table_calls.get(called_func, []))
                        
                        # Perform deep recursive analysis
                        deep_tables = table_analyzer.analyze_called_function(called_func)
                        all_tables.update(deep_tables)
                    
                    tables = list(all_tables)
                    
                    routes.append(BackendRoute(
                        file=str(rel_path),
                        method=method,
                        route_pattern=full_route,
                        line_number=i + 1,
                        function_name=func_name,
                        tags=[],
                        raw_code=full_decorator[:100],
                        tables=tables
                    ))
                
                i = j
            else:
                i += 1
        
        return routes
    
    def _get_prefix(self, rel_path: Path) -> str:
        # COMPLETE prefix mapping from original
        parts = rel_path.parts[:-1]
        filename = rel_path.stem
        prefix = "/api/v2"
        
        # Add directory prefixes
        for part in ["workflows", "admin", "manager", "support", "sdp"]:
            if part in parts:
                prefix += f"/{part}"
        
        # Add specific file mappings - COMPLETE from original
        file_routes = {
            # Workflows
            "signoff": "/sign_off", "actions": "/actions", "notifications": "/notifications",
            "downloads": "/downloads", "evidence_uploads": "/evidence_uploads", 
            "lookups": "/lookups", "macd": "/macd",
            # Admin
            "unverified": "/bookings/unverified", "verified": "/bookings/verified",
            "revenue": "/revenue", "contracts": "/contracts",
            "tasks": "/tasks", "subtasks": "/subtasks", "deliverables": "/deliverables",
            # Manager  
            "bookings": "/bookings", "scv": "/scv", "super_customers": "/scv",
            "users": "/users", "pool": "/pool_manager",
            # Support
            "user": "/cases", "agent": "/agent",
            # SDP
            "completions": "/completions", "time_tracking": "/time_tracking",
            # Top-level
            "engagements": "/engagements", "tags": "/tags", "tagsets": "/tagsets",
            "stakeholders": "/stakeholders", "canvas": "/canvas", "links": "/links",
            "thought_spot": "/thought_spot", "thought_spot_tag": "/thought_spot_tag",
            "dc_types": "/dc_types", "user_defined_types": "/udt", 
            "documentation": "/documentation", "announcements": "/announcements",
            "file_management": "/file_management", "static": "/static"
        }
        
        for key, route in file_routes.items():
            if key in filename:
                prefix += route
                break
        
        # Handle edge cases - COMPLETE from original
        if "financial" in str(rel_path) and "/financial" not in prefix:
            prefix += "/financial"
        if filename == "tagsets":
            prefix = "/api/v2/tagsets"
        if filename == "thought_spot_tag":
            return "/api/v2/thought_spot_tag"
        if filename == "user_defined_types":
            return "/api/v2/udt"
        
        return prefix
    
    def _get_function_name(self, lines: List[str], start_idx: int) -> str:
        for i in range(start_idx, min(start_idx + 5, len(lines))):
            if i < len(lines) and not lines[i].strip().startswith('@'):
                func_match = re.search(r'def\s+(\w+)', lines[i])
                if func_match:
                    return func_match.group(1)
        return "unknown"

class APIMapper:
    def __init__(self, frontend_calls: List[FrontendCall], backend_routes: List[BackendRoute]):
        self.frontend_calls = frontend_calls
        self.backend_routes = backend_routes
    
    def create_mappings(self) -> List[Mapping]:
        mappings = []
        for frontend_call in self.frontend_calls:
            backend_route = self._find_match(frontend_call)
            mappings.append(Mapping(frontend=frontend_call, backend=backend_route))
        return mappings
    
    def _find_match(self, frontend_call: FrontendCall) -> Optional[BackendRoute]:
        # Exact match first
        for backend_route in self.backend_routes:
            if self._routes_match(frontend_call, backend_route):
                return backend_route
        
        # Fuzzy match
        best_match = None
        best_score = 0.6
        
        for backend_route in self.backend_routes:
            if backend_route.method == frontend_call.method:
                score = self._similarity(frontend_call.url_pattern, backend_route.route_pattern)
                if score > best_score:
                    best_score = score
                    best_match = backend_route
        
        return best_match
    
    def _routes_match(self, frontend: FrontendCall, backend: BackendRoute) -> bool:
        if frontend.method != backend.method:
            return False
        
        fe_url = frontend.url_pattern.replace('/api/v2', '').strip('/')
        be_url = backend.route_pattern.replace('/api/v2', '').strip('/')
        
        if fe_url == be_url:
            return True
        
        fe_parts = fe_url.split('/') if fe_url else []
        be_parts = be_url.split('/') if be_url else []
        
        if len(fe_parts) != len(be_parts):
            return False
        
        for fe_part, be_part in zip(fe_parts, be_parts):
            if (fe_part.startswith('{') and be_part.startswith('{')) or fe_part == be_part:
                continue
            else:
                return False
        return True
    
    def _similarity(self, str1: str, str2: str) -> float:
        parts1 = set(str1.split('/'))
        parts2 = set(str2.split('/'))
        if not parts1 or not parts2:
            return 0.0
        intersection = parts1.intersection(parts2)
        union = parts1.union(parts2)
        return len(intersection) / len(union)

def generate_reports(mappings: List[Mapping], output_base: str, formats: List[str]):
    if "json" in formats:
        data = []
        for m in mappings:
            data.append({
                "frontend": {
                    "file": m.frontend.file,
                    "function": m.frontend.function_name,
                    "method": m.frontend.method,
                    "url": m.frontend.url_pattern,
                    "line": m.frontend.line_number
                },
                "backend": {
                    "file": m.backend.file if m.backend else None,
                    "function": m.backend.function_name if m.backend else None,
                    "method": m.backend.method if m.backend else None,
                    "route": m.backend.route_pattern if m.backend else None,
                    "line": m.backend.line_number if m.backend else None,
                    "tables": m.backend.tables if m.backend else []
                } if m.backend else None
            })
        
        with open(f"{output_base}.json", 'w') as f:
            json.dump(data, f, indent=2)
    
    if "csv" in formats:
        import csv
        with open(f"{output_base}.csv", 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([
                "Frontend File", "Frontend Function", "HTTP Method", "Frontend URL", 
                "Backend File", "Backend Function", "Backend Route", "Tables"
            ])
            for m in mappings:
                # Join tables with comma, or empty string if no backend match
                tables_str = ",".join(m.backend.tables) if m.backend and m.backend.tables else ""
                
                writer.writerow([
                    m.frontend.file, m.frontend.function_name, m.frontend.method, m.frontend.url_pattern,
                    m.backend.file if m.backend else "", 
                    m.backend.function_name if m.backend else "", 
                    m.backend.route_pattern if m.backend else "",
                    tables_str
                ])

def print_summary(mappings: List[Mapping]):
    total = len(mappings)
    matched = sum(1 for m in mappings if m.backend)
    unmatched = total - matched
    with_tables = sum(1 for m in mappings if m.backend and m.backend.tables)
    
    print("\nAPI MAPPING SUMMARY")
    print("=" * 50)
    print(f"Total Frontend Calls: {total}")
    print(f"Matched:              {matched} ({matched/total*100:.1f}%)")
    print(f"Unmatched:            {unmatched} ({unmatched/total*100:.1f}%)")
    print(f"With Tables:          {with_tables} ({with_tables/total*100:.1f}%)")
    
    # Show some examples of table mappings
    print("\nSample Table Mappings:")
    print("-" * 30)
    count = 0
    for m in mappings:
        if m.backend and m.backend.tables and count < 5:
            tables_str = ", ".join(m.backend.tables[:3])  # Show first 3 tables
            if len(m.backend.tables) > 3:
                tables_str += f" (+{len(m.backend.tables)-3} more)"
            print(f"  {m.backend.route_pattern} -> {tables_str}")
            count += 1
    
    if count == 0:
        print("  No table mappings found")

def main():
    parser = argparse.ArgumentParser(description="Complete frontend-backend API mapping with deep table analysis")
    parser.add_argument("--frontend", default="guided-workflow", help="Frontend project path")
    parser.add_argument("--backend", default="guided-workflow-backend", help="Backend project path")
    parser.add_argument("--output", default="complete_api_mapping_with_tables", help="Output file base name")
    parser.add_argument("--format", choices=["json", "csv", "all"], default="all", help="Output format")
    
    args = parser.parse_args()
    
    print("Complete Frontend-Backend API Mapping Tool with Deep Table Analysis")
    print("=" * 70)
    
    # Analyze frontend with COMPLETE analyzer
    print("\n1. Analyzing frontend with complete patterns...")
    frontend_analyzer = CompleteFrontendAnalyzer(args.frontend)
    frontend_calls = frontend_analyzer.extract_frontend_calls()
    print(f"   Found {len(frontend_calls)} frontend API calls")
    
    # Analyze backend with COMPLETE analyzer
    print("\n2. Analyzing backend with deep table analysis...")
    backend_analyzer = CompleteBackendAnalyzer(args.backend)
    backend_routes = backend_analyzer.extract_backend_routes()
    print(f"   Found {len(backend_routes)} backend routes")
    
    # Show table analysis summary
    routes_with_tables = sum(1 for route in backend_routes if route.tables)
    print(f"   Routes with tables: {routes_with_tables}")
    
    # Create mappings
    print("\n3. Creating mappings...")
    mapper = APIMapper(frontend_calls, backend_routes)
    mappings = mapper.create_mappings()
    
    # Generate reports
    print("\n4. Generating reports...")
    formats = ["json", "csv"] if args.format == "all" else [args.format]
    generate_reports(mappings, args.output, formats)
    
    for fmt in formats:
        print(f"   Generated: {args.output}.{fmt}")
    
    # Print summary
    print_summary(mappings)
    
    print("\nDone! 🎉")
    print("\nThis complete version includes:")
    print("✅ All frontend API call patterns from frontend_backend_api_mapping.py")
    print("✅ Deep table analysis with function call tracing from merged_route_analyzer_with_table_data.py")
    print("✅ Complete route prefix mapping")
    print("✅ Uppercase table names")
    print("✅ Comprehensive model-to-table mapping")

if __name__ == "__main__":
    main()