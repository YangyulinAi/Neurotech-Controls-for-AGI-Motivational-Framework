#!/usr/bin/env python3
"""
PyPhi Installation Script for Real Φ Calculation
Handles dependency conflicts and provides installation options
"""
import subprocess
import sys
import os

def run_command(cmd, description):
    """Run a command and handle errors"""
    print(f"\n{description}...")
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True, check=True)
        print(f"✓ {description} successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e.stderr}")
        return False

def check_pyphi():
    """Check if PyPhi is already installed and working"""
    try:
        import pyphi
        print(f"✓ PyPhi {pyphi.__version__} is already installed")
        
        # Test basic functionality
        import numpy as np
        tpm = np.array([[0, 0], [1, 1]])
        cm = np.array([[1, 1], [1, 1]])
        network = pyphi.Network(tpm, cm=cm)
        
        state = (0, 0)
        subsystem = pyphi.Subsystem(network, state, range(network.size))
        test_phi = pyphi.compute.phi(subsystem)
        
        print(f"✓ PyPhi test successful - Φ = {test_phi:.6f}")
        return True
        
    except ImportError:
        print("✗ PyPhi not installed")
        return False
    except Exception as e:
        print(f"✗ PyPhi test failed: {e}")
        return False

def install_pyphi_standard():
    """Standard PyPhi installation"""
    print("\n=== Standard PyPhi Installation ===")
    
    commands = [
        "pip install pyphi==1.2.0",
        "pip install networkx>=2.6,<3.0",
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd, f"Installing {cmd.split()[-1]}"):
            success = False
            break
    
    return success

def install_pyphi_force():
    """Force install PyPhi with specific numpy version"""
    print("\n=== Force Install with Numpy Downgrade ===")
    print("WARNING: This may break other dependencies!")
    
    commands = [
        "pip install --force-reinstall numpy==1.21.6",
        "pip install pyphi==1.2.0",
        "pip install networkx>=2.6,<3.0",
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd, f"Force installing {cmd.split()[-1]}"):
            success = False
            break
    
    return success

def create_conda_env():
    """Create separate conda environment for PyPhi"""
    print("\n=== Creating Conda Environment ===")
    
    commands = [
        "conda create -n pyphi python=3.9 -y",
        "conda activate pyphi && pip install pyphi==1.2.0",
        "conda activate pyphi && pip install networkx>=2.6,<3.0",
    ]
    
    success = True
    for cmd in commands:
        if not run_command(cmd, f"Running: {cmd}"):
            success = False
            
    if success:
        print("\n✓ PyPhi environment created successfully!")
        print("To use PyPhi:")
        print("  conda activate pyphi")
        print("  python tests/analyze_file_onnx.py --compute_phi --phi_method IIT3.0")
    
    return success

def main():
    """Main installation menu"""
    print("PyPhi Installation Tool for Neural Axis")
    print("=" * 40)
    
    # Check if already installed
    if check_pyphi():
        print("\nPyPhi is already working! You can enable real Φ calculation.")
        return
    
    print("\nInstallation Options:")
    print("1. Standard installation (recommended)")
    print("2. Force install with numpy downgrade (may break other packages)")
    print("3. Create separate conda environment (safest)")
    print("4. Check requirements only")
    print("5. Exit")
    
    while True:
        try:
            choice = input("\nEnter your choice (1-5): ").strip()
            
            if choice == "1":
                if install_pyphi_standard():
                    print("\n✓ Installation complete! Test with:")
                    print("  python -c 'import pyphi; print(pyphi.__version__)'")
                break
                
            elif choice == "2":
                confirm = input("This may break other packages. Continue? (y/N): ")
                if confirm.lower() == 'y':
                    if install_pyphi_force():
                        print("\n✓ Force installation complete!")
                break
                
            elif choice == "3":
                if create_conda_env():
                    print("\n✓ Conda environment created!")
                break
                
            elif choice == "4":
                print("\nSystem Requirements:")
                print("- Python 3.8-3.10 (PyPhi compatibility)")
                print("- NumPy 1.21-1.23 (older versions required)")
                print("- NetworkX 2.6+ for graph operations")
                print("- Sufficient memory (Φ calculation is intensive)")
                break
                
            elif choice == "5":
                print("Installation cancelled")
                break
                
            else:
                print("Invalid choice. Please enter 1-5.")
                
        except KeyboardInterrupt:
            print("\nInstallation cancelled")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()