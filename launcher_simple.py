import os
import shutil
from pathlib import Path

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QSizePolicy, QLabel, QFileDialog,
                             QTabWidget, QLineEdit, QCheckBox)
import numpy as np
from skimage import io
import napari
import pandas as pd

import utils
from napari_view_simple import launch_viewers
from predict import predict_3ax
from train import train_unet


class Loader(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.master = parent
        self.opath = ""
        self.modpath = ""
        self.btn1 = QPushButton('open', self)
        self.btn1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn1.clicked.connect(self.show_dialog_o)
        self.btn2 = QPushButton('open', self)
        self.btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn2.clicked.connect(self.show_dialog_mod)

        self.textbox = QLineEdit(self)
        self.textbox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.checkBox = QCheckBox("create new dataset?")
        self.checkBox.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)

        self.btn4 = QPushButton('launch napari', self)
        self.btn4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn4.clicked.connect(self.launch_napari)
        self.btnb = QPushButton('back', self)
        self.btnb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnb.clicked.connect(self.back)
        self.lbl = QLabel('original dir', self)
        self.lbl2 = QLabel('mask dir', self)
        self.lbl4 = QLabel('model type (do not use word "train")', self)
        self.build()

    def build(self):
        vbox = QVBoxLayout()
        vbox.addWidget(combine_blocks(self.btn1, self.lbl))
        vbox.addWidget(combine_blocks(self.btn2, self.lbl2))
        vbox.addWidget(combine_blocks(self.textbox, self.lbl4))
        vbox.addWidget(self.checkBox)
        vbox.addWidget(self.btn4)
        vbox.addWidget(self.btnb)

        self.setLayout(vbox)
        self.show()

    def show_dialog_o(self):
        default_path = max(self.opath, self.modpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.opath = f_name
            self.lbl.setText(self.opath)

    def show_dialog_mod(self):
        default_path = max(self.opath, self.modpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.modpath = f_name
            self.lbl2.setText(self.modpath)

    def back(self):
        self.master.setCurrentIndex(0)

    def launch_napari(self):
        images = utils.load_images(self.opath)
        if self.modpath == "":
            labels = np.zeros_like(images.compute())
            self.modpath = os.path.join(os.path.dirname(self.opath), self.textbox.text())
            os.makedirs(self.modpath, exist_ok=True)
            filenames = [fn.name for fn in sorted(list(Path(self.opath).glob('./*png')))]
            for i in range(len(labels)):
                io.imsave(os.path.join(self.modpath, str(i).zfill(4) + '.png'), labels[i])
        else:
            labels = utils.load_saved_masks(self.modpath)
        try:
            labels_raw = utils.load_raw_masks(self.modpath + '_raw')
        except:
            labels_raw = None
        view1 = launch_viewers(images, labels, labels_raw, self.modpath, self.textbox.text(), self.checkBox.isChecked())
        global view_l
        view_l.close()
        return view1


class Trainer(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.master = parent
        self.opath = ""
        self.labelpath = ""
        self.modelpath = ""
        self.btn1 = QPushButton('open', self)
        self.btn1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn1.clicked.connect(self.show_dialog_o)
        self.btn2 = QPushButton('open', self)
        self.btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn2.clicked.connect(self.show_dialog_label)
        self.btn3 = QPushButton('open', self)
        self.btn3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn3.clicked.connect(self.show_dialog_model)

        self.btn4 = QPushButton('start training', self)
        self.btn4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn4.clicked.connect(self.trainer)
        self.btnb = QPushButton('back', self)
        self.btnb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnb.clicked.connect(self.back)
        self.lbl = QLabel('original dir', self)
        self.lbl2 = QLabel('label dir', self)
        self.lbl3 = QLabel('model output dir', self)
        self.build()

    def build(self):
        vbox = QVBoxLayout()
        vbox.addWidget(combine_blocks(self.btn1, self.lbl))
        vbox.addWidget(combine_blocks(self.btn2, self.lbl2))
        vbox.addWidget(combine_blocks(self.btn3, self.lbl3))
        vbox.addWidget(self.btn4)
        vbox.addWidget(self.btnb)

        self.setLayout(vbox)
        self.show()

    def show_dialog_o(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.opath = f_name
            self.lbl.setText(self.opath)

    def show_dialog_label(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.labelpath = f_name
            self.lbl2.setText(self.labelpath)

    def show_dialog_model(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.modelpath = f_name
            self.lbl3.setText(self.modelpath)

    def back(self):
        self.master.setCurrentIndex(0)

    def get_newest_csv(self):
        csvs = sorted(list(Path(self.labelpath).glob('./*csv')))
        csv = pd.read_csv(str(csvs[-1]), index_col=0)
        return csv

    def trainer(self):
        ori_imgs, ori_filenames = utils.load_X_gray(self.opath)
        label_imgs, label_filenames = utils.load_Y_gray(self.labelpath, normalize=False)
        train_csv = self.get_newest_csv()
        train_ori_imgs, train_label_imgs = utils.select_train_data(
            dataframe=train_csv,
            ori_imgs=ori_imgs,
            label_imgs=label_imgs,
            ori_filenames=ori_filenames,
        )
        devided_train_ori_imgs = utils.divide_imgs(train_ori_imgs)
        devided_train_label_imgs = utils.divide_imgs(train_label_imgs)
        devided_train_label_imgs = np.where(
            devided_train_label_imgs < 0,
            0,
            devided_train_label_imgs
        )
        train_unet(
            X_train=devided_train_ori_imgs,
            Y_train=devided_train_label_imgs,
            csv_path=os.path.join(self.modelpath, "train_log.csv"),
            model_path=os.path.join(self.modelpath, "model.hdf5"),
            input_shape=(512, 512, 1),
            num_classes=1
        )


class Predicter(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.master = parent
        self.opath = ""
        self.labelpath = ""
        self.modelpath = ""
        self.outpath = ""
        self.btn1 = QPushButton('open', self)
        self.btn1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn1.clicked.connect(self.show_dialog_o)
        self.btn2 = QPushButton('open', self)
        self.btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn2.clicked.connect(self.show_dialog_label)
        self.btn3 = QPushButton('open', self)
        self.btn3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn3.clicked.connect(self.show_dialog_model)
        self.btn4 = QPushButton('open', self)
        self.btn4.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn4.clicked.connect(self.show_dialog_outdir)

        self.btn5 = QPushButton('predict', self)
        self.btn5.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn5.clicked.connect(self.predicter)
        self.btnb = QPushButton('back', self)
        self.btnb.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btnb.clicked.connect(self.back)
        self.lbl = QLabel('original dir', self)
        self.lbl2 = QLabel('label dir', self)
        self.lbl3 = QLabel('model dir (contains model.hdf5)', self)
        self.lbl4 = QLabel('output dir', self)
        self.build()

    def build(self):
        vbox = QVBoxLayout()
        vbox.addWidget(combine_blocks(self.btn1, self.lbl))
        vbox.addWidget(combine_blocks(self.btn2, self.lbl2))
        vbox.addWidget(combine_blocks(self.btn3, self.lbl3))
        vbox.addWidget(combine_blocks(self.btn4, self.lbl4))
        vbox.addWidget(self.btn5)
        vbox.addWidget(self.btnb)

        self.setLayout(vbox)
        self.show()

    def show_dialog_o(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.opath = f_name
            self.lbl.setText(self.opath)

    def show_dialog_label(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.labelpath = f_name
            self.lbl2.setText(self.labelpath)

    def show_dialog_model(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.modelpath = f_name
            self.lbl3.setText(self.modelpath)

    def show_dialog_outdir(self):
        default_path = max(self.opath, self.labelpath, os.path.expanduser('~'))
        f_name = QFileDialog.getExistingDirectory(self, 'Open Directory', default_path)
        if f_name:
            self.outpath = f_name
            self.lbl4.setText(self.outpath)

    def back(self):
        self.master.setCurrentIndex(0)

    def get_newest_csv(self):
        csvs = sorted(list(Path(self.labelpath).glob('./*csv')))
        try:
            csv = pd.read_csv(str(csvs[-1]), index_col=0)
        except:
            csv = None
        return csv, str(csvs[-1])

    def predicter(self):
        ori_imgs, ori_filenames = utils.load_X_gray(self.opath)

        predict_3ax(ori_imgs, os.path.join(self.modelpath, "model.hdf5"), self.outpath, input_shape=(512, 512, 1),
                    num_classes=1)

        if self.labelpath != "":
            csv, csv_path = self.get_newest_csv()
            if csv:
                label_names = [node.filename for node in csv.itertuples() if node.train == "Checked"]
                for ln in label_names:
                    shutil.copy(os.path.join(self.labelpath, ln), os.path.join(self.outpath, 'merged_prediction'))
                shutil.copy(str(csv_path), os.path.join(self.outpath, 'merged_prediction'))


class Entrance(QWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.master = parent
        self.btn1 = QPushButton('Loader', self)
        self.btn1.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn1.clicked.connect(self.move_to_loader)
        self.btn2 = QPushButton('Trainer', self)
        self.btn2.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn2.clicked.connect(self.move_to_trainer)
        self.btn3 = QPushButton('Predicter', self)
        self.btn3.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Fixed)
        self.btn3.clicked.connect(self.move_to_predicter)
        self.build()

    def build(self):
        vbox = QVBoxLayout()
        vbox.addWidget(self.btn1)
        vbox.addWidget(self.btn2)
        vbox.addWidget(self.btn3)

        self.setLayout(vbox)
        self.show()

    def move_to_loader(self):
        self.master.setCurrentIndex(1)

    def move_to_trainer(self):
        self.master.setCurrentIndex(2)

    def move_to_predicter(self):
        self.master.setCurrentIndex(3)


class App(QTabWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("napari launcher")
        self.tab1 = Entrance(self)
        self.tab2 = Loader(self)
        self.tab3 = Trainer(self)
        self.tab4 = Predicter(self)

        # add to tab page
        self.addTab(self.tab1, "Entrance")
        self.addTab(self.tab2, "Loader")
        self.addTab(self.tab3, "Trainer")
        self.addTab(self.tab4, "Predicter")

        self.setStyleSheet("QTabWidget::pane { border: 0; }")
        self.tabBar().hide()
        self.resize(500, 400)


def combine_blocks(block1, block2):
    temp_widget = QWidget()
    temp_layout = QHBoxLayout()
    temp_layout.addWidget(block1)
    temp_layout.addWidget(block2)
    temp_widget.setLayout(temp_layout)
    return temp_widget


if __name__ == '__main__':
    with napari.gui_qt():
        view_l = napari.Viewer()
        launcher = App()
        view_l.window.add_dock_widget(launcher, area='right')
