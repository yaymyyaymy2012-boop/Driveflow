import os, shutil

# 1) permissies (internet voor DriveFlow-cloud)
mf = 'android/app/src/main/AndroidManifest.xml'
try:
    s = open(mf, encoding='utf8').read()
    for p in ('INTERNET', 'ACCESS_NETWORK_STATE', 'VIBRATE'):
        tag = '<uses-permission android:name="android.permission.%s" />' % p
        if tag not in s:
            s = s.replace('</manifest>', '    ' + tag + '\n</manifest>')
    open(mf, 'w', encoding='utf8').write(s)
    print('permissions ok')
except Exception as e:
    print('permissions skipped:', e)

# 2) icoon (wordt overgeslagen als icon-512.png ontbreekt, de build gaat dan gewoon door)
try:
    from PIL import Image
    icon = 'assets/icon-512.png'
    if not os.path.exists(icon):
        print('geen icon-512.png gevonden, standaardicoon blijft')
    else:
        res = 'android/app/src/main/res'
        src = Image.open(icon).convert('RGB')
        shutil.rmtree(os.path.join(res, 'mipmap-anydpi-v26'), ignore_errors=True)
        for d, px in {'mdpi': 48, 'hdpi': 72, 'xhdpi': 96, 'xxhdpi': 144, 'xxxhdpi': 192}.items():
            f = os.path.join(res, 'mipmap-' + d); os.makedirs(f, exist_ok=True)
            img = src.resize((px, px), Image.LANCZOS)
            for n in ('ic_launcher.png', 'ic_launcher_round.png', 'ic_launcher_foreground.png'):
                img.save(os.path.join(f, n))
        print('icon ok')
except Exception as e:
    print('icon skipped:', e)
print('patched')

# 3) geen fullscreen: app blijft binnen statusbalk en navigatiebalk (en boven het toetsenbord)
try:
    import glob, re
    hits = glob.glob('android/app/src/main/java/**/MainActivity.java', recursive=True)
    if not hits:
        print('MainActivity niet gevonden, insets overgeslagen')
    for path in hits:
        pkg = re.search(r'^package\s+([\w.]+);', open(path, encoding='utf8').read(), re.M).group(1)
        open(path, 'w', encoding='utf8').write('''package %s;

import android.graphics.Color;
import android.os.Bundle;
import android.view.View;
import androidx.core.graphics.Insets;
import androidx.core.view.ViewCompat;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;
import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        getWindow().getDecorView().setBackgroundColor(Color.parseColor("#0B1220"));
        View content = findViewById(android.R.id.content);
        new WindowInsetsControllerCompat(getWindow(), content).setAppearanceLightStatusBars(false);
        new WindowInsetsControllerCompat(getWindow(), content).setAppearanceLightNavigationBars(false);
        ViewCompat.setOnApplyWindowInsetsListener(content, (v, insets) -> {
            Insets bars = insets.getInsets(WindowInsetsCompat.Type.systemBars() | WindowInsetsCompat.Type.displayCutout());
            Insets ime = insets.getInsets(WindowInsetsCompat.Type.ime());
            v.setPadding(bars.left, bars.top, bars.right, Math.max(bars.bottom, ime.bottom));
            return WindowInsetsCompat.CONSUMED;
        });
        ViewCompat.requestApplyInsets(content);
    }
}
''' % pkg)
        print('insets ok', path)
except Exception as e:
    print('insets skipped:', e)
