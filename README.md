# Intro

**imagenet-resumable-downloader** is GUI based utility created to download images for 
the ImageNet data set. It does so by making use of publicly available image URLs 
provided by http://image-net.org.

Also, the download can be paused 
and resumed later. That means that if a user quits the program and starts it the 
next day, the download will continue from the last stopping point.

Currently, the utility can only download images. If you want to create an 
actual data set that can be used to train (for example) Keras models, you 
will have to use additional tools for that.

## A few warnings

Notice that it has been a while since ImageNet URLs were collected for the 
first time. Therefore, many images are no longer available via these URLs.

__Also, be warned! there are many placeholder images with text such as "This photo
is no longer available". Here is an example of a Flickr image obtainable via one of 
ImageNet URLs:__

![alt text](image_not_available.jpg "One of images among downloaded ones")

__You definitely don't want to include this one in the training set. But 
unfortunately, the program cannot distinguish them from the images with 
actual content. So after the download is complete, you will have to use 
other tools to find and remove placeholders like one above.__

# Features

- Qt based user interface
- option to download all images
- option to specify the number of images to download
- option to specify the number of images per category to download
- option to specify the download location
- capability to pause and resume the download
- progress bar, estimated time till the end 
- report file containing a list of urls of images that were 
unavailable or could not be downloaded

# Installation and launch


Clone the repository or download it as a zip archive.
Open a terminal.

Go inside the repository git directory (the one containing a .git folder and 
requirements.txt file)
```
    cd /path/to/repo
```
Go inside the repository git directory and install project's dependencies.
```
    pip install -r requirements.txt
```
Launch it by issuing the command
```
    python main.py
```

# Usage

- Launch the program
- click a button "Choose" to specify ImageNet destination folder
- set a spin box value next to "# of images to download" to 1000
- set a spin box value next to "# of images per category" to 200
- click a "Download" button
- wait until program finishes

Now go to your destination directory. By the end of the download you should see 
a few directories with names like "n932939" each of them containing about 
200 images. These names match the word net ids of images contained in such folder. 

# License
This software is licensed under GPL v3 license (see LICENSE).

## Third party libraries licenses
The software uses third party libraries that are distributed under 
their own terms (see LICENSE-3RD-PARTY).
