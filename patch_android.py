import os, re, shutil
from PIL import Image

root = 'android/app/src/main'
# 1) permissies
mf = os.path.join(root, 'AndroidManifest.xml')
s = open(mf, encoding='utf-8').read()
perms = '''
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
    <uses-permission android:name="android.permission.ACCESS_MEDIA_LOCATION" />
'''
for name in ('READ_MEDIA_IMAGES', 'READ_MEDIA_VIDEO', 'ACCESS_MEDIA_LOCATION'):
    pass
if 'READ_MEDIA_IMAGES' not in s:
    s = s.replace('</manifest>', perms + '</manifest>')
open(mf, 'w', encoding='utf-8').write(s)

# 2) app-icoon
src = Image.open('assets/icon-512.png').convert('RGB')
sizes = {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}
res = os.path.join(root, 'res')
shutil.rmtree(os.path.join(res, 'mipmap-anydpi-v26'), ignore_errors=True)
for d, px in sizes.items():
    folder = os.path.join(res, 'mipmap-' + d)
    os.makedirs(folder, exist_ok=True)
    img = src.resize((px, px), Image.LANCZOS)
    for n in ('ic_launcher.png', 'ic_launcher_round.png', 'ic_launcher_foreground.png'):
        img.save(os.path.join(folder, n))
print('patched')
