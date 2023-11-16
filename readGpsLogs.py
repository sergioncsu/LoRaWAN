import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

def monitor_folder(folder_to_watch):
    class MyHandler(FileSystemEventHandler):
        def __init__(self):
            super().__init__()
            self.last_line = None

        def on_modified(self, event):
            if event.is_directory:
                return

            if event.event_type == 'modified' and event.src_path.endswith('vehicleOut.txt'):
                directory = os.path.dirname(event.src_path)
                last_modified_file = get_last_modified_file(directory)
                self.last_line = get_last_line(last_modified_file)

    def get_last_line(file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            if lines:
                return lines[-1].strip()
            else:
                return None

    def get_last_modified_file(folder_path):
        files = [f for f in os.listdir(folder_path) if f.endswith('vehicleOut.txt')]
        full_paths = [os.path.join(folder_path, f) for f in files]
        return max(full_paths, key=os.path.getmtime, default=None)

    observer = Observer()
    event_handler = MyHandler()
    observer.schedule(event_handler, path=folder_to_watch, recursive=False)
    observer.start()

    try:
        while True:
            time.sleep(1)
            # Continuously yield the latest line
            if event_handler.last_line:
                yield event_handler.last_line
    except KeyboardInterrupt:
        observer.stop()
    observer.join()
