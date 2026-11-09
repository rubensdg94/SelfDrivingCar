"""camera_pid controller."""

from controller import Display, Keyboard, Robot, Camera
from vehicle import Car, Driver
import numpy as np
import cv2
from datetime import datetime
import os
from tensorflow.keras.models import load_model

#Getting image from camera
def get_image(camera):
    raw_image = camera.getImage()  
    image = np.frombuffer(raw_image, np.uint8).reshape((camera.getHeight(), camera.getWidth(), 4 ))
    bgr_image = image[:, :, :3]  # Convert to BGR format
    return bgr_image

#Image processing
def greyscale_cv2(image):
    gray_img = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    return gray_img

#Display image 
def display_image(display, image):
    # Image to display
    image_rgb = np.dstack((image, image,image,))
    # Display image
    image_ref = display.imageNew(
        image_rgb.tobytes(),
        Display.RGB,
        width=image_rgb.shape[1],
        height=image_rgb.shape[0],
    )
    display.imagePaste(image_ref, 0, 0, False)

#initial angle and speed 
manual_steering = 0
steering_angle = 0
angle = 0.0
speed = 25

# set target speed
def set_speed(kmh):
    global speed            #robot.step(50)
    speed = kmh # speed + kmh
#update steering angle
def set_steering_angle(wheel_angle):
    global angle, steering_angle
    # Check limits of steering
    if (wheel_angle - steering_angle) > 0.1:
        wheel_angle = steering_angle + 0.1
    if (wheel_angle - steering_angle) < -0.1:
        wheel_angle = steering_angle - 0.1
    steering_angle = wheel_angle
  
    # limit range of the steering angle
    # if wheel_angle > 0.5:
    #     wheel_angle = 0.5
    # elif wheel_angle < -0.5:
    #     wheel_angle = -0.5
    # update steering angle
    angle = wheel_angle

#validate increment of steering angle
def change_steer_angle(inc):
    global manual_steering
    # Apply increment
    new_manual_steering = manual_steering + inc
    # Validate interval 
    if new_manual_steering <= 25.0 and new_manual_steering >= -25.0: 
        manual_steering = new_manual_steering
        set_steering_angle(manual_steering * 0.02)
    # Debugging
    if manual_steering == 0:
        print("going straight")
    else:
        turn = "left" if steering_angle < 0 else "right"
        print("turning {} rad {}".format(str(steering_angle),turn))


# main
def main():
    # Create the Robot instance.
    robot = Car()
    driver = Driver()
    
    # base_filename = "Proyecto_Final_Modelo_2025-06-21_23-05-34.keras"
    base_filename = "Modelo_2025-06-22_12-32-00.keras"
    # folder_path = r"/mnt/c/Users/Raven/Desktop/MNA/Navegacion/Proyecto Final/Models"
    folder_path = r"/home/raven/Desktop/MNA/ProyectoFinal/Models"
    model_path = os.path.join(folder_path, base_filename)

    modelo = load_model(model_path)
    
    # Get the time step of the current world.
    timestep = int(robot.getBasicTimeStep())

    nombre_camaras=["camera izquierda", "camera central", "camera derecha"]
    camaras={}
    for nombre in nombre_camaras:
        camaras[nombre] = robot.getDevice(nombre)
        camaras[nombre].enable(timestep)
        
    camaraizq = camaras["camera izquierda"]
    camaracen = camaras["camera central"]
    camarader = camaras["camera derecha"]
    
    # processing display
    display_img = Display("display")

    #create keyboard instance
    keyboard=Keyboard()
    keyboard.enable(timestep)

    while robot.step() != -1:
        # Get image from camera
        #imageizq = get_image(camaraizq)
        imagecen = get_image(camaracen)
        #imageright = get_image(camarader)

        # Process and display image 
        #display_image(display_img, imageizq)
        display_image(display_img, imagecen)
        #display_image(display_img, imageright)
        
        display_img.setColor(0x000000)
        display_img.fillRectangle(0,0,250,30)
        # Blanco para texto
        display_img.setColor(0xFFFFFF)
                
               
        image = cv2.cvtColor(imagecen, cv2.COLOR_BGR2GRAY)
        recorte=image[54:120]
        image1 = cv2.resize(recorte, (200,66))  # Resize to match model input
        img = image1 / 255.0  # Normalización
        image2 = img.reshape(1, 66, 200, 1)  # Reshape for model input
        Steering=modelo.predict(np.array(image2))
        set_steering_angle(Steering)
        
        #display_img.drawText(f"Steering angle: {Steering:.2f} rad", 10, 20)
        
        # Read keyboard
        key=keyboard.getKey()
        if key == ord('W'): #up
            set_speed(+5.0)
            print("up")
        elif key == ord('S'): #down
            set_speed(-5.0)
            print("down")
        elif key == ord('D'): #right
            change_steer_angle(+0.5)
            print("right")
        elif key == ord('A'): #left
            change_steer_angle(-0.5)
            print("left")

        #update angle and speed
        driver.setSteeringAngle(angle)
        driver.setCruisingSpeed(speed)
    


if __name__ == "__main__":
    main()
