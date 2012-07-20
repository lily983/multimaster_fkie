# Software License Agreement (BSD License)
#
# Copyright (c) 2012, Fraunhofer FKIE/US, Alexander Tiderko
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above
#    copyright notice, this list of conditions and the following
#    disclaimer in the documentation and/or other materials provided
#    with the distribution.
#  * Neither the name of I Heart Engineering nor the names of its
#    contributors may be used to endorse or promote products derived
#    from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

from PySide import QtCore, QtGui

import sys
import roslib
import rospy
import node_manager_fkie as nm

from parameter_handler import ParameterHandler

class ParameterDescription(object):
  def __init__(self, name, msg_type, value=None, widget=None):
    self._name = name
    self._type = msg_type
    if isinstance(self._type, dict):
      self._type = 'dict'
    elif isinstance(self._type, list):
      self._type = 'list'
    self._value = value
    self._widget = widget
    self._base_type, self._is_array_type, array_length = roslib.msgs.parse_type(self._type)
    self._is_primitive_type =  self._base_type in roslib.msgs.PRIMITIVE_TYPES or self._base_type in ['int', 'float', 'time', 'duration']
    self._is_time_type = self._base_type in ['time', 'duration']
  
  def name(self):
    return self._name
  
  def setWidget(self, widget):
    self._widget = widget
    self.addCachedValuesToWidget()
  
  def widget(self):
    return self._widget

  def fullName(self):
    result = self.name()
    widget = self._widget
    while not widget is None:
      if isinstance(widget, (MainBox, GroupBox, ArrayBox)):
        result = roslib.names.ns_join(widget.name, result)
      widget = widget.parent()
    return result

  def isArrayType(self):
    return self._is_array_type

  def isPrimitiveType(self):
    return self._is_primitive_type

  def isTimeType(self):
    return self._is_time_type
  
  def baseType(self):
    return self._base_type
  
  def updateValueFromField(self):
    field = self.widget()
    result = ''
    if isinstance(field, QtGui.QCheckBox):
      result = repr(field.isChecked())
    elif isinstance(field, QtGui.QLineEdit):
      result = field.text()
    elif isinstance(field, QtGui.QComboBox):
      result = field.currentText()
    self.setValue(result)

  def setValue(self, value):
    try:
      if isinstance(value, (dict, list)):
        self._value = value
      elif value:
        self.addParamCache(self.fullName(), self._value)
        if self.isArrayType():
          if 'int' in self.baseType():
            self._value = map(int, value.split(','))
          elif 'float' in self.baseType():
            self._value = map(float, value.split(','))
          elif 'bool' in self.baseType():
            self._value = map(bool, value.split(','))
          else:
            self._value = [ s.encode(sys.getfilesystemencoding()) for s in value.split(',')]
        else:
          if 'int' in self.baseType():
            self._value = int(value)
          elif 'float' in self.baseType():
            self._value = float(value)
          elif 'bool' in self.baseType():
            self._value = bool(value)
          elif self.isTimeType():
            if value == 'now':
              self._value = 'now'
            else:
              val = float(value)
              secs = int(val)
              nsecs = int((val - secs) * 1000000000)
              self._value = {'secs': secs, 'nsecs': nsecs}
          else:
            self._value = value.encode(sys.getfilesystemencoding())
      else:
        if self.isArrayType():
          arr = []
          self._value = arr
        else:
          if 'int' in self.baseType():
            self._value = 0
          elif 'float' in self.baseType():
            self._value = 0.0
          elif 'bool' in self.baseType():
            self._value = False
          elif self.isTimeType():
            self._value = {'secs': 0, 'nsecs': 0}
          else:
            self._value = ''
      self.addParamCache(self.fullName(), value)
    except Exception, e:
      raise Exception(''.join(["Error while set value '", unicode(value), "' for '", self.fullName(), "': ", str(e)]))
    return self._value

  def value(self):
    return self._value

  def cachedValues(self):
    try:
      return nm.PARAM_CACHE[self.fullName()]
    except:
      result = []
      return result

  def addParamCache(self, key, value):
    if value:
      if not nm.PARAM_CACHE.has_key(key):
        nm.PARAM_CACHE[key] = [unicode(value)]
      elif not key in nm.PARAM_CACHE[key]:
        nm.PARAM_CACHE[key].append(unicode(value))


  def createTypedWidget(self, parent):
    result = None
    if self.isPrimitiveType():
      if 'bool' in self.baseType():
        result = QtGui.QCheckBox(parent=parent)
        result.setObjectName(self.name())
        result.setChecked(bool(self.value()))
      else:
        result = QtGui.QComboBox(parent=parent)
        result.setObjectName(self.name())
        result.setSizePolicy(QtGui.QSizePolicy(QtGui.QSizePolicy.Expanding, QtGui.QSizePolicy.Fixed))
        result.setEditable(True)
        items = []
        if isinstance(self.value(), list):
          items[len(items):] = self.value()
        else:
          if not self.value() is None and self.value():
            items.append(unicode(self.value()))
          elif self.isTimeType():
            items.append(now)
        result.addItems(items)
    else:
      if self.isArrayType():
        result = ArrayBox(self.name(), self._type, parent=parent)
      else:
        result = GroupBox(self.name(), self._type, parent=parent)
    return result

  def addCachedValuesToWidget(self):
    if isinstance(self.widget(), QtGui.QComboBox):
      values = self.cachedValues()
      try:
        values.remove(self.widget().currentText())
      except:
        pass
      self.widget().addItems(values)

class MainBox(QtGui.QWidget):
  def __init__(self, name, type, parent=None):
    QtGui.QWidget.__init__(self, parent)
    self.setObjectName(name)
    self.name = name
    self.type = type
    self.createLayout()
  
  def createLayout(self):
    boxLayout = QtGui.QFormLayout()
    boxLayout.setVerticalSpacing(0)
    self.setLayout(boxLayout)
  
  def createFieldFromValue(self, value):
    self.setUpdatesEnabled(False)
    if isinstance(value, list):
      for v in value:
        if isinstance(v, dict):
          self._createFieldFromDict(v)
          line = QtGui.QFrame()
          line.setFrameShape(QtGui.QFrame.HLine)
          line.setFrameShadow(QtGui.QFrame.Sunken)
          line.setObjectName("__line__")
          self.layout().addRow(line)
        #@TODO add an ADD button
    elif isinstance(value, dict):
      self._createFieldFromDict(value)
    self.setUpdatesEnabled(True)
        
  def _createFieldFromDict(self, value):
    for name, (_type, val) in sorted(value.iteritems(), key=lambda (k,v): (k.lower(),v)):
      if not hasattr(self, 'params'):
        self.params = []
      field = self.getField(name)
      if field is None:
        param_desc = ParameterDescription(name, _type, val)
        self.params.append(param_desc)
        field = param_desc.createTypedWidget(self)
        param_desc.setWidget(field)
        if isinstance(field, (GroupBox, ArrayBox)):
          field.createFieldFromValue(val)
          self.layout().addRow(field)
        else:
          label_name = name if _type == 'string' else ''.join([name, ' (', _type, ')'])
          label = QtGui.QLabel(label_name, self)
          label.setObjectName(''.join([name, '_label']))
          label.setBuddy(field)
          self.layout().addRow(label, field)
      else:
        if isinstance(field, (GroupBox, ArrayBox)):
          field.createFieldFromValue(val)
        else:
          self.setUpdatesEnabled(True)
          raise Exception(''.join(["Parameter with name '", name, "' already exists!"]))

  def value(self):
    if isinstance(self, ArrayBox):
      result = list()
      result_dict = dict()
      result.append(result_dict)
    else:
      result = result_dict = dict()
    if hasattr(self, 'params'):
      for param in self.params:
        if param.isPrimitiveType():
          param.updateValueFromField()
          result_dict[param.name()] = param.value()
        elif isinstance(param.widget(), (GroupBox, GroupBox)):
          result_dict[param.name()] = param.widget().value()
    return result

  def getField(self, name):
    for child in self.children():
      if child.objectName() == name:
        return child
    return None

  def filter(self, arg):
    '''
    Hide the parameter input field, which label dosn't contains the C{arg}.
    @param arg: the filter text
    @type art: C{str}
    '''
    for child in self.children():
      if isinstance(child, (GroupBox, ArrayBox)):
        child.filter(arg)
        show_group = False
        # hide group, if no parameter are visible
        for cchild in child.children():
          if isinstance(cchild, (QtGui.QWidget)) and cchild.objectName() != '__line__' and cchild.isVisible():
            show_group = True
            break
        child.setVisible(show_group)
      elif isinstance(child, (QtGui.QWidget)) and not isinstance(child, (QtGui.QLabel)):
        label = child.parentWidget().layout().labelForField(child)
        if not label is None:
          show = not (child.objectName().lower().find(arg.lower()) == -1)
          # set the parent group visible if it is not visible
          if show and not child.parentWidget().isVisible():
            child.parentWidget().setVisible(show)
          label.setVisible(show)
          child.setVisible(show)

  def setVisible(self, arg):
    if arg and not self.parentWidget() is None and not self.parentWidget().isVisible():
      self.parentWidget().setVisible(arg)
    QtGui.QWidget.setVisible(self, arg)


class GroupBox(QtGui.QGroupBox, MainBox):
  def __init__(self, name, type, parent=None):
    QtGui.QGroupBox.__init__(self, ''.join([name, ' (', type, ')']), parent)
    self.setObjectName(name)
    self.name = name
    self.type = type
    self.setAlignment(QtCore.Qt.AlignLeft)
    self.createLayout()

class ArrayBox(GroupBox):
  def __init__(self, name, type, parent=None):
    GroupBox.__init__(self, name, type, parent)
    self.setFlat(True)



class ScrollArea(QtGui.QScrollArea):
  
  def viewportEvent(self, arg):
    if self.widget() and self.viewport().size().width() != self.widget().maximumWidth():
      self.widget().setMaximumWidth(self.viewport().size().width())
    return QtGui.QScrollArea.viewportEvent(self, arg)


class ParameterDialog(QtGui.QDialog):
  '''
  This dialog creates an input mask for the given slots and their types.
  '''

  def __init__(self, params=dict(), masteruri=None, ns='/', buttons=QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok, parent=None):
    '''
    Creates an input dialog.
    @param params: a dictionary with parameter names and (type, values). 
    The C{value}, can be a primitive value, a list with values or parameter 
    dictionary to create groups. In this case the type is the name of the group.
    @type params: C{dict(str:(str, {value, [..], dict()}))}
    @param masteruri: if the master uri is not None, the parameter are retrieved from ROS parameter server.
    @type masteruri: C{str}
    @param ns: namespace of the parameter retrieved from the ROS parameter server. Only used if C{masteruri} is not None.
    @type ns: C{str}
    '''
    QtGui.QDialog.__init__(self, parent=parent)
    self.setObjectName(' - '.join(['ParameterDialog', str(params) if params else str(masteruri)]))
    self.masteruri = masteruri
    self.ns = ns

    self.verticalLayout = QtGui.QVBoxLayout(self)
    self.verticalLayout.setObjectName("verticalLayout")
    self.verticalLayout.setContentsMargins(1, 1, 1, 1)
    # add filter row
    self.filter_frame = QtGui.QFrame(self)
    filterLayout = QtGui.QHBoxLayout(self.filter_frame)
    filterLayout.setContentsMargins(1, 1, 1, 1)
    label = QtGui.QLabel("Filter:", self.filter_frame)
    self.filter_field = QtGui.QLineEdit(self.filter_frame)
    filterLayout.addWidget(label)
    filterLayout.addWidget(self.filter_field)
    self.filter_field.textChanged.connect(self._on_filter_changed)
    self.filter_visible = True

    self.verticalLayout.addWidget(self.filter_frame)
    
    # create area for the parameter
    self.scrollArea = scrollArea = ScrollArea(self);
    scrollArea.setObjectName("scrollArea")
    scrollArea.setWidgetResizable(True)
#    scrollArea.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
    self.content = MainBox(ns, 'str', self)
    scrollArea.setWidget(self.content)
    self.verticalLayout.addWidget(scrollArea)

    # add info text field
    self.info_field = QtGui.QTextEdit(self)
    self.info_field.setVisible(False)
    palette = QtGui.QPalette()
    brush = QtGui.QBrush(QtGui.QColor(255, 254, 242))
    brush.setStyle(QtCore.Qt.SolidPattern)
    palette.setBrush(QtGui.QPalette.Active, QtGui.QPalette.Base, brush)
    brush = QtGui.QBrush(QtGui.QColor(255, 254, 242))
    brush.setStyle(QtCore.Qt.SolidPattern)
    palette.setBrush(QtGui.QPalette.Inactive, QtGui.QPalette.Base, brush)
    brush = QtGui.QBrush(QtGui.QColor(244, 244, 244))
    brush.setStyle(QtCore.Qt.SolidPattern)
    palette.setBrush(QtGui.QPalette.Disabled, QtGui.QPalette.Base, brush)
    self.info_field.setPalette(palette)
    self.info_field.setFrameShadow(QtGui.QFrame.Plain)
    self.info_field.setReadOnly(True)
    self.info_field.setTextInteractionFlags(QtCore.Qt.LinksAccessibleByKeyboard|QtCore.Qt.LinksAccessibleByMouse|QtCore.Qt.TextBrowserInteraction|QtCore.Qt.TextSelectableByKeyboard|QtCore.Qt.TextSelectableByMouse)
    self.info_field.setObjectName("dialog_info_field")
    self.verticalLayout.addWidget(self.info_field)

    # create buttons
    self.buttonBox = QtGui.QDialogButtonBox(self)
    self.buttonBox.setObjectName("buttonBox")
    self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
    self.buttonBox.setStandardButtons(buttons)
    self.buttonBox.accepted.connect(self.accept)
    self.buttonBox.rejected.connect(self.reject)
    if not masteruri is None:
      self.add_new_button = QtGui.QPushButton(self.tr("&Add"))
      self.add_new_button.clicked.connect(self._on_add_parameter)
      self.buttonBox.addButton(self.add_new_button, QtGui.QDialogButtonBox.ActionRole)
    self.verticalLayout.addWidget(self.buttonBox)

    # set the input fields
    if params:
      self.content.createFieldFromValue(params)
      self.setInfoActive(False)

    self.is_delivered = False
    self.is_send = False
    if not masteruri is None:
      self.resize(450,300)
      self.mIcon = QtGui.QIcon(":/icons/default_cfg.png")
      self.setWindowIcon(self.mIcon)
      self.setText(' '.join(['Obtaining parameters from the parameter server', masteruri, '...']))
      self.parameterHandler = ParameterHandler()
      self.parameterHandler.parameter_list_signal.connect(self._on_param_list)
      self.parameterHandler.parameter_values_signal.connect(self._on_param_values)
      self.parameterHandler.delivery_result_signal.connect(self._on_delivered_values)
      self.parameterHandler.requestParameterList(masteruri, ns)
      
    self.filter_field.setFocus()
#    print '=============== create', self.objectName()
#
#  def __del__(self):
#    print "************ destroy", self.objectName()

  def _on_filter_changed(self):
    self.content.filter(self.filter_field.text())

  def setFilterVisible(self, val):
    '''
    Shows or hides the filter row.
    '''
    self.filter_visible = val
    self.filter_frame.setVisible(val&self.scrollArea.isHidden())

  def setText(self, text):
    '''
    Adds a label to the dialog's layout and shows the given text.
    @param text: the text to add to the dialog
    @type text: C{str}
    '''
    self.info_field.setText(text)
    self.setInfoActive(True)

  def setInfoActive(self, val):
    if val and self.info_field.isHidden():
      self.filter_frame.setVisible(False&self.filter_visible)
      self.scrollArea.setVisible(False)
      self.info_field.setVisible(True)
    elif not val and self.scrollArea.isHidden():
      self.filter_frame.setVisible(True&self.filter_visible)
      self.scrollArea.setVisible(True)
      self.info_field.setVisible(False)
      if self.filter_frame.isVisible():
        self.filter_field.setFocus()


  def getKeywords(self, skip_empty=False, use_group_as_namespace=False):
    '''
    @returns: a directory with parameter and value for all entered fields.
    @rtype: C{dict(str(param) : str(value))}
    '''
    return self.content.value()


#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%          ROS parameter handling       %%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%


  def _on_add_parameter(self):
    params_arg = {'namespace' : ('string', self.ns), 'name' : ('string', ''), 'type' : ('string', ['string', 'int', 'float', 'bool']), 'value' : ('string', '') }
    dia = ParameterDialog(params_arg)
    dia.setFilterVisible(False)
    if dia.exec_():
      try:
        params = dia.getKeywords()
        if params['type'] == 'int':
          value = int(params['value'])
        elif params['type'] == 'float':
          value = float(params['value'])
        elif params['type'] == 'bool':
          value = bool(params['value'])
        else:
          value = params['value']
        self._on_param_values(self.masteruri, 1, '', {roslib.names.ns_join(params['namespace'], params['name']) : (1, '', value)})
      except ValueError, e:
        QtGui.QMessageBox.warning(self, self.tr("Warning"), unicode(e), QtGui.QMessageBox.Ok)

  def _on_param_list(self, masteruri, code, msg, params):
    '''
    @param masteruri: The URI of the ROS parameter server
    @type masteruri: C{str}
    @param code: The return code of the request. If not 1, the message is set and the list can be ignored.
    @type code: C{int}
    @param msg: The message of the result. 
    @type msg: C{str}
    @param params: The list the parameter names.
    @type param: C{[str]}
    '''
    if code == 1:
      params.sort()
      self.parameterHandler.requestParameterValues(masteruri, params)
    else:
      self.setText(msg)
      
  def _on_param_values(self, masteruri, code, msg, params):
    '''
    @param masteruri: The URI of the ROS parameter server
    @type masteruri: C{str}
    @param code: The return code of the request. If not 1, the message is set and the list can be ignored.
    @type code: C{int}
    @param msg: The message of the result. 
    @type msg: C{str}
    @param params: The dictionary the parameter names and request result.
    @type param: C{dict(paramName : (code, statusMessage, parameterValue))}
    '''
    if code == 1:
      self.setText('')
      values = dict()
      dia_params = dict()
      for p, (code_n, msg_n, val) in params.items():
        if code_n != 1:
          val = ''
        type_str = 'string'
        value = val
        if isinstance(val, bool):
          type_str = 'bool'
        elif isinstance(val, int):
          type_str = 'int'
        elif isinstance(val, float):
          type_str = 'float'
        elif isinstance(val, list) or isinstance(val, dict):
          value = unicode(val)
        param = p.replace(self.ns, '')
        names_sep = param.split(roslib.names.SEP)
        param_name = names_sep.pop()
        if names_sep:
          group = dia_params
          for n in names_sep:
            group_name = n
            if group.has_key(group_name):
              group = group[group_name][1]
            else:
              tmp_dict = dict()
              group[group_name] = (n, tmp_dict)
              group = tmp_dict
          group[param_name] = (type_str, value)
        else:
          dia_params[param_name] = (type_str, value)
      try:
        self.content.createFieldFromValue(dia_params)
        self.setInfoActive(False)
      except Exception, e:
        QtGui.QMessageBox.warning(self, self.tr("Warning"), unicode(e), QtGui.QMessageBox.Ok)
    else:
      self.setText(msg)

  def _on_delivered_values(self, masteruri, code, msg, params):
    '''
    @param masteruri: The URI of the ROS parameter server
    @type masteruri: C{str}
    @param code: The return code of the request. If not 1, the message is set and the list can be ignored.
    @type code: C{int}
    @param msg: The message of the result. 
    @type msg: C{str}
    @param params: The dictionary the parameter names and request result.
    @type param: C{dict(paramName : (code, statusMessage, parameterValue))}
    '''
    self.is_delivered = True
    errmsg = ''
    if code == 1:
      for p, (code_n, msg, val) in params.items():
        if code_n != 1:
          errmsg = '\n'.join([errmsg, msg])
    else:
      errmsg = msg if msg else 'Unknown error on set parameter'
    if errmsg:
      QtGui.QMessageBox.warning(self, self.tr("Warning"), errmsg, QtGui.QMessageBox.Ok)
      self.is_delivered = False
      self.is_send = False
      self.setInfoActive(False)
    if self.is_delivered:
      self.close()

#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%% close handling                        %%%%%%%%%%%%%%%%%%%%%
#%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

  def accept(self):
    self.setResult(QtGui.QDialog.Accepted)
    self.hide()
  
  def reject(self):
    self.setResult(QtGui.QDialog.Rejected)
    self.hide()

  def hideEvent(self, event):
    self.close()

  def closeEvent (self, event):
    '''
    Test the open files for changes and save this if needed.
    '''
    if not self.masteruri is None and self.result() == QtGui.QDialog.Accepted and not self.is_send:
      try:
        params = self.getKeywords(use_group_as_namespace=True)
        ros_params = dict()
        for p,v in params.items():
          ros_params[roslib.names.ns_join(self.ns, p)] = v
        if ros_params:
          self.is_send = True
          self.setText('Send the parameter into server...')
          self.parameterHandler.deliverParameter(self.masteruri, ros_params)
          event.ignore()
        else:
          event.accept()
      except Exception, e:
        QtGui.QMessageBox.warning(self, self.tr("Warning"), str(e), QtGui.QMessageBox.Ok)
    else:
      event.accept()

    if event.isAccepted():
      self.setAttribute(QtCore.Qt.WA_DeleteOnClose, True)
      QtGui.QDialog.closeEvent(self, event)
