import sys
import json
import os
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QMenu, QInputDialog, QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

class DanaOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Настройки по умолчанию
        self.config_file = "settings.json"
        self.work_time = 1500 
        self.pause_time = 300  
        self.total_rounds = 10
        self.scale_factor = 1.0
        
        # Загружаем сохраненные настройки, если они есть
        self.load_settings()
        
        self.current_round = 1
        self.time_left = self.work_time
        self.is_work_phase = True
        self.is_running = False

        self.init_ui()

    def load_settings(self):
        """Загрузка настроек из JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r") as f:
                    data = json.load(f)
                    self.work_time = data.get("work_time", 1500)
                    self.pause_time = data.get("pause_time", 300)
                    self.total_rounds = data.get("total_rounds", 10)
                    self.scale_factor = data.get("scale_factor", 1.0)
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Сохранение настроек в JSON"""
        try:
            data = {
                "work_time": self.work_time,
                "pause_time": self.pause_time,
                "total_rounds": self.total_rounds,
                "scale_factor": self.scale_factor
            }
            with open(self.config_file, "w") as f:
                json.dump(data, f, indent=4)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | 
                            Qt.WindowType.WindowStaysOnTopHint | 
                            Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(5, 5, 5, 5)
        
        self.content_frame = QFrame()
        self.layout = QVBoxLayout(self.content_frame)
        self.layout.setSpacing(0)
        
        self.label_status = QLabel("")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.label_time = QLabel("START")
        self.label_time.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.shadow = QGraphicsDropShadowEffect()
        self.shadow.setColor(QColor(0, 0, 0, 255))
        self.shadow.setOffset(0, 0)
        self.label_time.setGraphicsEffect(self.shadow)

        self.layout.addWidget(self.label_status)
        self.layout.addWidget(self.label_time)
        self.main_layout.addWidget(self.content_frame)

        self.timer = QTimer()
        self.timer.timeout.connect(self.update_timer)

        self.update_styles()
        self.setFixedSize(int(500 * self.scale_factor), int(160 * self.scale_factor))
        self.show()

    def format_time(self, seconds):
        if seconds < 60:
            return str(seconds)
        h = seconds // 3600
        m = (seconds % 3600) // 60
        s = seconds % 60
        if h > 0:
            return f"{h:02}:{m:02}:{s:02}"
        return f"{m:02}:{s:02}"

    def update_styles(self):
        s = self.scale_factor
        status_size = int(16 * s)
        display_text = self.label_time.text()
        
        if ":" in display_text:
            fs = int(75 * s) if len(display_text) <= 5 else int(55 * s)
        elif display_text.isdigit():
            fs = int(90 * s)
        else:
            fs = int(55 * s)
            
        time_color = "white"
        if self.is_running:
            time_color = "#27ae60" if self.is_work_phase else "#e67e22"

        self.label_status.setStyleSheet(f"color: {time_color}; font-size: {status_size}px; font-weight: bold; font-family: 'Segoe UI';")
        self.label_time.setStyleSheet(f"color: {time_color}; font-size: {fs}px; font-weight: 900; font-family: 'Arial Black';")
        self.shadow.setBlurRadius(max(3, int(15 * s)))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor = min(3.0, self.scale_factor + 0.1)
        else:
            self.scale_factor = max(0.4, self.scale_factor - 0.1)
        
        self.setFixedSize(int(500 * self.scale_factor), int(160 * self.scale_factor))
        self.update_styles()
        self.save_settings() # Сохраняем масштаб

    def show_time_dialog(self, title, is_work):
        units = ["Seconds", "Minutes", "Hours"]
        unit, ok_u = QInputDialog.getItem(self, title, "Select Unit:", units, 1, False)
        if ok_u:
            max_val = 3600 if unit == "Seconds" else 1440
            val, ok_v = QInputDialog.getInt(self, title, f"Enter {unit}:", 1, 1, max_val)
            if ok_v:
                seconds = val
                if unit == "Minutes": seconds = val * 60
                elif unit == "Hours": seconds = val * 3600
                
                if is_work: self.work_time = seconds
                else: self.pause_time = seconds
                
                self.stop_timer()
                self.save_settings() # Сохраняем новое время

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.label_time.setText(self.format_time(self.time_left))
            self.update_styles()
        else:
            self.switch_phase()

    def switch_phase(self):
        if self.is_work_phase:
            self.is_work_phase = False
            self.time_left = self.pause_time
            self.label_status.setText(f"PAUSE {self.current_round}/{self.total_rounds}")
        else:
            self.is_work_phase = True
            self.current_round += 1
            if self.current_round <= self.total_rounds:
                self.time_left = self.work_time
                self.label_status.setText(f"WORK {self.current_round}/{self.total_rounds}")
            else:
                self.stop_timer()
                self.label_status.setText("COMPLETED")
                self.label_time.setText("FINISH")
                return
        self.label_time.setText(self.format_time(self.time_left))
        self.update_styles()

    def start_timer(self):
        self.is_running = True
        self.current_round = 1
        self.is_work_phase = True
        self.time_left = self.work_time
        self.label_status.setText(f"WORK {self.current_round}/{self.total_rounds}")
        self.label_time.setText(self.format_time(self.time_left))
        self.update_styles()
        self.timer.start(1000)

    def stop_timer(self):
        self.timer.stop()
        self.is_running = False
        self.label_time.setText("START")
        self.label_status.setText("")
        self.update_styles()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu { background: #1e1e1e; color: white; border: 1px solid #444; padding: 5px; }
            QMenu::item:selected { background: #0078d4; }
        """)
        
        act_start = menu.addAction("▶ Start")
        act_stop = menu.addAction("⏹ Stop")
        menu.addSeparator()
        
        act_work = menu.addAction("⏱ Set Work Time")
        act_pause = menu.addAction("☕ Set Pause Time")
        act_rounds = menu.addAction("🔄 Set Total Rounds")
        
        menu.addSeparator()
        act_exit = menu.addAction("❌ Exit")

        action = menu.exec(self.mapToGlobal(event.pos()))
        
        if action == act_work: self.show_time_dialog("Work Time", True)
        elif action == act_pause: self.show_time_dialog("Pause Time", False)
        elif action == act_rounds:
            val, ok = QInputDialog.getInt(self, "Rounds", "Total Rounds:", self.total_rounds, 1, 999)
            if ok: 
                self.total_rounds = val
                self.stop_timer()
                self.save_settings() # Сохраняем раунды
        elif action == act_start: self.start_timer()
        elif action == act_stop: self.stop_timer()
        elif action == act_exit: QApplication.quit()

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.dragPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.MouseButton.LeftButton:
            self.move(self.pos() + event.globalPosition().toPoint() - self.dragPos)
            self.dragPos = event.globalPosition().toPoint()

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if not self.is_running: self.start_timer()
            else: self.stop_timer()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = DanaOverlay()
    sys.exit(app.exec())