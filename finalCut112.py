import cv2
from cmu_graphics import *
import numpy as np
from PyQt5 import *
from PyQt5.QtWidgets import *
import sys
import uuid



def onAppStart(app):
    app.counter = 0
    app.isPaused = True
    app.sampleRate = 1
    app.blurColor = "white"
    app.videos = []
    #app.videos = [Video("Earth", "/Users/kevincong/Downloads/file_example_MP4_480_1_5MG.mp4"), Video("Nature", "/Users/kevincong/Downloads/sample-5s.mp4"), Video("Ocean", "/Users/kevincong/Downloads/sample_960x400_ocean_with_audio (1).mp4")]
    app.photos = []
    for i in range(len(app.videos)):
        video = app.videos[i]
        cap = cv2.VideoCapture(video.path)
        if cap.get(cv2.CAP_PROP_FPS) != 30:
            tempPath = f"{video.path.split('.')[0]}_temp.mp4"
            modifyFpsAndTime(video.path, tempPath, 30, adjustTime=False)
            app.videos[i] = Video(video.name, tempPath)
    for video in app.videos:
        FrameCapture(app, video)

    app.timelineHeight = 190
    if app.videos != []:
        app.timelineDuration = max(video.videoDuration for video in app.videos)
    else:
        app.timelineDuration = 0  # Longest video duration
    app.timelineWidth = app.width - 70 
    app.timelineX = 70 

    #ScrollBAR
    app.scrollY = 150
    app.scrollDragging = False
    app.scrollStartY = 0  
    app.scrollOffset = 0 
    app.mediaOffsetY = 0
    
    # Initialize each video's start and end times
    for i in range(len(app.videos)):
        video = app.videos[i]
        video.startTime = 0 
        video.endTime = video.startTime + video.videoDuration
        video.timelineRect = {
            "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
            "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
            "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
            "height": app.timelineHeight // len(app.videos) - 2
        }

    # app.path = "/Users/kevincong/Downloads/file_example_MP4_480_1_5MG.mp4"
    # #app.path = "/Users/kevincong/Downloads/sample-5s.mp4"
    maxFrames = 0
    for video in app.videos:
        if video.totalFrames > maxFrames:
            maxFrames = video.totalFrames
    app.totalFrames = maxFrames
    app.currentFrame = 0

    maxDuration = 0
    for video in app.videos:
        if video.videoDuration > maxDuration:
            maxDuration = video.videoDuration
    app.videoDuration = maxDuration
    app.currentFrame = 0
    # app.stepsPerSecond = (app.totalFrames / app.videoDuration) / app.sampleRate
    app.barX = 70
    app.mode = ""

    #menu
    app.menuMode = "Filters"
    
    #dragging
    app.draggingVideo = False
    app.draggingTransitionEdge = None
    #resize
    app.resizingCorner = None

    #select and resize:
    app.selectedIndex = None
    app.selectedTransitionIndex = None
    #drag
    app.timeDrag = False
    app.rectDrag = False
    app.draggingVideo = False
    app.resizingCorner = None

    #copypaste
    app.clipBoardPath = None

    # button colors:
    app.PFColor = "white"
    app.AMColor = "white"
    app.FOColor = 'white'
    app.FIColor = "white"


    app.draggingTransition = None
    #help
    app.help = False
    #FrameCapture(app, app.path)
    #app.setMaxShapeCount(100000)
# Function to extract frames 
class Video:
    def __init__(self, name,  path, sampleRate=1):
        self.name = name
        self.path = path
        self.sampleRate = sampleRate
        self.cap = cv2.VideoCapture(self.path)
        
        if not self.cap.isOpened():
            raise ValueError(f"Could not open video: {self.path}")
        
        self.totalFrames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
        self.frameRate = self.cap.get(cv2.CAP_PROP_FPS)
        self.videoDuration = self.totalFrames / self.frameRate
        self.currentFrameIndex = 0
        self.width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.aspectRatio = self.width / self.height
        if self.width > 900 or self.height > 500:
            if self.width / 900 > self.height / 500:
                self.width = 900
                self.height = int(self.width / self.aspectRatio)
            else:
                self.height = 500
                self.width = int(self.height * self.aspectRatio)
        self.counter = 0
        self.stepsPerSecond = self.frameRate / sampleRate
        self.left = 500
        self.top = 100
        self.mode = ""
        self.sobelThreshold = 50
        self.sobelColor = "white"
        self.invertedColor = "white"
        self.grayColor = "white"
        self.opac = 100
        self.transitions = []

def applySobelFilter(image, threshold): #Cite OPENCV.org tutorials
    grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    sobelX = cv2.Sobel(grayImage, cv2.CV_64F, 1, 0, ksize=3)
    sobelY = cv2.Sobel(grayImage, cv2.CV_64F, 0, 1, ksize=3)
    sobelCombined = cv2.magnitude(sobelX, sobelY)
    sobelCombined[sobelCombined < threshold] = 0  
    sobelCombined = np.uint8(sobelCombined)
    return cv2.cvtColor(sobelCombined, cv2.COLOR_GRAY2BGR)


def modifyFpsAndTime(inputPath, outputPath, newFps, adjustTime=False): #cite Chat GPT and OPENCV.org tutorials
    cap = cv2.VideoCapture(inputPath)
    originalFps = cap.get(cv2.CAP_PROP_FPS)
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    codec = cv2.VideoWriter_fourcc(*'mp4v')
    totalFrames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if adjustTime == True:
        newFrameCount = int((totalFrames / originalFps) * newFps)
        frameInterval = totalFrames / newFrameCount
    else:
        frameInterval = max(1, originalFps / newFps)

    out = cv2.VideoWriter(outputPath, codec, newFps, (width, height))

    frameCount = 0
    writtenFrames = 0

    while True:
        ret, frame = cap.read()
        if not ret:
            break
        if frameCount % int(frameInterval) == 0:
            out.write(frame)
            writtenFrames += 1

        frameCount += 1

def FrameCapture(app, video): #CiteOpenCV.org for the sobel tutorials
    vidObj = cv2.VideoCapture(video.path) 
    count = 0
    success = True
    while success: 
        success, image = vidObj.read()
        if image is not None:
            image = cv2.resize(image, (video.width, video.height))
        if success and count % app.sampleRate == 0:
            cv2.imwrite(f"frame{video.name}{count}.jpg", image) 

            grayImage = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"frameGray{video.name}{count}.jpg", grayImage)
            sobelX = cv2.Sobel(grayImage, cv2.CV_64F, 1, 0, ksize=3)
            sobelY = cv2.Sobel(grayImage, cv2.CV_64F, 0, 1, ksize=3)
            sobelCombined = cv2.magnitude(sobelX, sobelY)
            sobelCombined = np.uint8(sobelCombined)
            sobelImage = cv2.cvtColor(sobelCombined, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(f"frameSobel{video.name}{count}.jpg", sobelImage)
            sobelInverted = 255-sobelCombined
            sobelImageInverted = cv2.cvtColor(sobelInverted, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(f"frameSobelInverted{video.name}{count}.jpg", sobelImageInverted)
            

        count += 1

def uploadMedia(): #CITE doc.qt.io
    app = QApplication(sys.argv)
    filePath, _ = QFileDialog.getOpenFileName(None, "Select Media File", "", "Media Files (*.mp4 *.avi *.mov *.mkv *.jpg *.jpeg *.png *.bmp *.gif)")
    app.quit()
    return filePath

def addVideo(app, filePath):
    unique_id = str(uuid.uuid4())[:8] #cite chatGPT for Unique id Implementation
    videoName = filePath.split("/")[-1].split(".")[0]+unique_id
    cap = cv2.VideoCapture(filePath)
    if cap.get(cv2.CAP_PROP_FPS) != 30:
        tempPath = f"{filePath}_temp{unique_id}.mp4"
        modifyFpsAndTime(filePath, tempPath, 30, adjustTime=False)
        newVideo = Video(videoName, tempPath)
    else:
        newVideo = Video(videoName, filePath)
    app.videos.append(newVideo)
    app.timelineDuration = max(video.videoDuration for video in app.videos)
    newVideo.startTime = 0
    newVideo.endTime = newVideo.startTime + newVideo.videoDuration
    maxDuration = 0
    for video in app.videos:
        if video.videoDuration > maxDuration:
            maxDuration = video.videoDuration
    app.videoDuration = maxDuration
    maxFrames = 0
    for video in app.videos:
        if video.totalFrames > maxFrames:
            maxFrames = video.totalFrames
    app.totalFrames = maxFrames
    for i in range(len(app.videos)):
        video = app.videos[i]
        video.startTime = 0 
        video.endTime = video.startTime + video.videoDuration
        video.timelineRect = {
            "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
            "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
            "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
            "height": app.timelineHeight // len(app.videos) - 2}
    
    FrameCapture(app, newVideo)

def addPhoto(app, filePath):
    unique_id = str(uuid.uuid4())[:8]
    photoName = filePath.split("/")[-1].split(".")[0]+unique_id
    frameRate = 30
    duration  = 1
    totalFrames = frameRate * duration
    photo = Video(photoName, filePath)
    photo.totalFrame = totalFrames
    photo.frameRate = frameRate
    photo.videoDuration = duration

    photo.cap = None

    for i in range(totalFrames):
        frame = cv2.imread(filePath)
        if frame is not None:
            frame = cv2.resize(frame, (photo.width, photo.height))
            cv2.imwrite(f"frame{photoName}{i}.jpg", frame)
            
            grayFrame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            cv2.imwrite(f"frameGray{photoName}{i}.jpg", grayFrame)
            
            sobelFrame = applySobelFilter(frame, photo.sobelThreshold)
            cv2.imwrite(f"frameSobel{photoName}{i}.jpg", sobelFrame)

            # Save inverted Sobel frame
            sobelInverted = 255 - cv2.cvtColor(sobelFrame, cv2.COLOR_BGR2GRAY)
            sobelInvertedFrame = cv2.cvtColor(sobelInverted, cv2.COLOR_GRAY2BGR)
            cv2.imwrite(f"frameSobelInverted{photoName}{i}.jpg", sobelInvertedFrame)
    app.videos.append(photo)
    app.timelineDuration = max(video.videoDuration for video in app.videos)
    photo.startTime = 0
    photo.endTime = photo.startTime + photo.videoDuration
    maxDuration = 0
    for video in app.videos:
        if video.videoDuration > maxDuration:
            maxDuration = video.videoDuration
    app.videoDuration = maxDuration
    maxFrames = 0
    for video in app.videos:
        if video.totalFrames > maxFrames:
            maxFrames = video.totalFrames
    app.totalFrames = maxFrames
    for i in range(len(app.videos)):
        video = app.videos[i]
        video.startTime = 0 
        video.endTime = video.startTime + video.videoDuration
        video.timelineRect = {
            "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
            "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
            "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
            "height": app.timelineHeight // len(app.videos) - 2}
def exportScreenRecording(app, outputPath="newVideo.mp4"): #Cite CHATGPT for the technicals in OPENCV
    rectLeft = 500
    rectTop = 100
    rectWidth = 900
    rectHeight = 500
    frameRate = 30
    backgroundColor = (0, 0, 0)
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(outputPath, fourcc, frameRate, (rectWidth, rectHeight))
    for frameIdx in range(app.totalFrames):
        canvas = np.full((rectHeight, rectWidth, 3), backgroundColor, dtype=np.uint8)
        for video in app.videos:
            currentTime = frameIdx / video.frameRate
            if video.transitions != []:
                for transition in video.transitions:
                    if transition["startTime"] <= currentTime < transition["startTime"] + transition["duration"]:
                        elapsedTime = currentTime - transition["startTime"]
                        transitionDuration = transition["duration"]
                        if transition["type"] == "fadeOutFadeIn":
                            midPoint = transitionDuration / 2
                            if elapsedTime < midPoint:
                                video.opac = 100 - int((elapsedTime / midPoint) * 100)
                            else:
                                video.opac = 100 - int(((transitionDuration - elapsedTime) / midPoint) * 100)
                            break

                        elif transition["type"] == "fadeOut":
                            video.opac = 100 - int((elapsedTime / transitionDuration) * 100)
                            break

                        elif transition["type"] == "fadeIn":
                            video.opac = int((elapsedTime / transitionDuration) * 100)
                            break
            else:
                video.opac = 100
            if video.startTime <= currentTime < video.startTime + video.videoDuration:
                videoFrameIdx = int((currentTime - video.startTime) * video.frameRate)
                framePath = f"frame{video.mode}{video.name}{videoFrameIdx}.jpg"
                videoFrame = cv2.imread(framePath)
                if videoFrame is None:
                    print(f"Error: Unable to load image at {framePath}")
                    continue
                videoFrame = cv2.resize(videoFrame, (int(video.width), int(video.height))) 
                top = int(video.top - rectTop)
                left = int(video.left - rectLeft)
                if 0 <= top < rectHeight and 0 <= left < rectWidth:
                    y1 = max(0, top)
                    y2 = min(rectHeight, top + int(video.height))
                    x1 = max(0, left)
                    x2 = min(rectWidth, left + int(video.width))
                    opacity = video.opac / 100.0
                    croppedFrame = videoFrame[y1-top:y2-top, x1-left:x2-left]
                    canvasRegion = canvas[y1:y2, x1:x2]
                    blendedRegion = cv2.addWeighted(croppedFrame, opacity, canvasRegion, 1-opacity, 0.0)

                    # Place the blended region back onto the canvas
                    canvas[y1:y2, x1:x2] = blendedRegion
        out.write(canvas)
    out.release()

def getVideoDurationAndFrames(path):
    vidObj = cv2.VideoCapture(path)
    totalFrames = int(vidObj.get(cv2.CAP_PROP_FRAME_COUNT))
    frameRate = vidObj.get(cv2.CAP_PROP_FPS)
    duration = totalFrames / frameRate
    return duration, totalFrames

def redrawAll(app):
    if app.menuMode == "Media":
        drawRect(120, 100, 330, 500, fill = rgb(32,32,36), border = "black")
        frameWidth = 135
        frameHeight = 80
        spacingX = 15
        spacingY = 40
        startX = 135 
        startY = 170
        for i in range(len((app.videos))):
            video = app.videos[i]
            row = i // 2
            col = i % 2
            x = startX + col * (frameWidth + spacingX)
            y = startY + row * (frameHeight + spacingY) + app.mediaOffsetY 
            drawImage(f"frame{video.name}0.jpg", x, y, width=frameWidth, height=frameHeight, border = "white")
            drawLabel(video.name[:10], x + frameWidth / 2, y + frameHeight + 15, align="center", size=10, fill = "white")
    drawBG(app)
    drawTimeline(app)
    drawTimer(app)
    drawVideo(app)
    drawPlayPause(app)
    drawScaling(app)
    #drawMenu(app)
    if app.menuMode == "Filters":
        drawFilters(app)
    elif app.menuMode == "FX":
        drawFX(app)
    elif app.menuMode == "Media":
        drawMedia(app)
    if app.help == True:
        drawHelp(app)
    


def drawBG(app):

    drawRect(0, 0, app.width, 100, fill = rgb(21,21,25))
    drawRect(0, 0, 120, app.height, fill = rgb(21,21,25))
    drawRect(450, 0, app.width-450, app.height, fill = rgb(21,21,25))
    drawRect(0, 500, app.width, app.height-500, fill = rgb(21,21,25))
    drawRect(0, 700, app.width, app.height - 700, fill = rgb(32,32,36))
    drawRect(0, 0, 70, app.height, fill = rgb(32,32,36))
    drawRect(950, 350, 900, 500, align = "center", fill = rgb(32,32,36))
    drawLine(70, 720, app.width, 720, fill = "white")
    drawLine(70,0,70,app.height)
    drawLabel("Final Cut 112", app.width//2, 50, fill = "white", bold = True, size = 25)
    drawRect(app.width - 40, 10, 30, 30, fill = rgb(32,32,36), border = "black")
    drawLabel("?", app.width - 25, 25, fill = "white", size = 16)
    

def drawFilters(app):
    drawRect(120, 100, 330, 500, fill=rgb(32,32,36), border="black")
    drawRect(120, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Filters" else "steelBlue", border="black")
    drawRect(230, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "FX" else "steelBlue", border="black")
    drawRect(340, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Media" else "steelBlue", border="black")
    drawLabel("Filters", 175, 125, fill="white", size=16, bold=True)
    drawLabel("FX", 285, 125, fill="white", size=16, bold=True)
    drawLabel("Media", 395, 125, fill="white", size=16, bold=True)
    drawRect(285, 630, 120, 40, fill=rgb(32,32,36), align="center", border = "black")
    drawLabel("Export Video", 285, 630, size=14, bold=True, fill = "white")

    sliderX = 280
    sliderY = 187 
    sliderWidth = 140
    if app.selectedIndex is not None:
        video = app.videos[app.selectedIndex]
        knobX = sliderX + (video.sobelThreshold / 100) * sliderWidth
        drawRect(sliderX, sliderY + 20, sliderWidth, 5, fill="white")
        drawCircle(knobX, sliderY + 22.5, 8, fill="gray", border="black")
        drawLabel(f"{video.sobelThreshold}", sliderX + sliderWidth + 20, sliderY + 20, size=12, fill="white")

        drawRect(140, 160, 120, 40, fill=video.sobelColor)
        drawLabel("Sobel", 200, 180)
        drawRect(140, 220, 120, 40, fill=video.invertedColor)
        drawLabel("Inverted", 200, 240)
        drawRect(140, 280, 120, 40, fill=video.grayColor)
        drawLabel("Gray", 200, 300)
    else:
        drawLabel("Select Media", 285, 550, fill = "white")

def drawFX(app):
    drawRect(120, 100, 330, 500, fill = rgb(32,32,36), border = "black")
    drawRect(120, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Filters" else "steelBlue", border="black") 
    drawRect(230, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "FX" else "steelBlue", border="black")       
    drawRect(340, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Media" else "steelBlue", border="black") 
    drawLabel("Filters", 175, 125, fill="white", size=16, bold=True)
    drawLabel("FX", 285, 125, fill="white", size=16, bold=True)       
    drawLabel("Media", 395, 125, fill="white", size=16, bold=True)
    drawRect(285, 630, 120, 40, fill=rgb(32,32,36), align = "center" , border = "black")
    drawLabel("Export Video", 285, 630, size=14, bold=True, fill = "white")
    if app.selectedIndex is not None:
        drawRect(140, 160, 120, 40, fill=app.PFColor)
        drawLabel("FadeOutFadeIn", 200, 180)
        drawRect(140, 220, 120, 40, fill=app.FOColor)
        drawLabel("Fade Out", 200, 240)
        drawRect(140, 280, 120, 40, fill=app.FIColor)
        drawLabel("Fade In", 200, 300)
    else:
        drawLabel("Select Media", 285, 550, fill = "white")

def drawMedia(app):
    
    drawRect(120, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Filters" else "steelBlue", border="black") 
    drawRect(230, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "FX" else "steelBlue", border="black")       
    drawRect(340, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Media" else "steelBlue", border="black") 
    drawLabel("Filters", 175, 125, fill="white", size=16, bold=True)
    drawLabel("FX", 285, 125, fill="white", size=16, bold=True)       
    drawLabel("Media", 395, 125, fill="white", size=16, bold=True)
    drawRect(285, 630, 120, 40, fill=rgb(32,32,36), align = "center" , border = "black")
    drawLabel("Export Video", 285, 630, size=14, bold=True, fill = "white")

    scrollHeight = 350
    drawRect(120, 500, 330, 100, fill = rgb(32,32,36), border = "black")
    drawRect(285, 550, 120, 40, fill=app.AMColor, align = "center")
    drawLabel("Add Media", 285, 550)
    drawRect(435, 150, 15, 350, fill = "silver", border = "black")

    totalHeight = 15+120*((len(app.videos)+1)//2)
    shownHeight = 350
    scrollHeight = min(350, int(shownHeight/totalHeight*350))
    scrollHeight = max(scrollHeight, 10)

    drawRect(435, app.scrollY, 15, scrollHeight, fill = "dimgray", border = "black")
    drawRect(435, 150, 15, 350, fill = None, border = "black")

def drawHelp(app):
    drawRect(0, 0, app.width, app.height, fill=rgb(0, 0, 0), opacity = 70)
    boxX, boxY = (app.width - 900) // 2, (app.height - 730) // 2
    drawRect(boxX, boxY, 900, 730, fill=rgb(32, 32, 36), border="white")
    drawLabel("Help - Final Cut 112 Instructions", app.width // 2, boxY + 40, size=24, fill="white", bold=True)

    instructions = [
        "General:",
        "- Click the '?' button in the top-right corner for the help menu.",
        "- Press 'Space' to play/pause the video.",
        "",
        "Media Controls:",
        "- Add Media: Click the 'Add Media' button to import a video or photo.",
        "- Select Media: Click on the thumbnail, video, or timeline rectangles to select media.",
        "- Resize media by dragging the corners of selected media.",
        "",
        "Timeline Controls:",
        "- Drag the orange marker to scrub through the timeline.",
        "- Drag and reorder timeline rectangles to adjust video/photo order.",
        "- Press Up/Down Arrows to reorder selected media in the timeline.",
        "- Press 'Backspace' to delete selected media from the timeline.",
        "",
        "FX:",
        "- Add Transitions: Click the fade-in, fade-out, or fade-out-fade-in buttons.",
        "- Move Transitions: Drag transitions on the timeline to reposition them.",
        "- Resize Transitions: Drag the edges of a transition rectangle to adjust its duration.",
        "- Transitions cannot exceed the video bounds or overlap incorrectly.",
        "",
        "Filters:",
        "- Select a video/photo, then navigate to the 'Filters' or 'FX' tab.",
        "- Adjust Sobel Threshold using the slider under the 'Filters' menu.",
        "- Apply effects like 'Gray' or 'Inverted' by selecting respective buttons.",
        "",
        "Export:",
        "- Click 'Export Video' to save the current timeline as 'Screen_recording.mp4'.",
        "",
        "Keyboard Shortcuts:",
        "- 'Command+C': Copy selected media.",
        "- 'Command+V': Paste previously copied media into the timeline.",
    ]

    for i in range(len(instructions)):
        line = instructions[i]
        drawLabel(line, boxX + 20, (boxY + 70) + i * 20, size=16, fill="white", align="left")

    drawRect(boxX + 850,  boxY + 10, 40, 40, fill="red", border="white")
    drawLabel("X", boxX + 870, boxY + 30, size=20, fill="white", bold=True, align="center")
    
    

def drawTimeline(app):
    for i in range(len(app.videos)):
        video = app.videos[i]
        rect = video.timelineRect
        rect["x"] = app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth
        rect["width"] = (video.videoDuration / app.timelineDuration) * app.timelineWidth
        drawRect(rect["x"], rect["y"], rect["width"], rect["height"], fill="steelBlue", border=("black" if i != app.selectedIndex else "red"))
        drawLabel(f"{video.name}", rect["x"] + 5, rect["y"] + rect["height"] / 2, align="left")
        for j in range(len(video.transitions)):
            transition = video.transitions[j]
            transitionStartX = app.timelineX + (transition["startTime"] / app.timelineDuration) * app.timelineWidth
            transitionEndX = app.timelineX + ((transition["startTime"] + transition["duration"]) / app.timelineDuration) * app.timelineWidth
            transitionWidth = max(10, transitionEndX - transitionStartX)
            border = "black"
            if j == app.selectedTransitionIndex and app.draggingTransitionEdge == None:  
                border = "red"
            elif j == app.selectedTransitionIndex and app.draggingTransitionEdge != None:  
                border = "yellow"
            
            drawRect(transitionStartX, rect["y"], transitionWidth, rect["height"], fill="orange", opacity=70, border=border)
            if transition["type"] == "fadeOutFadeIn":
                drawLabel("><", (transitionStartX+transitionWidth//2), (rect["y"]+ rect["height"]//2))
            elif transition["type"] == "fadeOut":
                drawLabel(">", (transitionStartX+transitionWidth//2), (rect["y"]+ rect["height"]//2))
            elif transition["type"] == "fadeIn":
                drawLabel("<", (transitionStartX+transitionWidth//2), (rect["y"]+ rect["height"]//2))
def drawTimer(app):
    intervalCount = 10
    intervalDuration = app.videoDuration / intervalCount
    for i in range(intervalCount + 1):
        
        intervalX= 70 + (i * (app.width - 70) / intervalCount)
        timeLabel = f"{int(i * intervalDuration // 60)}:{int(i * intervalDuration % 60) if ((int(i * intervalDuration % 60)) >= 10) else "0" + str(int(i * intervalDuration % 60))}"
        drawLine(intervalX, 720, intervalX, 710, fill = "white")
        drawLabel(timeLabel, intervalX, 690, size=12, fill="white")
    drawRect(app.barX, 720, 1, app.height-720, fill = "orange")
    drawPolygon(app.barX, 720, app.barX-5, 710, app.barX+5, 710, fill = "orange")
    drawRect(app.barX, 705, 10, 10, fill = "orange", align = "center")


def drawPlayPause(app):
    if app.isPaused:
        drawPolygon(955, 640, 930, 625, 930, 655, fill="white")

    else:
        drawRect(930, 625, 10, 30, fill="white")
        drawRect(945, 625, 10, 30, fill="white")

def drawVideo(app):
    for i in range(len(app.videos)):
        video = app.videos[i]
        currentTime = app.currentFrame / video.frameRate
        if video.transitions != []:
            video.opac = 100

        for transition in video.transitions:
            if transition["startTime"] <= currentTime < transition["startTime"] + transition["duration"]:
                elapsedTime = currentTime - transition["startTime"]
                transitionDuration = transition["duration"]

                if transition["type"] == "fadeOutFadeIn":
                    midPoint = transitionDuration / 2
                    if elapsedTime < midPoint:
                        video.opac = 100 - int((elapsedTime / midPoint) * 100)
                    else:
                        video.opac = 100 - int(((transitionDuration - elapsedTime) / midPoint) * 100)
                    break

                elif transition["type"] == "fadeOut":
                    video.opac = 100 - int((elapsedTime / transitionDuration) * 100)
                    break

                elif transition["type"] == "fadeIn":
                    video.opac = int((elapsedTime / transitionDuration) * 100)
                    break

        if video.startTime <= currentTime < video.startTime + video.videoDuration:
            videoFrame = int((currentTime - video.startTime) * video.frameRate)
            imagePath = f"frame{video.name}{videoFrame}.jpg"
            frame = cv2.imread(imagePath)

            if video.mode == "Sobel":
                frame = applySobelFilter(frame, video.sobelThreshold)
            elif video.mode == "SobelInverted":
                sobelFrame = applySobelFilter(frame, video.sobelThreshold)
                frame = 255 - sobelFrame
            elif video.mode == "Gray":
                drawImage(f"frameGray{video.name}{videoFrame}.jpg", video.left, video.top,width=video.width, height=video.height, opacity = video.opac)
                continue

            tempPath = f"temp{video.name}{videoFrame}.jpg"
            cv2.imwrite(tempPath, frame)
            drawImage(tempPath, video.left, video.top, width=video.width, height=video.height, opacity = video.opac)


def drawScaling(app):
    if app.selectedIndex != None:
        drawCircle(app.videos[app.selectedIndex].left, app.videos[app.selectedIndex].top, 5, fill = "white", border = "black")
        drawCircle(app.videos[app.selectedIndex].left, app.videos[app.selectedIndex].top + app.videos[app.selectedIndex].height, 5, fill = "white", border = "black")
        drawCircle(app.videos[app.selectedIndex].left + app.videos[app.selectedIndex].width, app.videos[app.selectedIndex].top, 5, fill = "white", border = "black")
        drawCircle(app.videos[app.selectedIndex].left + app.videos[app.selectedIndex].width, app.videos[app.selectedIndex].top + app.videos[app.selectedIndex].height, 5, fill = "white", border = "black")

def drawMenu(app):
    drawRect(120, 100, 330, 500, fill = rgb(32,32,36), border = "black")
    drawRect(120, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Filters" else "steelBlue", border="black") 
    drawRect(230, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "FX" else "steelBlue", border="black")       
    drawRect(340, 100, 110, 50, fill=rgb(32,32,36) if app.menuMode != "Media" else "steelBlue", border="black") 
    drawLabel("Filters", 175, 125, fill="white", size=16, bold=True)
    drawLabel("FX", 285, 125, fill="white", size=16, bold=True)       
    drawLabel("Media", 395, 125, fill="white", size=16, bold=True)
    drawRect(285, 630, 120, 40, fill=rgb(32,32,36), align = "center", border = "black")
    drawLabel("Export Video", 285, 630, size=14, bold=True, fill = "white")


def onKeyPress(app, key, modifiers):
    if key == "space":
        if app.videos != []:
            app.isPaused = not app.isPaused
    elif key == "down":
        if app.selectedIndex != 0:   
            app.videos.insert(app.selectedIndex-1, app.videos.pop(app.selectedIndex))
            app.selectedIndex -= 1
        for i in range(len(app.videos)):
            video = app.videos[i]
            video.timelineRect = {
                "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
                "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
                "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
                "height": app.timelineHeight // len(app.videos) - 2
            }

        
    elif key == "up":
        if app.selectedIndex != len(app.videos)-1:   
            app.videos.insert(app.selectedIndex+1, app.videos.pop(app.selectedIndex))
            app.selectedIndex += 1
        for i in range(len(app.videos)):
            video = app.videos[i]
            video.timelineRect = {
                "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
                "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
                "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
                "height": app.timelineHeight // len(app.videos) - 2
            }

    elif key == "backspace" and app.selectedIndex != None and app.selectedTransitionIndex == None:
        app.videos.pop(app.selectedIndex)
        app.selectedIndex = None
        maxDuration = 0
        for video in app.videos:
            if video.videoDuration > maxDuration:
                maxDuration = video.videoDuration
        app.videoDuration = maxDuration
        app.timelineDuration = app.videoDuration
        maxFrames = 0
        for video in app.videos:
            if video.totalFrames > maxFrames:
                maxFrames = video.totalFrames
        app.totalFrames = maxFrames
        for i in range(len(app.videos)):
            video = app.videos[i]
            video.timelineRect = {
            "x": app.timelineX + (video.startTime / app.timelineDuration) * app.timelineWidth,
            "y": 720 + (len(app.videos) - 1 - i) * app.timelineHeight // len(app.videos),
            "width": (video.videoDuration / app.timelineDuration) * app.timelineWidth,
            "height": app.timelineHeight // len(app.videos) - 2}
        if app.videos == []:
            app.paused = True
    elif key == "backspace" and app.selectedIndex != None and app.selectedTransitionIndex != None and app.videos[app.selectedIndex].transitions != []:
        app.videos[app.selectedIndex].transitions.pop(app.selectedTransitionIndex)
    app.selectedTransitionIndex = None
        
    if app.selectedIndex != None:
        videos = [".mp4", ".avi", ".mov", ".mkv"]
        photos = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
        if "meta" in modifiers and key == "c":
            app.clipboardPath = app.videos[app.selectedIndex].path
        if "meta" in modifiers and key == "v" and app.clipboardPath != None:
            if ("." + app.clipboardPath.split(".")[-1]) in videos:
                addVideo(app, app.clipboardPath)
            elif ("." + app.clipboardPath.split(".")[-1]) in photos:
                addPhoto(app, app.clipboardPath)
    
    

def distance(x1, y1, x2, y2):
    return ((x1-x2)**2 + (y1-y2)**2)**0.5


def onMousePress(app, mouseX, mouseY):
    #help
    if (app.width - 40 <= mouseX <= app.width - 10) and (10 <= mouseY <= 40):
        app.help  = True
    if app.help and 1120 <= mouseX <= 1160 and 95 <= mouseY <= 135:
        app.help = False
    #export
    if 225 <= mouseX <= 345 and 610 <= mouseY <= 650:
        exportScreenRecording(app, "screen_recording.mp4")

    #transitions
    if app.selectedIndex is not None:
        video = app.videos[app.selectedIndex]
        rect = video.timelineRect
        for j in range(len(video.transitions)):
            transition = video.transitions[j]
            transitionStartX = app.timelineX + (transition["startTime"] / app.timelineDuration) * app.timelineWidth
            transitionWidth = (transition["duration"] / app.timelineDuration) * app.timelineWidth

            if (transitionStartX - 5 <= mouseX <= transitionStartX + 5) and rect["y"] <= mouseY <= rect["y"] + rect["height"]:
                app.draggingTransition = transition
                app.selectedTransitionIndex = j
                app.draggingTransitionEdge = "left"
                return None

            elif (transitionStartX + transitionWidth - 5 <= mouseX <= transitionStartX + transitionWidth + 5) and rect["y"] <= mouseY <= rect["y"] + rect["height"]:
                app.draggingTransition = transition
                app.selectedTransitionIndex = j
                app.draggingTransitionEdge = "right"
                return None

            elif transitionStartX <= mouseX <= transitionStartX + transitionWidth and rect["y"] <= mouseY <= rect["y"] + rect["height"]:
                app.draggingTransition = transition
                app.selectedTransitionIndex = j
                app.xOffsetTransition = mouseX - transitionStartX
                return None
            else:
                app.selectedTransitionIndex = None
                app.draggingTransitionEdge = None
    if app.draggingTransition == None:
        for i in range(len(app.videos)):
            video = app.videos[i]
            rect = video.timelineRect
            if rect["x"] <= mouseX <= rect["x"] + rect["width"] and rect["y"] <= mouseY <= rect["y"] + rect["height"]:
                app.selectedIndex = i
                app.xOffsetRect = mouseX - rect["x"]
                app.rectDrag = True
                return None

    app.resizingCorner = None

    # ResizingByCorner
    if app.selectedIndex is not None:
        video = app.videos[app.selectedIndex]
        corners = {
            "topLeft": (video.left, video.top),
            "topRight": (video.left + video.width, video.top),
            "bottomLeft": (video.left, video.top + video.height),
            "bottomRight": (video.left + video.width, video.top + video.height),
        }
        for corner in corners:
            cx, cy = corners[corner]
            if distance(mouseX, mouseY, cx, cy) <= 10:
                app.resizingCorner = corner
                return None
    
    #dragging video
    for i in range(len(app.videos) - 1, -1, -1):
        video = app.videos[i]
        app.dragOffsetX = 0
        currentTime = app.currentFrame / video.frameRate
        if (video.left <= mouseX <= video.left + video.width and
            video.top <= mouseY <= video.top + video.height and
            video.startTime <= currentTime < video.startTime + video.videoDuration):
            app.selectedIndex = i
            app.xOffset = mouseX - video.left
            app.yOffset = mouseY - video.top
            app.draggingVideo = True
            return None
    #rectdrag
    

    #PlayPause
    if 930 <= mouseX <= 955 and 625 <= mouseY <= 655 and app.videos != []:
        app.isPaused = not app.isPaused

    #timedarg
    elif 70 <= mouseX <= app.width and 700 <= mouseY <= 720:
        app.timeDrag = True
        app.barX = mouseX
        app.currentFrame = (app.barX - 70)*app.totalFrames//(app.width-70)
        app.counter = app.currentFrame//app.sampleRate
    #Filters
    if app.selectedIndex != None:
        video = app.videos[app.selectedIndex]
    if app.menuMode == "Filters" and app.videos != []:
        if 140 <= mouseX <= 260 and 160 <= mouseY <= 200:  #Sobel button
            if video.mode == "Sobel":
                video.mode = ""
                video.sobelColor = "white"
            else:
                video.mode = "Sobel"
                video.sobelColor = "gray"
                video.grayColor = "white"
                video.invertedColor = "white"

        elif 140 <= mouseX <= 260 and 280 <= mouseY <= 320:  #Gray button
            if video.mode == "Gray":
                video.mode = ""
                video.grayColor = "white"
            else:
                video.mode = "Gray"
                video.grayColor = "gray"
                video.sobelColor = "white"
                video.invertedColor = "white"

        elif 140 <= mouseX <= 260 and 220 <= mouseY <= 260:  #sobelInverted button
            if video.mode == "SobelInverted":
                video.mode = ""
                video.invertedColor = "white"
            else:
                video.mode = "SobelInverted"
                video.invertedColor = "gray"
                video.sobelColor = "white"
                video.grayColor = "white"
    elif app.menuMode == "FX":
        if 140 <= mouseX <= 260 and 160 <= mouseY <= 200:  # FOFI
            app.PFColor = "gray"
            if app.selectedIndex is not None:
                transition = {
                    "type": "fadeOutFadeIn",
                    "startTime": app.videos[app.selectedIndex].startTime,
                    "duration": 1,
                }
                app.videos[app.selectedIndex].transitions.append(transition)
        if 140 <= mouseX <= 260 and 220 <= mouseY <= 260:  # FO
            app.FOColor = "gray"
            if app.selectedIndex is not None:
                transition = {
                    "type": "fadeOut",
                    "startTime": app.videos[app.selectedIndex].startTime,
                    "duration": 1,
                }
                app.videos[app.selectedIndex].transitions.append(transition)
        if 140 <= mouseX <= 260 and 280 <= mouseY <= 320:  # FI
            app.FIColor = "gray"
            if app.selectedIndex is not None:
                transition = {
                    "type": "fadeIn",
                    "startTime": app.videos[app.selectedIndex].startTime,
                    "duration": 1,
                }
                app.videos[app.selectedIndex].transitions.append(transition)
    elif app.menuMode == "Media":
        if 225 <= mouseX <= 345 and 530 <= mouseY <= 570:  # Add Media button
            app.AMColor = "gray"
            filePath = uploadMedia()
            videos = [".mp4", ".avi", ".mov", ".mkv"]
            photos = [".jpg", ".jpeg", ".png", ".bmp", ".gif"]
            if filePath != "":
                if ("." + filePath.split(".")[-1]) in videos:
                    addVideo(app, filePath)
                elif ("." + filePath.split(".")[-1]) in photos:
                    addPhoto(app, filePath)
        frameWidth = 135
        frameHeight = 80
        spacingX = 20
        spacingY = 40
        startX = 140 
        startY = 170
        for i in range(len(app.videos)):
            row = i // 2
            col = i%2 
            x = startX + col*(spacingX + frameWidth)
            y = startY + row*(spacingY + frameHeight)
            if x <= mouseX <= x+frameWidth and y <= mouseY <= y+frameHeight:
                app.selectedIndex = i
                break
        totalHeight = 15 + 120 * ((len(app.videos) + 1) // 2)
        shownHeight = 350
        scrollHeight = min(350, int(shownHeight / totalHeight * 350))
        scrollHeight = max(scrollHeight, 10)

        if 435 <= mouseX <= 450 and app.scrollY <= mouseY <= app.scrollY + scrollHeight:
            app.scrollDragging = True
            app.scrollStartY = mouseY
            app.scrollOffset = mouseY - app.scrollY

    #mode select
    if 120 <= mouseX <= 230 and 100 <= mouseY <= 150:
        app.menuMode = "Filters"
    elif 230 <= mouseX <= 340 and 100 <= mouseY <= 150:
        app.menuMode = "FX"
    elif 340 <= mouseX <= 450 and 100 <= mouseY <= 150:
        app.menuMode = "Media"
        


def onMouseDrag(app, mouseX, mouseY):
#changing Transition Duration
    if app.selectedIndex != None:
        video = app.videos[app.selectedIndex]

    if app.draggingTransition is not None and app.selectedIndex is not None and app.draggingTransitionEdge == None:
        video = app.videos[app.selectedIndex]
        newStartX = max(app.timelineX, min(mouseX - app.xOffsetTransition, app.timelineX + app.timelineWidth))
        app.draggingTransition["startTime"] = ((newStartX - app.timelineX) / app.timelineWidth) * app.timelineDuration
        app.draggingTransition["startTime"] = max(video.startTime, min(app.draggingTransition["startTime"], video.endTime - app.draggingTransition["duration"]))

    elif app.draggingTransition is not None and app.selectedIndex is not None and app.draggingTransitionEdge is not None:
        if app.draggingTransitionEdge == "right":
            newEndX = max(app.timelineX, min(mouseX, app.timelineX + app.timelineWidth))
            newEndTime = ((newEndX - app.timelineX) / app.timelineWidth) * app.timelineDuration
            newEndTime = max(app.draggingTransition["startTime"], min(newEndTime, video.endTime))
            app.draggingTransition["duration"] = newEndTime - app.draggingTransition["startTime"]

        elif app.draggingTransitionEdge == "left":
            newStartX = max(app.timelineX, min(mouseX, app.timelineX + app.timelineWidth))
            newStartTime = ((newStartX - app.timelineX) / app.timelineWidth) * app.timelineDuration
            newStartTime = max(video.startTime, min(newStartTime, app.draggingTransition["startTime"] + app.draggingTransition["duration"]))
            app.draggingTransition["duration"] = max(0, app.draggingTransition["startTime"] + app.draggingTransition["duration"] - newStartTime)
            app.draggingTransition["startTime"] = newStartTime


 #sobelAdjust
    if app.menuMode == "Filters":
        sliderX = 280
        sliderWidth = 140  
        if 280 <= mouseX <= 420 and 207 <= mouseY <= 247: 
            video.sobelThreshold = int(((mouseX - sliderX) / sliderWidth) * 100)
            video.sobelThreshold = max(0, min(100, video.sobelThreshold))
    elif app.menuMode == "Media":
        if app.scrollDragging == True:
                totalHeight = 15 + 120 * ((len(app.videos) + 1) // 2)  
                shownHeight = 350
                scrollHeight = min(350, int(shownHeight / totalHeight * 350))
                scrollHeight = max(scrollHeight, 10)

                newScrollY = mouseY - app.scrollOffset
                app.scrollY = max(150, min(newScrollY, 150 + 350 - scrollHeight))

                scrollRatio = (app.scrollY - 150) / (350.1 - scrollHeight)
                app.mediaOffsetY = -scrollRatio * (totalHeight - shownHeight)
    #timedrag
    if app.timeDrag == True and 70 <= mouseX <= app.width:
        app.barX = mouseX
        app.currentFrame = (app.barX - 70)*app.totalFrames//(app.width-70)
        app.counter = app.currentFrame//app.sampleRate
    #resize
    if app.resizingCorner and app.selectedIndex is not None:
        video = app.videos[app.selectedIndex]
        minWidth = 100
        minHeight = minWidth / video.aspectRatio

        minX, maxX = 500, 1400
        minY, maxY = 100, 600

        if app.resizingCorner == "topLeft":
            newWidth = video.width + (video.left - mouseX)
            newHeight = newWidth / video.aspectRatio
            if newWidth >= minWidth and newHeight >= minHeight:
                deltaWidth = newWidth - video.width
                deltaHeight = newHeight - video.height
                newLeft = video.left - deltaWidth
                newTop = video.top - deltaHeight
                if newLeft >= minX and newTop >= minY and (newLeft + newWidth) <= maxX and (newTop + newHeight) <= maxY:
                    video.left = newLeft
                    video.top = newTop
                    video.width = newWidth
                    video.height = newHeight

        elif app.resizingCorner == "topRight":
            newWidth = video.width + (mouseX - (video.left + video.width))
            newHeight = newWidth / video.aspectRatio
            if newWidth >= minWidth and newHeight >= minHeight:
                deltaHeight = newHeight - video.height
                newTop = video.top - deltaHeight
                if newTop >= minY and (video.left + newWidth) <= maxX and (newTop + newHeight) <= maxY:
                    video.top = newTop
                    video.width = newWidth
                    video.height = newHeight

        elif app.resizingCorner == "bottomLeft":
            newWidth = video.width + (video.left - mouseX)
            newHeight = newWidth / video.aspectRatio
            if newWidth >= minWidth and newHeight >= minHeight:
                newLeft = video.left - (newWidth - video.width)
                newBottom = video.top + newHeight
                if newLeft >= minX and newBottom <= maxY and (newLeft + newWidth) <= maxX:
                    video.left = newLeft
                    video.width = newWidth
                    video.height = newHeight

        elif app.resizingCorner == "bottomRight":
            newWidth = mouseX - video.left
            newHeight = newWidth / video.aspectRatio
            if newWidth >= minWidth and newHeight >= minHeight:
                newBottom = video.top + newHeight
                newRight = video.left + newWidth
                if newRight <= maxX and newBottom <= maxY and video.top >= minY:
                    video.width = newWidth
                    video.height = newHeight
    #rectDrag
    if app.selectedIndex is not None and app.rectDrag:
        video = app.videos[app.selectedIndex]
        rect = video.timelineRect
        rect['x'] = max(app.timelineX, min(mouseX - app.xOffsetRect, app.timelineX + app.timelineWidth - rect["width"]))
        newStartTime = ((rect["x"] - app.timelineX) / app.timelineWidth) * app.timelineDuration
        deltaTime = newStartTime - video.startTime
        video.startTime = newStartTime
        video.endTime = video.startTime + video.videoDuration
        video.timelineRect = rect
        for transition in video.transitions:
            transition["startTime"] += deltaTime
            if transition["startTime"] < video.startTime:
                transition["startTime"] = video.startTime
            if transition["startTime"] + transition["duration"] > video.endTime:
                transition["startTime"] = video.endTime - transition["duration"]
        
    #dragginVideo
    if app.draggingVideo and app.selectedIndex is not None:
        video = app.videos[app.selectedIndex]
        newLeft = mouseX - app.xOffset
        newTop = mouseY - app.yOffset
        video.left = max(500, min(1400 - video.width, newLeft))
        video.top = max(100, min(600 - video.height, newTop))
        
def onMouseRelease(app, mouseX, mouseY):
    app.draggingVideo = False
    app.resizingCorner = None
    app.timeDrag = False
    app.rectDrag = False
    app.draggingTransitionEdge = None
    app.PFColor = "white"
    app.FOColor = "white"
    app.FIColor = "white" 
    app.AMColor = "white"
    if app.draggingTransition is not None:
        app.draggingTransition = None

def onStep(app):
    if not app.isPaused:
        app.counter += 1
        app.currentFrame = (app.counter*app.sampleRate)
        if app.totalFrames != 0:
            app.barX = 70 + app.currentFrame/app.totalFrames * (app.width-70)
        else:
            app.barX = 70
    if app.currentFrame >= app.totalFrames:
        app.currentFrame = 1
        app.counter = 0

  
# RUNNNN
if __name__ == '__main__': 
    runApp(width = 1440, height = 900)