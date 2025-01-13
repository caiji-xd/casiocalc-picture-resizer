import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageQt, ImageOps


class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Image Processor")
        self.setGeometry(100, 100, 800, 600)

        # 主窗口布局
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # 左侧控制区域
        self.control_frame = QWidget()
        self.control_layout = QVBoxLayout(self.control_frame)
        self.layout.addWidget(self.control_frame, stretch=1)

        # 右侧预览区域
        self.preview_frame = QLabel()
        self.preview_frame.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_frame.setStyleSheet("background-color: white;")
        self.layout.addWidget(self.preview_frame, stretch=4)

        # 初始化按钮
        self.init_buttons()

        # 初始化图像变量
        self.image = None
        self.pixelated_image = None
        self.current_image = None

    def init_buttons(self):
        # 选择图片按钮
        self.select_button = QPushButton("选择图片")
        self.select_button.clicked.connect(self.select_image)
        self.control_layout.addWidget(self.select_button)

        # 旋转按钮
        self.rotate_button = QPushButton("旋转")
        self.rotate_button.clicked.connect(self.rotate_image)
        self.control_layout.addWidget(self.rotate_button)

        # 像素化按钮
        self.pixelate_button = QPushButton("像素化")
        self.pixelate_button.clicked.connect(self.pixelate_image)
        self.control_layout.addWidget(self.pixelate_button)

        # 四级灰度化按钮
        self.grayscale_button = QPushButton("四级灰度化")
        self.grayscale_button.clicked.connect(self.grayscale_image)
        self.control_layout.addWidget(self.grayscale_button)

        # 导出按钮
        self.export_button = QPushButton("导出图片")
        self.export_button.clicked.connect(self.export_image)
        self.control_layout.addWidget(self.export_button)

    def select_image(self):
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif)")
        if file_path:
            # 加载图像并显示在预览区
            self.image = Image.open(file_path)
            self.current_image = self.image
            self.update_preview()

    def update_preview(self):
        if self.current_image:
            # 将 PIL 图像转换为 QPixmap
            qimage = ImageQt.ImageQt(self.current_image)
            pixmap = QPixmap.fromImage(qimage)

            # 缩放图像以适应预览区域
            scaled_pixmap = pixmap.scaled(
                self.preview_frame.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.SmoothTransformation
            )
            self.preview_frame.setPixmap(scaled_pixmap)

    def resizeEvent(self, event):
        # 窗口大小改变时更新预览
        self.update_preview()
        super().resizeEvent(event)

    def rotate_image(self):
        if self.current_image:
            # 顺时针旋转 90 度
            self.current_image = self.current_image.rotate(-90, expand=True)
            self.update_preview()
        else:
            QMessageBox.warning(self, "警告", "请先选择图片")

    def pixelate_image(self):
        if self.current_image:
            # 将图像缩放到 193x63 分辨率
            self.pixelated_image = self.current_image.resize((193, 63), Image.Resampling.NEAREST)
            self.current_image = self.pixelated_image
            self.update_preview()
        else:
            QMessageBox.warning(self, "警告", "请先选择图片")

    def grayscale_image(self):
        if self.pixelated_image:
            # 将图像转换为灰度图
            grayscale_image = ImageOps.grayscale(self.pixelated_image)

            # 将灰度图转换为四级灰度
            quantized_image = grayscale_image.quantize(colors=4)

            # 显示四级灰度图像
            self.current_image = quantized_image
            self.update_preview()
        else:
            QMessageBox.warning(self, "警告", "请先像素化图片")

    def export_image(self):
        if self.current_image:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "图片文件 (*.png *.jpg *.bmp)")
            if file_path:
                # 保存图像
                self.current_image.save(file_path)
                QMessageBox.information(self, "成功", "图片已成功导出！")
        else:
            QMessageBox.warning(self, "警告", "没有图片可以导出")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec())