# Kenneth Lipke
# 3/27/2018
# Popup.py

"""
Containts Popup class, which makes a popup window for use with the gui
"""

import tkinter as tk

class Popup:
	"""
	Popup window, only for use with other tkinter program that 
	has its own mainloop running
	"""


	def __init__(self, message, title="Warning"):
		"""
		Creates a popup window, displaying a message,
		with an optional title (for the window)
		"""
		# Create window
		win = tk.Toplevel()
		win.wm_title(title)
		#win.geometry("200x100")

		# Create Label with messages
		l = tk.Label(win, text=message)
		l.pack()

		# Create button to close
		b = tk.Button(win, text="Okay", command=win.destroy)
		b.pack(pady=10)

