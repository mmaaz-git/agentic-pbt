"""Realistic scenario showing how control characters could break devhelp generation"""

import sys
sys.path.insert(0, '/root/hypothesis-llm/envs/sphinxcontrib-mermaid_env/lib/python3.13/site-packages')

import xml.etree.ElementTree as etree
import gzip
import tempfile

def simulate_devhelp_build_with_bad_title():
    """
    Simulate what happens when Sphinx processes documentation with control characters.
    
    This could happen when:
    1. Documentation is auto-generated from code with control characters in docstrings
    2. Documentation is copied from external sources with hidden control characters
    3. Documentation uses special Unicode characters that get mangled
    """
    
    # Realistic scenarios where control characters might appear
    scenarios = [
        {
            'config_title': 'My Project\x08 Documentation',  # Accidental backspace in config
            'project_name': 'MyProject',
            'description': 'Backspace character from bad copy-paste in conf.py'
        },
        {
            'config_title': 'API Docs',
            'project_name': 'api\x00lib',  # Null byte in project name
            'description': 'Null byte in project name from encoding issue'
        },
        {
            'config_title': 'Documentation',
            'project_name': 'Project',
            'function_name': 'process_data\x0c',  # Form feed in function name
            'description': 'Form feed character in auto-extracted function name'
        }
    ]
    
    for i, scenario in enumerate(scenarios, 1):
        print(f"\n{'='*60}")
        print(f"Scenario {i}: {scenario['description']}")
        print(f"{'='*60}")
        
        try:
            # Create the root element as DevhelpBuilder.build_devhelp does
            root = etree.Element('book',
                                title=scenario.get('config_title', 'Documentation'),
                                name=scenario.get('project_name', 'Project'),
                                link="index.html",
                                version="1.0")
            
            # Add functions element
            functions = etree.SubElement(root, 'functions')
            
            # Add a function if specified (as write_index does)
            if 'function_name' in scenario:
                etree.SubElement(functions, 'function',
                                name=scenario['function_name'],
                                link='api.html#' + scenario['function_name'])
            
            # Create the tree
            tree = etree.ElementTree(root)
            
            # Write to gzipped file as done in build_devhelp
            with tempfile.NamedTemporaryFile(suffix='.devhelp.gz', delete=False) as f:
                output_file = f.name
            
            with gzip.GzipFile(filename=output_file, mode='w', mtime=0) as gz:
                tree.write(gz, 'utf-8')
            
            print(f"✓ Devhelp file written successfully to {output_file}")
            
            # Now try to read and parse the generated file
            # (This simulates what devhelp or other tools would do)
            print("\nAttempting to parse the generated devhelp file...")
            
            with gzip.open(output_file, 'rt', encoding='utf-8') as gz:
                xml_content = gz.read()
            
            # Try to parse the XML
            parsed = etree.fromstring(xml_content)
            print("✓ XML parsed successfully!")
            
        except etree.ParseError as e:
            print(f"\n✗ CRITICAL BUG: Generated devhelp file is invalid XML!")
            print(f"  Error: {e}")
            print(f"\n  Impact: The devhelp file cannot be used by GNOME Devhelp")
            print(f"          or any other XML-based documentation viewer.")
            
            # Show the problematic XML content
            try:
                with gzip.open(output_file, 'rt', encoding='utf-8') as gz:
                    xml_content = gz.read()
                print(f"\n  Problematic XML (first 200 chars):")
                print(f"  {repr(xml_content[:200])}")
            except:
                pass
                
        except Exception as e:
            print(f"\n✗ Unexpected error: {e}")
        
        finally:
            # Clean up
            import os
            if 'output_file' in locals() and os.path.exists(output_file):
                os.unlink(output_file)


if __name__ == "__main__":
    simulate_devhelp_build_with_bad_title()