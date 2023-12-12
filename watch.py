from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess
import sys
import time

class GameHandler(FileSystemEventHandler):
    def __init__(self):
        self.start_game()

    def on_modified(self, event):
        if event.src_path.endswith('.py'):
            print("Change detected. Restarting game.")
            self.restart_game()

    def restart_game(self):
        self.stop_game()
        self.start_game()
    
    def stop_game(self):
        if self.game_process:
            self.game_process.terminate()  # Terminate the current game process
            self.game_process.wait()       # Wait for the process to actually terminate

    def start_game(self):
        # Start a new instance of the game
        self.game_process = subprocess.Popen([sys.executable, 'main.py'])


if __name__ == "__main__":
    path = '.'  # The directory you want to watch

    # Start the game for the first time
    game_handler = GameHandler()
    observer = Observer()
    observer.schedule(game_handler, path, recursive=True)
    observer.start()

    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        game_handler.stop_game()
        observer.stop()
    observer.join()