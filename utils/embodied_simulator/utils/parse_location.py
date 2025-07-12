def parse_location_id(location_id: str):
    """
    解析location_id，返回(介词, 真实id)
    例如: 'in:bedroom' -> ('in', 'bedroom')
    """
    if isinstance(location_id, str) and ':' in location_id:
        preposition, real_id = location_id.split(':', 1)
        return preposition, real_id
    return None, location_id 