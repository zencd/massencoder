import PySimpleGUI as sg

# Sample table data
data = [
    ["Alice", 32, "Engineer"],
    ["Bob", 41, "Manager"],
    ["Charlie", 29, "Designer"],
]

headings = ["Name", "Age", "Job"]

layout = [
    # Table fills most of the window
    [sg.Table(
        values=data,
        headings=headings,
        max_col_width=25,
        auto_size_columns=True,
        display_row_numbers=False,
        justification='left',
        num_rows=10,
        key='-TABLE-',
        enable_events=True,
        expand_x=True,
        expand_y=True,
    )],

    # Buttons row
    [
        sg.Button("Add", key='-ADD-'),
        sg.Button("Edit", key='-EDIT-'),
        sg.Button("Delete", key='-DELETE-'),
        sg.Button("Refresh", key='-REFRESH-'),
        sg.Push(),  # pushes next elements to the right
        sg.Button("Exit", key='-EXIT-')
    ],

    # Status bar
    [sg.Text("Ready", key='-STATUS-', relief=sg.RELIEF_SUNKEN, expand_x=True)]
]

window = sg.Window(
    "PySimpleGUI Demo",
    layout,
    resizable=True,
    finalize=True,
)

# Allow table to expand with window
window['-TABLE-'].expand(True, True)

# Event loop
while True:
    event, values = window.read()

    if event in (sg.WINDOW_CLOSED, '-EXIT-'):
        break

    # Status updates for actions
    if event == '-ADD-':
        window['-STATUS-'].update("Add button clicked")
    elif event == '-EDIT-':
        window['-STATUS-'].update("Edit button clicked")
    elif event == '-DELETE-':
        window['-STATUS-'].update("Delete button clicked")
    elif event == '-REFRESH-':
        window['-STATUS-'].update("Refresh button clicked")
    elif event == '-TABLE-':
        row = values['-TABLE-'][0] if values['-TABLE-'] else None
        window['-STATUS-'].update(f"Selected row: {row}")

window.close()
