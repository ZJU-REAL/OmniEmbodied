#!/usr/bin/env python3
"""
Simple HTTP server to serve the OmniEAR project page locally.
Usage: python3 run_server.py [port]
Default port: 8000
"""

import http.server
import socketserver
import sys
import os
import webbrowser
from pathlib import Path

def main():
    # Default port
    PORT = 8005
    
    # Check if port is provided as argument
    if len(sys.argv) > 1:
        try:
            PORT = int(sys.argv[1])
        except ValueError:
            print(f"Invalid port number: {sys.argv[1]}")
            print("Usage: python3 run_server.py [port]")
            sys.exit(1)
    
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Create server
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"🚀 OmniEAR Project Page Server")
            print(f"📍 Serving at: http://localhost:{PORT}")
            print(f"📁 Directory: {script_dir}")
            print(f"🌐 Opening browser...")
            print(f"⏹️  Press Ctrl+C to stop the server")
            
            # Open browser automatically
            webbrowser.open(f'http://localhost:{PORT}')
            
            # Start server
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print(f"\n🛑 Server stopped.")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Port {PORT} is already in use. Try a different port:")
            print(f"   python3 run_server.py {PORT + 1}")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
