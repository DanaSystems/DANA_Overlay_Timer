import sys
import json
import os
import ctypes
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QMenu, QInputDialog, QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, QTimer, QPoint
from PyQt6.QtGui import QColor

class DanaOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        # Настройки
        self.config_file = "settings.json"
        self.work_time = 1500 
        self.pause_time = 300  
        self.total_rounds = 10
        self.scale_factor = 1.0
        self.window_pos = None
        
        # Загружаем сохраненные настройки
        self.load_settings()
        
        self.current_round = 1
        self.time_left = self.work_time
        self.is_work_phase = True
        self.is_running = False

        self.init_ui()

    def set_file_hidden(self, filepath):
        """Делает файл скрытым в Windows"""
        if os.name == 'nt':
            try:
                # Атрибут 0x02 — скрытый файл
                ctypes.windll.kernel32.SetFileAttributesW(filepath, 0x02)
            except Exception:
                pass

    def load_settings(self):
        """Загрузка настроек из JSON"""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.work_time = data.get("work_time", 1500)
                    self.pause_time = data.get("pause_time", 300)
                    self.total_rounds = data.get("total_rounds", 10)
                    self.scale_factor = data.get("scale_factor", 1.0)
                    pos_raw = data.get("window_pos")
                    if pos_raw:
                        self.window_pos = QPoint(pos_raw[0], pos_raw[1])
            except Exception as e:
                print(f"Error loading settings: {e}")

    def save_settings(self):
        """Сохранение настроек в JSON и скрытие файла"""
        try:
            data = {
                "work_time": self.work_time,
                "pause_time": self.pause_time,
                "total_rounds": self.total_rounds,
                "scale_factor": self.scale_factor,
                "window_pos": [self.pos().x(), self.pos().y()]
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4)
            
            self.set_file_hidden(self.config_file)
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
        
        # Восстанавливаем позицию, если она была сохранена
        if self.window_pos:
            self.move(self.window_pos)
            
        self.show()

    def format_time(self, seconds):
        if seconds < 60: return str(seconds)
        h, m = divmod(seconds, 3600)
        m, s = divmod(m, 60)
        return f"{h:02}:{m:02}:{s:02}" if h > 0 else f"{m:02}:{s:02}"

    def update_styles(self):
        s = self.scale_factor
        display_text = self.label_time.text()
        fs = int(75 * s) if ":" in display_text else int(90 * s)
        if len(display_text) > 5: fs = int(55 * s)
            
        time_color = "white"
        if self.is_running:
            time_color = "#27ae60" if self.is_work_phase else "#e67e22"

        self.label_status.setStyleSheet(f"color: {time_color}; font-size: {int(16*s)}px; font-weight: bold;")
        self.label_time.setStyleSheet(f"color: {time_color}; font-size: {fs}px; font-weight: 900; font-family: 'Arial Black';")
        self.shadow.setBlurRadius(max(3, int(15 * s)))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        self.scale_factor = min(3.0, max(0.4, self.scale_factor + (0.1 if delta > 0 else -0.1)))
        self.setFixedSize(int(500 * self.scale_factor), int(160 * self.scale_factor))
        self.update_styles()
        self.save_settings()

    def show_time_dialog(self, title, is_work):
        units = ["Seconds", "Minutes", "Hours"]
        unit, ok_u = QInputDialog.getItem(self, title, "Select Unit:", units, 1, False)
        if ok_u:
            val, ok_v = QInputDialog.getInt(self, title, f"Enter {unit}:", 1, 1, 3600)
            if ok_v:
                sec = val * (60 if unit == "Minutes" else 3600 if unit == "Hours" else 1)
                if is_work: self.work_time = sec
                else: self.pause_time = sec
                self.stop_timer()
                self.save_settings()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.label_time.setText(self.format_time(self.time_left))
            self.update_styles()
        else:
            self.switch_phase()

    def switch_phase(self):
        if self.is_work_phase:
            self.is_work_phase, self.time_left = False, self.pause_time
            self.label_status.setText(f"PAUSE {self.current_round}/{self.total_rounds}")
        else:
            self.is_work_phase, self.current_round = True, self.current_round + 1
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
        self.is_running, self.current_round, self.is_work_phase = True, 1, True
        self.time_left = self.work_time
        self.label_status.setText(f"WORK 1/{self.total_rounds}")
        self.label_time.setText(self.format_time(self.time_left))
        self.timer.start(1000)
        self.update_styles()

    def stop_timer(self):
        self.timer.stop()
        self.is_running = False
        self.label_time.setText("START")
        self.label_status.setText("")
        self.update_styles()

    def contextMenuEvent(self, event):
        menu = QMenu(self)
        menu.setStyleSheet("QMenu { background: #1e1e1e; color: white; border: 1px solid #444; } QMenu::item:selected { background: #0078d4; }")
        act_start, act_stop = menu.addAction("▶ Start"), menu.addAction("⏹ Stop")
        menu.addSeparator()
        act_work, act_pause = menu.addAction("⏱ Set Work Time"), menu.addAction("☕ Set Pause Time")
        act_rounds, act_exit = menu.addAction("🔄 Set Total Rounds"), menu.addAction("❌ Exit")

        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == act_work: self.show_time_dialog("Work Time", True)
        elif action == act_pause: self.show_time_dialog("Pause Time", False)
        elif action == act_rounds:
            v, ok = QInputDialog.getInt(self, "Rounds", "Total Rounds:", self.total_rounds, 1, 999)
            if ok: self.total_rounds = v; self.stop_timer(); self.save_settings()
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
            self.save_settings() # Сохраняем позицию при перемещении

    def mouseDoubleClickEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.start_timer() if not self.is_running else self.stop_timer()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    overlay = DanaOverlay()
    sys.exit(app.exec())