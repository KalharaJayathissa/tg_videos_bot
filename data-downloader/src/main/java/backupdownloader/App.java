package backupdownloader;

import com.dropbox.core.DbxException;
import com.dropbox.core.DbxRequestConfig;
import com.dropbox.core.v2.DbxClientV2;
import com.dropbox.core.v2.files.WriteMode;
import com.dropbox.core.v2.files.FileMetadata;
import com.dropbox.core.v2.files.ListFolderResult;
import com.dropbox.core.v2.files.Metadata;

import java.io.*;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URI;
import java.nio.charset.StandardCharsets;
import java.util.Base64;
import java.util.concurrent.Executors;
import java.util.concurrent.ScheduledExecutorService;
import java.util.concurrent.TimeUnit;

import com.google.gson.JsonObject;
import com.google.gson.JsonParser;

/**
 * Hello world!
 */
public class App {

    private static final String APP_KEY = "";
    private static final String APP_SECRET = "";

    private static final String REFRESH_TOKEN = "";

    private static String accessToken;
    private static long accessTokenExpiry;

    public static String refreshAccessToken() throws IOException {
        URI uri = URI.create("https://api.dropboxapi.com/oauth2/token");
        URL url = uri.toURL();
        HttpURLConnection conn = (HttpURLConnection) url.openConnection();
        conn.setRequestMethod("POST");
        conn.setDoOutput(true);

        // Basic Auth Header with app key & secret
        String auth = APP_KEY + ":" + APP_SECRET;
        String encodedAuth = Base64.getEncoder().encodeToString(auth.getBytes(StandardCharsets.UTF_8));
        conn.setRequestProperty("Authorization", "Basic " + encodedAuth);
        conn.setRequestProperty("Content-Type", "application/x-www-form-urlencoded");

        // POST body parameters
        String body = "grant_type=refresh_token&refresh_token=" + REFRESH_TOKEN;

        try (OutputStream os = conn.getOutputStream()) {
            os.write(body.getBytes(StandardCharsets.UTF_8));
            os.flush();
        }

        int responseCode = conn.getResponseCode();
        if (responseCode == 200) {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getInputStream()))) {
                StringBuilder response = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    response.append(line);
                }

                // Parse JSON response using Gson
                JsonObject jsonObject = JsonParser.parseString(response.toString()).getAsJsonObject();
                accessToken = jsonObject.get("access_token").getAsString();
                int expiresIn = jsonObject.get("expires_in").getAsInt();

                // Set new expiry time (current time + expiresIn seconds)
                accessTokenExpiry = System.currentTimeMillis() + expiresIn * 1000L;

                System.out.println("Access token refreshed. Expires in " + expiresIn + " seconds.");
            }
        } else {
            try (BufferedReader reader = new BufferedReader(new InputStreamReader(conn.getErrorStream()))) {
                StringBuilder errorResponse = new StringBuilder();
                String line;
                while ((line = reader.readLine()) != null) {
                    errorResponse.append(line);
                }
                throw new IOException(
                        "Failed to refresh token. HTTP " + responseCode + ": " + errorResponse.toString());
            }
        }
        return accessToken;
    }

    public static void DownloadFile(String DOWNLOAD_PATH, String DROPBOX_PATH) {
        DbxRequestConfig config = DbxRequestConfig.newBuilder("dropbox/java-uploader").build();

        DbxClientV2 client = new DbxClientV2(config, accessToken);

        try (OutputStream outputStream = new FileOutputStream(DOWNLOAD_PATH)) {

            FileMetadata metadata = client.files().downloadBuilder(DROPBOX_PATH).download(outputStream);
            System.out.println("successful");

        } catch (Exception e) {
            System.out.println("error occurred");
            e.printStackTrace();
        }

    }

    public static void downloadAll() {
        String[] FileNames = {
                "videos.json",
                "video_stats.json",
                "stickers.json",
                "valid_users.json",
                "add_valid_users.txt",
                "users_info.json"
        };
        for (String file : FileNames) {
            String dropboxPath = "/Apps/tg_bot_files/tg_bot_files/" + file;
            // file name will be the download path by default
            DownloadFile(file, dropboxPath);
            System.out.println(file + " : successfully downloaded");
        }
    }

    public static void main(String[] args) {

        try {
            accessToken = refreshAccessToken();
        } catch (Exception e) {
            System.out.println("access token refreshing faild!");
            e.printStackTrace();
        }

        downloadAll();
        try {
            Thread.sleep(20000);
        } catch (Exception e) {
            System.out.println("thread sleep error");
        }

    }
}
