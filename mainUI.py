from PyQt6 import QtWidgets, QtCore, QtGui
from PyQt6.QtWidgets import QScrollArea, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, QTextEdit, QApplication, QSplitter, QPushButton, QFileDialog, QTreeView, QLabel, QMessageBox
import sys
import os
from draw_plot import generate_plots
from workers import model_worker, save_df
from PyQt6.QtCore import QThreadPool, QRunnable, QByteArray, QObject, pyqtSignal, QTimer
from PyQt6.QtGui import QIcon, QMovie, QPixmap
import pandas as pd


FOLDER_PATH = ''
DF = None

class WorkerSignals(QObject):
    started = pyqtSignal()
    finished = pyqtSignal()

class Worker(QRunnable):
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        self.signals = WorkerSignals()

    def run(self):
        self.signals.started.emit()
        self.func(*self.args, **self.kwargs)
        self.signals.finished.emit()

def application():
    app = QApplication(sys.argv)
    window = QMainWindow()
    window.setWindowTitle("Формирование регистраций животных")
    window.setGeometry(300, 250, 750, 500)
    
    # Создаем виджет для центральной области окна
    central_widget = QWidget()
    window.setCentralWidget(central_widget)
    # Создаем вертикальный макет для всего окна
    main_layout = QVBoxLayout()
    central_widget.setLayout(main_layout)
    
    # Создаем виджет с кнопками
    buttons_widget = QWidget()
    buttons_layout = QHBoxLayout()
    buttons_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
    buttons_widget.setLayout(buttons_layout)
    buttons_widget.setMaximumHeight(80)
    buttons_widget.setMaximumWidth(450)
    buttons_layout.setSpacing(5)

    # <---------------КНОПКИ--------------->
    # Кнопка открыть файл
    buttonOpen = QtWidgets.QToolButton()
    buttonOpen.setFixedSize(QtCore.QSize(65, 65))
    icon = QtGui.QIcon("icons/Opened_Folder.png")
    buttonOpen.setIcon(icon)
    buttonOpen.setText('Открыть')
    buttonOpen.setIconSize(QtCore.QSize(40, 40))
    buttonOpen.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    buttons_layout.addWidget(buttonOpen)
    
    #Кнопка запуска
    buttonStart = QtWidgets.QToolButton()
    buttonStart.setFixedSize(QtCore.QSize(65, 65))
    icon = QtGui.QIcon("icons/Start.png")
    buttonStart.setIcon(icon)
    buttonStart.setText('Запуск')
    buttonStart.setIconSize(QtCore.QSize(40, 40))
    buttonStart.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    buttons_layout.addWidget(buttonStart)

    # Кнопка сохранения
    buttonSave = QtWidgets.QToolButton()
    buttonSave.setFixedSize(QtCore.QSize(65, 65))
    icon = QtGui.QIcon("icons/Save.png")
    buttonSave.setIcon(icon)
    buttonSave.setText('Сохранить')
    buttonSave.setIconSize(QtCore.QSize(40, 40))
    buttonSave.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    buttons_layout.addWidget(buttonSave)

    # Кнопка информации
    buttonInfo = QtWidgets.QToolButton()
    buttonInfo.setFixedSize(QtCore.QSize(65, 65))
    icon = QtGui.QIcon("icons/Info.png")
    buttonInfo.setIcon(icon)
    buttonInfo.setText('Info')
    buttonInfo.setIconSize(QtCore.QSize(40, 40))
    buttonInfo.setToolButtonStyle(QtCore.Qt.ToolButtonStyle.ToolButtonTextUnderIcon)
    buttons_layout.addWidget(buttonInfo)
    
    # Добавляем виджет с кнопками в главный макет
    main_layout.addWidget(buttons_widget)
    
    # Создаем горизонтальный макет с QSplitter
    splitter_layout = QHBoxLayout()
    main_layout.addLayout(splitter_layout)
    
    # Создаем QSplitter
    splitter = QSplitter()
    splitter.setOrientation(QtCore.Qt.Orientation.Horizontal)
    splitter_layout.addWidget(splitter)
    
    # Создаем левый и правый виджеты
    left_widget = QTreeView()
    right_splitter = QSplitter()
    right_splitter.setOrientation(QtCore.Qt.Orientation.Vertical)

    # Добавляем виджеты в QSplitter
    splitter.addWidget(left_widget)
    splitter.addWidget(right_splitter)

    scroll_area = QScrollArea()
    scroll_area.setWidgetResizable(True)
    # Устанавливаем QPixmap на QLabel
    right_widget_1 = QLabel()
    scroll_area.setWidget(right_widget_1)
    # Добавляем QLabel в правый сплиттер вместо QTextEdit
    right_widget_2 = QTextEdit()  # Тут таблица
    
    # Добавляем виджеты в правый сплитер
    right_splitter.addWidget(scroll_area)
    right_splitter.addWidget(right_widget_2)

    splitter.setSizes([200, 550])
    right_splitter.setSizes([300, 300])


    
    #Вствка графиков
    def display_plot(image_path):
        pixmap = QPixmap(image_path)
        right_widget_1.setPixmap(pixmap)
        right_widget_1.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

    # Функция для открытия проводника и выбора папки
    def open_folder():
        folder_path = QFileDialog.getExistingDirectory()
        global FOLDER_PATH
        FOLDER_PATH = folder_path
        print(FOLDER_PATH)
        if folder_path:
            model = QtGui.QFileSystemModel()
            model.setRootPath(folder_path)
            left_widget.setModel(model)
            left_widget.setRootIndex(model.index(folder_path))

    # Функция для запуска работы моделей
    def model_processing():
        print("Функция детектора")
        print(FOLDER_PATH)
        if FOLDER_PATH != '':
            print("Детектор запустился")
            global DF
            DF = model_worker(FOLDER_PATH)
            print("Обработка завершена")
            pass
      
    pool = QThreadPool()
    # Создаем QLabel для отображения GIF
    gif_label = QLabel(buttons_widget)
    gif_label.setFixedSize(65, 65)  # Фиксированный размер
    movie = QMovie("icons/progres.gif", QByteArray(), buttons_widget)
    gif_label.setMovie(movie)
    movie.start()
    buttons_layout.addWidget(gif_label)
    gif_label.hide()  # Скрываем GIF по умолчанию

    def start_model_processing(label):
        worker = Worker(model_processing)
        worker.signals.started.connect(lambda: label.show()) 
        pool.start(worker)
        worker.signals.finished.connect(lambda: label.hide())
        worker.signals.finished.connect(lambda: right_widget_2.setText(DF.to_string()))
        worker.signals.finished.connect(lambda: display_plot(generate_plots(DF)))
        
    # Функция для сохранения результата
    def save_result():
        save_path = QFileDialog.getExistingDirectory()
        save_df(DF, save_path)
        pass

    # Функция для открытия окна информации
    def program_info():
        message_box = QMessageBox()
        message_box.setWindowTitle("О приложении")
        message_box.setIcon(QMessageBox.Icon.Information)
        message_box.setText("Приложение для формирования регистраций животных")
        message_box.setInformativeText("Версия 1.0\n\nРазработано командой Ping")
        message_box.setDetailedText("Это приложение предназначено для обработки данных регистраций животных.\n\nОсновные возможности:\n- Загрузка данных из CSV-файла\n- Построение графиков активности животных по часам суток\n- Отображение информации в табличном виде")
        message_box.setStandardButtons(QMessageBox.StandardButton.Ok)
        message_box.exec()

    # Добавляем функцию для кнопок
    buttonOpen.clicked.connect(open_folder)
    buttonStart.clicked.connect(lambda: start_model_processing(gif_label))
    buttonSave.clicked.connect(save_result)
    buttonInfo.clicked.connect(program_info)
    buttonInfo.clicked.connect(program_info)
    

    #Показываем окно
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    application()