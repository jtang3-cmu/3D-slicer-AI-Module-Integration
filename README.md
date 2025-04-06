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
   - Supports frameworks like PyTorch, TensorFlow, etc.
   - Includes inference scripts and preprocessing logic

2. **Docker Container**
   - Dockerfile for packaging model and dependencies
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
  -  Please develop a Python script which is used for inferencing. (Please refer to inference.py in each example)
  -  Also, we need a main script to costimize the command. (Please refer to main.py in each example)
  -  Use the command window to test whether the inference.py and main.py is working or not.

3. **Dockerize The Model**
  - Create a project folder. The folder structure should be corresponding to your system design.
  - Write Dockerfile
   ![圖片1](https://github.com/user-attachments/assets/86d9b8b9-56ac-40ea-97aa-d3a40761b80b)
  - Build Docker Image `bash docker build -t {your_image_name} . (❗Don't forget the "." in the end of the command!!!)
  - Activate Docker Container `bash docker run -d {your_image_name}
  - Check in Docker Desktop image and container tab.

4. **Develop the slicer API Using Slicer Jupyter Kernel**
  - Download SlicerJupyter extension in 3D slicer
  - Start Jupyter server in 3D slicer

5. **UI Design in 3D slicer**
![image](https://github.com/user-attachments/assets/c3b4df33-3ef1-4e7e-a2f5-8ad5b3a3bca0)
  - Click and Drag the object you want to the work station on the middle.
  - The most useful button is push Button.
  - Click the object and you can edit the properties on the right list.
  - Be aware of the objectName of each object because we need to specify the objectName in the API to functionalize the button.
6. 


## 🎖️ Examples
1. Image Detection: Using YOLOv8 to do lung nodules detection on chest X-ray image.
![image](https://github.com/user-attachments/assets/f9db9675-1f94-4a11-86af-c3858e5fab43)
  - Please refer to the
  - In 3D slicer, we need to use 4 lines to simulate bounding boxes in YOLO. In this example, you can see how to do it and how to group 4 lines into 1 bounding box.
3. Image Classification: Using Seresnext and LSTM to do muti-class classification.

  - Please refer to the folder
  - The model will generate the prediction of the type of Pulmonary Embolism based on a Lung CT scan, and the UI will show the probability for each class.
  - demo video


