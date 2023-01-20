import tkinter
import customtkinter
from pytube import YouTube
from tkinter import filedialog
import os
import sys
import ctypes
import urllib.parse
from PIL import Image, ImageTk, ImageColor
from io import BytesIO
import logging
from collections import OrderedDict
import re
from threading import Thread
import youtube_dl
from CTkColorPicker import AskColor
import configparser

logging.basicConfig(level=logging.DEBUG)

global update_video_info_finish
update_video_info_finish = False

def load_colors():
    config = configparser.ConfigParser()
    config.read("Settings.ini")
    try:
        colorfg = config.get("ColorSettings", "fg_color")
        hovercolor = config.get("ColorSettings", "hovercolor")
        font_color = config.get("ColorSettings", "font_color")
        return colorfg, hovercolor, font_color
    except configparser.Error:
        return "#10ab6b", "#0c8050","#000000"

colorfg, hovercolor, font_color = load_colors()

def set_app_icon():
    try:
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("assets/icon.ico")
        myappid = 'assets/icon.ico'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    except Exception as e:
        logging.error(e)
        pass

def check_valid_url(*args):
    url = url_var.get()
    parsed_url = urllib.parse.urlparse(url)
    ydl = youtube_dl.YoutubeDL({'quiet': True})
    if parsed_url.scheme != "" and parsed_url.netloc != "":
        if url.startswith("https://www.youtube.com/watch?v="):
            try:
                query_params = urllib.parse.parse_qs(parsed_url.query)
                video_id = query_params['v'][0]
                ydl.extract_info(url, download=False)
                print("Video exists")
                update_video_info_Thread = Thread(target=update_video_info(url))
                update_video_info_Thread.start()
                ResButton.configure(state="normal")
                return True
            except Exception() as e:
                if "this video is unavailable" in e.args[0]:
                    print("Video does not exist")
                    return False
                    ResButton.configure(state="disabled")
                else:
                    raise

def update_video_info(url):
    try:
        global update_video_info_finish
        update_video_info_finish = False
        video_resolutions = []
        ytObject = YouTube(url)
        thumbnail_url = ytObject.thumbnail_url
        with urllib.request.urlopen(thumbnail_url) as url:
            s = url.read()
        image = Image.open(BytesIO(s))
        width = 360
        height = 240
        imageresize = image.resize((width, height), Image.LANCZOS)
        photo = ImageTk.PhotoImage(imageresize)
        label.configure(image=photo)
        InfoVideo.configure(state="normal")
        InfoVideo.delete("0.0", "end")
        InfoVideo.insert("2.0", "Titre : " + str(ytObject.title) + "\n")
        InfoVideo.insert("5.0", "Auteur : " + str(ytObject.author) + "\n")
        InfoVideo.insert("10.0", "Vues : " + str(ytObject.views) + "\n")
        InfoVideo.insert("15.0", "Longueur : " + str(ytObject.length) + " s" + "\n")
        InfoVideo.insert("20.0", "Description : " + str(ytObject.description) + "\n")
        InfoVideo.configure(state="disabled")
        for stream in ytObject.streams.order_by('resolution'):
            video_resolutions.append(stream.resolution)
            video_resolutions = [item for item in OrderedDict.fromkeys(video_resolutions).keys()]
        ResButton.configure(state="normal")
        ResButton.configure(values=video_resolutions)
        update_video_info_finish = True
    except Exception as e:
        logging.error(e)
        
def select_download_path():
    try:
        path = filedialog.askdirectory()
        if os.path.isdir(path):
            dir_var.set(path)
            global DIR; DIR = str(path+"/")
            logging.info("Selected path " + path)
        else:
            logging.info("No selected path, default download path set")
            path = os.path.join(os.path.expanduser("~"), "Downloads")
            dir_var.set(path)
    except Exception as e:
        logging.error(e)

def download_button_event():
    if url_var.get():
        if checkboxSound.get() == True and checkboxVideo.get() == True:
            download_thread = Thread(target=download_video_and_audio)
            download_thread.start()
        elif checkboxSound.get() == True:
            download_thread = Thread(target=download_audio)
            download_thread.join()
        elif checkboxVideo.get() == True:
            download_thread = Thread(target=download_video)
            download_thread.start()

def download_video_and_audio():
    ytLink = urlEntry.get()
    ytObject = YouTube(ytLink, on_progress_callback=on_progress)
    selected_resolution = ResButton.get()
    video = ytObject.streams.filter(adaptive=True, resolution=selected_resolution).first()
    audio = ytObject.streams.get_audio_only()
    title = re.sub(r'[^\w\s-]', '', ytObject.title)
    video.download(filename= title + ".mp4", output_path=DIR)
    audio.download(filename= title + ".mp3", output_path=DIR)
    logging.info("Video and audio downloaded")

def download_video():
    ytLink = urlEntry.get()
    ytObject = YouTube(ytLink, on_progress_callback=on_progress)
    selected_resolution = ResButton.get()
    video = ytObject.streams.filter(adaptive=True, resolution=selected_resolution).first()
    title = re.sub(r'[^\w\s-]', '', ytObject.title)
    video.download(filename= title + ".mp4", output_path=DIR)
    logging.info("Video downloaded")

def download_audio():
    ytLink = urlEntry.get()
    ytObject = YouTube(ytLink, on_progress_callback=on_progress)
    audio = ytObject.streams.get_audio_only()
    title = re.sub(r'[^\w\s-]', '', ytObject.title)
    audio.download(filename= title + ".mp3", output_path=DIR)
    logging.info("Audio downloaded")
        
def on_progress(stream, chunk, bytes_remaining):
    total_size = stream.filesize
    bytes_downloaded = total_size - bytes_remaining
    percentage_of_completion = bytes_downloaded / total_size * 100
    per = str(int(percentage_of_completion))
    percentageLabel.configure(text=per + "%")
    percentageLabel.update()
    p = percentage_of_completion/100
    while progressBar.get() < p:
        progress = progressBar.get()
        percentageLabel.configure(text=str(int(progress*100 + 0.008*100)) + "%")
        progressBar.set(progress + 0.008)
    if progressBar.get() >= 1:
        progressBar.set(0.0)
        
def clamp(val, minimum=0, maximum=255):
    if val < minimum:
        return minimum
    if val > maximum:
        return maximum
    return val

def colorscale(hexstr, scalefactor):
    """
    Scales a hex string by ``scalefactor``. Returns scaled hex string.
    To darken the color, use a float value between 0 and 1.
    To brighten the color, use a float value greater than 1.

    >>> colorscale("#DF3C3C", .5)
    #6F1E1E
    >>> colorscale("#52D24F", 1.6)
    #83FF7E
    >>> colorscale("#4F75D2", 1)
    #4F75D2
    """
    hexstr = hexstr.strip('#')
    if scalefactor < 0 or len(hexstr) != 6:
        return hexstr
    r, g, b = int(hexstr[:2], 16), int(hexstr[2:4], 16), int(hexstr[4:], 16)
    r = clamp(r * scalefactor)
    g = clamp(g * scalefactor)
    b = clamp(b * scalefactor)

    return "#%02x%02x%02x" % (int(r), int(g), int(b))

def hex_to_rgb(hex_color):
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def is_color_light(hex_color):
    r, g, b = hex_to_rgb(hex_color)
    brightness = (0.2126 * r) + (0.7152 * g) + (0.0722 * b)
    if brightness > 128:
        return True
    else:
        return False

def ask_color():
    pick_color = AskColor()
    color = pick_color.get()
    print(color)
    hover_color = colorscale(color, .75)
    print(hover_color)
    if is_color_light(color):
        text_color="#000000"
    else:
        text_color="#FFFFFF"
    save_colors(color, hover_color, text_color)
    colorfg, hovercolor, font_color = load_colors()
    tabview.configure(segmented_button_unselected_color=colorfg, 
                      segmented_button_selected_color=colorfg, 
                      segmented_button_selected_hover_color=hovercolor,
                      segmented_button_unselected_hover_color=hovercolor,
                      text_color=font_color)
    PathButton.configure(fg_color=colorfg, 
                        hover_color=hovercolor, 
                        text_color=font_color)
    DownloadButton.configure(fg_color=colorfg, 
                        hover_color=hovercolor, 
                        text_color=font_color)
    ResButton.configure(fg_color=colorfg,
                        button_color=colorfg,
                        button_hover_color=hovercolor,
                        text_color=font_color)
    progressBar.configure(progress_color=colorfg)
    checkboxSound.configure(fg_color=colorfg, 
                            hover_color=hovercolor)
    checkboxVideo.configure(fg_color=colorfg, 
                            hover_color=hovercolor)
    buttonColor.configure(fg_color=colorfg, 
                        hover_color=hovercolor, 
                        text_color=font_color)
    
def save_colors(colorfg, hovercolor, font_color):
    config = configparser.ConfigParser()
    config.add_section("ColorSettings")
    config.set("ColorSettings", "fg_color", colorfg)
    config.set("ColorSettings", "hovercolor", hovercolor)
    config.set("ColorSettings", "font_color", font_color)
    with open("Settings.ini", "w") as configfile:
        config.write(configfile)
        
def check_button(): 
    if checkboxSound.get() == False and checkboxVideo.get() == False:
        DownloadButton.configure(state="disabled")
    elif checkboxSound.get() == True or checkboxVideo.get() == True:
        if update_video_info_finish == True and ResButton.get() != "Résolution":
            DownloadButton.configure(state="normal")
    
customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("green")

app = customtkinter.CTk()
app.geometry("420x880")
app.minsize(420,880)
app.maxsize(420,880)
app.title("Utility by Ziakary#4173")
app.iconbitmap("assets\icon.ico")

labelTitle = customtkinter.CTkLabel(master=app, text="Utility by Ziakary#4173", font=customtkinter.CTkFont(family="Montserrat", size=17))
labelTitle.pack(padx=10, pady=10)

tabview = customtkinter.CTkTabview(master=app,segmented_button_unselected_color=colorfg, 
                      segmented_button_selected_color=colorfg, 
                      segmented_button_selected_hover_color=hovercolor,
                      segmented_button_unselected_hover_color=hovercolor,
                      text_color=font_color)

tabview.pack(padx=20, pady=20)

tabview.add("Youtube Downloader")  # add tab at the end
tabview.add("Upscaler")  # add tab at the end
tabview.add("Option")  # add tab at the end
tabview.set("Youtube Downloader")  # set currently visible tab

url_var = tkinter.StringVar()
urlEntry = customtkinter.CTkEntry(tabview.tab("Youtube Downloader"), 
                                  width=300, 
                                  textvariable=url_var, 
                                  placeholder_text="Entrer un lien", 
                                  font=customtkinter.CTkFont(family="Montserrat", size=14))
urlEntry.pack(padx=10, pady=10)
url_var.trace("w", check_valid_url)

dir_var = tkinter.StringVar()
pathEntry = customtkinter.CTkEntry(tabview.tab("Youtube Downloader"), 
                                   width=300, 
                                   textvariable=dir_var, 
                                   placeholder_text="Choisir l'emplacement du fichier", 
                                   font=customtkinter.CTkFont(family="Montserrat", size=14), 
                                   text_color="#949a9f")

pathEntry.pack(padx=10, pady=10)

PathButton = customtkinter.CTkButton(tabview.tab("Youtube Downloader"), 
                                     text="...", 
                                     command=lambda: select_download_path(), 
                                     width=40, 
                                     fg_color=colorfg, 
                                     hover_color=hovercolor, 
                                     text_color=font_color)

PathButton.place(x=294, y=58)

DownloadButton = customtkinter.CTkButton(tabview.tab("Youtube Downloader"), 
                                         text="Télécharger", 
                                         command=download_button_event, 
                                         font=customtkinter.CTkFont(family="Montserrat", size=14), 
                                         fg_color=colorfg, 
                                         hover_color=hovercolor, 
                                         text_color=font_color)

DownloadButton.configure(state="disabled")
DownloadButton.pack(padx=10, pady=10)

def optionmenu_callback(choice):
    print("Dropdown clicked:", choice)
    check_button()
    
ResButton = customtkinter.CTkOptionMenu(tabview.tab("Youtube Downloader"),
                                       values=["Résolution"],
                                       command=optionmenu_callback
                                       ,font=customtkinter.CTkFont(family="Montserrat", size=12), 
                                       fg_color=colorfg, 
                                       button_hover_color=hovercolor, 
                                       button_color=colorfg, 
                                       text_color=font_color,
                                       dropdown_font=customtkinter.CTkFont(family="Montserrat", size=14))

ResButton.pack(padx=20, pady=10)
ResButton.set("Résolution")
ResButton.configure(state="disabled")

percentageLabel = customtkinter.CTkLabel(tabview.tab("Youtube Downloader"), 
                                         text="0%", 
                                         font=customtkinter.CTkFont(family="Montserrat", size=16))

percentageLabel.pack(padx=20, pady=10)

progressBar = customtkinter.CTkProgressBar(tabview.tab("Youtube Downloader"), 
                                           width=300,
                                           progress_color=colorfg)

progressBar.pack(padx=20, pady=10)
progressBar.set(0.0)

check_varSon = tkinter.StringVar()
check_varVideo = tkinter.StringVar()

def checkboxSound_event():
    logging.info("Checkbox_sound : " + check_varSon.get())
    check_button()
        
def checkboxVideo_event():
    logging.info("Checkbox_Video : " + check_varVideo.get())
    check_button()
    
checkboxSound = customtkinter.CTkCheckBox(tabview.tab("Youtube Downloader"), 
                                          text="Audio", command=checkboxSound_event, 
                                          variable=check_varSon, 
                                          font=customtkinter.CTkFont(family="Montserrat", size=14), 
                                          fg_color=colorfg, 
                                          hover_color=hovercolor)

checkboxSound.pack(padx=10, pady=10)

checkboxVideo = customtkinter.CTkCheckBox(tabview.tab("Youtube Downloader"), 
                                          text="Video", 
                                          command=checkboxVideo_event, 
                                          variable=check_varVideo, 
                                          font=customtkinter.CTkFont(family="Montserrat", size=14), 
                                          fg_color=colorfg, 
                                          hover_color=hovercolor)

checkboxVideo.pack(padx=10, pady=10)

miniature = customtkinter.CTkImage(light_image=Image.open("assets\White_miniature.png"),
                                  dark_image=Image.open("assets\Black_miniature.png"),
                                  size=(360, 240))

label = customtkinter.CTkLabel(tabview.tab("Youtube Downloader"), 
                               text="", 
                               width=1, 
                               height=1, 
                               image=miniature)

label.pack(padx=10, pady=10)

InfoVideo = customtkinter.CTkTextbox(tabview.tab("Youtube Downloader"), 
                                     font=customtkinter.CTkFont(family="Montserrat", size=14), width = 400)

InfoVideo.insert("0.0", "Information :")
InfoVideo.pack(padx=10, pady=10)
InfoVideo.configure(state="disabled")

buttonColor = customtkinter.CTkButton(tabview.tab("Option"), 
                                      text="Couleur du programme", 
                                      command=ask_color, 
                                      font=customtkinter.CTkFont(family="Montserrat", size=14), 
                                      fg_color=colorfg, 
                                      hover_color=hovercolor, 
                                      text_color=font_color)

buttonColor.pack(padx=10, pady=10)

app.mainloop()