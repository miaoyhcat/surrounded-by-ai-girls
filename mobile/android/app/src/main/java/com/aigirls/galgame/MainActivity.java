package com.aigirls.galgame;

import android.os.Build;
import android.os.Bundle;
import android.view.View;
import android.view.WindowManager;
import androidx.core.view.WindowCompat;
import androidx.core.view.WindowInsetsCompat;
import androidx.core.view.WindowInsetsControllerCompat;

import com.getcapacitor.BridgeActivity;

public class MainActivity extends BridgeActivity {
    private WindowInsetsControllerCompat insetsController;

    @Override
    public void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        // 沉浸式全屏：隐藏状态栏 + 导航栏（游戏画面占满整块屏幕）
        // 用 WindowCompat 兼容写法（setDecorFitsSystemWindows 是 API 30+ 方法，直接调用在安卓 10 及以下会 NoSuchMethodError 闪退）
        WindowCompat.setDecorFitsSystemWindows(getWindow(), false);
        // 刘海屏/水滴屏：内容延伸到短边凹口区域（横屏消灭黑边，红米14R 等 20:9 水滴屏必需）
        // （主题 values-v28 里也配置了 shortEdges，双保险）
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.P) {
            WindowManager.LayoutParams lp = getWindow().getAttributes();
            lp.layoutInDisplayCutoutMode = WindowManager.LayoutParams.LAYOUT_IN_DISPLAY_CUTOUT_MODE_SHORT_EDGES;
            getWindow().setAttributes(lp);
        }
        insetsController = WindowCompat.getInsetsController(getWindow(), getWindow().getDecorView());
        hideSystemBars();
        // 保持屏幕常亮（游玩时不熄屏）
        getWindow().addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON);
    }

    private void hideSystemBars() {
        if (insetsController == null) return;
        insetsController.hide(WindowInsetsCompat.Type.systemBars());
        insetsController.setSystemBarsBehavior(WindowInsetsControllerCompat.BEHAVIOR_SHOW_TRANSIENT_BARS_BY_SWIPE);
    }

    @Override
    public void onWindowFocusChanged(boolean hasFocus) {
        super.onWindowFocusChanged(hasFocus);
        // 焦点回来（通知栏下拉后、弹窗关闭后）重放隐藏，防止系统栏重现（HyperOS/MIUI 常见）
        if (hasFocus) hideSystemBars();
    }
}
