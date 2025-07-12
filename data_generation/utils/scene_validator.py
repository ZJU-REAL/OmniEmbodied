import json
import re
import os
import csv
from typing import List, Dict, Any, Tuple, Optional, Set

class SceneValidator:
    """场景JSON验证器"""
    
    def __init__(self, csv_path: str = None):
        self.errors = []
        self.warnings = []
        self.csv_attributes = set()  # 存储CSV中定义的所有属性
        
        # 加载CSV属性
        if csv_path:
            self._load_csv_attributes(csv_path)
        else:
            # 默认CSV路径 - 使用相对路径
            from pathlib import Path
            default_csv_path = Path(__file__).parent.parent / 'data' / 'attribute_actions.csv'
            if default_csv_path.exists():
                self._load_csv_attributes(str(default_csv_path))
    
    def _load_csv_attributes(self, csv_path: str):
        """从CSV文件加载属性定义"""
        try:
            with open(csv_path, 'r', encoding='utf-8') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    attribute = row.get('attribute', '').strip()
                    if attribute:
                        self.csv_attributes.add(attribute)
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Loaded {len(self.csv_attributes)} CSV attribute definitions")
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to load CSV attributes: {e}")
            self.csv_attributes = set()
    
    def validate_scene_json_detailed(self, scene_data: Dict[Any, Any]) -> List[str]:
        """详细验证场景JSON的结构和内容"""
        self.errors = []
        
        try:
            # 1. Check top-level structure
            if not isinstance(scene_data, dict):
                self.errors.append("Top-level structure must be an object, not array or other types")
                return self.errors
            
            # Check required top-level fields
            required_top_fields = ['description', 'rooms', 'objects']
            for field in required_top_fields:
                if field not in scene_data:
                    self.errors.append(f"Missing required '{field}' field")

            # Check optional abilities field (auto-generated)
            if 'abilities' in scene_data:
                if not isinstance(scene_data['abilities'], list):
                    self.errors.append("'abilities' field must be an array")
                else:
                    # Validate that all abilities are strings
                    for i, ability in enumerate(scene_data['abilities']):
                        if not isinstance(ability, str):
                            self.errors.append(f"abilities[{i}] must be a string")
            
            # Check description field type
            if 'description' in scene_data and not isinstance(scene_data['description'], str):
                self.errors.append("'description' field must be a string")
            
            if not isinstance(scene_data.get('rooms', []), list):
                self.errors.append("'rooms' field must be an array")
            if not isinstance(scene_data.get('objects', []), list):
                self.errors.append("'objects' field must be an array")
            
            # 2. Validate rooms
            rooms = scene_data.get('rooms', [])
            room_ids = set()
            
            for i, room in enumerate(rooms):
                if not isinstance(room, dict):
                    self.errors.append(f"rooms[{i}] must be an object")
                    continue
                
                # Check required fields
                required_fields = ['id', 'name', 'properties', 'connected_to_room_ids']
                for field in required_fields:
                    if field not in room:
                        self.errors.append(f"rooms[{i}] missing required field '{field}'")
                
                # Check id format
                room_id = room.get('id', '')
                if not re.match(r'^[a-z][a-z0-9_]*$', room_id):
                    self.errors.append(f"rooms[{i}].id '{room_id}' must use lowercase_snake_case format")
                
                if room_id in room_ids:
                    self.errors.append(f"rooms[{i}].id '{room_id}' is duplicated")
                else:
                    room_ids.add(room_id)
                
                # Check properties
                if 'properties' in room and not isinstance(room['properties'], dict):
                    self.errors.append(f"rooms[{i}].properties must be an object")
                elif 'properties' in room and 'type' not in room['properties']:
                    self.errors.append(f"rooms[{i}].properties missing required 'type' field")
                
                # Check connected_to_room_ids
                if 'connected_to_room_ids' in room and not isinstance(room['connected_to_room_ids'], list):
                    self.errors.append(f"rooms[{i}].connected_to_room_ids must be an array")
            
            # 3. Validate objects
            objects = scene_data.get('objects', [])
            object_ids = set()
            
            for i, obj in enumerate(objects):
                if not isinstance(obj, dict):
                    self.errors.append(f"objects[{i}] must be an object")
                    continue
                
                # Check required fields
                required_fields = ['id', 'name', 'type', 'location_id', 'properties']
                for field in required_fields:
                    if field not in obj:
                        self.errors.append(f"objects[{i}] missing required field '{field}'")
                
                # Check id format
                obj_id = obj.get('id', '')
                if not re.match(r'^[a-z][a-z0-9_]*_\d+$', obj_id):
                    self.errors.append(f"objects[{i}].id '{obj_id}' must use lowercase_snake_case_number format")
                
                if obj_id in object_ids:
                    self.errors.append(f"objects[{i}].id '{obj_id}' is duplicated")
                else:
                    object_ids.add(obj_id)
                
                # Check type
                obj_type = obj.get('type', '')
                if obj_type not in ['FURNITURE', 'ITEM']:
                    self.errors.append(f"objects[{i}].type '{obj_type}' must be 'FURNITURE' or 'ITEM'")
                
                # Check properties
                properties = obj.get('properties', {})
                if not isinstance(properties, dict):
                    self.errors.append(f"objects[{i}].properties must be an object")
                    continue
                
                # Check that states is not inside properties
                if 'states' in properties:
                    self.errors.append(f"objects[{i}].properties should not contain 'states' field - states should be at the same level as properties")
                
                # Check that properties values are not objects (except for reserved functional keys)
                reserved_keys = {'weight', 'size', 'is_container', 'provides_abilities'}
                for prop_key, prop_value in properties.items():
                    if prop_key not in reserved_keys and isinstance(prop_value, dict):
                        self.errors.append(f"objects[{i}].properties.{prop_key} should not be an object - properties should contain simple values only")
                
                # Weight validation removed as requested
                
                # Check FURNITURE size
                if obj_type == 'FURNITURE':
                    if 'size' not in properties:
                        self.errors.append(f"objects[{i}].properties missing required 'size' field for FURNITURE")
                    else:
                        size = properties['size']
                        if not isinstance(size, list) or len(size) != 3:
                            self.errors.append(f"objects[{i}].properties.size must be an array of length 3")
                        elif not all(isinstance(x, (int, float)) and x > 0 for x in size):
                            self.errors.append(f"objects[{i}].properties.size all values must be positive numbers")
                
                # Check location_id format
                location_id = obj.get('location_id', '')
                if not (location_id.startswith('on:') or location_id.startswith('in:')):
                    self.errors.append(f"objects[{i}].location_id '{location_id}' has invalid format (must start with 'in:' or 'on:')")
            
            # 4. Validate container logic and object references
            for i, obj in enumerate(objects):
                location_id = obj.get('location_id', '')
                if location_id.startswith('on:') or location_id.startswith('in:'):
                    parent_id = location_id.split(':', 1)[1]
                    
                    # Check if parent_id is a room
                    if parent_id in room_ids:
                        # If it's a room, only 'in:' is valid
                        if location_id.startswith('on:'):
                            self.errors.append(f"objects[{i}].location_id cannot use 'on:' with room '{parent_id}', use 'in:' instead")
                        continue  # Room reference is valid, no further checks needed
                    
                    # Find parent object (not room)
                    parent_obj = None
                    for parent in objects:
                        if parent.get('id') == parent_id:
                            parent_obj = parent
                            break
                    
                    if not parent_obj:
                        self.errors.append(f"objects[{i}].location_id references non-existent object or room '{parent_id}'")
                    else:
                        parent_props = parent_obj.get('properties', {})
                        if not parent_props.get('is_container', False):
                            self.errors.append(f"objects[{i}].location_id references object '{parent_id}' which must have is_container: true")
                        
                        # Check 'in:' references have is_open state
                        if location_id.startswith('in:'):
                            parent_states = parent_obj.get('states', {})
                            if 'is_open' not in parent_states:
                                self.errors.append(f"objects[{i}].location_id references container '{parent_id}' which must have is_open state")
            
            # 5. Check for duplicate IDs across rooms and objects
            all_ids = list(room_ids) + list(object_ids)
            if len(all_ids) != len(set(all_ids)):
                self.errors.append("Duplicate IDs found between rooms and objects")
            
            # 6. Additional validations
            self._validate_english_names(scene_data)
            self._validate_states_consistency(scene_data)
            self._validate_csv_attributes_placement(scene_data)
            
        except Exception as e:
            self.errors.append(f"Exception occurred during validation: {str(e)}")
        
        return self.errors
    
    def _validate_english_names(self, scene_data: Dict[Any, Any]):
        """验证名称是否为英文"""
        # 验证顶级description字段
        description = scene_data.get('description', '')
        if description and not self._is_english_text(description):
            self.errors.append(f"description '{description}' should be in English")
        
        rooms = scene_data.get('rooms', [])
        objects = scene_data.get('objects', [])
        
        for i, room in enumerate(rooms):
            name = room.get('name', '')
            if name and not self._is_english_text(name):
                self.errors.append(f"rooms[{i}].name '{name}' should be in English")
        
        for i, obj in enumerate(objects):
            name = obj.get('name', '')
            if name and not self._is_english_text(name):
                self.errors.append(f"objects[{i}].name '{name}' should be in English")
    
    def _validate_states_consistency(self, scene_data: Dict[Any, Any]):
        """验证状态一致性"""
        objects = scene_data.get('objects', [])
        
        for i, obj in enumerate(objects):
            states = obj.get('states', {})
            properties = obj.get('properties', {})
            
            # Check if states are properly formatted
            if states and not isinstance(states, dict):
                self.errors.append(f"objects[{i}].states must be an object")
            
            # Check boolean states
            for state_key, state_value in states.items():
                if state_key.startswith('is_') and not isinstance(state_value, bool):
                    self.errors.append(f"objects[{i}].states.{state_key} should be a boolean value")
    
    def _validate_csv_attributes_placement(self, scene_data: Dict[Any, Any]):
        """验证CSV属性只能出现在states中"""
        if not self.csv_attributes:
            return  # 如果没有加载CSV属性，跳过验证
        
        objects = scene_data.get('objects', [])
        
        for i, obj in enumerate(objects):
            # 检查properties中是否有CSV属性
            properties = obj.get('properties', {})
            for prop_key in properties.keys():
                if prop_key in self.csv_attributes:
                    self.errors.append(f"objects[{i}].properties.{prop_key} is a CSV-defined attribute and should be in states, not properties")
            
            # 检查对象顶级是否有CSV属性（除了states）
            for obj_key in obj.keys():
                if obj_key not in ['id', 'name', 'type', 'location_id', 'properties', 'states'] and obj_key in self.csv_attributes:
                    self.errors.append(f"objects[{i}].{obj_key} is a CSV-defined attribute and should be in states")
            
            # Check if attributes in states are all valid CSV attributes (optional strict check)
            states = obj.get('states', {})
            for state_key in states.keys():
                if state_key not in self.csv_attributes:
                    # Here we only record warnings, not as errors, because there may be other custom states
                    pass  # Can be enabled as needed: self.warnings.append(f"objects[{i}].states.{state_key} is not defined in CSV")

    def _is_english_text(self, text: str) -> bool:
        """Simple check if text is primarily in English"""
        if not text:
            return True

        # Check if it contains Chinese characters
        chinese_char_count = sum(1 for char in text if '\u4e00' <= char <= '\u9fff')
        total_chars = len([c for c in text if c.isalpha()])

        if total_chars == 0:
            return True

        # If Chinese characters exceed 50% of total letter characters, consider it not English
        return chinese_char_count / total_chars < 0.5

    def _fix_object_id(self, obj_id: str, used_ids: set) -> str:
        """Intelligently fix object ID format"""
        if not obj_id:
            return obj_id
        
        # Convert to lowercase
        obj_id = obj_id.lower()
        
        # Strategy 1: Extract numbers from the end and reformat
        # Examples: vial_a12 -> vial_12, table_b7 -> table_7
        match = re.search(r'([a-z][a-z0-9_]*)([a-z]+)(\d+)$', obj_id)
        if match:
            base_part, letter_part, number_part = match.groups()
            
            # Remove trailing underscore if exists
            base_part = base_part.rstrip('_')
            
            # Try different strategies
            candidates = []
            
            # Strategy 1a: Just use base + number (preferred for simplicity)
            # vial_a12 -> vial_12
            candidates.append(f"{base_part}_{number_part}")
            
            # Strategy 1b: Include letter part as separate component
            # vial_a12 -> vial_a_12 (if we want to preserve the letter)
            if letter_part:
                candidates.append(f"{base_part}_{letter_part}_{number_part}")
            
            # Find the first available candidate
            for candidate in candidates:
                if candidate not in used_ids:
                    return candidate
            
            # If all candidates conflict, increment the number
            base_candidate = candidates[0]  # Use the simplest form
            counter = int(number_part) + 1
            while f"{base_part}_{counter}" in used_ids:
                counter += 1
            return f"{base_part}_{counter}"
        
        # Strategy 2: Handle IDs that don't end with numbers
        # Add _1 suffix if no number at the end
        if not re.search(r'_\d+$', obj_id):
            # Clean up the ID first
            clean_id = re.sub(r'[^a-z0-9_]', '', obj_id)
            clean_id = re.sub(r'_+', '_', clean_id)  # Remove multiple underscores
            clean_id = clean_id.strip('_')  # Remove leading/trailing underscores
            
            if clean_id:
                counter = 1
                while f"{clean_id}_{counter}" in used_ids:
                    counter += 1
                return f"{clean_id}_{counter}"
        
        # Strategy 3: If all else fails, ensure it starts with a letter
        if not re.match(r'^[a-z]', obj_id):
            obj_id = f"object_{obj_id}"
        
        # Ensure it ends with _number
        if not re.search(r'_\d+$', obj_id):
            counter = 1
            base = re.sub(r'_*$', '', obj_id)  # Remove trailing underscores
            while f"{base}_{counter}" in used_ids:
                counter += 1
            return f"{base}_{counter}"
        
        return obj_id
    
    def generate_error_report(self, json_str: str, parse_error: Optional[str], validation_errors: List[str]) -> str:
        """生成详细的错误报告"""
        report_lines = []
        
        report_lines.append("=== JSON Generation Error Report ===")
        report_lines.append("")
        
        # JSON parsing errors
        if parse_error:
            report_lines.append("1. JSON Parsing Error:")
            report_lines.append(f"   - {parse_error}")
            report_lines.append("")
            
            # Analyze common JSON syntax errors
            if "Invalid control character" in str(parse_error):
                report_lines.append("   Possible cause: String contains unescaped control characters")
            elif "Expecting" in str(parse_error):
                report_lines.append("   Possible cause: JSON syntax error, missing comma, bracket or quote")
            elif "Unterminated string" in str(parse_error):
                report_lines.append("   Possible cause: String not properly closed")
            report_lines.append("")
        
        # Structure validation errors
        if validation_errors:
            report_lines.append("2. Structure Validation Errors:")
            for i, error in enumerate(validation_errors, 1):
                report_lines.append(f"   - {error}")
            report_lines.append("")
        
        # Fix suggestions
        report_lines.append("3. Fix Suggestions:")
        report_lines.append("   - Ensure all strings are wrapped in double quotes")
        report_lines.append("   - Check all object and array bracket matching")
        report_lines.append("   - Ensure all field names are wrapped in double quotes")
        report_lines.append("   - Remove comments and extra commas")
        report_lines.append("   - Verify all numeric formats are correct")
        report_lines.append("   - Ensure all IDs use lowercase_snake_case format")
        report_lines.append("   - Verify all object names are in English")
        report_lines.append("")
        
        # Show first few lines of JSON for reference
        if json_str:
            lines = json_str.split('\n')[:10]
            report_lines.append("4. JSON Content (First 10 lines for reference):")
            for i, line in enumerate(lines, 1):
                report_lines.append(f"   {i:2d}: {line}")
            if len(json_str.split('\n')) > 10:
                total_lines = len(json_str.split('\n'))
                report_lines.append(f"   ... (Total {total_lines} lines)")
        
        return '\n'.join(report_lines)
    
    def auto_fix_scene_json(self, scene_data: Dict[Any, Any]) -> Tuple[Dict[Any, Any], List[str]]:
        """自动修复场景JSON的常见问题"""
        fixes_applied = []
        
        # 0. Add missing description field if needed
        if 'description' not in scene_data:
            scene_data['description'] = "Generated scene description"
            fixes_applied.append("Added missing 'description' field")
        
        room_ids = {room.get('id', '') for room in scene_data.get('rooms', [])}
        objects = scene_data.get('objects', [])
        
        # 1. Fix CSV attributes placement (move to states)
        for i, obj in enumerate(objects):
            properties = obj.get('properties', {})
            states = obj.setdefault('states', {})
            
            # Move CSV attributes from properties to states
            csv_attrs_in_properties = []
            for prop_key, prop_value in list(properties.items()):
                if prop_key in self.csv_attributes:
                    csv_attrs_in_properties.append((prop_key, prop_value))
                    properties.pop(prop_key)
            
            for attr_key, attr_value in csv_attrs_in_properties:
                states[attr_key] = attr_value
                fixes_applied.append(f"Moved CSV attribute '{attr_key}' from objects[{i}].properties to objects[{i}].states")
            
            # Move CSV attributes from object top level to states
            csv_attrs_in_obj = []
            for obj_key, obj_value in list(obj.items()):
                if obj_key not in ['id', 'name', 'type', 'location_id', 'properties', 'states'] and obj_key in self.csv_attributes:
                    csv_attrs_in_obj.append((obj_key, obj_value))
                    obj.pop(obj_key)
            
            for attr_key, attr_value in csv_attrs_in_obj:
                states[attr_key] = attr_value
                fixes_applied.append(f"Moved CSV attribute '{attr_key}' from objects[{i}] top level to objects[{i}].states")
        
        # 2. Fix states position (move from properties to object level)
        for i, obj in enumerate(objects):
            properties = obj.get('properties', {})
            if 'states' in properties:
                # Merge states from properties to object level (don't overwrite existing states)
                states_from_properties = properties.pop('states')
                existing_states = obj.setdefault('states', {})
                
                # Merge the two states dictionaries
                for key, value in states_from_properties.items():
                    if key not in existing_states:  # Don't overwrite existing states
                        existing_states[key] = value
                
                fixes_applied.append(f"Moved states from objects[{i}].properties to objects[{i}].states")
        
        # 3. Fix object ID format issues
        used_ids = set()
        for i, obj in enumerate(objects):
            obj_id = obj.get('id', '')
            original_id = obj_id
            
            # Check if ID matches the required format: lowercase_snake_case_number
            if not re.match(r'^[a-z][a-z0-9_]*_\d+$', obj_id):
                # Try to fix the ID intelligently
                fixed_id = self._fix_object_id(obj_id, used_ids)
                if fixed_id != obj_id:
                    obj['id'] = fixed_id
                    used_ids.add(fixed_id)
                    fixes_applied.append(f"Fixed objects[{i}].id: changed '{original_id}' to '{fixed_id}'")
                    
                    # Also update any location_id references to this object
                    for j, other_obj in enumerate(objects):
                        other_location_id = other_obj.get('location_id', '')
                        if other_location_id in [f'on:{original_id}', f'in:{original_id}']:
                            prefix = 'on:' if other_location_id.startswith('on:') else 'in:'
                            other_obj['location_id'] = f'{prefix}{fixed_id}'
                            fixes_applied.append(f"Updated objects[{j}].location_id reference: '{original_id}' -> '{fixed_id}'")
                else:
                    used_ids.add(obj_id)
            else:
                used_ids.add(obj_id)
        
        # 4. Fix incorrect 'on:room_id' references (should be 'in:room_id')
        for i, obj in enumerate(objects):
            location_id = obj.get('location_id', '')
            if location_id.startswith('on:'):
                parent_id = location_id.split(':', 1)[1]
                if parent_id in room_ids:
                    # Fix: change 'on:room_id' to 'in:room_id'
                    obj['location_id'] = f'in:{parent_id}'
                    fixes_applied.append(f"Fixed objects[{i}].location_id: changed 'on:{parent_id}' to 'in:{parent_id}'")
        
        # 5. Add missing is_container and is_open for referenced objects
        # First, collect all object references (after fixing room references)
        referenced_objects = set()
        for obj in objects:
            location_id = obj.get('location_id', '')
            if location_id.startswith('on:') or location_id.startswith('in:'):
                parent_id = location_id.split(':', 1)[1]
                # Check if it's an object reference (not room)
                if parent_id not in room_ids:
                    referenced_objects.add(parent_id)
        
        # Add missing is_container and is_open
        for i, obj in enumerate(objects):
            obj_id = obj.get('id', '')
            if obj_id in referenced_objects:
                properties = obj.setdefault('properties', {})
                states = obj.setdefault('states', {})
                
                # Add is_container if missing
                if not properties.get('is_container', False):
                    properties['is_container'] = True
                    fixes_applied.append(f"Added is_container: true to objects[{i}] ({obj_id})")
                
                # Add is_open if missing (for containers that are referenced with 'in:')
                has_in_reference = any(
                    other_obj.get('location_id', '').startswith(f'in:{obj_id}')
                    for other_obj in objects
                )
                if has_in_reference and 'is_open' not in states:
                    states['is_open'] = False
                    fixes_applied.append(f"Added is_open: false to objects[{i}].states ({obj_id})")
        
        return scene_data, fixes_applied
    
    def validate_and_fix_json_file(self, file_path: str, auto_fix: bool = False) -> Tuple[bool, List[str], Optional[Dict], List[str]]:
        """验证JSON文件并可选择性地自动修复"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Try to parse JSON
            try:
                scene_data = json.loads(content)
                parse_error = None
            except Exception as e:
                return False, [f"JSON parsing failed: {str(e)}"], None, []
            
            fixes_applied = []
            
            # Auto-fix if requested
            if auto_fix:
                scene_data, fixes_applied = self.auto_fix_scene_json(scene_data)
            
            # Validate structure
            validation_errors = self.validate_scene_json_detailed(scene_data)
            
            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors, scene_data, fixes_applied
            
        except FileNotFoundError:
            return False, [f"File not found: {file_path}"], None, []
        except Exception as e:
            return False, [f"Error reading file: {str(e)}"], None, []
    
    def validate_json_file(self, file_path: str) -> Tuple[bool, List[str], Optional[Dict]]:
        """验证JSON文件"""
        is_valid, errors, scene_data, _ = self.validate_and_fix_json_file(file_path, auto_fix=False)
        return is_valid, errors, scene_data
    
    def validate_and_fix_json_data(self, scene_data: Dict[Any, Any], auto_fix: bool = False) -> Tuple[bool, List[str], Optional[Dict], List[str]]:
        """验证JSON数据并可选择性地自动修复（模块化方式，不读取文件）"""
        try:
            fixes_applied = []
            
            # Auto-fix if requested
            if auto_fix:
                scene_data, fixes_applied = self.auto_fix_scene_json(scene_data)
            
            # Validate structure
            validation_errors = self.validate_scene_json_detailed(scene_data)
            
            is_valid = len(validation_errors) == 0
            return is_valid, validation_errors, scene_data, fixes_applied
            
        except Exception as e:
            return False, [f"Error during validation: {str(e)}"], None, []


def main():
    """测试验证器和自动修复功能"""
    validator = SceneValidator()
    test_file = "/Users/wangzixuan/workspace/data_generation/gen_scene/output_json/00002.json"
    
    print(f"Testing scene validator with file: {test_file}")
    print("=" * 60)
    
    # 1. 先验证原始文件
    print("🔍 Step 1: Validating original file...")
    is_valid, errors, scene_data = validator.validate_json_file(test_file)
    
    if is_valid:
        print("✅ JSON validation PASSED")
        print(f"   - Rooms: {len(scene_data.get('rooms', []))}")
        print(f"   - Objects: {len(scene_data.get('objects', []))}")
    else:
        print("❌ JSON validation FAILED")
        print(f"   - Total errors: {len(errors)}")
        print("   - First 5 errors:")
        for i, error in enumerate(errors[:5], 1):
            print(f"     {i}. {error}")
        if len(errors) > 5:
            print(f"     ... and {len(errors) - 5} more errors")
    
    # 2. 测试自动修复
    print("\n🔧 Step 2: Testing auto-fix functionality...")
    is_valid_fixed, errors_fixed, scene_data_fixed, fixes_applied = validator.validate_and_fix_json_file(test_file, auto_fix=True)
    
    if fixes_applied:
        print(f"✅ Applied {len(fixes_applied)} automatic fixes:")
        for i, fix in enumerate(fixes_applied[:10], 1):  # Show first 10 fixes
            print(f"   {i:2d}. {fix}")
        if len(fixes_applied) > 10:
            print(f"     ... and {len(fixes_applied) - 10} more fixes")
    else:
        print("ℹ️  No automatic fixes were needed")
    
    # 3. 验证修复后的结果
    print(f"\n📊 Step 3: Validation results after auto-fix...")
    if is_valid_fixed:
        print("✅ JSON validation PASSED after auto-fix")
        print(f"   - Rooms: {len(scene_data_fixed.get('rooms', []))}")
        print(f"   - Objects: {len(scene_data_fixed.get('objects', []))}")
    else:
        print("❌ JSON validation still has issues after auto-fix")
        print(f"   - Remaining errors: {len(errors_fixed)}")
        print("   - First 5 remaining errors:")
        for i, error in enumerate(errors_fixed[:5], 1):
            print(f"     {i}. {error}")
        if len(errors_fixed) > 5:
            print(f"     ... and {len(errors_fixed) - 5} more errors")
    
    # 4. 保存修复后的文件（可选）
    if fixes_applied and scene_data_fixed:
        fixed_file = test_file.replace('.json', '_fixed.json')
        try:
            with open(fixed_file, 'w', encoding='utf-8') as f:
                json.dump(scene_data_fixed, f, ensure_ascii=False, indent=2)
            print(f"\n💾 Fixed JSON saved to: {fixed_file}")
        except Exception as e:
            print(f"\n❌ Failed to save fixed JSON: {e}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main() 