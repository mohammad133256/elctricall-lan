[app]

# (str) Title of your application
title = Electrical Industrial Lab

# (str) Package name
package.name = electricallab

# (str) Package domain (needed for android/ios packaging)
package.domain = org.electricallab

# (str) Source code where the main.py live
source.dir = .

# (list) Source files to include (let empty to include all the files)
source.include_exts = py,png,jpg,kv,atlas,ttf,txt,md

# (list) List of inclusions using pattern matching
#source.include_patterns = assets/*,images/*.png

# (list) Source files to exclude (let empty to not exclude anything)
source.exclude_exts = spec

# (list) List of directory to exclude (let empty to not exclude anything)
source.exclude_dirs = tests, bin, .buildozer

# (str) Application versioning (method 1)
version = 1.0.0

# (list) Application requirements
requirements = python3,kivy==2.3.1,kivymd==1.2.0,pillow,android

# (str) Presplash background color (for android toolchain)
presplash.bgcolor = #0D1B2A

# (str) Orientation
orientation = portrait

# (bool) Indicate if the application should be fullscreen or not
fullscreen = 0

# (list) Permissions
android.permissions = INTERNET,VIBRATE

# (int) Target Android API
android.api = 33

# (int) Minimum API
android.minapi = 24

# (str) Android NDK version to use
android.ndk = 25b

# (bool) If True, then skip trying to update the Android sdk
android.skip_update = False

# (str) Android entry point
android.entrypoint = org.kivy.android.PythonActivity

# (str) The format used to package the app for release mode (apk or aab)
android.release_artifact = apk

# (str) Accepts a non-empty string, containing a valid Python package name.
# This package name will be used as the package name for the Android service.
#services =

# (str) The Android architecture to build for
android.archs = arm64-v8a, armeabi-v7a

# (bool) enables Android X support
android.enable_androidx = True

# (list) The Android application meta-data to include
#android.meta_data =

# (list) Copy these files to app assets folder
#android.add_assets =

# (list) Add Java .jar files into the libs
#android.add_jars =

[buildozer]

# (int) Log level (0 = error only, 1 = info, 2 = debug)
log_level = 2

# (int) Display warning if buildozer is run as root (0 = False, 1 = True)
warn_on_root = 0
