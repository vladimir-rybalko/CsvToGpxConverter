#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
import os, sys, csv, enum, json, fiona
from pyproj import Proj, transform
from PyQt4 import QtCore, QtGui
from operator import itemgetter
from itertools import groupby
from lxml import etree

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

class Window(QtGui.QMainWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.setFixedSize(269, 82)
        self.move(300, 300)
        # self.setGeometry(50, 50, 500, 300)
        self.setWindowTitle(u'Конвертер')
        self.setWindowIcon(QtGui.QIcon('icon.png'))

        self.pushButton = QtGui.QPushButton("...", self)
        self.pushButton.setGeometry(QtCore.QRect(220, 10, 31, 23))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton.setShortcut("Ctrl+O")
        self.pushButton.clicked.connect(self.select_file)
        
        self.lineEdit = QtGui.QLineEdit(self)
        self.lineEdit.setGeometry(QtCore.QRect(20, 10, 191, 20))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))

        self.convertButton = QtGui.QPushButton(u'Конвертировать', self)
        self.convertButton.setGeometry(QtCore.QRect(74, 50, 101, 25))
        self.convertButton.clicked.connect(self.convert)

        self.quitButton = QtGui.QPushButton(u'Выход', self)
        self.quitButton.setGeometry(QtCore.QRect(180, 50, 75, 25))
        self.quitButton.clicked.connect(self.close_application)

        self.show()

    def close_application(self):
        choice = QtGui.QMessageBox.question(self, u'Выход',
                                            u'Хотите закрыть конвертер?',
                                            QtGui.QMessageBox.Yes | QtGui.QMessageBox.No)
        if choice == QtGui.QMessageBox.Yes:
            print("Extracting ...")
            sys.exit()
        else:
            pass

    def select_file(self):
        self.filename = QtGui.QFileDialog.getOpenFileName(self, "Select file ","", '*.csv *.gpx')
        self.lineEdit.setText(self.filename)

    def convert(self):
        wgs84=Proj("+init=EPSG:4326")
        mercator=Proj("+init=EPSG:3857")
        filename = self.lineEdit.text()
        if not filename:
            print 'file name not exist'
            return

        filePath = unicode(filename)
        path = filePath[:filePath.rfind('/')+1]
        name = filePath[filePath.rfind('/')+1:].split('.')[0]
        ext = filePath[filePath.rfind('/')+1:].split('.')[1]

        if ext == 'csv':
            with open(filePath, 'rb') as file:
                reader = csv.reader(file)
                rows = [r for r in reader]
            type = rows[2][0].split(';')[1]

            root = etree.Element("gpx", version="1.1", creator="convertFromCsv", nsmap={None: 'http://www.topografix.com/GPX/1/1', 'xsi': 'http://www.w3.org/2001/XMLSchema-instance'}, attrib={'schemaLocation': 'http://www.topografix.com/GPX/1/1 http://www.topografix.com/GPX/1/1/gpx.xsd'})
            etree.SubElement(root, "metadata")
            objects = []
            data = []
            for r in rows[4:]:
                data.append([r[0] + '.' + r[1] + '.' + r[2], r[0].split(';')[1]])

            data.sort(key=itemgetter(1))
            polygon = [[x for x, y in g]
                       for k, g in groupby(data, key=itemgetter(1))]

            for points in polygon:
                poly = []
                rte = etree.Element("rte")
                for point in points:
                    point = point.split(';')
                    rtept = etree.SubElement(rte, 'rtept')
                    x, y = transform(mercator, wgs84, point[4], point[3])
                    rtept.set('lat', str(y))
                    rtept.set('lon', str(x))
                root.append(etree.XML(etree.tostring(rte)))

            handle = etree.tostring(root, pretty_print=True, encoding='utf-8', xml_declaration=True)
            applic = open(os.path.join(path, name + '.gpx'), "w")
            applic.writelines(handle)
            applic.close()
        elif ext == 'gpx':
            def writeData(string):
                text = string.decode('utf8')
                string = text.encode('cp1251')
                output_file.write(string)

            geometryType = ''
            rings = None
            layer = fiona.open(filePath, layer='tracks')
            for f in layer:
                g = f['geometry']
                if g['type'] == 'MultiLineString':
                    geometryType = 'MULTILINESTRING'
                rings = g['coordinates']
            
            output_file = open(os.path.join(path, name + '.csv'), 'w')
            writeData('Полное наименование:;\n')
            writeData('Кадастровый (иной) номер:;\n')
            writeData( 'Тип геометрии:;{}\n'.format( geometryType ) )
            writeData( 'Часть;Контур;№п/п;X;Y\n' )
            
            featureCount = 1
            count = 1
            pointCount = 1
            
            for p in rings[0]:
                writeData( '{};{};{};{};{}\n'.format(featureCount, count, pointCount, str(p[0]).replace(".", ","), str(p[1]).replace(".", ",") ) )
                pointCount = pointCount + 1

            output_file.close()
        sys.exit()
app = QtGui.QApplication(sys.argv)
GUI = Window()
sys.exit(app.exec_())