#!/usr/bin/python3

import os
import sys
import signal
import json
import shutil

from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QSizePolicy, QAction,
    QFormLayout, QLineEdit, QPushButton, QVBoxLayout, QHBoxLayout, 
    QFileDialog, QMessageBox, QComboBox, QLabel
)
from PyQt5.QtCore import Qt, QUrl
from PyQt5.QtGui import QIcon, QDesktopServices

import simple_project_generator.about as about
import simple_project_generator.modules.configure as configure
from simple_project_generator.modules.resources import resource_path

from simple_project_generator.modules.wabout import show_about_window
from simple_project_generator.desktop import (
    create_desktop_file,
    create_desktop_directory,
    create_desktop_menu
)

from simple_project_generator.modules.project_generator import (
    extract_zip_to_temp,
    generate_project
)

# ---------- Path to config file ----------
CONFIG_PATH = os.path.join(
    os.path.expanduser("~"),
    ".config",
    about.__package__,
    "config.json"
)

# ---------- DEFAULT CONFIG (REORDERED) ----------
DEFAULT_CONTENT = {

    # ---------------- Toolbar ----------------
    "toolbar_save": "Save Config",
    "toolbar_save_tooltip": "Save current form as project config file",

    "toolbar_load": "Load Config",
    "toolbar_load_tooltip": "Load previously saved project config file",

    "toolbar_configure": "Configure",
    "toolbar_configure_tooltip": "Open configuration file",

    "toolbar_about": "About",
    "toolbar_about_tooltip": "About the program",

    "toolbar_coffee": "Coffee",
    "toolbar_coffee_tooltip": "Buy me a coffee (TrucomanX)",


    # ---------------- Labels ----------------
    "label_template": "Template:",
    "label_output_dir": "Output directory:",


    # ---------------- Buttons ----------------
    "button_generate": "Generate Project",
    "button_generate_tooltip": "Generate project using selected template",

    "button_browse": "Browse",
    "button_browse_tooltip": "Select output directory",


    # ---------------- Placeholders ----------------
    "placeholder_output_dir": "Select output directory...",


    # ---------------- Tooltips (Main Fields) ----------------
    "tooltip_template_selector": "Select a template to generate the project from",
    "tooltip_output_dir_input": "Directory where the project will be created",


    # ---------------- Field Map Text Config ----------------
    "fields": {
        "{MODULE_NAME}": {
            "label": "Module name:",
            "placeholder": "example_module",
            "tooltip": "Python module/package name (lowercase, no spaces)"
        },
        "{PROGRAM_NAME}": {
            "label": "Program name:",
            "placeholder": "my-awesome-program",
            "tooltip": "The program name used when called from the system"
        },
        "{AUTHOR_NAME}": {
            "label": "Author name:",
            "placeholder": "John Doe",
            "tooltip": "Full author name"
        },
        "{AUTHOR_EMAIL}": {
            "label": "Author email:",
            "placeholder": "john@example.com",
            "tooltip": "Contact email address"
        },
        "{SUMMARY}": {
            "label": "Summary:",
            "placeholder": "Short description of the project",
            "tooltip": "One-line summary used in metadata"
        },
        "{REPOSITORY_PAGE}": {
            "label": "Repository page:",
            "placeholder": "https://github.com/trucomanx",
            "tooltip": "Repository URL"
        },
        "{REPOSITORY_NAME}": {
            "label": "Repository name:",
            "placeholder": "MyAwesomeProgram",
            "tooltip": "Repository short name, this is used to generate https://github.com/trucomanx/MyAwesomeProgram"
        },
        "{FUNDING_PAGE}": {
            "label": "Funding page:",
            "placeholder": "https://trucomanx.github.io/en/funding.html",
            "tooltip": "Funding or sponsorship URL"
        },
        "{BUY_ME_A_COFFEE}": {
            "label": "Buy me a coffee URL:",
            "placeholder": "https://ko-fi.com/trucomanx",
            "tooltip": "Coffee donation page"
        },
        "{REPOSITORY_RAW_PAGE}": {
            "label": "Repository raw page:",
            "placeholder": "https://raw.githubusercontent.com/trucomanx",
            "tooltip": "Raw content base URL"
        }
    },


    # ---------------- Messages ----------------
    "msg_success": "Project generated successfully!",
    "msg_extract_error": "Failed to extract template",
    "msg_invalid_template": "Invalid template selected",


    # ---------------- Window ----------------
    "window_width": 800,
    "window_height": 600
}

configure.verify_default_config(CONFIG_PATH, default_content=DEFAULT_CONTENT)
CONFIG = configure.load_config(CONFIG_PATH)


# ============================================================
# MAIN WINDOW
# ============================================================

class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()

        self.setWindowTitle(about.__program_name__)
        self.resize(CONFIG["window_width"], CONFIG["window_height"])

        self.icon_path = resource_path("icons", "logo.png")
        self.setWindowIcon(QIcon(self.icon_path))

        self.template_map = {
            "GUI pyqt5 template 1": resource_path("data", "pyqt5_project_template_1.zip"),
            "CMD template 1": resource_path("data", "pyqt5_project_template_1.zip")
        }

        self._create_toolbar()
        self._generate_ui()

    # ============================================================
    # UI
    # ============================================================

    def _generate_ui(self):

        central_widget = QWidget()
        layout = QVBoxLayout()
        form_layout = QFormLayout()

        # ---------------- Template selector ----------------
        self.template_selector = QComboBox()
        for keyname in self.template_map:
            self.template_selector.addItem(keyname)

        self.template_selector.setToolTip(CONFIG["tooltip_template_selector"])

        form_layout.addRow(CONFIG["label_template"], self.template_selector)

        # ---------------- Output directory ----------------
        output_widget = QWidget()
        output_layout = QHBoxLayout()
        output_layout.setContentsMargins(0, 0, 0, 0)

        self.output_dir_input = QLineEdit()
        self.output_dir_input.setPlaceholderText(CONFIG["placeholder_output_dir"])
        self.output_dir_input.setToolTip(CONFIG["tooltip_output_dir_input"])

        self.output_browse_button = QPushButton(CONFIG["button_browse"])
        self.output_browse_button.setIcon(QIcon.fromTheme("folder-open"))
        self.output_browse_button.setFixedWidth(110)
        self.output_browse_button.setToolTip(CONFIG["button_browse_tooltip"])
        self.output_browse_button.clicked.connect(self.select_output_directory)

        output_layout.addWidget(self.output_dir_input)
        output_layout.addWidget(self.output_browse_button)

        output_widget.setLayout(output_layout)

        form_layout.addRow(CONFIG["label_output_dir"], output_widget)
        
        form_layout.addRow(" ", None)

        # ---------------- Dynamic fields ----------------
        self.fields = {}

        for key, field_data in CONFIG["fields"].items():

            line = QLineEdit()
            line.setPlaceholderText(field_data["placeholder"])
            line.setToolTip(field_data["tooltip"])

            form_layout.addRow(field_data["label"], line)
            self.fields[key] = line

        # ---------------- Generate button ----------------
        self.generate_button = QPushButton(CONFIG["button_generate"])
        self.generate_button.setToolTip(CONFIG["button_generate_tooltip"])
        self.generate_button.clicked.connect(self.on_generate_clicked)

        layout.addLayout(form_layout)
        layout.addWidget(self.generate_button)

        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    # ============================================================
    # Toolbar
    # ============================================================

    def _create_toolbar(self):

        self.toolbar = self.addToolBar("Main")
        self.toolbar.setToolButtonStyle(Qt.ToolButtonTextUnderIcon)

        # ---------------- Save ----------------
        self.save_action = QAction(
            QIcon.fromTheme("document-save"),
            CONFIG["toolbar_save"],
            self
        )
        self.save_action.setToolTip(CONFIG["toolbar_save_tooltip"])
        self.save_action.triggered.connect(self.save_config_json)
        self.toolbar.addAction(self.save_action)

        # ---------------- Load ----------------
        self.load_action = QAction(
            QIcon.fromTheme("document-open"),
            CONFIG["toolbar_load"],
            self
        )
        self.load_action.setToolTip(CONFIG["toolbar_load_tooltip"])
        self.load_action.triggered.connect(self.load_config_json)
        self.toolbar.addAction(self.load_action)

        # Spacer
        spacer = QWidget()
        spacer.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.toolbar.addWidget(spacer)

        # ---------------- Configure ----------------
        configure_action = QAction(
            QIcon.fromTheme("document-properties"),
            CONFIG["toolbar_configure"],
            self
        )
        configure_action.setToolTip(CONFIG["toolbar_configure_tooltip"])
        configure_action.triggered.connect(self.open_configure_editor)
        self.toolbar.addAction(configure_action)

        # ---------------- About ----------------
        about_action = QAction(
            QIcon.fromTheme("help-about"),
            CONFIG["toolbar_about"],
            self
        )
        about_action.setToolTip(CONFIG["toolbar_about_tooltip"])
        about_action.triggered.connect(self.open_about)
        self.toolbar.addAction(about_action)

        # ---------------- Coffee ----------------
        coffee_action = QAction(
            QIcon.fromTheme("emblem-favorite"),
            CONFIG["toolbar_coffee"],
            self
        )
        coffee_action.setToolTip(CONFIG["toolbar_coffee_tooltip"])
        coffee_action.triggered.connect(self.on_coffee_action_click)
        self.toolbar.addAction(coffee_action)

    # ============================================================
    # Logic (rest unchanged)
    # ============================================================

    def select_output_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self,
            CONFIG["label_output_dir"]
        )
        if directory:
            self.output_dir_input.setText(directory)

    # ============================================================
    # Generator
    # ============================================================

    def on_generate_clicked(self):

        selected_template = self.template_selector.currentText()
        template_path = self.template_map.get(selected_template)

        if not template_path:
            QMessageBox.warning(self, "Error", CONFIG["msg_invalid_template"])
            return

        # ---------------- Clean + Validate fields ----------------
        replacements = {}
        empty_fields = []

        for key, field in self.fields.items():
            value = field.text().strip()

            if not value:
                empty_fields.append(CONFIG["fields"][key]["label"])

            replacements[key] = value

        if empty_fields:
            QMessageBox.warning(
                self,
                "Missing fields",
                "The following fields cannot be empty:\n\n"
                + "\n".join(empty_fields)
            )
            return

        # ---------------- Validate output directory ----------------
        output_dir = self.output_dir_input.text().strip()

        if not output_dir:
            QMessageBox.warning(
                self,
                "Missing output directory",
                "Please select an output directory."
            )
            return

        if not os.path.isdir(output_dir):
            QMessageBox.warning(
                self,
                "Invalid directory",
                "The selected output directory is not valid."
            )
            return

        # ---------------- Extract template ----------------
        temp_path = extract_zip_to_temp(template_path)

        if not temp_path:
            QMessageBox.critical(self, "Error", CONFIG["msg_extract_error"])
            return

        try:
            generate_project(
                template_dir=temp_path,
                output_dir=output_dir,
                replacements=replacements,
                replace_extensions=["*.py", "*.md", "*.sh"],
                overwrite=True
            )

            QMessageBox.information(self, "Success", CONFIG["msg_success"])

        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))

        finally:
            shutil.rmtree(temp_path, ignore_errors=True)


    # ---------------- Save / Load ----------------

    def save_config_json(self):

        path, _ = QFileDialog.getSaveFileName(
            self,
            CONFIG["toolbar_save"],
            "",
            "MyProject Config (*.myproject.json)"
        )

        if not path:
            return

        if not path.endswith(".myproject.json"):
            path += ".myproject.json"

        data = {
            "template": self.template_selector.currentText(),
            "output_dir": self.output_dir_input.text(),
            "replacements": {
                key: field.text()
                for key, field in self.fields.items()
            }
        }

        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def load_config_json(self):

        path, _ = QFileDialog.getOpenFileName(
            self,
            CONFIG["toolbar_load"],
            "",
            "MyProject Config (*.myproject.json)"
        )

        if not path:
            return

        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.template_selector.setCurrentText(data.get("template", ""))
        self.output_dir_input.setText(data.get("output_dir", ""))

        replacements = data.get("replacements", {})
        for key, value in replacements.items():
            if key in self.fields:
                self.fields[key].setText(value)

    # ============================================================
    # Misc
    # ============================================================

    def open_configure_editor(self):
        if os.name == 'nt':
            os.startfile(CONFIG_PATH)
        else:
            os.system(f'xdg-open "{CONFIG_PATH}"')

    def open_about(self):
        data = {
            "version": about.__version__,
            "package": about.__package__,
            "program_name": about.__program_name__,
            "author": about.__author__,
            "email": about.__email__,
            "description": about.__description__,
            "url_source": about.__url_source__,
            "url_doc": about.__url_doc__,
            "url_funding": about.__url_funding__,
            "url_bugs": about.__url_bugs__
        }
        show_about_window(data, self.icon_path)

    def on_coffee_action_click(self):
        QDesktopServices.openUrl(QUrl("https://ko-fi.com/trucomanx"))


# ============================================================
# Main
# ============================================================

def main():
    signal.signal(signal.SIGINT, signal.SIG_DFL)

    create_desktop_directory()    
    create_desktop_menu()
    create_desktop_file(os.path.join("~",".local","share","applications"), 
                        program_name=about.__program_name__)
    
    for n in range(len(sys.argv)):
        if sys.argv[n] == "--autostart":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".config","autostart"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
        if sys.argv[n] == "--applications":
            create_desktop_directory(overwrite = True)
            create_desktop_menu(overwrite = True)
            create_desktop_file(os.path.join("~",".local","share","applications"), 
                                overwrite=True, 
                                program_name=about.__program_name__)
            return
    
    app = QApplication(sys.argv)
    app.setApplicationName(about.__package__)

    window = MainWindow()
    window.show()

    sys.exit(app.exec_())


if __name__ == "__main__":
    main()

