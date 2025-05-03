import importlib.util
import os
import pytest

def test_create_xrsite_runs_without_error():
    # Get the path to the script
    script_path = os.path.join(os.path.dirname(__file__), "create_xrsite_from_vortex.py")
    # Load the module from the file
    spec = importlib.util.spec_from_file_location("create_xrsite_from_vortex", script_path)
    vortex_script = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(vortex_script)
    try:
        vortex_script.main()
    except Exception as e:
        pytest.fail(f"Script raised an exception: {e}") 