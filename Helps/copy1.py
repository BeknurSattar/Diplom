#Нужные библиотеки
from tkinter import *
import tkinter as tk
import tkinter.messagebox as mbox
from tkinter import font as tkfont
from PIL import ImageTk, Image
import cv2
import argparse
from detection.persondetection import DetectorAPI
import matplotlib.pyplot as plt
from fpdf import FPDF

# Main Window & Configuration
window = tk.Tk()
window.title("Analysis of class occupancy using computer vision methods")
window.iconbitmap('Images/eye.ico')
window.geometry('1200x800')

# Устанавливаем шрифт
custom_font = tkfont.Font(family="Roboto", size=50)

# Создаем метку с текстом
start1 = tk.Label(
    window,
    text="Analysis of class",
    font=custom_font,
    fg="black",
)
start1.place(relx=0.5, rely=0.2, anchor="center")  # Разместить метку в середине окна

# Function to clear the window and create a new layout
def clear_window():
    for widget in window.winfo_children():
        widget.destroy()

# function defined to start the main application
def start_fun():
    window.destroy()

# created a start button
Button(window, text="START",command=start_fun,font=("Arial", 25), bg = "green", fg = "black", cursor="hand2", borderwidth=3, relief="raised").place(relx=0.25, rely=0.7, anchor="center")

exit1 = False
# function created for exiting from window
def exit_win():
    global exit1
    if mbox.askokcancel("Exit", "Do you want to exit?"):
        exit1 = True
        window.destroy()

# exit button created
Button(window, text="EXIT",command=exit_win,font=("Arial", 25), bg = "red", fg = "black", cursor="hand2", borderwidth=3, relief="raised").place(relx=0.6, rely=0.7, anchor="center")

window.protocol("WM_DELETE_WINDOW", exit_win)
window.mainloop()

if exit1==False:
    # Main Window & Configuration of window1
    window1 = tk.Tk()
    window1.title("Analysis of class occupancy using computer vision methods")
    window1.iconbitmap('Images/eye.ico')
    window1.geometry('1000x700')

    filename=""
    filename1=""
    filename2=""

    def argsParser():
        arg_parse = argparse.ArgumentParser()
        arg_parse.add_argument("-c", "--camera", default=False, help="Установите true, если вы хотите использовать камеру.")
        args = vars(arg_parse.parse_args())
        return args

    # ---------------------------- camera section ------------------------------------------------------------
    def camera_option():
        # new window created for camera section
        windowc = tk.Tk()
        windowc.title("Analiz class")
        windowc.iconbitmap('Images/eye.ico')
        windowc.geometry('1000x700')

        max_count3 = 0
        framex3 = []
        county3 = []
        max3 = []
        avg_acc3_list = []
        max_avg_acc3_list = []
        max_acc3 = 0
        max_avg_acc3 = 0

        # function defined to open the camera
        def open_cam():
            global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
            max_count3 = 0
            framex3 = []
            county3 = []
            max3 = []
            avg_acc3_list = []
            max_avg_acc3_list = []
            max_acc3 = 0
            max_avg_acc3 = 0

            args = argsParser()

            info1.config(text="Status : Opening Camera...")
            mbox.showinfo("Status", "Opening Camera...Please Wait...", parent=windowc)

            writer = None
            if args['output'] is not None:
                writer = cv2.VideoWriter(args['output'], cv2.VideoWriter_fourcc(*'MJPG'), 10, (600, 600))
            if True:
                detectByCamera(writer)

        # function defined to detect from camera
        def detectByCamera(writer):
            #global variable created
            global max_count3, framex3, county3, max3, avg_acc3_list, max_avg_acc3_list, max_acc3, max_avg_acc3
            max_count3 = 0
            framex3 = []
            county3 = []
            max3 = []
            avg_acc3_list = []
            max_avg_acc3_list = []
            max_acc3 = 0
            max_avg_acc3 = 0

            # function defined to plot the people count in camera
            def cam_enumeration_plot():
                plt.figure(facecolor='orange', )
                ax = plt.axes()
                ax.set_facecolor("yellow")
                plt.plot(framex3, county3, label="Human Count", color="green", marker='o', markerfacecolor='blue')
                plt.plot(framex3, max3, label="Max. Human Count", linestyle='dashed', color='fuchsia')
                plt.xlabel('Time (sec)')
                plt.ylabel('Human Count')
                plt.legend()
                plt.title("Enumeration Plot")
                plt.get_current_fig_manager().canvas.set_window_title("Plot for Camera")
                plt.show()

            def cam_accuracy_plot():
                plt.figure(facecolor='orange', )
                ax = plt.axes()
                ax.set_facecolor("yellow")
                plt.plot(framex3, avg_acc3_list, label="Avg. Accuracy", color="green", marker='o', markerfacecolor='blue')
                plt.plot(framex3, max_avg_acc3_list, label="Max. Avg. Accuracy", linestyle='dashed', color='fuchsia')
                plt.xlabel('Time (sec)')
                plt.ylabel('Avg. Accuracy')
                plt.title('Avg. Accuracy Plot')
                plt.legend()
                plt.get_current_fig_manager().canvas.set_window_title("Plot for Camera")
                plt.show()

            def cam_gen_report():
                pdf = FPDF(orientation='P', unit='mm', format='A4')
                pdf.add_page()
                pdf.set_font("Arial", "", 20)
                pdf.set_text_color(128, 0, 0)
                pdf.image('Images/Crowd_Report.png', x=0, y=0, w=210, h=297)

                pdf.text(125, 150, str(max_count3))
                pdf.text(105, 163, str(max_acc3))
                pdf.text(125, 175, str(max_avg_acc3))
                if (max_count3 > 25):
                    pdf.text(26, 220, "Max. Human Detected is greater than MAX LIMIT.")
                    pdf.text(70, 235, "Region is Crowded.")
                else:
                    pdf.text(26, 220, "Max. Human Detected is in range of MAX LIMIT.")
                    pdf.text(65, 235, "Region is not Crowded.")

                pdf.output('Crowd_Report.pdf')
                mbox.showinfo("Status", "Report Generated and Saved Successfully.", parent = windowc)

            video = cv2.VideoCapture(0)
            odapi = DetectorAPI()
            threshold = 0.7

            x3 = 0
            while True:
                check, frame = video.read()
                img = cv2.resize(frame, (800, 600))
                boxes, scores, classes, num = odapi.processFrame(img)
                person = 0
                acc = 0
                for i in range(len(boxes)):

                    if classes[i] == 1 and scores[i] > threshold:
                        box = boxes[i]
                        person += 1
                        cv2.rectangle(img, (box[1], box[0]), (box[3], box[2]), (255, 0, 0), 2)  # cv2.FILLED
                        cv2.putText(img, f'P{person, round(scores[i], 2)}', (box[1] - 30, box[0] - 8),cv2.FONT_HERSHEY_COMPLEX, 0.5, (0, 0, 255), 1)  # (75,0,130),
                        acc += scores[i]
                        if (scores[i] > max_acc3):
                            max_acc3 = scores[i]

                if (person > max_count3):
                    max_count3 = person

                if writer is not None:
                    writer.write(img)

                cv2.imshow("Analiz", img)
                key = cv2.waitKey(1)
                if key & 0xFF == ord('q'):
                    break

                county3.append(person)
                x3 += 1
                framex3.append(x3)
                if(person>=1):
                    avg_acc3_list.append(acc / person)
                    if ((acc / person) > max_avg_acc3):
                        max_avg_acc3 = (acc / person)
                else:
                    avg_acc3_list.append(acc)

            video.release()
            info1.config(text="                                                  ")            # info2.config(text="                                                  ")
            info1.config(text="Status : Detection & Counting Completed")            # info2.config(text="Max. Human Count : " + str(max_count3))
            cv2.destroyAllWindows()

            for i in range(len(framex3)):
                max3.append(max_count3)
                max_avg_acc3_list.append(max_avg_acc3)

            Button(windowc, text="Enumeration\nPlot", command=cam_enumeration_plot, cursor="hand2", font=("Arial", 20),bg="orange", fg="blue").place(x=100, y=530)
            Button(windowc, text="Avg. Accuracy\nPlot", command=cam_accuracy_plot, cursor="hand2", font=("Arial", 20),bg="orange", fg="blue").place(x=700, y=530)
            Button(windowc, text="Generate  Crowd  Report", command=cam_gen_report, cursor="hand2", font=("Arial", 20),bg="gray", fg="blue").place(x=325, y=550)

        lbl1 = tk.Label(windowc, text="DETECT  FROM\nCAMERA", font=("Arial", 50, "underline"), fg="brown")  # same way bg
        lbl1.place(x=230, y=20)

        Button(windowc, text="OPEN CAMERA", command=open_cam, cursor="hand2", font=("Arial", 20), bg="light green", fg="blue").place(x=370, y=230)

        info1 = tk.Label(windowc, font=("Arial", 30), fg="gray")  # same way bg
        info1.place(x=100, y=330)

        # function defined to exit from the camera window
        def exit_winc():
            if mbox.askokcancel("Exit", "Do you want to exit?", parent = windowc):
                windowc.destroy()
        windowc.protocol("WM_DELETE_WINDOW", exit_winc)

    # options -----------------------------
    lbl1 = tk.Label(text="Menu", font=("Arial", 50), fg="black")  # same way bg
    lbl1.place(relx=0.5, rely=0.1, anchor="center")

    pathc1 = "Images/base1.png"
    img1 = Image.open(pathc1)
    # Изменяем размер до 200x200 с использованием антиалиасированной фильтрации
    img1 = img1.resize((200, 200))
    imgc1 = ImageTk.PhotoImage(img1)
    panelc1 = tk.Label(window1, image=imgc1)
    panelc1.place(relx=0.15, rely=0.3)

    Button(window1, text="Open database",command=camera_option, cursor="hand2", font=("Arial", 30), bg = "black", fg = "white").place(relx=0.6, rely=0.3)

    # image on the main window
    pathc2 = "Images/camera2.png"
    img2 = Image.open(pathc2)
    img2 = img2.resize((200, 200))  # Изменяем размер до 200x200
    imgc2 = ImageTk.PhotoImage(img2)
    panelc2 = tk.Label(window1, image=imgc2)
    panelc2.place(relx=0.15, rely=0.6)

    # created button for all three option
    Button(window1, text="Open camera",command=camera_option, cursor="hand2", font=("Arial", 30), bg = "black", fg = "white").place(relx=0.6, rely=0.6)

    # function defined to exit from window1
    def exit_win1():
        if mbox.askokcancel("Exit", "Do you want to exit?"):
            window1.destroy()

    # created exit button
    Button(window1, text="EXIT",command=exit_win1,  cursor="hand2", font=("Arial", 25), bg = "red", fg = "black").place(relx=0.5, rely=0.85)



    window1.protocol("WM_DELETE_WINDOW", exit_win1)
    window1.mainloop()

