
def improved_routes_match(frontend_call, backend_route):
    """Improved route matching with better parameter handling"""
    if frontend_call.method != backend_route.method:
        return False
    
    fe_url = frontend_call.url_pattern.replace('/api/v2', '').strip('/')
    be_url = backend_route.route_pattern.replace('/api/v2', '').strip('/')
    
    # Exact match
    if fe_url == be_url:
        return True
    
    # Normalize URLs for comparison
    fe_parts = [p for p in fe_url.split('/') if p]
    be_parts = [p for p in be_url.split('/') if p]
    
    # Allow some flexibility in path length
    if abs(len(fe_parts) - len(be_parts)) > 1:
        return False
    
    # Compare parts with parameter flexibility
    min_len = min(len(fe_parts), len(be_parts))
    matches = 0
    
    for i in range(min_len):
        fe_part = fe_parts[i]
        be_part = be_parts[i]
        
        # Both parameters
        if (fe_part.startswith('{') and be_part.startswith('{')):
            matches += 1
        # Exact match
        elif fe_part == be_part:
            matches += 1
        # Case insensitive match
        elif fe_part.lower() == be_part.lower():
            matches += 1
        # Parameter vs literal (acceptable)
        elif fe_part.startswith('{') or be_part.startswith('{'):
            matches += 0.8  # Partial match
    
    # Calculate match ratio
    match_ratio = matches / max(len(fe_parts), len(be_parts))
    return match_ratio >= 0.8  # 80% match threshold
