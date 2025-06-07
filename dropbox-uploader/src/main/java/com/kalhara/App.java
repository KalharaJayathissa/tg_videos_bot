package com.kalhara;

import com.dropbox.core.DbxRequestConfig;
import com.dropbox.core.v2.DbxClientV2;
import com.dropbox.core.v2.files.WriteMode;
import com.dropbox.core.v2.files.FileMetadata;

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

public class App {

    // Your Dropbox App key & secret
    private static final String APP_KEY = "";
    private static final String APP_SECRET = "";

    // Stored refresh token (from your JSON)
    private static final String REFRESH_TOKEN = "";

    // Hold the current access token here
    private static String accessToken = "";
    // Store token expiration timestamp (epoch ms)
    private static long accessTokenExpiry = 0;

    public static void main(String[] args) {
        ScheduledExecutorService scheduler = Executors.newSingleThreadScheduledExecutor();

        scheduler.scheduleAtFixedRate(() -> {
            try {
                // Refresh access token if expired or near expiry (say 1 min before)
                if (System.currentTimeMillis() > accessTokenExpiry - 60_000) {
                    System.out.println("Refreshing access token...");
                    refreshAccessToken();
                }
                // Proceed to upload files
                uploadAll();
                System.out.println("Scheduled upload completed at: " + System.currentTimeMillis());
            } catch (Exception e) {
                System.err.println("Error during scheduled upload: " + e.getMessage());
                e.printStackTrace();
            }
        }, 0, 30, TimeUnit.MINUTES);
    }

    public static void refreshAccessToken() throws IOException {
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
                throw new IOException("Failed to refresh token. HTTP " + responseCode + ": " + errorResponse.toString());
            }
        }
    }

    public static void uploadFileToDropbox(String localFilePath, String dropboxPath) {
        File file = new File(localFilePath);
        if (!file.exists()) {
            System.out.println("File does not exist: " + file.getAbsolutePath());
            return;
        } else {
            System.out.println("File exists: " + file.getAbsolutePath());
        }

        DbxRequestConfig config = DbxRequestConfig.newBuilder("dropbox/java-uploader").build();
        DbxClientV2 client = new DbxClientV2(config, accessToken);

        try (InputStream inputStream = new FileInputStream(localFilePath)) {
            FileMetadata metadata = client.files().uploadBuilder(dropboxPath)
                    .withMode(WriteMode.OVERWRITE)
                    .uploadAndFinish(inputStream);
            System.out.println("File uploaded successfully: " + metadata.getPathLower());
        } catch (Exception e) {
            System.err.println("Error uploading file: " + e.getMessage());
            e.printStackTrace();
        }
    }

    public static void uploadAll() {
        String[] files = {
                "videos.json",
                "video_stats.json",
                "stickers.json",
                "valid_users.json",
                "add_valid_users.txt",
                "users_info.json"
        };

        for (String file : files) {
            String localFilePath = file;
            String dropboxPath = "/tg_bot_files/" + file;
            uploadFileToDropbox(localFilePath, dropboxPath);
        }

        System.out.println("Upload completed.");
        System.out.println("You can check the file at https://www.dropbox.com/home/tg_bot_files");
    }
}
