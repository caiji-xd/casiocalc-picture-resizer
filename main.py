import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QGridLayout, QCheckBox
)
from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageQt, ImageOps


class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("四级灰度编辑器配套图片处理器")
        self.setGeometry(100, 100, 800, 600)

        # 主窗口布局
        self.main_widget = QWidget()
        self.setCentralWidget(self.main_widget)
        self.layout = QHBoxLayout(self.main_widget)

        # 左侧控制区域
        self.control_frame = QWidget()
        self.control_layout = QGridLayout(self.control_frame)  # 使用网格布局
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

        # 红绿模式状态
        self.red_green_mode = False

    def init_buttons(self):
        # 选择图片按钮
        self.select_button = QPushButton("选择图片")
        self.select_button.clicked.connect(self.select_image)
        self.select_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.select_button, 0, 0, 1, 2)  # 跨两列

        # 旋转按钮
        self.rotate_button = QPushButton("旋转")
        self.rotate_button.clicked.connect(self.rotate_image)
        self.rotate_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.rotate_button, 1, 0)

        # 像素化按钮
        self.pixelate_button = QPushButton("像素化")
        self.pixelate_button.clicked.connect(self.pixelate_image)
        self.pixelate_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.pixelate_button, 1, 1)

        # 维持原比例复选框
        self.maintain_aspect_ratio_checkbox = QCheckBox("维持原比例")
        self.maintain_aspect_ratio_checkbox.setChecked(True)  # 默认勾选
        self.control_layout.addWidget(self.maintain_aspect_ratio_checkbox, 2, 0, 1, 2)  # 跨两列

        # 四级灰度化按钮
        self.grayscale_button = QPushButton("四级灰度化")
        self.grayscale_button.clicked.connect(self.grayscale_image)
        self.grayscale_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.grayscale_button, 3, 0)

        # 红绿模式按钮
        self.red_green_button = QPushButton("红绿模式")
        self.red_green_button.clicked.connect(self.toggle_red_green_mode)
        self.red_green_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.red_green_button, 3, 1)

        # 导出按钮
        self.export_button = QPushButton("导出图片")
        self.export_button.clicked.connect(self.export_image)
        self.export_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.export_button, 4, 0, 1, 2)  # 跨两列

    def select_image(self):
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp)")
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

            # 使用最近邻插值缩放图像
            scaled_pixmap = pixmap.scaled(
                self.preview_frame.size(),
                Qt.AspectRatioMode.KeepAspectRatio,
                Qt.TransformationMode.FastTransformation  # 使用最近邻插值
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
            if self.maintain_aspect_ratio_checkbox.isChecked():
                # 保持原比例，计算新的宽度
                original_width, original_height = self.current_image.size
                aspect_ratio = original_width / original_height
                new_height = 63
                new_width = int(new_height * aspect_ratio)

                # 缩放图像
                resized_image = self.current_image.resize((new_width, new_height), Image.Resampling.NEAREST)

                # 创建一个 192x63 的空白图像
                self.pixelated_image = Image.new("RGB", (192, 63), (255, 255, 255))

                # 将缩放后的图像居中放置在空白图像上
                x_offset = (192 - new_width) // 2
                self.pixelated_image.paste(resized_image, (x_offset, 0))

            else:
                # 不保持原比例，直接缩放为 192x63
                self.pixelated_image = self.current_image.resize((192, 63), Image.Resampling.NEAREST)

            self.current_image = self.pixelated_image
            self.update_preview()
        else:
            QMessageBox.warning(self, "警告", "请先选择图片")

    def grayscale_image(self):
        if self.pixelated_image:
            # 将图像转换为灰度图
            grayscale_image = ImageOps.grayscale(self.pixelated_image)

            # 增强对比度，确保最浅色是白色
            grayscale_image = ImageOps.autocontrast(grayscale_image)

            # 将灰度图转换为四级灰度
            quantized_image = grayscale_image.quantize(colors=4)

            # 将四级灰度图像转换为 RGB 模式
            quantized_image = quantized_image.convert("RGB")

            # 获取四级灰度化后的四种颜色
            colors = quantized_image.getcolors()
            sorted_colors = sorted(colors, key=lambda x: sum(x[1]))  # 按颜色亮度排序

            # 定义替换颜色
            replace_colors = {
                sorted_colors[0][1]: (0, 0, 0),  # 最浅色 -> 白色
                sorted_colors[1][1]: (149, 149, 149),  # 第二浅色 -> #BABABA
                sorted_colors[2][1]: (186, 186, 186),  # 第三浅色 -> #959595
                sorted_colors[3][1]: (255, 255, 255),  # 第四浅色 -> 黑色
            }

            # 替换颜色
            pixels = quantized_image.load()
            for i in range(quantized_image.size[0]):
                for j in range(quantized_image.size[1]):
                    current_color = pixels[i, j]
                    if current_color in replace_colors:
                        pixels[i, j] = replace_colors[current_color]

            # 如果红绿模式开启，应用红绿模式逻辑
            if self.red_green_mode:
                self.apply_red_green_mode(quantized_image)

            # 显示处理后的图像
            self.current_image = quantized_image
            self.update_preview()
        else:
            QMessageBox.warning(self, "警告", "请先像素化图片")

    def apply_red_green_mode(self, image):
        pixels = image.load()
        for i in range(image.size[0]):
            for j in range(image.size[1]):
                r, g, b = pixels[i, j]
                if (r, g, b) == (186, 186, 186):  # #BABABA -> 浅绿色
                    pixels[i, j] = (144, 238, 144)  # 浅绿色
                elif (r, g, b) == (149, 149, 149):  # #959595 -> 红色
                    pixels[i, j] = (255, 0, 0)  # 红色
                # 白色和黑色保持不变

    def toggle_red_green_mode(self):
        # 切换红绿模式状态
        self.red_green_mode = not self.red_green_mode

        # 更新按钮文本
        if self.red_green_mode:
            self.red_green_button.setText("普通模式")
        else:
            self.red_green_button.setText("红绿模式")

        # 如果当前有图像，重新应用灰度化处理
        if self.pixelated_image:
            self.grayscale_image()

    def export_image(self):
        if self.current_image:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "图片文件 (*.png *.jpg *.bmp)")
            if file_path:
                # 保存图像，保持原始大小
                if self.maintain_aspect_ratio_checkbox.isChecked():
                    # 如果维持原比例，导出时保持 192x63 大小
                    self.current_image.resize((192, 63), Image.Resampling.NEAREST).save(file_path)
                else:
                    # 否则直接保存
                    self.current_image.save(file_path)
                QMessageBox.information(self, "成功", "图片已成功导出！")
        else:
            QMessageBox.warning(self, "警告", "没有图片可以导出")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageProcessorApp()
    window.show()
    sys.exit(app.exec())