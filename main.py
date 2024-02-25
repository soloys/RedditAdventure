from moviepy.editor import *
import reddit, screenshot, time, subprocess, random, configparser, sys, math
from os import listdir
from os.path import isfile, join
from moviepy.editor import TextClip
from PIL import Image, ImageDraw, ImageFont
import textwrap

def createVideo():
    config = configparser.ConfigParser()
    config.read('config.ini')
    outputDir = config["General"]["OutputDirectory"]

    startTime = time.time()

    # Get script from reddit
    # If a post id is listed, use that. Otherwise query top posts
    if (len(sys.argv) == 2):
        script = reddit.getContentFromId(outputDir, sys.argv[1])
    else:
        postOptionCount = int(config["Reddit"]["NumberOfPostsToSelectFrom"])
        script = reddit.getContent(outputDir, postOptionCount)
    fileName = script.getFileName()


    # Setup background clip
    bgDir = config["General"]["BackgroundDirectory"]
    bgPrefix = config["General"]["BackgroundFilePrefix"]
    bgFiles = [f for f in listdir(bgDir) if isfile(join(bgDir, f))]
    bgCount = len(bgFiles)
    bgIndex = random.randint(0, bgCount-1)
    backgroundVideo = VideoFileClip(
        filename=f"{bgDir}/{bgPrefix}{bgIndex}.mp4", 
        audio=False).subclip(0, script.getDuration())
    w, h = backgroundVideo.size

    def __createClip(comment, audioClip, marginSize):
        # Use a truetype font
        fnt = ImageFont.truetype('Fonts\RobotoCondensed-Bold.ttf', 30)  # Increase the font size to 30

        # Wrap the text
        wrapper = textwrap.TextWrapper(width=40)  # Adjust the width to your needs
        wrapped_text = wrapper.fill(text=comment)

        # Calculate the size of the text box
        text_width, text_height = fnt.getsize_multiline(wrapped_text)

        # Create a new image with white background
        img = Image.new('RGB', (text_width + marginSize, text_height + marginSize), color = (255, 255, 255))

        d = ImageDraw.Draw(img)
        # Draw text, half down the image
        d.multiline_text((marginSize // 2, marginSize // 2), wrapped_text, font=fnt, fill=(0, 0, 0))

        # Save the image
        img.save('comment.png')

        imageClip = ImageClip(
            'comment.png',
            duration=audioClip.duration
            ).set_position(("center", "center"))
        imageClip = imageClip.resize(width=(text_width + marginSize))
        videoClip = imageClip.set_audio(audioClip)
        videoClip.fps = 1
        return videoClip

    # Create video clips
    print("Editing clips together...")
    clips = []
    marginSize = int(config["Video"]["MarginSize"])
    clips.append(__createClip(script.title, script.titleAudioClip, marginSize))
    for comment in script.frames:
        clips.append(__createClip(comment.text, comment.audioClip, marginSize))

    # Merge clips into single track
    contentOverlay = concatenate_videoclips(clips).set_position(("center", "center"))

    # Compose background/foreground
    final = CompositeVideoClip(
        clips=[backgroundVideo, contentOverlay], 
        size=backgroundVideo.size).set_audio(contentOverlay.audio)
    final.duration = script.getDuration()
    final.set_fps(backgroundVideo.fps)

    # Write output to file
    print("Rendering final video...")
    bitrate = config["Video"]["Bitrate"]
    threads = config["Video"]["Threads"]
    outputFile = f"{outputDir}/{fileName}.mp4"
    final.write_videofile(
        outputFile, 
        codec = 'mpeg4',
        threads = threads, 
        bitrate = bitrate
    )
    print(f"Video completed in {time.time() - startTime}")

    # Preview in VLC for approval before uploading
    if (config["General"].getboolean("PreviewBeforeUpload")):
        vlcPath = config["General"]["VLCPath"]
        p = subprocess.Popen([vlcPath, outputFile])
        print("Waiting for video review. Type anything to continue")
        wait = input()

    print("Video is ready to upload!")
    print(f"Title: {script.title}  File: {outputFile}")
    endTime = time.time()
    print(f"Total time: {endTime - startTime}")

if __name__ == "__main__":
    createVideo()