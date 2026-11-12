package io.github.tolgaavan.yatirim;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

import androidx.webkit.WebViewAssetLoader;

/**
 * Uygulama ekranı APK'nın içindedir (assets/index.html); internetten yalnızca veri (ozet.json) çekilir.
 * Son alınan veri telefonda saklanır, internet yokken o gösterilir.
 */
public class AnaEkran extends Activity {
    private static final String ICERIK = "appassets.androidplatform.net";
    private static final String ADRES = "https://" + ICERIK + "/assets/index.html";
    private WebView web;

    @Override
    protected void onCreate(Bundle kayit) {
        super.onCreate(kayit);
        final WebViewAssetLoader yukleyici = new WebViewAssetLoader.Builder()
            .addPathHandler("/assets/", new WebViewAssetLoader.AssetsPathHandler(this))
            .build();
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0f1115"));
        WebSettings ayar = web.getSettings();
        ayar.setJavaScriptEnabled(true);
        ayar.setDomStorageEnabled(true);
        ayar.setAllowFileAccess(false);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebView v, WebResourceRequest istek) {
                return yukleyici.shouldInterceptRequest(istek.getUrl());
            }

            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest istek) {
                Uri u = istek.getUrl();
                if (ICERIK.equals(u.getHost())) return false;
                startActivity(new Intent(Intent.ACTION_VIEW, u));   // dış bağlantılar tarayıcıda açılır
                return true;
            }
        });
        setContentView(web);
        if (kayit != null) web.restoreState(kayit);
        else web.loadUrl(ADRES);
    }

    @Override
    protected void onSaveInstanceState(Bundle kayit) {
        super.onSaveInstanceState(kayit);
        web.saveState(kayit);
    }

    @Override
    public void onBackPressed() {
        if (web.canGoBack()) web.goBack();
        else super.onBackPressed();
    }
}
