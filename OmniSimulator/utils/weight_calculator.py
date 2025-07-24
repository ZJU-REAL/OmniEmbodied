def calculate_container_weight(env_manager, container_id):
    """
    Calculate total weight of container including direct children only
    
    Args:
        env_manager: Environment manager
        container_id: Container object ID
        
    Returns:
        float: Total weight (container + direct children)
    """
    # Get container weight
    container = env_manager.get_object_by_id(container_id)
    if not container:
        return 0.0
    
    container_weight = container.get('properties', {}).get('weight', 0.0)
    
    # Add direct children weight
    child_weight = 0.0
    edges = env_manager.world_state.graph.edges.get(container_id, {})
    for child_id, rels in edges.items():
        for rel in rels:
            if rel.get('type') in ('in', 'on'):
                child_obj = env_manager.get_object_by_id(child_id)
                if child_obj:
                    child_weight += child_obj.get('properties', {}).get('weight', 0.0)
    
    return container_weight + child_weight

def has_children(env_manager, container_id):
    """
    Check if container has direct children
    
    Returns:
        bool: True if container has children
    """
    edges = env_manager.world_state.graph.edges.get(container_id, {})
    for child_id, rels in edges.items():
        for rel in rels:
            if rel.get('type') in ('in', 'on'):
                return True
    return False
