"""
Event marking via LSL and CSV logging.

Handles all event markers for precise time synchronization with EEG, fNIRS, and eye tracking.
"""

import json
import csv
from typing import Dict, Optional, Any
from pathlib import Path
from datetime import datetime


class MarkerSystem:
    """
    Manages event markers via LSL and CSV logging.

    Attributes:
        lsl_outlet: LSL StreamOutlet for real-time markers
        csv_file: Open file handle for CSV log
        csv_writer: CSV DictWriter instance
        parallel_port: Parallel port object (if enabled)
        lsl_enabled: Whether LSL is active
        parallel_port_enabled: Whether parallel port is active
    """

    def __init__(self, config: Dict[str, Any], session_id: str, dry_run: bool = False):
        """
        Initialize marker system with LSL outlet and CSV logger.

        Args:
            config: Configuration dictionary
            session_id: Unique session identifier
            dry_run: If True, skip hardware initialization

        Notes:
            Creates CSV file immediately to ensure write access.
            LSL outlet is created but not started until first marker.
        """
        self.lsl_enabled = config.get('lsl_enabled', True) and not dry_run
        self.parallel_port_enabled = config.get('parallel_port_enabled', False) and not dry_run
        self.lsl_outlet = None
        self.parallel_port = None

        # Initialize LSL outlet if enabled
        if self.lsl_enabled:
            try:
                from pylsl import StreamInfo, StreamOutlet
                stream_name = config.get('lsl_stream_name', 'StimulusMarkers')
                info = StreamInfo(
                    name=stream_name,
                    type='Markers',
                    channel_count=1,
                    nominal_srate=0,  # Irregular rate
                    channel_format='string',
                    source_id=f'{stream_name}_{session_id}'
                )
                self.lsl_outlet = StreamOutlet(info)
                print(f"LSL outlet '{stream_name}' created successfully")
            except ImportError:
                print("Warning: pylsl not available, LSL markers disabled")
                self.lsl_enabled = False
            except Exception as e:
                print(f"Warning: Failed to create LSL outlet: {e}")
                self.lsl_enabled = False

        # Initialize parallel port if enabled
        if self.parallel_port_enabled:
            try:
                from psychopy import parallel
                port_address = config.get('parallel_port_address', '0x378')
                self.parallel_port = parallel.ParallelPort(address=port_address)
                print(f"Parallel port initialized at {port_address}")
            except ImportError:
                print("Warning: psychopy.parallel not available, parallel port disabled")
                self.parallel_port_enabled = False
            except Exception as e:
                print(f"Warning: Failed to initialize parallel port: {e}")
                self.parallel_port_enabled = False

        # Initialize CSV logger
        log_dir = Path(config.get('log_dir', 'logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        csv_filename = log_dir / f"session_{session_id}_{timestamp}.csv"

        self.csv_file = open(csv_filename, 'w', newline='', encoding='utf-8')

        # CSV columns matching all possible marker fields
        fieldnames = [
            'timestamp', 'event', 'mode', 'task', 'tier', 'congruence',
            'image_category', 'audio_category', 'image_file', 'audio_file',
            'trial_type', 'trial_index', 'response_key', 'rt_ms',
            'correct', 'block_number'
        ]

        self.csv_writer = csv.DictWriter(self.csv_file, fieldnames=fieldnames, extrasaction='ignore')
        self.csv_writer.writeheader()
        self.csv_file.flush()

        print(f"CSV log created: {csv_filename}")

    def send_marker(self, marker_data: Dict[str, Any], trigger_code: Optional[int] = None):
        """
        Send marker via LSL, parallel port, and write to CSV.

        Args:
            marker_data: Dictionary containing marker information
            trigger_code: Optional parallel port trigger code (0-255)

        Notes:
            Timing-critical: LSL marker is sent immediately.
            CSV write is buffered but flushed periodically.
        """
        # Add timestamp
        timestamp = datetime.now().isoformat()
        marker_data['timestamp'] = timestamp

        # Send via LSL
        if self.lsl_enabled and self.lsl_outlet:
            try:
                marker_json = json.dumps(marker_data)
                self.lsl_outlet.push_sample([marker_json])
            except Exception as e:
                print(f"Warning: Failed to send LSL marker: {e}")

        # Send parallel port trigger
        if self.parallel_port_enabled and self.parallel_port and trigger_code is not None:
            try:
                self.parallel_port.setData(trigger_code)
                # Reset after 10ms (handled by hardware or need explicit reset)
            except Exception as e:
                print(f"Warning: Failed to send parallel port trigger: {e}")

        # Write to CSV
        try:
            self.csv_writer.writerow(marker_data)
        except Exception as e:
            print(f"Warning: Failed to write CSV marker: {e}")

    def send_onset_marker(self, trial_data: Dict[str, Any], trial_index: int,
                         mode: str, task: Optional[str] = None):
        """
        Send stimulus onset marker.

        Args:
            trial_data: Trial information dictionary
            trial_index: Index of current trial
            mode: Experimental mode ('passive' or 'active')
            task: Task type if in active mode

        Notes:
            Called immediately after win.flip() for precise timing.
        """
        marker = {
            'event': 'onset',
            'mode': mode,
            'task': task,
            'tier': trial_data['tier'],
            'congruence': trial_data['congruence'],
            'image_category': trial_data['image_category'],
            'audio_category': trial_data['audio_category'],
            'image_file': trial_data.get('image_file', ''),
            'audio_file': trial_data.get('audio_file', ''),
            'trial_type': trial_data.get('trial_type', 'standard'),
            'trial_index': trial_index,
            'response_key': None,
            'rt_ms': None
        }

        # Parallel port trigger code based on tier (simple encoding)
        trigger_code = trial_data['tier']
        if trial_data['congruence'] == 'incongruent':
            trigger_code += 10  # 11-14 for incongruent, 1-4 for congruent

        self.send_marker(marker, trigger_code)

    def send_offset_marker(self, trial_data: Dict[str, Any], trial_index: int,
                          mode: str, task: Optional[str] = None):
        """
        Send stimulus offset marker.

        Args:
            trial_data: Trial information dictionary
            trial_index: Index of current trial
            mode: Experimental mode
            task: Task type if in active mode

        Notes:
            Called after stimulus duration has elapsed.
        """
        marker = {
            'event': 'offset',
            'mode': mode,
            'task': task,
            'tier': trial_data['tier'],
            'congruence': trial_data['congruence'],
            'image_category': trial_data['image_category'],
            'audio_category': trial_data['audio_category'],
            'image_file': trial_data.get('image_file', ''),
            'audio_file': trial_data.get('audio_file', ''),
            'trial_type': trial_data.get('trial_type', 'standard'),
            'trial_index': trial_index,
            'response_key': None,
            'rt_ms': None
        }

        self.send_marker(marker)

    def send_response_marker(self, trial_data: Dict[str, Any], trial_index: int,
                           response_key: str, rt_ms: float, correct: bool,
                           mode: str, task: Optional[str] = None):
        """
        Send response marker.

        Args:
            trial_data: Trial information dictionary
            trial_index: Index of current trial
            response_key: Key that was pressed
            rt_ms: Reaction time in milliseconds from stimulus onset
            correct: Whether response was correct
            mode: Experimental mode
            task: Task type

        Notes:
            Called immediately when response is detected.
        """
        marker = {
            'event': 'response',
            'mode': mode,
            'task': task,
            'tier': trial_data['tier'],
            'congruence': trial_data['congruence'],
            'image_category': trial_data['image_category'],
            'audio_category': trial_data['audio_category'],
            'image_file': trial_data.get('image_file', ''),
            'audio_file': trial_data.get('audio_file', ''),
            'trial_type': trial_data.get('trial_type', 'standard'),
            'trial_index': trial_index,
            'response_key': response_key,
            'rt_ms': rt_ms,
            'correct': correct
        }

        self.send_marker(marker)

    def send_block_marker(self, event: str, block_number: int, tier: int,
                         mode: str, task: Optional[str] = None):
        """
        Send block start/end marker.

        Args:
            event: 'block_start' or 'block_end'
            block_number: Block index
            tier: Tier number for this block
            mode: Experimental mode
            task: Task type if in active mode

        Notes:
            Used for segmenting data during analysis.
        """
        marker = {
            'event': event,
            'mode': mode,
            'task': task,
            'tier': tier,
            'block_number': block_number,
            'congruence': None,
            'image_category': None,
            'audio_category': None,
            'image_file': None,
            'audio_file': None,
            'trial_type': None,
            'trial_index': None,
            'response_key': None,
            'rt_ms': None
        }

        self.send_marker(marker)

    def flush(self):
        """
        Flush CSV buffer to disk.

        Notes:
            Called periodically and on cleanup to ensure data persistence.
        """
        if self.csv_file:
            self.csv_file.flush()

    def close(self):
        """
        Close all marker outputs and flush data.

        Notes:
            Must be called at session end to ensure all data is written.
            Handles exceptions gracefully to ensure cleanup succeeds.
        """
        try:
            if self.csv_file:
                self.csv_file.flush()
                self.csv_file.close()
                print("CSV log closed successfully")
        except Exception as e:
            print(f"Warning: Error closing CSV file: {e}")

        # LSL outlet closes automatically
        if self.lsl_enabled:
            print("LSL outlet closed")

        # Parallel port cleanup
        if self.parallel_port_enabled and self.parallel_port:
            try:
                self.parallel_port.setData(0)  # Reset to 0
            except Exception as e:
                print(f"Warning: Error resetting parallel port: {e}")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - ensures cleanup."""
        self.close()
        return False
