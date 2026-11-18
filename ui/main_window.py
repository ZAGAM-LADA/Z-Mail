from pathlib import Path
from PySide6.QtCore import QThread, Signal
from PySide6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel,
    QPushButton, QStackedWidget, QGridLayout, QFileDialog, QMessageBox,
    QProgressBar, QLineEdit, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox
)
from app.config import ensure_dirs, DB_PATH, EXPORT_DIR
from database.db_manager import Database
from core.local_scanner import scan_folder, discover_thunderbird_profiles
from core.exporter import export_eml, export_attachments
from reports.report_generator import write_json_report
from .styles import DARK, LIGHT

class ScanWorker(QThread):
    progress = Signal(int, int, int, str)
    finished_scan = Signal(int, int, int)
    failed = Signal(str)

    def __init__(self, root, db):
        super().__init__()
        self.root = root
        self.db = db
        self._cancel_requested = False

    def cancel(self):
        self._cancel_requested = True

    def run(self):
        try:
            result = scan_folder(
                self.root, self.db,
                progress=lambda seen, added, errors, path:
                    self.progress.emit(seen, added, errors, path),
                cancelled=lambda: self._cancel_requested
            )
            self.finished_scan.emit(*result)
        except Exception as exc:
            self.failed.emit(f"{type(exc).__name__}: {exc}")
            self.finished_scan.emit(0, 0, 1)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        ensure_dirs()
        self.db = Database(DB_PATH)
        self.worker = None
        self.current_root = ""
        self.dark = True
        self.setWindowTitle("Z-MAIL RECOVERY — Premium Edition")
        self.resize(1260, 780)
        self.setMinimumSize(980, 640)
        self._build()
        self.apply_theme()
        self.refresh_dashboard()
        self.refresh_results()

    def _build(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QHBoxLayout(central)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(235)
        side_layout = QVBoxLayout(sidebar)
        side_layout.setContentsMargins(16, 22, 16, 16)
        brand = QLabel("Z-MAIL")
        brand.setObjectName("Brand")
        subtitle = QLabel("RECOVERY  /  PREMIUM")
        subtitle.setObjectName("Muted")
        side_layout.addWidget(brand)
        side_layout.addWidget(subtitle)
        side_layout.addSpacing(24)

        self.stack = QStackedWidget()
        for label, index in [
            ("Dashboard", 0), ("Local Recovery", 1), ("Advanced Search", 2),
            ("Export Center", 3), ("Reports", 4), ("Settings", 5)
        ]:
            button = QPushButton(label)
            button.setObjectName("Nav")
            button.clicked.connect(lambda checked=False, i=index: self.stack.setCurrentIndex(i))
            side_layout.addWidget(button)
        side_layout.addStretch()
        foot = QLabel("LOCAL-FIRST INVESTIGATION\\nOriginal sources are not modified.")
        foot.setObjectName("Muted")
        foot.setWordWrap(True)
        side_layout.addWidget(foot)

        layout.addWidget(sidebar)
        layout.addWidget(self.stack, 1)
        self._dashboard_page()
        self._recovery_page()
        self._search_page()
        self._export_page()
        self._reports_page()
        self._settings_page()

    def _page(self, title, subtitle):
        widget = QWidget()
        vertical = QVBoxLayout(widget)
        vertical.setContentsMargins(28, 24, 28, 24)
        vertical.setSpacing(16)
        heading = QLabel(title)
        heading.setStyleSheet("font-size:22pt;font-weight:800;")
        description = QLabel(subtitle)
        description.setObjectName("Muted")
        description.setWordWrap(True)
        vertical.addWidget(heading)
        vertical.addWidget(description)
        self.stack.addWidget(widget)
        return widget, vertical

    def _dashboard_page(self):
        _, vertical = self._page(
            "Investigation Dashboard",
            "A live overview of authentic messages indexed from accessible local sources."
        )
        grid = QGridLayout()
        self.cards = {}
        card_specs = [
            ("messages", "Emails indexed"),
            ("sources", "Source files"),
            ("attachments", "Attachments found"),
            ("duplicates", "Duplicate source copies"),
        ]
        for index, (key, title) in enumerate(card_specs):
            card = QFrame()
            card.setObjectName("Card")
            card_layout = QVBoxLayout(card)
            value = QLabel("0")
            value.setStyleSheet("font-size:26pt;font-weight:800;")
            caption = QLabel(title)
            caption.setObjectName("Muted")
            card_layout.addWidget(value)
            card_layout.addWidget(caption)
            grid.addWidget(card, index // 2, index % 2)
            self.cards[key] = value
        vertical.addLayout(grid)
        warning = QLabel(
            "Important: messages permanently erased from Gmail's servers cannot be fetched "
            "by this local tool. This build searches local mail copies and archives."
        )
        warning.setWordWrap(True)
        warning.setObjectName("Muted")
        vertical.addWidget(warning)
        start = QPushButton("Open Local Investigation")
        start.setObjectName("Primary")
        start.clicked.connect(lambda: self.stack.setCurrentIndex(1))
        vertical.addWidget(start)
        vertical.addStretch()

    def _recovery_page(self):
        _, vertical = self._page(
            "Local Recovery",
            "Inspect a chosen folder for EML and MBOX messages. The source files are read-only."
        )
        row = QHBoxLayout()
        self.path_label = QLabel("No folder selected")
        self.path_label.setObjectName("Muted")
        choose = QPushButton("Choose Folder")
        choose.clicked.connect(self.choose_folder)
        self.scan_button = QPushButton("Start Scan")
        self.scan_button.setObjectName("Primary")
        self.scan_button.clicked.connect(self.start_scan)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self.stop_scan)
        row.addWidget(self.path_label, 1)
        row.addWidget(choose)
        row.addWidget(self.scan_button)
        row.addWidget(self.stop_button)
        vertical.addLayout(row)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        vertical.addWidget(self.progress)
        self.scan_status = QLabel("Ready.")
        self.scan_status.setObjectName("Muted")
        self.scan_status.setWordWrap(True)
        vertical.addWidget(self.scan_status)

        profiles = discover_thunderbird_profiles()
        text = "Detected Thunderbird profiles:\\n"
        text += "\\n".join(str(profile) for profile in profiles) if profiles else "No standard Linux Thunderbird profile detected."
        profile_label = QLabel(text)
        profile_label.setObjectName("Muted")
        profile_label.setWordWrap(True)
        vertical.addWidget(profile_label)
        vertical.addStretch()

    def _search_page(self):
        _, vertical = self._page(
            "Advanced Search",
            "Search messages actually extracted and indexed. Up to 500 results are shown."
        )
        row = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search sender, recipient, subject or message body…")
        self.search_input.returnPressed.connect(self.refresh_results)
        search_button = QPushButton("Search")
        search_button.setObjectName("Primary")
        search_button.clicked.connect(self.refresh_results)
        row.addWidget(self.search_input, 1)
        row.addWidget(search_button)
        vertical.addLayout(row)

        self.table = QTableWidget(0, 7)
        self.table.setHorizontalHeaderLabels(
            ["ID", "Sender", "Recipient", "Subject", "Date", "Source", "Status"]
        )
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setAlternatingRowColors(True)
        vertical.addWidget(self.table, 1)
        self.result_label = QLabel("0 results")
        self.result_label.setObjectName("Muted")
        vertical.addWidget(self.result_label)

    def _export_page(self):
        _, vertical = self._page(
            "Export Center",
            "Select a row in Advanced Search, then export the message or its MIME attachments."
        )
        note = QLabel(
            "Exports are written only to the destination you choose. Existing files are not overwritten."
        )
        note.setWordWrap(True)
        note.setObjectName("Muted")
        vertical.addWidget(note)
        eml_button = QPushButton("Export Selected Message as EML")
        eml_button.setObjectName("Primary")
        eml_button.clicked.connect(self.export_selected)
        attachment_button = QPushButton("Extract Selected Message Attachments")
        attachment_button.clicked.connect(self.attach_selected)
        vertical.addWidget(eml_button)
        vertical.addWidget(attachment_button)
        vertical.addStretch()

    def _reports_page(self):
        _, vertical = self._page(
            "Investigation Reports",
            "Create a portable JSON report containing source paths, message metadata and scan statistics."
        )
        button = QPushButton("Generate JSON Report")
        button.setObjectName("Primary")
        button.clicked.connect(self.generate_report)
        vertical.addWidget(button)
        vertical.addStretch()

    def _settings_page(self):
        _, vertical = self._page(
            "Settings",
            "Appearance and local application data. Gmail connection is planned for Phase 2."
        )
        row = QHBoxLayout()
        row.addWidget(QLabel("Appearance"))
        self.theme_box = QComboBox()
        self.theme_box.addItems(["Premium Dark", "Premium Light"])
        self.theme_box.currentIndexChanged.connect(lambda index: self.set_theme(index == 0))
        row.addWidget(self.theme_box)
        row.addStretch()
        vertical.addLayout(row)
        location = QLabel(
            f"Database: {self.db.path}\\n"
            f"Default exports: {EXPORT_DIR}\\n"
            "Phase 1 processes local files on this computer."
        )
        location.setObjectName("Muted")
        location.setWordWrap(True)
        vertical.addWidget(location)
        vertical.addStretch()

    def apply_theme(self):
        self.setStyleSheet(DARK if self.dark else LIGHT)

    def set_theme(self, dark):
        self.dark = bool(dark)
        self.apply_theme()

    def refresh_dashboard(self):
        counts = self.db.counts()
        for key, value in counts.items():
            self.cards[key].setText(f"{value:,}")

    def choose_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Choose folder to investigate", str(Path.home()))
        if folder:
            self.current_root = folder
            self.path_label.setText(folder)

    def start_scan(self):
        if not self.current_root:
            QMessageBox.information(self, "Choose a folder", "Select a folder before starting an investigation.")
            return
        if self.worker and self.worker.isRunning():
            return
        self.progress.setVisible(True)
        self.scan_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.scan_status.setText("Scanning selected folder…")
        self.worker = ScanWorker(self.current_root, self.db)
        self.worker.progress.connect(self.on_progress)
        self.worker.finished_scan.connect(self.on_scan_finished)
        self.worker.failed.connect(self.on_scan_failed)
        self.worker.start()

    def stop_scan(self):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.scan_status.setText("Cancellation requested. Finishing the current file safely…")

    def on_progress(self, seen, added, errors, current_path):
        self.scan_status.setText(
            f"Files inspected: {seen} | New messages indexed: {added} | Errors: {errors}\\n"
            f"Current file: {current_path}"
        )

    def on_scan_failed(self, message):
        self.scan_status.setText(f"Investigation stopped because of an error: {message}")

    def on_scan_finished(self, seen, added, errors):
        self.progress.setVisible(False)
        self.scan_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.scan_status.setText(
            f"Finished. Files inspected: {seen}; new messages indexed: {added}; errors: {errors}."
        )
        self.refresh_dashboard()
        self.refresh_results()
        QMessageBox.information(
            self, "Investigation complete",
            f"Files inspected: {seen}\\nNew messages indexed: {added}\\nErrors: {errors}"
        )

    def refresh_results(self):
        if not hasattr(self, "table"):
            return
        query = self.search_input.text() if hasattr(self, "search_input") else ""
        rows = self.db.search(query)
        self.table.setRowCount(len(rows))
        for row_index, row in enumerate(rows):
            values = [
                row["id"], row["sender"], row["recipient"], row["subject"],
                row["date_text"], row["source_path"], row["status"]
            ]
            for col_index, value in enumerate(values):
                self.table.setItem(row_index, col_index, QTableWidgetItem(str(value or "")))
        self.result_label.setText(f"{len(rows)} results")

    def selected_message_id(self):
        selected = self.table.selectionModel().selectedRows()
        if not selected:
            return None
        item = self.table.item(selected[0].row(), 0)
        return int(item.text()) if item else None

    def export_selected(self):
        message_id = self.selected_message_id()
        if message_id is None:
            QMessageBox.information(self, "Select a message", "Select a message in Advanced Search first.")
            return
        destination = QFileDialog.getExistingDirectory(self, "Choose export folder", str(EXPORT_DIR))
        if destination:
            path = export_eml(self.db.get(message_id), destination)
            QMessageBox.information(self, "Export complete", f"Saved message to:\\n{path}")

    def attach_selected(self):
        message_id = self.selected_message_id()
        if message_id is None:
            QMessageBox.information(self, "Select a message", "Select a message in Advanced Search first.")
            return
        destination = QFileDialog.getExistingDirectory(self, "Choose attachment folder", str(EXPORT_DIR))
        if destination:
            paths = export_attachments(self.db.get(message_id), destination)
            QMessageBox.information(self, "Attachment extraction", f"Extracted {len(paths)} attachment(s).")

    def generate_report(self):
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save investigation report", "zmail-investigation.json", "JSON files (*.json)"
        )
        if filename:
            write_json_report(self.db, filename, self.current_root or "Not specified")
            QMessageBox.information(self, "Report generated", f"Saved report to:\\n{filename}")

    def closeEvent(self, event):
        if self.worker and self.worker.isRunning():
            self.worker.cancel()
            self.worker.wait()
        self.db.close()
        event.accept()
