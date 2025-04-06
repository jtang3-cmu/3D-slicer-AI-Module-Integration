# 3D Slicer AI Integration Framework

This repository provides a general-purpose framework and tutorial for integrating AI-based medical image models into the 3D Slicer platform. It covers the complete workflow, from Docker packaging and model deployment to UI integration and inference visualization.


## 🎯 Project Objectives

- Provide a clear and adaptable guide to connect any medical imaging AI model with 3D Slicer.
- Demonstrate how to containerize models and services using Docker.
- Enable development and testing via the Slicer Jupyter Kernel.
- Design a user-friendly Slicer module UI for streamlined interaction.
- Provide recommand system structure for image classification task and image detection task.

## 📌 Architecture Overview

1. **AI Model Code**
   - Mainly support PyTorch Framework
   - Includes inference scripts and preprocessing logic

2. **Docker Container**
   - Writing Dockerfile
   - Build Docker Image
   - Activate Docker Container
   - API interface exposed for Slicer communication

3. **3D Slicer Integration**
   - UI designed with Qt Designer
   - Backend interaction through Jupyter Kernel or RESTful API
   - Displays inference results within Slicer views

---

## ⚒️ Workflow
1. **Download Applications**
  - Download [3D slicer](https://download.slicer.org/)
  - Download [Docker Desktop](https://www.docker.com/products/docker-desktop/)

2. **Python Script Prepareations**
  -  Once you have a trained medical image AI model and you want to integrate with 3D slicer, you can start the following procedures.
  -  Design a sturture prototype for the whole system. It's better to use Powerpoint to design the system stucture. You can refer to the example structural design figures.
    ![image](https://github.com/user-attachments/assets/cec37609-1c8e-4509-8ed1-f14f12776670)
  -  Please develop a Python script which is used for inferencing. (Please refer to inference.py in each example)
  -  Also, we need a main script to costimize the command. (Please refer to main.py in each example)
  -  Use the command window to test whether the inference.py and main.py is working or not.

3. **Dockerize The Model**
  - Create a project folder. The folder structure should be corresponding to your system design.
  - Write Dockerfile
   ![圖片1](https://github.com/user-attachments/assets/86d9b8b9-56ac-40ea-97aa-d3a40761b80b)
  - Build Docker Image: `bash docker build -t {your_image_name} .` (❗ Don't forget the `.` at the end!)
  - Activate Docker Container `bash docker run -d {your_image_name}`
  - Check in Docker Desktop image and container tab.

4. **Develop the slicer API Using Slicer Jupyter Kernel**
  - First, create a module using slicer extension wizard.
  - Download SlicerJupyter extension in 3D slicer (This is a Jupyter Notebook that can interact with 3D Slicer, it is good for developing slicer API.)
  - Open the module extension you created, click on Edit button to edit API
![image](https://github.com/user-attachments/assets/d14c7e18-401b-453b-a8b9-620473ef54d8)

  - Find the code section for setting button. Add button on this section and set to be listening.
![image](https://github.com/user-attachments/assets/501d1d23-c165-49a6-a977-85f492f4ae37)

  - Copy the code from the script you developed in Slicer Jupyter Kernel to the button function.
![image](https://github.com/user-attachments/assets/d2b6a58a-ca52-404c-bba0-805e1a836251)

  - Test on interating with the button to see whether it prints out the string.

5. **UI Design in 3D slicer**
![image](https://github.com/user-attachments/assets/eec50d82-ae61-4f85-bf36-71deaf7fbf0d)
  - Click and Drag the object you want to the work station on the middle.
  - The most useful button is push Button.
  - Click the object and you can edit the properties on the right list.
  - Be aware of the objectName of each object because we need to specify the objectName in the API to functionalize the button.


## 🎖️ Examples
1. Image Detection: Using YOLOv8 to do lung nodules detection on chest X-ray image.
  - Please refer to the chestyolo
  - In 3D slicer, we need to use 4 lines to simulate bounding boxes in YOLO. In this example, you can see how to do it and how to group 4 lines into 1 bounding box.
3. Image Classification: Using Seresnext and LSTM to do muti-class classification.

  - Please refer to the folder
  - The model will generate the prediction of the type of Pulmonary Embolism based on a Lung CT scan, and the UI will show the probability for each class.
  - [Demo video in Mandarin](https://youtu.be/SNgI4MpFOY8)


