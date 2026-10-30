#!/usr/bin/env python3
"""
Test Active Learning by simulating a failure and checking if it learns.
"""
import sys
import json
from pathlib import Path

# Add project to path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import Agent
from core.setup import ensure_config
from tools.base import ToolResult

def main():
    print("=== ACTIVE LEARNING TEST ===\n")
    
    # Step 1: Check baseline learnings
    learnings_file = Path.home() / ".hellochusquis" / "learnings.json"
    try:
        with open(learnings_file) as f:
            before = json.load(f)
        errors_before = len(before.get("errors", []))
        improvements_before = len(before.get("system_prompt_improvements", []))
        print(f"📊 Baseline learnings:")
        print(f"   Errors: {errors_before}")
        print(f"   Improvements: {improvements_before}\n")
    except FileNotFoundError:
        errors_before = 0
        improvements_before = 0
        print("📊 No learnings file yet (first run)\n")
    
    # Step 2: Initialize agent and simulate a strategic failure
    config = ensure_config()
    agent = Agent(config)
    
    # Simulate a security block (strategic failure)
    print("🧪 Simulating a security-blocked tool call...")
    fake_result = ToolResult(success=False, output="", error="Security audit: recursive force delete")
    
    # Trigger the active learning handler directly
    agent._handle_active_learning_trigger("shell", fake_result)
    print("✓ Active learning trigger fired\n")
    
    # Wait a moment for the background thread
    import time
    print("⏳ Waiting for background analysis (3 seconds)...")
    time.sleep(3)
    
    # Step 3: Check if new learnings were added
    try:
        with open(learnings_file) as f:
            after = json.load(f)
        errors_after = len(after.get("errors", []))
        improvements_after = len(after.get("system_prompt_improvements", []))
        
        print(f"\n📊 Learnings after failure:")
        print(f"   Errors: {errors_after} (+{errors_after - errors_before})")
        print(f"   Improvements: {improvements_after} (+{improvements_after - improvements_before})")
        
        if errors_after > errors_before or improvements_after > improvements_before:
            print("\n✅ ACTIVE LEARNING WORKING!")
            print("\nMost recent learnings:")
            if after.get("errors"):
                print(f"\n  Latest error: {after['errors'][-1]}")
            if after.get("system_prompt_improvements"):
                print(f"\n  Latest improvement: {after['system_prompt_improvements'][-1]}")
            sys.exit(0)
        else:
            print("\n⚠️  No new learnings detected (may need more time or different failure type)")
            sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error checking learnings: {e}")
        sys.exit(1)
    

if __name__ == "__main__":
    main()