import sys
from PyQt6.QtWidgets import (QApplication, QWidget, QLabel, QVBoxLayout, 
                             QMenu, QInputDialog, QGraphicsDropShadowEffect, QFrame)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

class DanaOverlay(QWidget):
    def __init__(self):
        super().__init__()
        
        self.work_time = 10
        self.pause_time = 10
        self.total_rounds = 10
        
        self.current_round = 1
        self.time_left = self.work_time
        self.is_work_phase = True
        self.is_running = False
        self.scale_factor = 1.0

        self.init_ui()

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
        
        # Статус (теперь здесь раунды типа 1/10)
        self.label_status = QLabel("")
        self.label_status.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Таймер
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
        self.resize(500, 160) 
        self.show()

    def update_styles(self):
        s = self.scale_factor
        status_size = int(16 * s)
        
        current_text = self.label_time.text()
        if current_text.isdigit():
            fs = int(85 * s)
        else:
            fs = int(55 * s) 
            
        time_color = "white"
        if self.is_running:
            time_color = "#27ae60" if self.is_work_phase else "#e67e22"

        self.label_status.setStyleSheet(f"color: {time_color}; font-size: {status_size}px; font-weight: bold; font-family: 'Segoe UI'; opacity: 0.8;")
        self.label_time.setStyleSheet(f"color: {time_color}; font-size: {fs}px; font-weight: 900; font-family: 'Arial Black';")
        
        self.shadow.setBlurRadius(max(3, int(15 * s)))

    def wheelEvent(self, event):
        delta = event.angleDelta().y()
        if delta > 0:
            self.scale_factor = min(3.0, self.scale_factor + 0.1)
        else:
            self.scale_factor = max(0.4, self.scale_factor - 0.1)
        
        new_w = int(500 * self.scale_factor)
        new_h = int(160 * self.scale_factor)
        self.setFixedSize(new_w, new_h)
        self.update_styles()

    def update_timer(self):
        if self.time_left > 0:
            self.time_left -= 1
            self.label_time.setText(str(self.time_left))
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
        self.update_styles()

    def start_timer(self):
        self.is_running = True
        self.current_round = 1
        self.is_work_phase = True
        self.time_left = self.work_time
        self.label_status.setText(f"WORK {self.current_round}/{self.total_rounds}")
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
        menu.setStyleSheet("QMenu { background: #1e1e1e; color: white; border: 1px solid #444; } QMenu::item:selected { background: #0078d4; }")
        act_start = menu.addAction("▶ Start")
        act_stop = menu.addAction("⏹ Stop")
        menu.addSeparator()
        act_work = menu.addAction("⏱ Work Time")
        act_pause = menu.addAction("☕ Pause Time")
        act_rounds = menu.addAction("🔄 Total Rounds")
        menu.addSeparator()
        act_exit = menu.addAction("❌ Exit")

        action = menu.exec(self.mapToGlobal(event.pos()))
        if action == act_start: self.start_timer()
        elif action == act_stop: self.stop_timer()
        elif action == act_exit: QApplication.quit()
        elif action == act_work:
            val, ok = QInputDialog.getInt(self, "Settings", "Work (sec):", self.work_time, 1, 9999)
            if ok: self.work_time = val; self.stop_timer()
        elif action == act_pause:
            val, ok = QInputDialog.getInt(self, "Settings", "Pause (sec):", self.pause_time, 1, 9999)
            if ok: self.pause_time = val; self.stop_timer()
        elif action == act_rounds:
            val, ok = QInputDialog.getInt(self, "Settings", "Total Rounds:", self.total_rounds, 1, 999)
            if ok: self.total_rounds = val; self.stop_timer()

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