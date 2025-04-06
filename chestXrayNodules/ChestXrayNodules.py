import logging
import os
from typing import Annotated, Optional

import vtk

import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)

from slicer import vtkMRMLScalarVolumeNode
import subprocess
import docker
import slicer
import os
import random
from PIL import Image
import numpy as np
import vtk
from vtk.util import numpy_support
import time
import json
#
# ChestXrayNodules
#


class ChestXrayNodules(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("ChestXrayNodules")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#ChestXrayNodules">module documentation</a>.
""")
        # TODO: replace with organization, grant and thanks
        self.parent.acknowledgementText = _("""
This file was originally developed by Jean-Christophe Fillion-Robin, Kitware Inc., Andras Lasso, PerkLab,
and Steve Pieper, Isomics, Inc. and was partially funded by NIH grant 3P41RR013218-12S1.
""")

        # Additional initialization step after application startup is complete
        slicer.app.connect("startupCompleted()", registerSampleData)


#
# Register sample data sets in Sample Data module
#


def registerSampleData():
    """Add data sets to Sample Data module."""
    # It is always recommended to provide sample data for users to make it easy to try the module,
    # but if no sample data is available then this method (and associated startupCompeted signal connection) can be removed.

    import SampleData

    iconsPath = os.path.join(os.path.dirname(__file__), "Resources/Icons")

    # To ensure that the source code repository remains small (can be downloaded and installed quickly)
    # it is recommended to store data sets that are larger than a few MB in a Github release.

    # ChestXrayNodules1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="ChestXrayNodules",
        sampleName="ChestXrayNodules1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "ChestXrayNodules1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="ChestXrayNodules1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="ChestXrayNodules1",
    )

    # ChestXrayNodules2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="ChestXrayNodules",
        sampleName="ChestXrayNodules2",
        thumbnailFileName=os.path.join(iconsPath, "ChestXrayNodules2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="ChestXrayNodules2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="ChestXrayNodules2",
    )


#
# ChestXrayNodulesParameterNode
#


@parameterNodeWrapper
class ChestXrayNodulesParameterNode:
    """
    The parameters needed by module.

    inputVolume - The volume to threshold.
    imageThreshold - The value at which to threshold the input volume.
    invertThreshold - If true, will invert the threshold.
    thresholdedVolume - The output volume that will contain the thresholded volume.
    invertedVolume - The output volume that will contain the inverted thresholded volume.
    """

    inputVolume: vtkMRMLScalarVolumeNode
    imageThreshold: Annotated[float, WithinRange(-100, 500)] = 100
    invertThreshold: bool = False
    thresholdedVolume: vtkMRMLScalarVolumeNode
    invertedVolume: vtkMRMLScalarVolumeNode


#
# ChestXrayNodulesWidget
#


class ChestXrayNodulesWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
    """Uses ScriptedLoadableModuleWidget base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent=None) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.__init__(self, parent)
        VTKObservationMixin.__init__(self)  # needed for parameter node observation
        self.logic = None
        self._parameterNode = None
        self._parameterNodeGuiTag = None
        self.confidence_score = None

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/ChestXrayNodules.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = ChestXrayNodulesLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.InferencePushButton.connect('clicked(bool)', self.onInferencePushButton) # inference push button
        self.ui.HomePagePushButton.connect('clicked(bool)', self.onHomePagePushButton) # home page push button
        self.ui.ClearBbxPushButton.connect('clicked(bool)', self.onClearBbxPushButton) # clear bounding box push button
        # slider
        confidenceScoreSlider = self.ui.ConfidenceScoreSlider  # 根据你的objectName获取滑动条
        confidenceScoreSlider.connect('valueChanged(double)', self.onConfidenceScoreSliderValueChanged)

        # Make sure parameter node is initialized (needed for module reload)
        self.initializeParameterNode()

    def cleanup(self) -> None:
        """Called when the application closes and the module widget is destroyed."""
        self.removeObservers()

    def enter(self) -> None:
        """Called each time the user opens this module."""
        # Make sure parameter node exists and observed
        self.initializeParameterNode()

    def exit(self) -> None:
        """Called each time the user opens a different module."""
        # Do not react to parameter node changes (GUI will be updated when the user enters into the module)
        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self._parameterNodeGuiTag = None
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

    def onSceneStartClose(self, caller, event) -> None:
        """Called just before the scene is closed."""
        # Parameter node will be reset, do not use it anymore
        self.setParameterNode(None)

    def onSceneEndClose(self, caller, event) -> None:
        """Called just after the scene is closed."""
        # If this module is shown while the scene is closed then recreate a new parameter node immediately
        if self.parent.isEntered:
            self.initializeParameterNode()

    def initializeParameterNode(self) -> None:
        """Ensure parameter node exists and observed."""
        # Parameter node stores all user choices in parameter values, node selections, etc.
        # so that when the scene is saved and reloaded, these settings are restored.

        self.setParameterNode(self.logic.getParameterNode())

        # Select default input nodes if nothing is selected yet to save a few clicks for the user
        if not self._parameterNode.inputVolume:
            firstVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
            if firstVolumeNode:
                self._parameterNode.inputVolume = firstVolumeNode

    def setParameterNode(self, inputParameterNode: Optional[ChestXrayNodulesParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            # self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            # self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            # self._checkCanApply()

    '''customized widgets' buttons'''
    # confidence slider
    def onConfidenceScoreSliderValueChanged(self, value):
        self.confidence_score = value

    # inference button
    def onInferencePushButton(self):
        # 創建 Docker 客戶端
        client = docker.from_env()

        # 定義容器參數
        image = "chestyolov5" # 指定映像檔名稱
        container_name = image + "_container"  # 給定容器指定名字

        # 獲取所有容器名稱
        all_containers = client.containers.list(all=True)

        # 搜尋名稱相同的容器
        matching_containers = [container for container in all_containers if container_name in container.name]
        if matching_containers:
            print("Container already exists and will be reused.")
            container = matching_containers[0]  # 重新啟用現有容器
            if container.status != "running":
                container.start()
        else:
            # 若容器不存在，則串建新容器
            volumes = {
                r"D:\Jonathan\AI_on_3Dslicer\Chest_YOLO_v4\chestxray\docker\nrrd": {'bind': '/workfolder/nrrd', 'mode': 'rw'},
                r"D:\Jonathan\AI_on_3Dslicer\Chest_YOLO_v4\chestxray\docker\png": {'bind': '/workfolder/png', 'mode': 'rw'},
                r"D:\Jonathan\AI_on_3Dslicer\Chest_YOLO_v4\chestxray\docker\result": {'bind': '/workfolder/result', 'mode': 'rw'}
            }
            container = client.containers.run(image, detach=True, name=container_name, volumes=volumes, auto_remove=False, device_requests=[docker.types.DeviceRequest(device_ids=['0'], capabilities=[['gpu']])])

        '''將slicer當前開啟的dcm檔案複製到local資料夾'''
        # 設定輸出資料夾路徑
        exportDir = r"D:\Jonathan\AI_on_3Dslicer\Chest_YOLO_v4\chestxray\docker\nrrd"

        # 檢查資料夾是否存在
        if not os.path.exists(exportDir):
            print("no such directory")

        # 獲取當前volume
        activeVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")
        if activeVolumeNode is not None:
            # 生成隨機五位數字
            randomFileName = f"{random.randint(10000, 99999)}"
            
            # 使用隨機五位數字作為檔案名稱
            exportFilePath = os.path.join(exportDir, f"{randomFileName}.nrrd")
            
            # 將當前volume保存至nrrd資料夾
            result = slicer.util.saveNode(activeVolumeNode, exportFilePath)
            if result:
                print(f"Volume exported to {exportFilePath}")
            else:
                print("Failed to export volume.")
        else:
            print("No active volume node found.")

        '''對container下指令'''
        basename = randomFileName + '.nrrd'
        command = "python /workfolder/main.py --run-type inference --input " + basename + ' --confidence ' + str(self.confidence_score)
        execute = container.exec_run(cmd=command)

        '''抓到result的json檔案，並呈現在3d slicer'''
        ResultFolderPath = r"D:\Jonathan\AI_on_3Dslicer\Chest_YOLO_v4\chestxray\docker\result"
        result_name = basename + '_result.json'
        jsonPath = os.path.join(ResultFolderPath, result_name)

        imageNode = slicer.mrmlScene.GetFirstNodeByClass('vtkMRMLScalarVolumeNode')
        imageToRAS = vtk.vtkMatrix4x4()
        imageNode.GetIJKToRASMatrix(imageToRAS)

        def create_line_node(start_point, end_point, index):
            lineNode = slicer.mrmlScene.AddNewNodeByClass('vtkMRMLMarkupsLineNode', f"{index}")
            lineNode.AddControlPointWorld(vtk.vtkVector3d(start_point))
            lineNode.AddControlPointWorld(vtk.vtkVector3d(end_point))
            displayNode = lineNode.GetDisplayNode()
            if displayNode:
                displayNode.SetColor(1.0, 0.0, 0.0)  # 红色
                displayNode.SetLineWidth(4)

        ### 等待運算結果出現 ###
        while not os.path.exists(jsonPath):
            time.sleep(1)

        ### 抓取json檔案，並成現在slicer ###
        if os.path.exists(jsonPath):
            # 讀取json檔案
            with open(jsonPath, 'r') as f:
                data = json.load(f)

            # 獲得當前紅色視窗node名稱
            compositeNode = slicer.app.layoutManager().sliceWidget("Red").mrmlSliceCompositeNode()
            volumeNodeID = compositeNode.GetBackgroundVolumeID()
            volumeNode = slicer.mrmlScene.GetNodeByID(volumeNodeID)
            if volumeNode is not None:
                nodeName = volumeNode.GetName()
                print("當前圖像節點名稱: ", nodeName)
            else:
                print("沒有圖現節點被選中")
                
            bounding_boxes = data['bounding_boxes']
            
            for index, bbox in enumerate(bounding_boxes):
                # 计算矩形的四个角点并进行坐标转换
                corners = [
                    (bbox['left'], bbox['bottom']), # 左下
                    (bbox['left'], bbox['top']),    # 左上
                    (bbox['right'], bbox['top']),   # 右上
                    (bbox['right'], bbox['bottom']) # 右下
                ]
                ras_corners = []
                for corner in corners:
                    ijk = [corner[0], corner[1], 0, 1]  # 假设Z坐标为0，添加1以适应齐次坐标
                    ras = imageToRAS.MultiplyPoint(ijk)[:3]  # 转换坐标并去除齐次坐标的部分
                    ras_corners.append(ras)
                
                # 创建四个线段
                create_line_node(ras_corners[0], ras_corners[1], index) # bottom_left_to_top_left
                create_line_node(ras_corners[1], ras_corners[2], index) # top_left_to_top_right
                create_line_node(ras_corners[2], ras_corners[3], index) # top_right_to_bottom_right
                create_line_node(ras_corners[3], ras_corners[0], index) # bottom_right_to_bottom_left
        else:
            print(f"File does not exist: {jsonPath}")

        container.stop()
        print("container is stopped")
        
    # clear bounding box
    def onClearBbxPushButton(self):
        bbxNumber = self.ui.BbxNumberSpinBox.value  # 獲取spin box 的值
        # 建立搜尋關鍵字"Line_{bbxNumber}_"
        searchKeyword = f"{bbxNumber}"
        # 查找並刪除符合關鍵字之項目
        allLineNodes = slicer.util.getNodesByClass('vtkMRMLMarkupsLineNode')
        for lineNode in allLineNodes:
            if searchKeyword in lineNode.GetName():
                slicer.mrmlScene.RemoveNode(lineNode) # 刪除node

    # back to home page button
    def onHomePagePushButton(self):
        slicer.util.selectModule('homePage')
#
# ChestXrayNodulesLogic
#


class ChestXrayNodulesLogic(ScriptedLoadableModuleLogic):
    """This class should implement all the actual
    computation done by your module.  The interface
    should be such that other python code can import
    this class and make use of the functionality without
    requiring an instance of the Widget.
    Uses ScriptedLoadableModuleLogic base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self) -> None:
        """Called when the logic class is instantiated. Can be used for initializing member variables."""
        ScriptedLoadableModuleLogic.__init__(self)

    def getParameterNode(self):
        return ChestXrayNodulesParameterNode(super().getParameterNode())

    def process(self,
                inputVolume: vtkMRMLScalarVolumeNode,
                outputVolume: vtkMRMLScalarVolumeNode,
                imageThreshold: float,
                invert: bool = False,
                showResult: bool = True) -> None:
        """
        Run the processing algorithm.
        Can be used without GUI widget.
        :param inputVolume: volume to be thresholded
        :param outputVolume: thresholding result
        :param imageThreshold: values above/below this threshold will be set to 0
        :param invert: if True then values above the threshold will be set to 0, otherwise values below are set to 0
        :param showResult: show output volume in slice viewers
        """

        if not inputVolume or not outputVolume:
            raise ValueError("Input or output volume is invalid")

        import time

        startTime = time.time()
        logging.info("Processing started")

        # Compute the thresholded output volume using the "Threshold Scalar Volume" CLI module
        cliParams = {
            "InputVolume": inputVolume.GetID(),
            "OutputVolume": outputVolume.GetID(),
            "ThresholdValue": imageThreshold,
            "ThresholdType": "Above" if invert else "Below",
        }
        cliNode = slicer.cli.run(slicer.modules.thresholdscalarvolume, None, cliParams, wait_for_completion=True, update_display=showResult)
        # We don't need the CLI module node anymore, remove it to not clutter the scene with it
        slicer.mrmlScene.RemoveNode(cliNode)

        stopTime = time.time()
        logging.info(f"Processing completed in {stopTime-startTime:.2f} seconds")

#
# ChestXrayNodulesTest
#

class ChestXrayNodulesTest(ScriptedLoadableModuleTest):
    """
    This is the test case for your scripted module.
    Uses ScriptedLoadableModuleTest base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def setUp(self):
        """Do whatever is needed to reset the state - typically a scene clear will be enough."""
        slicer.mrmlScene.Clear()

    def runTest(self):
        """Run as few or as many tests as needed here."""
        self.setUp()
        self.test_ChestXrayNodules1()

    def test_ChestXrayNodules1(self):
        """Ideally you should have several levels of tests.  At the lowest level
        tests should exercise the functionality of the logic with different inputs
        (both valid and invalid).  At higher levels your tests should emulate the
        way the user would interact with your code and confirm that it still works
        the way you intended.
        One of the most important features of the tests is that it should alert other
        developers when their changes will have an impact on the behavior of your
        module.  For example, if a developer removes a feature that you depend on,
        your test should break so they know that the feature is needed.
        """

        self.delayDisplay("Starting the test")

        # Get/create input data

        import SampleData

        registerSampleData()
        inputVolume = SampleData.downloadSample("ChestXrayNodules1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = ChestXrayNodulesLogic()

        # Test algorithm with non-inverted threshold
        logic.process(inputVolume, outputVolume, threshold, True)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], threshold)

        # Test algorithm with inverted threshold
        logic.process(inputVolume, outputVolume, threshold, False)
        outputScalarRange = outputVolume.GetImageData().GetScalarRange()
        self.assertEqual(outputScalarRange[0], inputScalarRange[0])
        self.assertEqual(outputScalarRange[1], inputScalarRange[1])

        self.delayDisplay("Test passed")


