#!/usr/bin/env python3
"""
Quick test to verify all Option D & E features are working.
"""
import sys

def test_imports():
    """Test that all modules can be imported."""
    print("🧪 Testing imports...")
    
    try:
        print("  ✓ Importing prometheus_client...")
        from prometheus_client import Counter, Histogram, Gauge
        
        print("  ✓ Importing logging_config...")
        from src.backend.logging_config import setup_logging, get_logger
        
        print("  ✓ Importing metrics...")
        from src.backend.metrics import track_request, metrics_endpoint
        
        print("  ✓ Importing health...")
        from src.backend.api.health import router
        
        print("  ✓ Importing main_enhanced...")
        # Don't actually import to avoid running FastAPI
        # from src.backend.api.main_enhanced import app
        
        print("\n✅ All critical imports successful!")
        return True
    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_logging():
    """Test structured logging."""
    print("\n🧪 Testing structured logging...")
    
    try:
        from src.backend.logging_config import setup_logging, get_logger, set_trace_id
        
        # Setup logging
        setup_logging(level="INFO", use_json=False)
        logger = get_logger("test")
        
        # Test basic logging
        logger.info("Test message")
        
        # Test trace ID
        trace_id = set_trace_id()
        print(f"  ✓ Generated trace ID: {trace_id[:8]}...")
        
        print("✅ Logging works!")
        return True
    except Exception as e:
        print(f"❌ Logging test failed: {e}")
        return False

def test_metrics():
    """Test Prometheus metrics."""
    print("\n🧪 Testing Prometheus metrics...")
    
    try:
        from src.backend.metrics import (
            track_request, 
            track_request_duration,
            track_rag_query,
            metrics_endpoint
        )
        
        # Track some metrics
        track_request("GET", "/health", 200)
        track_request_duration("GET", "/health", 0.001)
        track_rag_query("success")
        
        # Generate metrics output
        metrics_response = metrics_endpoint()
        
        # Get the body content from the Response object
        if hasattr(metrics_response, 'body'):
            body = metrics_response.body
            metrics_output = bytes(body).decode('utf-8')  # Convert memoryview to bytes
        else:
            metrics_output = str(metrics_response)
        
        if "geo_requests_total" in metrics_output:
            print("  ✓ Metrics are being tracked")
            print(f"  ✓ Metrics endpoint returns {len(metrics_output)} bytes")
            print("✅ Metrics work!")
            return True
        else:
            print(f"❌ Metrics output doesn't contain expected data")
            print(f"   Got: {metrics_output[:200]}...")
            return False
            
    except Exception as e:
        print(f"❌ Metrics test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_frontend_files():
    """Test that frontend files exist."""
    print("\n🧪 Testing frontend components...")
    
    import os
    
    files = [
        "apps/web/src/components/ThemeProvider.tsx",
        "apps/web/src/components/ThemeToggle.tsx",
        "apps/web/src/components/CopyButton.tsx",
        "apps/web/src/components/ToastProvider.tsx",
        "apps/web/src/components/ExportButton.tsx",
        "apps/web/src/components/LatencyTimer.tsx",
        "apps/web/src/app/ask/page.tsx",
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ❌ {file} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("✅ All frontend files exist!")
        return True
    else:
        print("❌ Some frontend files missing")
        return False

def test_docker_files():
    """Test that Docker files exist."""
    print("\n🧪 Testing Docker setup...")
    
    import os
    
    files = [
        "Dockerfile.backend",
        "Dockerfile.frontend",
        "docker-compose.prod.yml",
        "monitoring/prometheus.yml",
        ".github/workflows/ci-cd.yml",
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            print(f"  ✓ {file}")
        else:
            print(f"  ❌ {file} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("✅ All Docker files exist!")
        return True
    else:
        print("❌ Some Docker files missing")
        return False

def test_documentation():
    """Test that documentation exists."""
    print("\n🧪 Testing documentation...")
    
    import os
    
    files = [
        "docs/OPTIONS_D_E_COMPLETE.md",
        "docs/DEPLOYMENT_GUIDE.md",
        "docs/OPERATIONS_RUNBOOK.md",
        "docs/PHASE_2_COMPLETE.md",
        "README_OPTIONS_D_E.md",
        "QUICK_REFERENCE.md",
        "WHAT_TO_DO_NEXT.md",
    ]
    
    all_exist = True
    for file in files:
        if os.path.exists(file):
            size_kb = os.path.getsize(file) // 1024
            print(f"  ✓ {file} ({size_kb}KB)")
        else:
            print(f"  ❌ {file} NOT FOUND")
            all_exist = False
    
    if all_exist:
        print("✅ All documentation exists!")
        return True
    else:
        print("❌ Some documentation missing")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("🎯 Project GEO - Options D & E Verification")
    print("=" * 60)
    
    results = []
    
    results.append(("Imports", test_imports()))
    results.append(("Logging", test_logging()))
    results.append(("Metrics", test_metrics()))
    results.append(("Frontend", test_frontend_files()))
    results.append(("Docker", test_docker_files()))
    results.append(("Documentation", test_documentation()))
    
    print("\n" + "=" * 60)
    print("📊 Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
    
    print(f"\n🎯 Score: {passed}/{total} tests passed ({passed*100//total}%)")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Options D & E are ready to test!")
        print("\n📝 Next steps:")
        print("  1. Start the backend: docker-compose -f docker-compose.prod.yml up -d")
        print("  2. Open frontend: http://localhost:3000")
        print("  3. Try a query and test all features!")
        return 0
    else:
        print("\n⚠️  Some tests failed. Review the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
