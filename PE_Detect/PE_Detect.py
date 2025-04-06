import logging
import os
from typing import Annotated, Optional
import random
import vtk
import docker
import slicer
from slicer.i18n import tr as _
from slicer.i18n import translate
from slicer.ScriptedLoadableModule import *
from slicer.util import VTKObservationMixin
from slicer.parameterNodeWrapper import (
    parameterNodeWrapper,
    WithinRange,
)
import json
from slicer import vtkMRMLScalarVolumeNode
import numpy as np
import time
from vtk.util import numpy_support
import shutil
import pydicom

### self-define functions ###
def copy_dicom_files(source_folder, dest_folder_base):
    # 遍历源文件夹中的所有 DICOM 文件
    for root, _, files in os.walk(source_folder):
        for file in files:
            if file.endswith('.dcm'):
                file_path = os.path.join(root, file)
                
                # 读取 DICOM 文件以获取 UID
                ds = pydicom.dcmread(file_path)
                
                # 获取 Study Instance UID 和 Series Instance UID
                study_instance_uid = ds.StudyInstanceUID
                series_instance_uid = ds.SeriesInstanceUID
                
                # 创建目标文件夹路径
                study_folder = os.path.join(dest_folder_base, study_instance_uid)
                series_folder = os.path.join(study_folder, series_instance_uid)
                
                # 确保目标文件夹存在
                if not os.path.exists(series_folder):
                    os.makedirs(series_folder)
                
                # 构建目标文件路径
                dest_file_path = os.path.join(series_folder, file)
                
                # 复制 DICOM 文件
                shutil.copyfile(file_path, dest_file_path)
                # print(f"Copied {file_path} to {dest_file_path}")

def createUpdateLabelFunction(data, mainWindow):
    pe_on_image_label = slicer.util.findChild(mainWindow, 'label_19')

    def updateLabel(caller, event):
        pe_on_image_label = slicer.util.findChild(mainWindow, 'label_19')
        # 獲取當前顯示的切片節點
        sliceNode = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
        sliceLogic = slicer.app.applicationLogic().GetSliceLogic(sliceNode)
        layerLogic = sliceLogic.GetBackgroundLayer()

        # 獲取當前切片的 volume 节點
        SliceVolumeNode = layerLogic.GetVolumeNode()

        # 獲取當前切片的 slice offset
        sliceOffset = sliceNode.GetSliceOffset()

        # 獲取對應於當前 slice offset 的 Instance UID
        if SliceVolumeNode:
            # 獲取 volume 的 image data
            imageData = SliceVolumeNode.GetImageData()
            if imageData:
                # 獲取 slice index 對應於當前的 slice offset
                extent = imageData.GetExtent()
                spacing = SliceVolumeNode.GetSpacing()
                origin = SliceVolumeNode.GetOrigin()
                sliceIndex = int((sliceOffset - origin[2]) / spacing[2])

                if extent[4] <= sliceIndex <= extent[5]:
                    # 獲取 DICOM Instance UID
                    instanceUIDs = SliceVolumeNode.GetAttribute('DICOM.instanceUIDs').split()
                    target_instance_uid = instanceUIDs[sliceIndex]
                    # print(f'Current slice Instance UID: {target_instance_uid}')

                    # 查找並顯示相應的數值
                    pe_on_image_prob = None
                    for item in data:
                        if item['id'] == target_instance_uid:
                            pe_on_image_prob = item['probability']
                            break

                    if pe_on_image_prob is not None:
                        pe_on_image_prob = f"{pe_on_image_prob:.4f}"
                        pe_on_image_label.setText(pe_on_image_prob)
                    else:
                        pe_on_image_label.setText("No data available for current slice")
                else:
                    print('Slice index out of range')
                    pe_on_image_label.setText("Slice index out of range")
            else:
                print('No image data available')
                pe_on_image_label.setText("No image data available")
        else:
            print('No volume node available')
            pe_on_image_label.setText("No volume node available")
    return updateLabel
#
# PE_Detect
#


class PE_Detect(ScriptedLoadableModule):
    """Uses ScriptedLoadableModule base class, available at:
    https://github.com/Slicer/Slicer/blob/main/Base/Python/slicer/ScriptedLoadableModule.py
    """

    def __init__(self, parent):
        ScriptedLoadableModule.__init__(self, parent)
        self.parent.title = _("PE_Detect")  # TODO: make this more human readable by adding spaces
        # TODO: set categories (folders where the module shows up in the module selector)
        self.parent.categories = [translate("qSlicerAbstractCoreModule", "Examples")]
        self.parent.dependencies = []  # TODO: add here list of module names that this module requires
        self.parent.contributors = ["John Doe (AnyWare Corp.)"]  # TODO: replace with "Firstname Lastname (Organization)"
        # TODO: update with short description of the module and a link to online module documentation
        # _() function marks text as translatable to other languages
        self.parent.helpText = _("""
This is an example of scripted loadable module bundled in an extension.
See more information in <a href="https://github.com/organization/projectname#PE_Detect">module documentation</a>.
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

    # PE_Detect1
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="PE_Detect",
        sampleName="PE_Detect1",
        # Thumbnail should have size of approximately 260x280 pixels and stored in Resources/Icons folder.
        # It can be created by Screen Capture module, "Capture all views" option enabled, "Number of images" set to "Single".
        thumbnailFileName=os.path.join(iconsPath, "PE_Detect1.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        fileNames="PE_Detect1.nrrd",
        # Checksum to ensure file integrity. Can be computed by this command:
        #  import hashlib; print(hashlib.sha256(open(filename, "rb").read()).hexdigest())
        checksums="SHA256:998cb522173839c78657f4bc0ea907cea09fd04e44601f17c82ea27927937b95",
        # This node name will be used when the data set is loaded
        nodeNames="PE_Detect1",
    )

    # PE_Detect2
    SampleData.SampleDataLogic.registerCustomSampleDataSource(
        # Category and sample name displayed in Sample Data module
        category="PE_Detect",
        sampleName="PE_Detect2",
        thumbnailFileName=os.path.join(iconsPath, "PE_Detect2.png"),
        # Download URL and target file name
        uris="https://github.com/Slicer/SlicerTestingData/releases/download/SHA256/1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        fileNames="PE_Detect2.nrrd",
        checksums="SHA256:1a64f3f422eb3d1c9b093d1a18da354b13bcf307907c66317e2463ee530b7a97",
        # This node name will be used when the data set is loaded
        nodeNames="PE_Detect2",
    )


#
# PE_DetectParameterNode
#


@parameterNodeWrapper
class PE_DetectParameterNode:
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
# PE_DetectWidget
#


class PE_DetectWidget(ScriptedLoadableModuleWidget, VTKObservationMixin):
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

    def setup(self) -> None:
        """Called when the user opens the module the first time and the widget is initialized."""
        ScriptedLoadableModuleWidget.setup(self)

        # Load widget from .ui file (created by Qt Designer).
        # Additional widgets can be instantiated manually and added to self.layout.
        uiWidget = slicer.util.loadUI(self.resourcePath("UI/PE_Detect.ui"))
        self.layout.addWidget(uiWidget)
        self.ui = slicer.util.childWidgetVariables(uiWidget)

        # Set scene in MRML widgets. Make sure that in Qt designer the top-level qMRMLWidget's
        # "mrmlSceneChanged(vtkMRMLScene*)" signal in is connected to each MRML widget's.
        # "setMRMLScene(vtkMRMLScene*)" slot.
        uiWidget.setMRMLScene(slicer.mrmlScene)

        # Create logic class. Logic implements all computations that should be possible to run
        # in batch mode, without a graphical user interface.
        self.logic = PE_DetectLogic()

        # Connections

        # These connections ensure that we update parameter node when scene is closed
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.StartCloseEvent, self.onSceneStartClose)
        self.addObserver(slicer.mrmlScene, slicer.mrmlScene.EndCloseEvent, self.onSceneEndClose)

        # Buttons
        self.ui.inferencePushButton.connect("clicked(bool)", self.oninferencePushButton)

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
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)

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

    def setParameterNode(self, inputParameterNode: Optional[PE_DetectParameterNode]) -> None:
        """
        Set and observe parameter node.
        Observation is needed because when the parameter node is changed then the GUI must be updated immediately.
        """

        if self._parameterNode:
            self._parameterNode.disconnectGui(self._parameterNodeGuiTag)
            self.removeObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
        self._parameterNode = inputParameterNode
        if self._parameterNode:
            # Note: in the .ui file, a Qt dynamic property called "SlicerParameterName" is set on each
            # ui element that needs connection.
            self._parameterNodeGuiTag = self._parameterNode.connectGui(self.ui)
            self.addObserver(self._parameterNode, vtk.vtkCommand.ModifiedEvent, self._checkCanApply)
            self._checkCanApply()

    # def _checkCanApply(self, caller=None, event=None) -> None:
    #     if self._parameterNode and self._parameterNode.inputVolume and self._parameterNode.thresholdedVolume:
    #         self.ui.applyButton.toolTip = _("Compute output volume")
    #         self.ui.applyButton.enabled = True
    #     else:
    #         self.ui.applyButton.toolTip = _("Select input and output volume nodes")
    #         self.ui.applyButton.enabled = False

    def oninferencePushButton(self) -> None:
        '''創建docker container或重啟現有的container'''
        # 創建 Docker 客戶端
        client = docker.from_env()

        # 定義容器參數
        image = "pedetect_v1" # 指定映像檔名稱
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
            # 若容器不存在，則創建新容器
            print(container_name + ' will be created.')
            volumes = {
                r"D:\Jonathan\AI_on_3Dslicer\PE_detection\RSNA-STR-Pulmonary-Embolism-Detection-main\RSNA-STR-Pulmonary-Embolism-Detection-main\docker\input": {'bind': '/workfolder/input', 'mode': 'rw'},
                r"D:\Jonathan\AI_on_3Dslicer\PE_detection\RSNA-STR-Pulmonary-Embolism-Detection-main\RSNA-STR-Pulmonary-Embolism-Detection-main\docker\result": {'bind': '/workfolder/result', 'mode': 'rw'}
            }
            container = client.containers.run(image, detach=True, name=container_name, volumes=volumes, auto_remove=False, device_requests=[docker.types.DeviceRequest(device_ids=['0'], capabilities=[['gpu']])])

        '''將slicer當前開啟的ct檔案複製到local資料夾'''
        # 設定輸出資料夾路徑
        exportDir = r"D:\Jonathan\AI_on_3Dslicer\PE_detection\RSNA-STR-Pulmonary-Embolism-Detection-main\RSNA-STR-Pulmonary-Embolism-Detection-main\docker\input"

        # 檢查資料夾是否存在
        if not os.path.exists(exportDir):
            print("no such directory")

        # 獲取當前volume
        activeVolumeNode = slicer.mrmlScene.GetFirstNodeByClass("vtkMRMLScalarVolumeNode")

        # 獲取當前影像的上傳位置

        # 确认节点存在
        if activeVolumeNode:
            # 使用 DICOM 数据库获取影像的 DICOM 文件路径
            instanceUIDs = activeVolumeNode.GetAttribute("DICOM.instanceUIDs")
            # print('instanceUIDs= ', instanceUIDs)
            if instanceUIDs:
                instanceUID = instanceUIDs.split()[0]
                # print('instanceUID= ',instanceUID)
                filePath = slicer.dicomDatabase.fileForInstance(instanceUID)
                # print('filePath= ', filePath)
                if filePath:
                    # 读取 DICOM 文件中的 Study Instance UID 和 Series Instance UID
                    study_instance_uid = slicer.dicomDatabase.fileValue(filePath, "0020,000D")
                    series_instance_uid = slicer.dicomDatabase.fileValue(filePath, "0020,000E")
                    # print('seriesInstanceUID= ',series_instance_uid)
                    # print('studyInstanceUID= ',study_instance_uid)
                    upload_dir = os.path.dirname(filePath)
                    copy_dicom_files(upload_dir, exportDir)
                    print('successfully loaded dicom files')

                else:
                    print("Could not retrieve the file path for the given instance UID.")
            else:
                print("Volume node does not have associated DICOM instance UIDs.")
        else:
            print("No volume node found.")
    
        '''對container下指令''' # 大約花30秒
        basename = study_instance_uid + "_" + series_instance_uid
        # print(basename)
        command = "python /workfolder/main.py --run-type inference --input " + basename
        execute = container.exec_run(cmd=command)
        # print(command)

        '''讀取result的json檔'''
        result_folder = r'D:\Jonathan\AI_on_3Dslicer\PE_detection\RSNA-STR-Pulmonary-Embolism-Detection-main\RSNA-STR-Pulmonary-Embolism-Detection-main\docker\result'
        resultDir = os.path.join(result_folder, study_instance_uid + "_" + series_instance_uid + "_result.json")
        print(resultDir)
        if os.path.exists(resultDir):
            with open(resultDir, 'r') as file:
                data = json.load(file)
                # print(data)
        else:
            print("No such file or directory")

        '''顯示fixed probability'''
        negative_exam_for_pe_prob = f"{data[0]['probability']:.4f}"
        indeterminate_prob = f"{data[1]['probability']:.4f}"
        chronic_pe_prob = f"{data[2]['probability']:.4f}"
        acute_and_chronic_pe_prob = f"{data[3]['probability']:.4f}"
        central_pe_prob = f"{data[4]['probability']:.4f}"
        leftsided_pe_prob = f"{data[5]['probability']:.4f}"
        rightsided_pe_prob = f"{data[6]['probability']:.4f}"
        rv_lv_ratio_gte_1_prob = f"{data[7]['probability']:.4f}"
        rv_lv_ratio_lt_1_prob = f"{data[8]['probability']:.4f}"
        # 獲取Text Label元件並更新內容
        mainWindow = slicer.util.mainWindow()
        negative_exam_for_pe_label = slicer.util.findChild(mainWindow, 'label_9')
        negative_exam_for_pe_label.setText(negative_exam_for_pe_prob)

        indeterminate__label = slicer.util.findChild(mainWindow, 'label_20')
        indeterminate__label.setText(indeterminate_prob)

        chronic_pe_label = slicer.util.findChild(mainWindow, 'label_10')
        chronic_pe_label.setText(chronic_pe_prob)

        acute_and_chronic_pe_label = slicer.util.findChild(mainWindow, 'label_11')
        acute_and_chronic_pe_label.setText(acute_and_chronic_pe_prob)

        central_pe_label = slicer.util.findChild(mainWindow, 'label_12')
        central_pe_label.setText(central_pe_prob)

        leftsided_pe_label = slicer.util.findChild(mainWindow, 'label_13')
        leftsided_pe_label.setText(leftsided_pe_prob)

        rightsided_pe_label = slicer.util.findChild(mainWindow, 'label_14')
        rightsided_pe_label.setText(rightsided_pe_prob)

        rv_lv_ratio_gte_1_label = slicer.util.findChild(mainWindow, 'label_15')
        rv_lv_ratio_gte_1_label.setText(rv_lv_ratio_gte_1_prob)

        rv_lv_ratio_lt_1_label = slicer.util.findChild(mainWindow, 'label_16')
        rv_lv_ratio_lt_1_label.setText(rv_lv_ratio_lt_1_prob)


        '''處理pe_on_image_prob'''
        # 創建帶參數的更新函數
        updateLabelWithParams = createUpdateLabelFunction(data, mainWindow)
        # 添加監聽器監控切片變化事件
        sliceNode = slicer.app.layoutManager().sliceWidget('Red').mrmlSliceNode()
        observerTag = sliceNode.AddObserver(vtk.vtkCommand.ModifiedEvent, updateLabelWithParams)
        # # 在退出時移除監聽器
        # def removeObserver():
        #     sliceNode.GetSliceCompositeNode().RemoveObserver(observerTag)
        # slicer.app.connect("aboutToQuit()", removeObserver)


        


#
# PE_DetectLogic
#


class PE_DetectLogic(ScriptedLoadableModuleLogic):
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
        return PE_DetectParameterNode(super().getParameterNode())

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
# PE_DetectTest
#


class PE_DetectTest(ScriptedLoadableModuleTest):
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
        self.test_PE_Detect1()

    def test_PE_Detect1(self):
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
        inputVolume = SampleData.downloadSample("PE_Detect1")
        self.delayDisplay("Loaded test data set")

        inputScalarRange = inputVolume.GetImageData().GetScalarRange()
        self.assertEqual(inputScalarRange[0], 0)
        self.assertEqual(inputScalarRange[1], 695)

        outputVolume = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLScalarVolumeNode")
        threshold = 100

        # Test the module logic

        logic = PE_DetectLogic()

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
