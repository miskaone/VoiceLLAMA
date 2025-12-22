"""VoiceLLAMA TTS Server CLI.

Usage:
    voicellama serve                    # Start server on default port 8333
    voicellama serve --port 9000        # Custom port
    voicellama serve --host 127.0.0.1   # Localhost only
    voicellama serve --config my.toml   # Custom config file
"""

import argparse
import sys


def cmd_serve(args):
    """Start the TTS API server."""
    import uvicorn
    from voicellama.config import Config
    from voicellama.server import create_app

    config = Config.load(args.config)

    # CLI args override config
    if args.port:
        config.server.port = args.port
    if args.host:
        config.server.host = args.host
    if args.log_level:
        config.server.log_level = args.log_level

    print(f"Starting VoiceLLAMA server on http://{config.server.host}:{config.server.port}")

    app = create_app(config)
    uvicorn.run(
        app,
        host=config.server.host,
        port=config.server.port,
        log_level=config.server.log_level.lower()
    )


def cmd_version(args):
    """Show version information."""
    from voicellama import __version__
    print(f"VoiceLLAMA v{__version__}")


def main():
    parser = argparse.ArgumentParser(
        prog='voicellama',
        description='VoiceLLAMA - Ultra-fast TTS API Server powered by Kokoro'
    )
    parser.add_argument(
        '-v', '--version',
        action='store_true',
        help='Show version and exit'
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # serve command
    serve_parser = subparsers.add_parser('serve', help='Start the TTS API server')
    serve_parser.add_argument(
        '--port', '-p',
        type=int,
        help='Server port (default: 8333)'
    )
    serve_parser.add_argument(
        '--host', '-H',
        help='Server host (default: 0.0.0.0)'
    )
    serve_parser.add_argument(
        '--config', '-c',
        help='Path to voicellama.toml config file'
    )
    serve_parser.add_argument(
        '--log-level', '-l',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        help='Log level (default: INFO)'
    )
    serve_parser.set_defaults(func=cmd_serve)

    # version command
    version_parser = subparsers.add_parser('version', help='Show version information')
    version_parser.set_defaults(func=cmd_version)

    args = parser.parse_args()

    # Handle --version flag
    if args.version:
        cmd_version(args)
        return

    # Handle no command
    if args.command is None:
        parser.print_help()
        sys.exit(0)

    # Execute command
    args.func(args)


if __name__ == "__main__":
    main()
