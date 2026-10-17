import os, shutil
from PIL import Image

root = 'android/app/src/main'
pkg_dir = os.path.join(root, 'java', 'com', 'driveflow', 'app')
os.makedirs(pkg_dir, exist_ok=True)

# 1) permissies
mf = os.path.join(root, 'AndroidManifest.xml')
s = open(mf, encoding='utf-8').read()
perms = '''
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.READ_MEDIA_IMAGES" />
    <uses-permission android:name="android.permission.READ_MEDIA_VIDEO" />
    <uses-permission android:name="android.permission.READ_EXTERNAL_STORAGE" android:maxSdkVersion="32" />
'''
if 'READ_MEDIA_IMAGES' not in s:
    s = s.replace('</manifest>', perms + '</manifest>')
open(mf, 'w', encoding='utf-8').write(s)

# 2) eigen galerij-plugin
gallery = r'''package com.driveflow.app;

import android.Manifest;
import android.content.ContentUris;
import android.database.Cursor;
import android.net.Uri;
import android.os.Build;
import android.provider.MediaStore;
import com.getcapacitor.JSArray;
import com.getcapacitor.JSObject;
import com.getcapacitor.PermissionState;
import com.getcapacitor.Plugin;
import com.getcapacitor.PluginCall;
import com.getcapacitor.PluginMethod;
import com.getcapacitor.annotation.CapacitorPlugin;
import com.getcapacitor.annotation.Permission;
import com.getcapacitor.annotation.PermissionCallback;
import java.io.File;
import java.io.FileOutputStream;
import java.io.InputStream;

@CapacitorPlugin(
    name = "Gallery",
    permissions = {
        @Permission(alias = "images", strings = { Manifest.permission.READ_MEDIA_IMAGES }),
        @Permission(alias = "storage", strings = { Manifest.permission.READ_EXTERNAL_STORAGE })
    }
)
public class GalleryPlugin extends Plugin {

    private String alias() {
        return Build.VERSION.SDK_INT >= 33 ? "images" : "storage";
    }

    @PluginMethod
    public void ensurePermission(PluginCall call) {
        if (getPermissionState(alias()) == PermissionState.GRANTED) {
            JSObject r = new JSObject();
            r.put("granted", true);
            call.resolve(r);
        } else {
            requestPermissionForAlias(alias(), call, "permCallback");
        }
    }

    @PermissionCallback
    private void permCallback(PluginCall call) {
        JSObject r = new JSObject();
        r.put("granted", getPermissionState(alias()) == PermissionState.GRANTED);
        call.resolve(r);
    }

    @PluginMethod
    public void list(PluginCall call) {
        if (getPermissionState(alias()) != PermissionState.GRANTED) {
            call.reject("geen toegang tot foto's");
            return;
        }
        Integer li = call.getInt("limit", 100);
        int limit = li == null ? 100 : li;
        Long sl = call.getLong("since", 0L);
        long since = sl == null ? 0L : sl;
        String[] proj = {
            MediaStore.Images.Media._ID,
            MediaStore.Images.Media.DISPLAY_NAME,
            MediaStore.Images.Media.DATE_ADDED,
            MediaStore.Images.Media.DATE_TAKEN,
            MediaStore.Images.Media.SIZE
        };
        String sel = since > 0 ? MediaStore.Images.Media.DATE_ADDED + " > ?" : null;
        String[] args = since > 0 ? new String[] { String.valueOf(since / 1000) } : null;
        JSArray items = new JSArray();
        try (Cursor c = getContext().getContentResolver().query(
            MediaStore.Images.Media.EXTERNAL_CONTENT_URI, proj, sel, args,
            MediaStore.Images.Media.DATE_ADDED + " DESC")) {
            if (c != null) {
                int n = 0;
                while (c.moveToNext() && n < limit) {
                    long added = c.getLong(2) * 1000L;
                    long taken = c.getLong(3);
                    JSObject o = new JSObject();
                    o.put("id", c.getLong(0));
                    o.put("name", c.getString(1));
                    o.put("date", taken > 0 ? taken : added);
                    o.put("size", c.getLong(4));
                    items.put(o);
                    n++;
                }
            }
        } catch (Exception e) {
            call.reject("lezen mislukt: " + e.getMessage());
            return;
        }
        JSObject r = new JSObject();
        r.put("items", items);
        call.resolve(r);
    }

    @PluginMethod
    public void copy(PluginCall call) {
        Long id = call.getLong("id");
        if (id == null) {
            call.reject("id ontbreekt");
            return;
        }
        try {
            File dir = getContext().getCacheDir();
            File[] old = dir.listFiles();
            if (old != null) {
                long now = System.currentTimeMillis();
                for (File f : old) {
                    if (f.getName().startsWith("dfimg_") && now - f.lastModified() > 600000L) f.delete();
                }
            }
            Uri uri = ContentUris.withAppendedId(MediaStore.Images.Media.EXTERNAL_CONTENT_URI, id);
            File out = new File(dir, "dfimg_" + id);
            try (InputStream in = getContext().getContentResolver().openInputStream(uri);
                 FileOutputStream os = new FileOutputStream(out)) {
                if (in == null) {
                    call.reject("bestand niet te openen");
                    return;
                }
                byte[] buf = new byte[65536];
                int len;
                while ((len = in.read(buf)) > 0) os.write(buf, 0, len);
            }
            JSObject r = new JSObject();
            r.put("path", out.getAbsolutePath());
            call.resolve(r);
        } catch (Exception e) {
            call.reject("kopieren mislukt: " + e.getMessage());
        }
    }
}
'''
open(os.path.join(pkg_dir, 'GalleryPlugin.java'), 'w', encoding='utf-8').write(gallery)

main = '''package com.driveflow.app;

import android.os.Bundle;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        registerPlugin(GalleryPlugin.class);
        super.onCreate(savedInstanceState);
    }
}
'''
open(os.path.join(pkg_dir, 'MainActivity.java'), 'w', encoding='utf-8').write(main)

# 3) app-icoon
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
