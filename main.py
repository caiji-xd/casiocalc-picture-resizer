import sys
import cv2
import numpy as np
from PyQt6.QtWidgets import QApplication, QMainWindow, QWidget, QHBoxLayout, QPushButton, QFileDialog, QLabel, QMessageBox, QGridLayout, QCheckBox,QListWidget,QVBoxLayout

from PyQt6.QtGui import QPixmap, QImage
from PyQt6.QtCore import Qt
from PIL import Image, ImageQt, ImageOps,ImageFile,ImageDraw
import os, PyQt6
dirname = os.path.dirname(PyQt6.__file__)
qt_dir = os.path.join(dirname, 'Qt5', 'plugins', 'platforms')
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = qt_dir
def pixel_line(img:ImageFile.ImageFile):
    # 读取图片宽高并乘以3
    w = img.width * 6
    h = img.height * 6
    # 调整图片大小
    img_resize = img.resize((w,h),Image.NEAREST)
    # 初始化画笔
    draw = ImageDraw.Draw(img_resize)
    # 画竖线
    for i in range(w):
        draw.line([(6*i,0),(6*i,h)],fill=(0,0,255))
    # 画横线
    for j in range(h):
        draw.line([(0,6*j),(w,6*j)],fill=(0,0,255))
    # 返回图片
    return img_resize

class ImageProcessorApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("四级灰度编辑器配套图片处理器")
        self.setGeometry(100, 100, 800, 600)

        # -------------/ 撤销相关变量 /-------------
        # 撤销列表的相关变量
        self.undo_list_vars = []

        """
        undo_list_vars存储的信息格式为:
        {"pixel_image":self.pixelated_image, # 像素化后的图片
        "pixeled":self.pixeled, # 是否有像素边框
        "maintain_ratio":self.maintain_aspect_ratio_checkbox.isChecked(), # 是否维持原比例
        "pixel_type":self.last_pixel_type, # 上一次灰度化的类型
        "red_green_mode":False # 红绿模式} 
        """

        # 是否开启撤销
        self.undo_mode = True
        # 跳转列表中每一项对应的图片文件
        self.undo_images = [] # 存储的是current_image
        # 是否开启撤销
        self.undo_mode = True
        # -------------/ 撤销相关变量结束 /-------------

        # 是否有像素边框
        self.pixeled = False
        # 红绿模式前的四级像素模式
        self.last_pixel_type = ""
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

        # 最右侧的list视图
        # 撤销列表
        self.undo_list = QListWidget()
        # 撤销提示文字
        self.undo_tip = QLabel("选择相应项并点击按钮即可跳转")
        # 撤销widget
        self.undo_frame = QWidget()
        # 加入到主布局
        self.layout.addWidget(self.undo_frame, stretch=1)
        # 在撤销widget创建VBox布局
        self.undo_layout = QVBoxLayout(self.undo_frame)
        # 将列表添加到布局
        self.undo_layout.addWidget(self.undo_tip)
        self.undo_layout.addWidget(self.undo_list)


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
        self.control_layout.addWidget(self.grayscale_button, 3, 0,1,2)

        # 用opencv四级灰度化
        self.grayscale_button = QPushButton("opencv四级灰度化\n(效果与上面有差异,\n仍在测试中)")
        self.grayscale_button.clicked.connect(self._4level_cv2)
        self.grayscale_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.grayscale_button, 4,0, 1,2)

        # 二级灰度化按钮
        self.binary_grayscale_button = QPushButton("二级灰度化")
        self.binary_grayscale_button.clicked.connect(self._2level_gray)
        self.binary_grayscale_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.binary_grayscale_button, 6, 0, 1, 2)  # 跨两列

        # 红绿模式按钮
        self.red_green_button = QPushButton("红绿模式")
        self.red_green_button.clicked.connect(self.toggle_red_green_mode)
        self.red_green_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.red_green_button, 5,0, 1,2)

        # 像素边框按钮
        self.pixel_border_button = QPushButton("像素边框(请最后再用)")
        self.pixel_border_button.clicked.connect(self.pixel_border)
        self.pixel_border_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.pixel_border_button, 7, 0, 1, 2) # 跨两列

        # 导出按钮
        self.export_button = QPushButton("导出图片")
        self.export_button.clicked.connect(self.export_image)
        self.export_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.control_layout.addWidget(self.export_button, 8, 0, 1, 2)  # 跨两列

        # 版本号
        self.info_label = QLabel("版本号: v1.5\n本产品为完全免费的开源软件")
        self.info_label.setFixedHeight(50) # 占高度50像素
        self.control_layout.addWidget(self.info_label, 9, 0, 1, 2)

        # 撤销按钮
        self.undo_button = QPushButton("跳转到此步")
        self.undo_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.undo_button.clicked.connect(self.undo_jump_to)
        self.undo_layout.addWidget(self.undo_button)

        # 关闭撤销
        self.close_undo_button = QPushButton("不记录操作(节省内存)")
        self.close_undo_button.setStyleSheet("QPushButton { padding: 10px; font-size: 14px; }")
        self.close_undo_button.clicked.connect(self.switch_undo_mode)
        self.undo_layout.addWidget(self.close_undo_button)

    def undo_jump_to(self):
        if self.undo_mode:
            index = self.undo_list.currentRow()
            # 设置图片和变量到跳转的位置
            self.current_image = self.undo_images[index]
            self.pixelated_image = self.undo_list_vars[index]["pixel_image"]
            self.pixeled = self.undo_list_vars[index]["pixeled"]
            self.maintain_aspect_ratio_checkbox.setChecked(self.undo_list_vars[index]["maintain_ratio"])
            self.last_pixel_type = self.undo_list_vars[index]["pixel_type"]
            if self.last_pixel_type:
                self.red_green_mode = not self.undo_list_vars[index]["red_green_mode"]
                self.toggle_red_green_mode()
            # 删除多余的记录
            for i in range(index+1, len(self.undo_images)):
                self.undo_images.pop()
                self.undo_list_vars.pop()
                self.undo_list.takeItem(index+1)
            # 设置跳转的位置变量
            self.update_preview()

    def switch_undo_mode(self):
        self.undo_mode = not self.undo_mode
        if not self.undo_mode:
            self.close_undo_button.setText("开始记录操作")
            self.undo_list.clear()
            self.undo_images = []
            self.undo_list_vars = []

        else:
            self.close_undo_button.setText("不记录操作(节省内存)")

    def _4level_cv2(self):
        # 使用opencv将图片转为4级灰度(似乎效果比pillow更好,仅供测试)
        # 将Pillow图像转换为OpenCV格式
        if self.pixelated_image:
            # 设置红绿模式的上一个模式标记
            self.last_pixel_type = "cv2"
            image_np = np.array(self.pixelated_image.convert("RGB"))
            gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

            # 将灰度图像量化为四个级别
            # 0-63 -> 0, 64-127 -> 85, 128-191 -> 170, 192-255 -> 255
            four_level_image = np.clip((gray_image // 64) * 85, 0, 255).astype(np.uint8)

            # 定义四个颜色级别
            color_levels = {
                0: (0, 0, 0),  # 最浅色 -> 白色
                85: (149, 149, 149),  # 第二浅色 -> #959595
                170: (186, 186, 186),  # 第三浅色 -> #BABABA
                255: (255, 255, 255)  # 第四浅色 -> 黑色
            }

            # 创建一个新的RGB图像
            rgb_image = np.zeros((gray_image.shape[0], gray_image.shape[1], 3), dtype=np.uint8)

            # 替换颜色
            for level, color in color_levels.items():
                rgb_image[four_level_image == level] = color

            # 将OpenCV图像转换回Pillow格式
            four_level_pillow_image = Image.fromarray(rgb_image)

            self.current_image = four_level_pillow_image
            self.update_preview()
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image":self.pixelated_image,"pixeled":self.pixeled,"maintain_ratio":self.maintain_aspect_ratio_checkbox.isChecked(),"pixel_type":self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("opencv四级灰度化")
        else:
            QMessageBox.warning(self, "警告", "请先像素化图片")

    def select_image(self):
        # 打开文件选择对话框
        file_path, _ = QFileDialog.getOpenFileName(self, "选择图片", "", "图片文件 (*.jpg *.jpeg *.png *.bmp *.gif *.webp)")
        if file_path:
            # 加载图像并显示在预览区
            self.image = Image.open(file_path)
            self.current_image = self.image
            self.update_preview()
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                            "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                            "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("打开文件")

    def pixel_border(self):
        if self.current_image:
            if not self.pixeled:
                # 调用 pixel_line 函数,并存储到 current_image
                self.current_image = pixel_line(self.current_image)
                # 标记,以保证在导出图片时不进行resize
                self.pixeled = True
                # 更新预览
                self.update_preview()
                if self.undo_mode:
                    self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                                "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                                "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                    self.undo_images.append(self.current_image)
                    self.undo_list.addItem("像素分割线")
            else:
                QMessageBox.warning(self, "警告", "已经进行像素分割线,请勿再次使用\n如果你多次这么做,你的内存会当场爆炸(")
        else:
            QMessageBox.warning(self, "警告", "请先选择图片")

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
            # 检查undo_list
            self.check_undo_list()

    def check_undo_list(self):
        # 检查undo_list是否超过15项,超过则删除第2项到最后一个
        while self.undo_list.count() > 15:
            self.undo_list.takeItem(1)
            # 删除文件列表的第二个到最后一个
            self.undo_images.__delitem__(1)

    def resizeEvent(self, event):
        # 窗口大小改变时更新预览
        self.update_preview()
        super().resizeEvent(event)

    def rotate_image(self):
        if self.current_image:
            # 顺时针旋转 90 度
            self.current_image = self.current_image.rotate(-90, expand=True)
            self.update_preview()
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                            "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                            "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("旋转图片")
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
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                            "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                            "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("像素化图片")
        else:
            QMessageBox.warning(self, "警告", "请先选择图片")

    def _2level_gray(self):
        if self.pixelated_image:
            # 使用 OpenCV 进行二级灰度化处理
            image_np = np.array(self.pixelated_image)
            gray_image = cv2.cvtColor(image_np, cv2.COLOR_RGB2GRAY)

            # 使用自适应阈值增强辨识度
            binary_image = cv2.adaptiveThreshold(gray_image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

            # 将二值图像转换回 PIL 图像
            self.current_image = Image.fromarray(binary_image).convert("RGB")
            # 更新图像
            self.update_preview()
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                            "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                            "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("二级灰度化")
        else:
            QMessageBox.warning(self, "警告", "请先像素化图片")

    def grayscale_image(self):
        if self.pixelated_image:
            # 设置红绿模式的上一个模式标记
            self.last_pixel_type = "grayscale"
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

            # 显示处理后的图像
            self.current_image = quantized_image

            self.update_preview()
            if self.undo_mode:
                self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                            "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                            "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                self.undo_images.append(self.current_image)
                self.undo_list.addItem("标准四级灰度化")
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
        self.current_image = image
        self.update_preview()
        if self.undo_mode:
            self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                        "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                        "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
            self.undo_images.append(self.current_image)
            self.undo_list.addItem("开启红绿模式")

    def toggle_red_green_mode(self):
        if self.last_pixel_type:
            # 切换红绿模式状态
            self.red_green_mode = not self.red_green_mode

            # 更新按钮文本
            if self.red_green_mode:
                self.red_green_button.setText("普通模式")
            else:
                self.red_green_button.setText("红绿模式")
            # 如果红绿模式开启，应用红绿模式逻辑
            if self.red_green_mode:
                self.apply_red_green_mode(self.current_image)
            else:
                if self.undo_mode:
                    self.undo_list_vars.append({"pixel_image": self.pixelated_image, "pixeled": self.pixeled,
                                                "maintain_ratio": self.maintain_aspect_ratio_checkbox.isChecked(),
                                                "pixel_type": self.last_pixel_type,"red_green_mode":self.red_green_mode})
                    self.undo_images.append(self.current_image)
                    self.undo_list.addItem("关闭红绿模式")
                if self.last_pixel_type == "cv2":
                    self._4level_cv2()
                else:
                    self.grayscale_image()
            # 如果当前有图像，重新应用灰度化处理(暂时不使用)
            """if self.pixelated_image:
                self.grayscale_image()"""
        else:
            QMessageBox.warning(self, "警告", "请先灰度化图片")

    def export_image(self):
        if self.current_image:
            # 打开文件保存对话框
            file_path, _ = QFileDialog.getSaveFileName(self, "保存图片", "", "图片文件 (*.png *.jpg *.bmp)")
            if file_path:
                # 如果有像素边框,则直接保存(不进行resize)
                if self.pixeled:
                    self.current_image.save(file_path)
                # 保存图像，保持原始大小
                elif self.maintain_aspect_ratio_checkbox.isChecked():
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