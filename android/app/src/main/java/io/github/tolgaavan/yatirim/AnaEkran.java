package io.github.tolgaavan.yatirim;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.webkit.WebResourceError;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

/** Telefondaki yarış sayfasını (GitHub Pages) tam ekran gösteren basit kabuk. */
public class AnaEkran extends Activity {
    private static final String ADRES = "https://tolgaavan.github.io/yatirim-yarisi/";
    private static final String SITE = "tolgaavan.github.io";
    private WebView web;

    @Override
    protected void onCreate(Bundle kayit) {
        super.onCreate(kayit);
        web = new WebView(this);
        web.setBackgroundColor(Color.parseColor("#0f1115"));
        WebSettings ayar = web.getSettings();
        ayar.setJavaScriptEnabled(true);
        ayar.setDomStorageEnabled(true);
        ayar.setCacheMode(WebSettings.LOAD_DEFAULT);
        web.setWebViewClient(new WebViewClient() {
            @Override
            public boolean shouldOverrideUrlLoading(WebView v, WebResourceRequest istek) {
                Uri u = istek.getUrl();
                if (SITE.equals(u.getHost())) return false;
                startActivity(new Intent(Intent.ACTION_VIEW, u));   // dış bağlantılar tarayıcıda açılır
                return true;
            }

            @Override
            public void onReceivedError(WebView v, WebResourceRequest istek, WebResourceError hata) {
                if (istek.isForMainFrame()) {
                    v.loadDataWithBaseURL(null,
                        "<html><body style='background:#0f1115;color:#e8eaf0;font-family:sans-serif;"
                        + "padding:40px 24px;text-align:center'><h2>İnternet bağlantısı yok</h2>"
                        + "<p>Bağlantı gelince aşağıdaki düğmeye bas.</p>"
                        + "<p><a style='color:#3ecf8e;font-size:18px' href='" + ADRES + "'>Yeniden dene</a></p>"
                        + "</body></html>", "text/html", "utf-8", null);
                }
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
