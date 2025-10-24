import time

import rich

from rich.console import Console

# Create a Console object
console = Console()

# Print some content to demonstrate clearing
console.print("This is some content before clearing.")
console.print("It will be cleared shortly.")

# Clear the screen
console.clear()

for i in range(100):
    console.clear()
    console.print(f'First line {i}')
    console.print(f'Second line {i}')
    time.sleep(0.5)
