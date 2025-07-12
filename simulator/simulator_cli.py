#!/usr/bin/env python3
"""
Embodied Simulator CLI - Interactive command-line interface for the simulator

Usage:
    python3 simulator_cli.py

Or with PYTHONPATH:
    PYTHONPATH=/path/to/embodied_simulator python3 simulator_cli.py
"""

import cmd
import sys
import os
import re
from typing import List, Dict, Optional, Tuple
from pathlib import Path

# Add the current directory to the path so we can import the simulator modules
current_dir = os.path.dirname(os.path.abspath(__file__))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

try:
    from .core.engine import SimulationEngine
    from .utils.data_loader import default_data_loader
    from .core.enums import ActionStatus
except ImportError:
    # 如果相对导入失败，尝试绝对导入
    try:
        from simulator.core.engine import SimulationEngine
        from simulator.utils.data_loader import default_data_loader
        from simulator.core.enums import ActionStatus
    except ImportError:
        # 最后尝试从utils.embodied_simulator导入
        from utils.embodied_simulator.core.engine import SimulationEngine
        from utils.embodied_simulator.utils.data_loader import default_data_loader
        from utils.embodied_simulator import ActionStatus

class SimulatorCLI(cmd.Cmd):
    """Interactive CLI for Embodied Simulator"""
    
    intro = """
╔═══════════════════════════════════════════════════════════════╗
║            🤖 Embodied Simulator Interactive CLI 🤖           ║
╠═══════════════════════════════════════════════════════════════╣
║  Type 'help' for commands | Tab for auto-completion          ║
║  Type 'quit' or 'exit' to leave                              ║
╚═══════════════════════════════════════════════════════════════╝
    """
    
    prompt = '🤖 > '
    
    def __init__(self):
        super().__init__()
        self.engine = None
        self.current_scene_id = None
        self.current_agent_id = None
        self.available_scenes = self._get_available_scenes()
        self.last_command_result = None
        
    def _get_available_scenes(self) -> List[str]:
        """Get list of available scene IDs"""
        scene_dir = Path(__file__).parent / "data" / "scene"
        if scene_dir.exists():
            scenes = []
            for file in scene_dir.glob("*_scene.json"):
                scene_id = file.stem.replace("_scene", "")
                scenes.append(scene_id)
            return sorted(scenes)
        return []
    
    def _print_header(self, text: str):
        """Print a formatted header"""
        print(f"\n{'─' * 60}")
        print(f"  {text}")
        print(f"{'─' * 60}")
    
    def _print_success(self, text: str):
        """Print success message in green"""
        print(f"✅ {text}")
    
    def _print_error(self, text: str):
        """Print error message in red"""
        print(f"❌ {text}")
    
    def _print_info(self, text: str):
        """Print info message"""
        print(f"ℹ️  {text}")
    
    def _print_status(self, status: ActionStatus, message: str):
        """Print status with appropriate icon"""
        if status == ActionStatus.SUCCESS:
            self._print_success(message)
        elif status == ActionStatus.FAILURE:
            self._print_error(message)
        else:
            self._print_info(message)
    
    def do_load(self, arg):
        """Load a scene: load <scene_id>
        Example: load 00001"""
        if not arg:
            self._print_error("Please specify a scene ID. Available scenes:")
            for scene in self.available_scenes:
                print(f"  - {scene}")
            return
        
        scene_id = arg.strip()
        
        try:
            # Load scene data
            print(f"Loading scene data for {scene_id}...")
            result = default_data_loader.load_complete_scenario(scene_id)
            if not result:
                self._print_error("Failed to load scene data")
                return

            scene_data, task_data = result
            print(f"Scene data loaded: {len(scene_data.get('rooms', []))} rooms, {len(scene_data.get('objects', []))} objects")
            print(f"Task data loaded: {len(task_data.get('agents_config', []))} agents")

            verify_data = None  # Verify data is optional

            # Try to load verify data if it exists
            try:
                verify_data = default_data_loader.load_verify(scene_id)
                print("Verify data loaded")
            except Exception as e:
                print(f"No verify data: {e}")
                pass  # Verify data is optional

            # Create engine with visualization disabled for CLI
            config = {'visualization': {'enabled': False}}
            abilities = scene_data.get('abilities', [])
            print(f"Creating engine with abilities: {abilities}")
            self.engine = SimulationEngine(config=config, scene_abilities=abilities)

            # Initialize simulator
            data = {'scene': scene_data, 'task': task_data}
            if verify_data:
                data['verify'] = verify_data
            print("Initializing engine with data...")
            success = self.engine.initialize_with_data(data)
            
            if success:
                self.current_scene_id = scene_id
                self._print_success(f"Scene '{scene_id}' loaded successfully!")
                
                # Set first agent as current if available
                agents = list(self.engine.agent_manager.get_all_agents().keys())
                if agents:
                    self.current_agent_id = agents[0]
                    self._print_info(f"Current agent set to: {self.current_agent_id}")
                
                # Show initial state
                self.do_state("")
            else:
                self._print_error("Failed to initialize scene")
                
        except Exception as e:
            self._print_error(f"Error loading scene: {str(e)}")
    
    def complete_load(self, text, line, begidx, endidx):
        """Tab completion for load command"""
        return [s for s in self.available_scenes if s.startswith(text)]
    
    def do_agent(self, arg):
        """Select or list agents: agent [agent_id]
        Example: agent robot_1"""
        if not self.engine:
            self._print_error("No scene loaded. Use 'load <scene_id>' first.")
            return
        
        agents = list(self.engine.agent_manager.get_all_agents().keys())
        
        if not arg:
            # List all agents
            self._print_header("Available Agents")
            for agent_id in agents:
                agent = self.engine.agent_manager.get_agent(agent_id)
                marker = "→" if agent_id == self.current_agent_id else " "
                inventory = f"[carrying: {', '.join(agent.inventory)}]" if agent.inventory else ""
                print(f" {marker} {agent_id}: {agent.name} @ {agent.location_id} {inventory}")
            return
        
        agent_id = arg.strip()
        if agent_id in agents:
            self.current_agent_id = agent_id
            agent = self.engine.agent_manager.get_agent(agent_id)
            self._print_success(f"Switched to agent: {agent_id} ({agent.name})")
            self.do_whereami("")
        else:
            self._print_error(f"Agent '{agent_id}' not found. Available agents: {', '.join(agents)}")
    
    def complete_agent(self, text, line, begidx, endidx):
        """Tab completion for agent command"""
        if not self.engine:
            return []
        agents = list(self.engine.agent_manager.get_all_agents().keys())
        return [a for a in agents if a.startswith(text)]
    
    def do_goto(self, arg):
        """Move agent to location: goto <location>
        Example: goto kitchen"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify a location")
            return
        
        self._execute_command(f"GOTO {arg}")
    
    def complete_goto(self, text, line, begidx, endidx):
        """Tab completion for goto command"""
        if not self.engine:
            return []
        
        # Get all possible locations (rooms and objects)
        locations = []
        
        # Add all room IDs
        for room in self.engine.env_manager.rooms.values():
            locations.append(room.id)

        # Add all object IDs
        for obj in self.engine.env_manager.objects.values():
            locations.append(obj.id)
        
        # Return matching locations
        return [loc for loc in locations if loc.startswith(text)]
    
    def do_grab(self, arg):
        """Grab an object: grab <object>
        Example: grab mug"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify an object")
            return
        
        self._execute_command(f"GRAB {arg}")
    
    def complete_grab(self, text, line, begidx, endidx):
        """Tab completion for grab command"""
        if not self._check_ready(silent=True):
            return []
        
        # Get objects in current agent's room
        agent = self.engine.agent_manager.get_agent(self.current_agent_id)
        room_objects = self.engine.env_manager.get_objects_in_room(agent.location_id)
        
        # Get grabbable objects (not already grabbed)
        grabbable = []
        for obj in room_objects:
            obj_id = obj.get('id') if isinstance(obj, dict) else obj.id
            if obj_id not in agent.inventory:
                grabbable.append(obj_id)
        
        return [obj for obj in grabbable if obj.startswith(text)]
    
    def do_place(self, arg):
        """Place an object: place <object> [on <location>]
        Example: place mug on table"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify what to place")
            return
        
        self._execute_command(f"PLACE {arg}")
    
    def do_open(self, arg):
        """Open an object: open <object>
        Example: open door"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify what to open")
            return
        
        self._execute_command(f"OPEN {arg}")
    
    def do_close(self, arg):
        """Close an object: close <object>
        Example: close door"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify what to close")
            return
        
        self._execute_command(f"CLOSE {arg}")
    
    def do_clean(self, arg):
        """Clean an object: clean <object>
        Example: clean table"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify what to clean")
            return
        
        self._execute_command(f"CLEAN {arg}")
    
    def do_explore(self, arg):
        """Explore current location: explore [thorough]
        Example: explore or explore thorough"""
        if not self._check_ready():
            return
        
        cmd = "EXPLORE"
        if arg.strip().lower() == "thorough":
            cmd = "EXPLORE THOROUGH"
        
        self._execute_command(cmd)
    
    def do_room(self, arg):
        """Show current room description"""
        if not self._check_ready():
            return
        
        agent = self.engine.agent_manager.get_agent(self.current_agent_id)
        room_id = agent.location_id
        
        self._print_header(f"Room Description")
        
        # Get all agents data for the description
        agents_data = {}
        if self.engine.agent_manager:
            for agent_id, ag in self.engine.agent_manager.get_all_agents().items():
                agents_data[agent_id] = {
                    'name': ag.name,
                    'location_id': ag.location_id,
                    'inventory': list(ag.inventory),
                    'abilities': list(ag.abilities),
                    'corporate_mode_object_id': ag.corporate_mode_object_id
                }
        
        # Get room description
        room_desc = self.engine.world_state.describe_room_natural_language(
            room_id,
            agents=agents_data,
            sim_config=self.engine.config
        )
        print(room_desc)
    
    def do_cmd(self, arg):
        """Execute raw command: cmd <command>
        Example: cmd TURN_ON light"""
        if not self._check_ready():
            return
        
        if not arg:
            self._print_error("Please specify a command")
            return
        
        self._execute_command(arg)
    
    def do_state(self, arg):
        """Show current state description"""
        if not self.engine:
            self._print_error("No scene loaded")
            return
        
        self._print_header("Current State")
        
        # Get all agents data
        agents_data = {}
        if self.engine.agent_manager:
            for agent_id, agent in self.engine.agent_manager.get_all_agents().items():
                agents_data[agent_id] = {
                    'name': agent.name,
                    'location_id': agent.location_id,
                    'inventory': list(agent.inventory),
                    'abilities': list(agent.abilities),
                    'corporate_mode_object_id': agent.corporate_mode_object_id
                }
        
        # Get environment description
        state_desc = self.engine.world_state.describe_environment_natural_language(
            agents=agents_data,
            sim_config=self.engine.config
        )
        print(state_desc)
        
        # Show current agent status if selected
        if self.current_agent_id:
            print()
            self.do_whereami("")
    
    def do_whereami(self, arg):
        """Show current agent location and inventory"""
        if not self._check_ready():
            return
        
        agent = self.engine.agent_manager.get_agent(self.current_agent_id)
        
        self._print_header(f"Agent Status: {agent.name}")
        
        # Get agent's natural language description
        agent_data = {
            'name': agent.name,
            'location_id': agent.location_id,
            'inventory': list(agent.inventory),
            'abilities': list(agent.abilities),
            'corporate_mode_object_id': agent.corporate_mode_object_id
        }
        
        agent_desc = self.engine.world_state.describe_agent_natural_language(
            self.current_agent_id,
            agent_data
        )
        print(agent_desc)
        
        # Show nearby objects in a simpler format
        print("\n📦 Quick View - Nearby Objects:")
        room_objects = self.engine.env_manager.get_objects_in_room(agent.location_id)
        if room_objects:
            nearby = []
            for obj in room_objects:
                obj_id = obj.get('id') if isinstance(obj, dict) else obj.id
                if obj_id not in agent.inventory:
                    nearby.append(obj_id)

            if nearby:
                for obj_id in nearby[:10]:
                    obj = self.engine.world_state.graph.get_node(obj_id)
                    if obj:
                        print(f"  - {obj.get('name', obj_id)} ({obj_id})")
                if len(nearby) > 10:
                    print(f"  ... and {len(nearby) - 10} more objects")
    
    def do_actions(self, arg):
        """Show available actions for current agent"""
        if not self._check_ready():
            return
        
        self._print_header("Available Actions")
        
        # Get supported actions description
        desc = self.engine.get_agent_supported_actions_description([self.current_agent_id])
        print(desc)
    
    def do_task(self, arg):
        """Show current task information"""
        if not self.engine:
            self._print_error("No scene loaded")
            return
        
        self._print_header("Task Information")
        
        # Show task information from task_config
        if self.engine.task_config:
            tasks = self.engine.task_config.get('tasks', [])
            if tasks:
                print(f"📋 Total Tasks: {len(tasks)}")
                for i, task in enumerate(tasks):
                    print(f"\n🎯 Task {i+1}:")
                    print(f"  Description: {task.get('task_description', 'N/A')}")
                    print(f"  Category: {task.get('task_category', 'N/A')}")
                    
                    # Show validation checks
                    checks = task.get('validation_checks', [])
                    if checks:
                        print("  ✅ Validation Requirements:")
                        for check in checks:
                            if 'location_id' in check:
                                print(f"    - Object {check.get('id', '')} should be at {check.get('location_id', '')}")
                            elif 'is_on' in check:
                                state = "ON" if check.get('is_on') else "OFF"
                                print(f"    - Device {check.get('id', '')} should be {state}")
                            elif 'holders' in check:
                                holders = check.get('holders', [])
                                print(f"    - Object {check.get('id', '')} should be held by {', '.join(holders)}")
            else:
                print("No tasks defined")
        else:
            print("No task configuration loaded")
        
        # Show verification status if available
        if hasattr(self.engine, 'task_verifier') and self.engine.task_verifier:
            print("\n📊 Verification Status:")
            try:
                # Try to check current verification status
                from typing import Dict, Any
                results = []
                if self.engine.task_config and 'tasks' in self.engine.task_config:
                    for i, task in enumerate(self.engine.task_config['tasks']):
                        is_complete = self.engine.task_verifier.verify_task_completion(i)
                        results.append(f"Task {i+1}: {'✅ Complete' if is_complete else '❌ Incomplete'}")
                
                if results:
                    for result in results:
                        print(f"  {result}")
            except:
                print("  Unable to retrieve verification status")
    
    def do_history(self, arg):
        """Show command history"""
        self._print_header("Command History")
        # Show last 10 commands from readline history
        import readline
        for i in range(max(1, readline.get_current_history_length() - 10), 
                       readline.get_current_history_length() + 1):
            print(f"  {i}: {readline.get_history_item(i)}")
    
    def do_reset(self, arg):
        """Reset the simulator to initial state"""
        if not self.engine:
            self._print_error("No scene loaded")
            return
        
        if self.current_scene_id:
            print("Resetting scene...")
            self.do_load(self.current_scene_id)
    
    def do_clear(self, arg):
        """Clear the screen"""
        os.system('clear' if os.name == 'posix' else 'cls')
        print(self.intro)
    
    def do_help(self, arg):
        """Show help for commands"""
        if arg:
            # Show help for specific command
            super().do_help(arg)
        else:
            # Show categorized help
            self._print_header("Available Commands")
            
            print("\n🎮 Scene Management:")
            print("  load <scene_id>  - Load a scene")
            print("  reset            - Reset current scene")
            print("  state (s)        - Show full environment state")
            print("  room             - Show current room details")
            print("  task             - Show task information")
            
            print("\n🤖 Agent Control:")
            print("  agent [id] (a)   - Select/list agents")
            print("  whereami (w)     - Show agent status")
            print("  actions          - Show available actions")
            
            print("\n🎯 Basic Actions:")
            print("  goto <loc> (g)   - Move to location")
            print("  grab <obj> (gr)  - Pick up object")
            print("  place <obj> (p)  - Put down object")
            print("  explore          - Explore current area")
            
            print("\n🔧 Object Actions:")
            print("  open <object>    - Open something")
            print("  close <object>   - Close something")
            print("  clean <object>   - Clean something")
            
            print("\n⚙️  Utility:")
            print("  cmd <command>    - Execute raw command")
            print("  history          - Show command history")
            print("  clear            - Clear screen")
            print("  help [command]   - Show help")
            print("  quit/exit        - Exit CLI")
            
            print("\n💡 Tip: Shortcuts in parentheses (e.g., 'g' for 'goto')")
    
    def do_quit(self, arg):
        """Exit the CLI"""
        print("\n👋 Goodbye!")
        return True
    
    def do_exit(self, arg):
        """Exit the CLI"""
        return self.do_quit(arg)
    
    def do_EOF(self, arg):
        """Handle Ctrl+D"""
        print()  # New line after ^D
        return self.do_quit(arg)
    
    # Shortcuts
    def do_g(self, arg):
        """Shortcut for goto"""
        return self.do_goto(arg)
    
    def do_gr(self, arg):
        """Shortcut for grab"""
        return self.do_grab(arg)
    
    def do_p(self, arg):
        """Shortcut for place"""
        return self.do_place(arg)
    
    def do_s(self, arg):
        """Shortcut for state"""
        return self.do_state(arg)
    
    def do_w(self, arg):
        """Shortcut for whereami"""
        return self.do_whereami(arg)
    
    def do_a(self, arg):
        """Shortcut for agent"""
        return self.do_agent(arg)
    
    def complete_g(self, text, line, begidx, endidx):
        """Tab completion for goto shortcut"""
        return self.complete_goto(text, line, begidx, endidx)
    
    def complete_a(self, text, line, begidx, endidx):
        """Tab completion for agent shortcut"""
        return self.complete_agent(text, line, begidx, endidx)
    
    def _check_ready(self, silent: bool = False) -> bool:
        """Check if engine and agent are ready"""
        if not self.engine:
            if not silent:
                self._print_error("No scene loaded. Use 'load <scene_id>' first.")
            return False
        
        if not self.current_agent_id:
            if not silent:
                self._print_error("No agent selected. Use 'agent <agent_id>' first.")
            return False
        
        return True
    
    def _execute_command(self, command: str):
        """Execute a command through the engine"""
        print(f"🎯 Executing: {command}")
        
        try:
            status, message, result = self.engine.action_handler.process_command(
                self.current_agent_id, command
            )
            
            self._print_status(status, message)
            
            # Store result for potential future use
            self.last_command_result = (status, message, result)
            
            # Show task completion if applicable
            if result and 'task_completed' in result:
                if result['task_completed']:
                    self._print_success("🎉 Task completed!")
            
            # Show explore results if it was an explore command
            if command.startswith("EXPLORE") and status == ActionStatus.SUCCESS and result:
                if 'room_description' in result:
                    print("\n📋 Room Description:")
                    print(result['room_description'])
                if 'object_descriptions' in result:
                    print("\n📦 Objects Found:")
                    for obj_desc in result['object_descriptions']:
                        print(f"  - {obj_desc}")
        
        except Exception as e:
            self._print_error(f"Command execution failed: {str(e)}")
    
    def emptyline(self):
        """Do nothing on empty line"""
        pass
    
    def default(self, line):
        """Handle unknown commands"""
        self._print_error(f"Unknown command: '{line}'. Type 'help' for available commands.")


def main():
    """Main entry point"""
    try:
        # Enable readline for better input handling
        import readline
        readline.set_completer_delims(' \t\n')
        
        # Start CLI
        cli = SimulatorCLI()
        cli.cmdloop()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()