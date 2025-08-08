Troubleshooting
===============

This guide helps you diagnose and resolve common issues with OmniEmbodied. Issues are organized by category with detailed solutions and prevention tips.

Installation Issues
-------------------

ImportError: No module named 'OmniSimulator'
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- Python can't find the OmniSimulator module
- Import statements fail

**Causes:**
- OmniSimulator package not installed correctly
- Python path issues
- Virtual environment problems

**Solutions:**

1. **Reinstall OmniSimulator:**

   .. code-block:: bash

      cd OmniEmbodied/OmniSimulator
      pip install -e .

2. **Check Python path:**

   .. code-block:: python

      import sys
      print(sys.path)
      # Ensure OmniEmbodied directory is in the path

3. **Verify virtual environment:**

   .. code-block:: bash

      which python
      pip list | grep -i omnisimulator

Permission Denied Errors
^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- Can't write to directories
- Installation fails with permission errors

**Solutions:**

1. **Use virtual environment (recommended):**

   .. code-block:: bash

      python -m venv omniembodied-env
      source omniembodied-env/bin/activate
      pip install -e .

2. **Install for current user only:**

   .. code-block:: bash

      pip install --user -e .

3. **Check directory permissions:**

   .. code-block:: bash

      ls -la
      # Ensure you have write permissions

YAML Configuration Errors
^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- "yaml.scanner.ScannerError" messages
- Configuration not loading

**Solutions:**

1. **Validate YAML syntax:**

   .. code-block:: bash

      python -c "import yaml; yaml.safe_load(open('config.yaml'))"

2. **Check indentation (use spaces, not tabs):**

   .. code-block:: yaml

      # Correct
      dataset:
        default: "eval_single"
      
      # Incorrect (mixed tabs/spaces)
      dataset:
      	default: "eval_single"

3. **Escape special characters:**

   .. code-block:: yaml

      # For strings with special characters
      message: "Task: \"find the key\""

Runtime Errors
---------------

Simulation Hangs or Times Out
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- Simulation appears stuck
- No progress for extended periods
- Timeout errors

**Diagnostic Steps:**

1. **Enable debug logging:**

   .. code-block:: python

      import logging
      logging.basicConfig(level=logging.DEBUG)

2. **Check LLM connectivity:**

   .. code-block:: bash

      curl -I https://api.openai.com/v1/models
      # Or test your LLM endpoint

3. **Monitor system resources:**

   .. code-block:: bash

      top        # Linux/Mac
      htop       # Enhanced version
      # Check CPU, memory usage

**Solutions:**

1. **Set reasonable timeouts:**

   .. code-block:: yaml

      execution:
        max_steps_per_task: 35
        timeout_seconds: 300

2. **Check API rate limits:**

   .. code-block:: yaml

      llm_config:
        timeout: 30
        max_retries: 3

3. **Use faster models for testing:**

   .. code-block:: yaml

      llm_config:
        model_name: "gpt-3.5-turbo"  # Faster than GPT-4

Invalid Action Errors
^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- Agent attempts impossible actions
- Action validation failures
- "Action not allowed" messages

**Diagnostic Steps:**

1. **Check action logs:**

   .. code-block:: bash

      grep -i "action" simulation.log

2. **Verify environment state:**

   .. code-block:: python

      # Add debug prints in your agent
      print(f"Current room: {agent.current_room}")
      print(f"Available objects: {environment.get_objects()}")

**Solutions:**

1. **Improve agent prompting:**

   .. code-block:: yaml

      agent_config:
        environment_description:
          detail_level: 'full'
          show_object_properties: true

2. **Add action validation:**

   .. code-block:: python

      # In custom agent code
      if not self.can_execute_action(action, target):
          return self.fallback_action()

3. **Enable step-by-step verification:**

   .. code-block:: yaml

      task_verification:
        enabled: true
        mode: "step_by_step"

LLM API Issues
--------------

Authentication Errors
^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- "Invalid API key" errors
- "Authentication failed" messages
- HTTP 401 responses

**Solutions:**

1. **Verify API key:**

   .. code-block:: bash

      echo $OPENAI_API_KEY
      # Should show your actual API key

2. **Test API access:**

   .. code-block:: bash

      curl -H "Authorization: Bearer $OPENAI_API_KEY" \
           https://api.openai.com/v1/models

3. **Check key permissions:**
   - Ensure API key has required permissions
   - Check account billing status
   - Verify key hasn't expired

Rate Limit Errors
^^^^^^^^^^^^^^^^^^

**Symptoms:**
- "Rate limit exceeded" messages
- HTTP 429 responses
- Slow or failed requests

**Solutions:**

1. **Reduce request frequency:**

   .. code-block:: yaml

      parallel_evaluation:
        scenario_parallelism:
          max_parallel_scenarios: 2  # Reduce from default

2. **Add request delays:**

   .. code-block:: python

      import time
      time.sleep(1)  # Add delay between requests

3. **Upgrade API plan:**
   - Consider higher tier for increased limits
   - Monitor usage in API provider dashboard

Model Not Found Errors
^^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- "Model not found" errors
- Invalid model name responses

**Solutions:**

1. **Check available models:**

   .. code-block:: bash

      curl -H "Authorization: Bearer $OPENAI_API_KEY" \
           https://api.openai.com/v1/models

2. **Use correct model names:**

   .. code-block:: yaml

      llm_config:
        model_name: "gpt-4-turbo-preview"  # Check exact name

3. **Verify model access:**
   - Some models require special access
   - Check account eligibility

Performance Issues
------------------

Slow Simulation Speed
^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- Simulations take much longer than expected
- High CPU or memory usage
- System becomes unresponsive

**Diagnostic Tools:**

1. **Profile execution:**

   .. code-block:: python

      import cProfile
      pr = cProfile.Profile()
      pr.enable()
      # Run simulation
      pr.disable()
      pr.print_stats()

2. **Monitor resources:**

   .. code-block:: bash

      # Memory usage
      ps aux | grep python
      
      # Disk I/O
      iotop
      
      # Network activity
      netstat -i

**Solutions:**

1. **Optimize configuration:**

   .. code-block:: yaml

      agent_config:
        max_history: 10  # Reduce from default 20
      
      execution:
        max_steps_per_task: 25  # Reduce if appropriate

2. **Use parallel processing wisely:**

   .. code-block:: yaml

      parallel_evaluation:
        scenario_parallelism:
          max_parallel_scenarios: 4  # Based on your CPU cores

3. **Clean up regularly:**

   .. code-block:: bash

      # Remove old logs
      find . -name "*.log" -mtime +7 -delete
      
      # Clear temporary files
      rm -rf /tmp/omniembodied_*

Memory Issues
^^^^^^^^^^^^^

**Symptoms:**
- "Out of memory" errors
- System swapping excessively
- Process killed by OS

**Solutions:**

1. **Reduce memory usage:**

   .. code-block:: yaml

      agent_config:
        max_history: 5  # Smaller history
      
      logging:
        level: "WARNING"  # Less verbose logging

2. **Process scenarios in batches:**

   .. code-block:: python

      # Instead of processing all at once
      scenarios = get_all_scenarios()
      batch_size = 10
      for i in range(0, len(scenarios), batch_size):
          batch = scenarios[i:i+batch_size]
          process_batch(batch)

3. **Monitor memory usage:**

   .. code-block:: python

      import psutil
      process = psutil.Process()
      print(f"Memory usage: {process.memory_info().rss / 1024 / 1024:.2f} MB")

Data and File Issues
--------------------

Missing Dataset Files
^^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- "File not found" errors for scenarios
- Empty evaluation results

**Solutions:**

1. **Verify data directory structure:**

   .. code-block:: bash

      ls -la data/
      # Should contain eval/, sft/, data-all/ directories

2. **Check file paths in configuration:**

   .. code-block:: yaml

      dataset:
        default: "eval_single"  # Must match directory structure

3. **Download missing data:**
   
   .. code-block:: bash

      # If data is in separate repository
      git submodule update --init --recursive

Corrupted JSON Files
^^^^^^^^^^^^^^^^^^^^^

**Symptoms:**
- JSON parsing errors
- "Invalid JSON" messages
- Partial data loading

**Diagnostic Steps:**

1. **Validate JSON files:**

   .. code-block:: bash

      python -m json.tool scenario.json > /dev/null
      echo $?  # Should be 0 for valid JSON

2. **Find corrupted files:**

   .. code-block:: bash

      find data/ -name "*.json" -exec sh -c 'python -m json.tool "$1" > /dev/null || echo "Invalid: $1"' _ {} \;

**Solutions:**

1. **Restore from backup:**

   .. code-block:: bash

      git checkout HEAD -- data/corrupted_file.json

2. **Fix manually:**
   - Use JSON validator to identify issues
   - Common problems: missing commas, unescaped quotes

Logging and Debugging
---------------------

Enable Detailed Logging
^^^^^^^^^^^^^^^^^^^^^^^^

**For general debugging:**

.. code-block:: python

   import logging
   
   # Enable debug for all modules
   logging.basicConfig(
       level=logging.DEBUG,
       format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
   )

**For specific components:**

.. code-block:: python

   # Simulator core
   logging.getLogger("OmniSimulator.core").setLevel(logging.DEBUG)
   
   # Agent decisions
   logging.getLogger("modes.single_agent").setLevel(logging.DEBUG)
   
   # LLM interactions
   logging.getLogger("llm").setLevel(logging.DEBUG)

**In configuration file:**

.. code-block:: yaml

   logging:
     level: "DEBUG"
     show_llm_details: true

Save Debug Information
^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   # Save detailed state
   import json
   
   debug_info = {
       'agent_state': agent.get_state(),
       'environment_state': env.get_state(),
       'action_history': agent.get_history(),
       'error_context': str(exception)
   }
   
   with open('debug_output.json', 'w') as f:
       json.dump(debug_info, f, indent=2)

Getting Help
------------

**Before asking for help, collect:**

1. **System information:**

   .. code-block:: bash

      python --version
      pip list | grep -E "(omni|llm|yaml)"
      uname -a  # Linux/Mac
      # Windows: systeminfo

2. **Error details:**
   - Complete error messages
   - Stack traces
   - Configuration files (remove sensitive data)
   - Steps to reproduce

3. **Log files:**
   - Enable debug logging
   - Include relevant log excerpts
   - Timestamp information

**Where to get help:**

- Check this troubleshooting guide first
- Search existing GitHub issues
- Create new issue with detailed information
- Ask in GitHub Issues for usage questions

**Creating effective bug reports:**

1. **Clear title:** Describe the problem concisely
2. **Environment:** System details, versions
3. **Steps to reproduce:** Exact sequence of actions
4. **Expected vs actual:** What should happen vs what does
5. **Logs and errors:** Relevant error messages
6. **Minimal example:** Simplest case that shows the problem

Common Error Patterns
---------------------

**Pattern: "Attribute 'X' not found"**
- Usually indicates missing configuration
- Check spelling and indentation in YAML
- Verify all required fields are present

**Pattern: "Connection refused" or "Timeout"**
- Network connectivity issues
- API endpoint problems
- Firewall or proxy blocking requests

**Pattern: "Permission denied"**
- File system permissions
- Virtual environment not activated
- Trying to modify read-only files

**Pattern: "Module not found"**
- Installation incomplete
- Python path issues
- Wrong virtual environment

Remember: most issues have been encountered before. Take time to search existing solutions before creating new issues. 