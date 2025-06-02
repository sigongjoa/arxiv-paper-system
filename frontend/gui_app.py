import tkinter as tk
from tkinter import ttk
import sys
import os

# 프로젝트 루트를 sys.path에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

from frontend.gui.main_window import ArxivToShortsGUI

def main():
    root = tk.Tk()
    app = ArxivToShortsGUI(root)
    root.mainloop()

if __name__ == "__main__":
    main()
