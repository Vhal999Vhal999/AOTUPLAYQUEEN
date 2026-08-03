#!/usr/bin/env python3
"""
autoplay.py

Simple autoplay script for AOTUPLAYQUEEN repository.
Behavior (default): sequentially plays audio files found under SHUKLAMUSIC/ and loops the playlist.

Usage examples:
  python3 autoplay.py                # sequential, loop
  python3 autoplay.py --no-loop      # play once through
  python3 autoplay.py --shuffle      # shuffle playlist
  python3 autoplay.py --delay 2      # wait 2 seconds between tracks
  python3 autoplay.py --player ffplay # prefer ffplay (ffmpeg) for playback

Playback methods tried (in order):
 - ffplay (ffmpeg) via subprocess
 - pydub playback (requires simpleaudio or pyaudio installed)
 - playsound module

The script will print helpful messages if no player is available.
"""

import argparse
import os
import random
import subprocess
import sys
import time
from pathlib import Path

AUDIO_EXTS = {'.mp3', '.wav', '.ogg', '.m4a', '.flac', '.aac'}
DEFAULT_MUSIC_DIR = Path(__file__).resolve().parent / 'SHUKLAMUSIC'


class Player:
    def __init__(self, preferred=None):
        self.preferred = preferred
        self._test_ffplay = None

    def _has_ffplay(self):
        if self._test_ffplay is not None:
            return self._test_ffplay
        try:
            subprocess.run(['ffplay', '-version'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            self._test_ffplay = True
        except FileNotFoundError:
            self._test_ffplay = False
        return self._test_ffplay

    def play(self, path):
        path = str(path)
        # If user requested ffplay explicitly, try that first
        if self.preferred == 'ffplay' or (self.preferred is None and self._has_ffplay()):
            try:
                # -nodisp hides display, -autoexit quits when done, -loglevel quiet to reduce output
                subprocess.run(['ffplay', '-nodisp', '-autoexit', '-loglevel', 'quiet', path])
                return
            except FileNotFoundError:
                pass
            except Exception:
                # fall through to other players
                pass

        # Try pydub playback
        try:
            from pydub import AudioSegment, playback
            seg = AudioSegment.from_file(path)
            playback.play(seg)
            return
        except Exception:
            pass

        # Try playsound
        try:
            from playsound import playsound
            playsound(path)
            return
        except Exception:
            pass

        raise RuntimeError('No available playback method found. Install ffmpeg (ffplay), pydub+simpleaudio, or playsound.')


def find_tracks(folder: Path):
    folder = Path(folder)
    if not folder.exists() or not folder.is_dir():
        return []
    tracks = []
    for root, _, files in os.walk(folder):
        for f in files:
            if Path(f).suffix.lower() in AUDIO_EXTS:
                tracks.append(Path(root) / f)
    # natural sort by name
    tracks.sort()
    return tracks


def main():
    parser = argparse.ArgumentParser(description='Autoplay audio from SHUKLAMUSIC/')
    parser.add_argument('--dir', '-d', default=str(DEFAULT_MUSIC_DIR), help='Directory to scan for audio files')
    parser.add_argument('--shuffle', action='store_true', help='Shuffle playlist')
    parser.add_argument('--no-loop', dest='loop', action='store_false', help='Do not loop the playlist (play only once)')
    parser.add_argument('--delay', type=float, default=0.0, help='Seconds to wait between tracks')
    parser.add_argument('--player', choices=['ffplay', 'pydub', 'playsound', 'auto'], default='auto', help='Preferred player (auto tries ffplay then pydub then playsound)')
    args = parser.parse_args()

    music_dir = Path(args.dir)
    tracks = find_tracks(music_dir)

    if not tracks:
        print(f'No audio files found in {music_dir}. Please add files to the SHUKLAMUSIC/ directory.')
        sys.exit(1)

    player = Player(preferred=(args.player if args.player != 'auto' else None))

    print(f'Autoplay starting: {len(tracks)} track(s) found in {music_dir}')
    print(f"Options -> shuffle={args.shuffle}, loop={args.loop}, delay={args.delay}, preferred_player={args.player}")

    try:
        while True:
            playlist = list(tracks)
            if args.shuffle:
                random.shuffle(playlist)
            for t in playlist:
                print(f'Playing: {t.name}')
                try:
                    player.play(t)
                except Exception as e:
                    print(f'Error playing {t.name}: {e}')
                if args.delay and args.delay > 0:
                    time.sleep(args.delay)
            if not args.loop:
                break
    except KeyboardInterrupt:
        print('\nAutoplay stopped by user.')


if __name__ == '__main__':
    main()
