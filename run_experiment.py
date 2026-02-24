#!/usr/bin/env python3
"""
Entry point for stimulus presentation system.

Handles command-line arguments, loads configuration, and launches experimental session.
"""

import argparse
import sys
from pathlib import Path

from utils import load_config, validate_config, check_paths, print_config_summary
from session import ExperimentSession


def parse_arguments():
    """
    Parse command-line arguments.

    Returns:
        Parsed arguments namespace

    Notes:
        Supports config file path and dry-run flag.
    """
    parser = argparse.ArgumentParser(
        description='Stimulus Presentation System for Neural Decoding Experiment',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run experiment with default config
  python run_experiment.py

  # Run with custom config
  python run_experiment.py --config my_config.yaml

  # Validate setup without running (dry run)
  python run_experiment.py --dry-run

  # Validate custom config
  python run_experiment.py --config my_config.yaml --dry-run
        """
    )

    parser.add_argument(
        '--config',
        type=str,
        default='config.yaml',
        help='Path to configuration file (default: config.yaml)'
    )

    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Validate configuration and manifest without running experiment'
    )

    parser.add_argument(
        '--version',
        action='version',
        version='Stimulus Presentation System v1.0'
    )

    return parser.parse_args()


def main():
    """
    Main entry point for stimulus presentation system.

    Notes:
        Loads config, validates, and launches session.
        Handles errors gracefully with informative messages.
    """
    print("="*60)
    print("STIMULUS PRESENTATION SYSTEM")
    print("Neural Decoding Experiment - Cross-Modal Matrix")
    print("="*60)

    # Parse arguments
    args = parse_arguments()

    try:
        # Load configuration
        print(f"\nLoading configuration from {args.config}...")
        config = load_config(args.config)

        # Validate configuration
        print("Validating configuration...")
        is_valid, errors = validate_config(config)

        if not is_valid:
            print("\nConfiguration validation failed:")
            for error in errors:
                print(f"  ERROR: {error}")
            sys.exit(1)

        print("Configuration valid ✓")

        # Check paths
        print("Checking paths...")
        paths_ok, warnings = check_paths(config)

        if warnings:
            print("\nPath warnings:")
            for warning in warnings:
                print(f"  WARNING: {warning}")

        if not paths_ok:
            print("\nCritical path errors - cannot continue")
            sys.exit(1)

        print("Paths OK ✓")

        # Print configuration summary
        if args.dry_run:
            print_config_summary(config)

        # Check if menu mode is enabled (skip in dry-run)
        if config.get('menu_mode', False) and not args.dry_run:
            print("\nMenu mode enabled - launching configuration interface...")

            # Import menu and display (only if needed)
            from display import DisplayManager
            from menu import MenuSystem

            # Initialize display for menu
            display = DisplayManager(config, dry_run=False)

            try:
                # Create and run menu
                menu = MenuSystem(display, config)
                menu_config = menu.run_menu_flow()

                if menu_config is None:
                    print("\nConfiguration cancelled by user")
                    display.close()
                    sys.exit(0)

                # Update config with menu selections
                config.update(menu_config)
                print("\nConfiguration complete!")
                print_config_summary(config)

                # Close menu display (ExperimentSession will create its own)
                display.close()

            except Exception as e:
                print(f"\nMenu error: {e}")
                display.close()
                raise

        # Initialize session
        print("\nInitializing experiment session...")
        session = ExperimentSession(config, dry_run=args.dry_run)

        if args.dry_run:
            # Dry run: validate only
            session.validate_only()
            print("\nDry run complete - ready to run experiment")
            sys.exit(0)

        else:
            # Run full experiment
            print("\nStarting experiment...")
            print("Press Escape at any time to quit\n")

            session.run()

            print("\nSession complete!")
            sys.exit(0)

    except FileNotFoundError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    except ValueError as e:
        print(f"\nERROR: {e}")
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n\nExperiment interrupted by user (Ctrl+C)")
        sys.exit(130)

    except Exception as e:
        print(f"\n\nUNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
